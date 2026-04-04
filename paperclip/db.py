from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    requester_id TEXT NOT NULL,
    requester_display_name TEXT NOT NULL,
    state TEXT NOT NULL,
    request_payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS task_results (
    task_id TEXT PRIMARY KEY,
    result_payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);
"""


class PaperclipDB:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def create_task(self, record: dict) -> None:
        self.conn.execute(
            """
            INSERT INTO tasks (
                id, schema_version, type, title, description, priority, risk_level,
                requester_id, requester_display_name, state, request_payload,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                record["state"],
                json.dumps(record["request_payload"]),
                record["created_at"],
                record["updated_at"],
            ),
        )
        self.conn.commit()

    def get_task(self, task_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["request_payload"] = json.loads(data["request_payload"])
        return data

    def update_task_state(self, task_id: str, state: str, updated_at: str) -> None:
        self.conn.execute(
            "UPDATE tasks SET state = ?, updated_at = ? WHERE id = ?",
            (state, updated_at, task_id),
        )
        self.conn.commit()

    def add_audit_event(self, task_id: str, event_type: str, actor: str, payload: dict, created_at: str) -> None:
        self.conn.execute(
            "INSERT INTO audit_events (task_id, event_type, actor, payload_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (task_id, event_type, actor, json.dumps(payload), created_at),
        )
        self.conn.commit()

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

    def store_result(self, task_id: str, payload: dict, created_at: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO task_results (task_id, result_payload, created_at) VALUES (?, ?, ?)",
            (task_id, json.dumps(payload), created_at),
        )
        self.conn.commit()

    def get_result(self, task_id: str) -> dict | None:
        row = self.conn.execute("SELECT result_payload, created_at FROM task_results WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            return None
        return {
            "payload": json.loads(row["result_payload"]),
            "created_at": row["created_at"],
        }
