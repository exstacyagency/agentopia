from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from paperclip.postgres_db import PostgresPaperclipDB
from scripts.migrations import apply_migrations


class PaperclipDB:
    def __init__(self, path: Path):
        database_url = os.environ.get("PAPERCLIP_DATABASE_URL", "")
        if database_url.startswith("postgres://") or database_url.startswith("postgresql://"):
            delegate = PostgresPaperclipDB(database_url)
            self.__dict__ = delegate.__dict__
            self.__class__ = delegate.__class__
            return
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        apply_migrations(self.path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def run_in_transaction(self, operations) -> None:
        with self.conn:
            operations(self)

    def create_task(self, record: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO tasks (
                id, schema_version, type, title, description, priority, risk_level,
                requester_id, requester_display_name, tenant_id, org_id, client_id, state, approval_status, request_payload,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["schema_version"],
                record["type"],
                record["title"],
                record["description"],
                record["priority"],
                record["risk_level"],
                record["requester_id"],
                record["requester_display_name"],
                record.get("tenant_id", ""),
                record.get("org_id", ""),
                record.get("client_id", ""),
                record["state"],
                record["approval_status"],
                json.dumps(record["request_payload"]),
                record["created_at"],
                record["updated_at"],
            ),
        )

    def get_task(self, task_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["request_payload"] = json.loads(data["request_payload"])
        return data

    def update_task_state(self, task_id: str, state: str, updated_at: str, approval_status: str | None = None) -> None:
        if approval_status is None:
            self.conn.execute(
                "UPDATE tasks SET state = ?, updated_at = ? WHERE id = ?",
                (state, updated_at, task_id),
            )
        else:
            self.conn.execute(
                "UPDATE tasks SET state = ?, approval_status = ?, updated_at = ? WHERE id = ?",
                (state, approval_status, updated_at, task_id),
            )

    def add_audit_event(self, task_id: str, event_type: str, actor: str, payload: dict, created_at: str) -> None:
        self.conn.execute(
            "INSERT INTO audit_events (task_id, event_type, actor, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (task_id, event_type, actor, json.dumps(payload), created_at),
        )

    def get_audit_events(self, task_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, task_id, event_type, actor, payload_json, created_at FROM audit_events WHERE task_id = ? ORDER BY id ASC",
            (task_id,),
        ).fetchall()
        events: list[dict] = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            events.append(item)
        return events

    def list_tasks(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY created_at ASC").fetchall()
        tasks: list[dict] = []
        for row in rows:
            data = dict(row)
            data["request_payload"] = json.loads(data["request_payload"])
            tasks.append(data)
        return tasks

    def enqueue_task(self, task_id: str, correlation_id: str | None, created_at: str, max_attempts: int = 3) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO task_queue (task_id, status, correlation_id, attempt_count, max_attempts, next_attempt_at, started_at, timeout_at, worker_id, lease_expires_at, last_error, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, "queued", correlation_id, 0, max_attempts, created_at, None, None, None, None, None, created_at, created_at),
        )

    def claim_queue_item(self, task_id: str, worker_id: str, lease_expires_at: str, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE task_queue SET worker_id = ?, lease_expires_at = ?, updated_at = ? WHERE task_id = ?",
            (worker_id, lease_expires_at, updated_at, task_id),
        )

    def mark_queue_running(self, task_id: str, started_at: str, timeout_at: str, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE task_queue SET status = ?, started_at = ?, timeout_at = ?, updated_at = ? WHERE task_id = ?",
            ("running", started_at, timeout_at, updated_at, task_id),
        )

    def mark_queue_timed_out(self, task_id: str, last_error: str, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE task_queue SET status = ?, last_error = ?, updated_at = ? WHERE task_id = ?",
            ("timed_out", last_error, updated_at, task_id),
        )

    def reset_queue_to_queued(self, task_id: str, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE task_queue SET status = ?, worker_id = NULL, lease_expires_at = NULL, started_at = NULL, timeout_at = NULL, updated_at = ? WHERE task_id = ?",
            ("queued", updated_at, task_id),
        )

    def mark_queue_retry(self, task_id: str, attempt_count: int, next_attempt_at: str, last_error: str, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE task_queue SET status = ?, attempt_count = ?, next_attempt_at = ?, last_error = ?, updated_at = ? WHERE task_id = ?",
            ("queued", attempt_count, next_attempt_at, last_error, updated_at, task_id),
        )

    def mark_queue_dead_letter(self, task_id: str, attempt_count: int, last_error: str, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE task_queue SET status = ?, attempt_count = ?, last_error = ?, updated_at = ? WHERE task_id = ?",
            ("dead_letter", attempt_count, last_error, updated_at, task_id),
        )

    def mark_queue_cancelled(self, task_id: str, updated_at: str, last_error: str = "cancelled") -> None:
        self.conn.execute(
            "UPDATE task_queue SET status = ?, last_error = ?, updated_at = ? WHERE task_id = ?",
            ("cancelled", last_error, updated_at, task_id),
        )

    def mark_queue_dispatched(self, task_id: str, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE task_queue SET status = ?, updated_at = ? WHERE task_id = ?",
            ("dispatched", updated_at, task_id),
        )

    def get_queue_item(self, task_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT task_id, status, correlation_id, attempt_count, max_attempts, next_attempt_at, started_at, timeout_at, worker_id, lease_expires_at, last_error, created_at, updated_at FROM task_queue WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        return dict(row) if row is not None else None

    def list_queue_items(self, status: str | None = None) -> list[dict]:
        if status is None:
            rows = self.conn.execute(
                "SELECT task_id, status, correlation_id, attempt_count, max_attempts, next_attempt_at, started_at, timeout_at, worker_id, lease_expires_at, last_error, created_at, updated_at FROM task_queue ORDER BY created_at ASC"
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT task_id, status, correlation_id, attempt_count, max_attempts, next_attempt_at, started_at, timeout_at, worker_id, lease_expires_at, last_error, created_at, updated_at FROM task_queue WHERE status = ? ORDER BY created_at ASC",
                (status,),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_idempotency_record(self, idempotency_key: str, task_id: str, created_at: str) -> None:
        self.conn.execute(
            "INSERT INTO task_idempotency (idempotency_key, task_id, created_at) VALUES (?, ?, ?)",
            (idempotency_key, task_id, created_at),
        )

    def get_idempotent_task_id(self, idempotency_key: str) -> str | None:
        row = self.conn.execute(
            "SELECT task_id FROM task_idempotency WHERE idempotency_key = ?",
            (idempotency_key,),
        ).fetchone()
        return row["task_id"] if row is not None else None

    def store_result(self, task_id: str, payload: dict, created_at: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO task_results (task_id, result_payload, created_at) VALUES (?, ?, ?)",
            (task_id, json.dumps(payload), created_at),
        )

    def get_result(self, task_id: str) -> dict | None:
        row = self.conn.execute("SELECT result_payload, created_at FROM task_results WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        return {
            "payload": json.loads(row["result_payload"]),
            "created_at": row["created_at"],
        }

    def delete_task_data(self, task_id: str) -> None:
        def operations(db: PaperclipDB) -> None:
            db.conn.execute("DELETE FROM task_idempotency WHERE task_id = ?", (task_id,))
            db.conn.execute("DELETE FROM task_results WHERE task_id = ?", (task_id,))
            db.conn.execute("DELETE FROM task_queue WHERE task_id = ?", (task_id,))
            db.conn.execute("DELETE FROM audit_events WHERE task_id = ?", (task_id,))
            db.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

        self.run_in_transaction(operations)

    def transition_task_with_audit(self, task_id: str, state: str, updated_at: str, actor: str, details: dict, approval_status: str | None = None) -> None:
        def operations(db: PaperclipDB) -> None:
            db.update_task_state(task_id, state, updated_at, approval_status=approval_status)
            db.add_audit_event(task_id, f"state_changed", actor, {"state": state, **details}, updated_at)

        self.run_in_transaction(operations)

    def store_result_with_audit(self, task_id: str, result: dict, status: str, created_at: str) -> None:
        def operations(db: PaperclipDB) -> None:
            db.store_result(task_id, result, created_at)
            db.add_audit_event(task_id, "result_recorded", "paperclip", {"status": status}, created_at)

        self.run_in_transaction(operations)
