from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hermes.memory.provenance import extract_memory_provenance
from paperclip.db import PaperclipDB
from paperclip.dispatch import HermesDispatchClient
from paperclip.state_machine import assert_transition
from scripts.contracts import validate_payload
from scripts.storage_layout import PaperclipStorageLayout
from scripts.trace_log import TraceLogger


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PaperclipService:
    def __init__(self, db_path: Path, dispatch_client: HermesDispatchClient | None = None):
        self.db = PaperclipDB(db_path)
        self.dispatch_client = dispatch_client or HermesDispatchClient()
        self.traces = TraceLogger(db_path.parent.parent if db_path.parent.name == 'data' else db_path.parent)
        self.storage = PaperclipStorageLayout(db_path.parent.parent if db_path.parent.name == 'data' else db_path.parent)
        self.approval_ttl_seconds = int(os.environ.get("PAPERCLIP_APPROVAL_TTL_SECONDS", "3600"))
        self.queue_max_attempts = int(os.environ.get("PAPERCLIP_QUEUE_MAX_ATTEMPTS", "3"))
        self.queue_backoff_seconds = int(os.environ.get("PAPERCLIP_QUEUE_BACKOFF_SECONDS", "5"))
        self.queue_timeout_seconds = int(os.environ.get("PAPERCLIP_QUEUE_TIMEOUT_SECONDS", "300"))
        self.queue_lease_seconds = int(os.environ.get("PAPERCLIP_QUEUE_LEASE_SECONDS", "60"))

    def submit_task(self, payload: dict, tenant_context: dict | None = None, idempotency_key: str | None = None) -> dict:
        if idempotency_key:
            existing_task_id = self.db.get_idempotent_task_id(idempotency_key)
            if existing_task_id:
                existing_task = self.get_task(existing_task_id)
                if existing_task is not None:
                    return existing_task

        errors = validate_payload("task_request_v1.json", payload)
        if errors:
            raise ValueError("; ".join(errors))

        task = payload["task"]
        approval = payload["execution_policy"]["approval"]
        created_at = utcnow()
        initial_state = "received"
        tenant_context = tenant_context or {}
        self.db.create_task(
            {
                "id": task["id"],
                "schema_version": payload["schema_version"],
                "type": task["type"],
                "title": task["title"],
                "description": task["description"],
                "priority": task["priority"],
                "risk_level": task["risk_level"],
                "requester_id": task["requester"]["id"],
                "requester_display_name": task["requester"]["display_name"],
                "tenant_id": tenant_context.get("tenant_id", ""),
                "org_id": tenant_context.get("org_id", ""),
                "client_id": tenant_context.get("client_id", ""),
                "state": initial_state,
                "approval_status": approval["status"],
                "request_payload": payload,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
        self.db.add_audit_event(task["id"], "task_received", "paperclip", {"state": initial_state}, created_at)
        if idempotency_key:
            self.db.create_idempotency_record(idempotency_key, task["id"], created_at)
            self.db.add_audit_event(task["id"], "idempotency_key_recorded", "paperclip", {"idempotency_key": idempotency_key}, created_at)
        if approval["required"]:
            self.db.add_audit_event(task["id"], "approval_requested", "paperclip", {"approval_status": approval["status"]}, created_at)
        self.traces.record(payload["trace"]["trace_id"], "paperclip", "task_submitted", task_id=task["id"], state=initial_state)

        self.transition_task(task["id"], "validating", actor="paperclip", details={"schema_version": payload["schema_version"]})
        next_state = "pending_approval" if approval["required"] and approval["status"] != "approved" else "approved"
        self.transition_task(task["id"], next_state, actor="paperclip", details={"approval_status": approval["status"]})
        if next_state == "approved":
            self.enqueue_task(task["id"], correlation_id=payload.get("trace", {}).get("trace_id"))
            self.process_queue(task["id"])
        return self.get_task(task["id"])

    def transition_task(self, task_id: str, target_state: str, actor: str, details: dict | None = None) -> dict:
        task = self.db.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        assert_transition(task["state"], target_state)
        updated_at = utcnow()
        approval_status = None
        if target_state == "pending_approval":
            approval_status = "pending"
        elif target_state == "approved":
            approval_status = "approved"
        elif target_state == "rejected":
            approval_status = "rejected"
        def operations(db):
            db.update_task_state(task_id, target_state, updated_at, approval_status=approval_status)
            db.add_audit_event(
                task_id,
                f"state_changed:{task['state']}->{target_state}",
                actor,
                details or {},
                updated_at,
            )
            if target_state == "approved":
                db.add_audit_event(task_id, "approval_granted", actor, details or {}, updated_at)
            elif target_state == "rejected":
                db.add_audit_event(task_id, "approval_rejected", actor, details or {}, updated_at)

        self.db.run_in_transaction(operations)
        return self.get_task(task_id)

    def enqueue_task(self, task_id: str, correlation_id: str | None = None) -> dict:
        task = self.db.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        if task["state"] != "approved":
            raise ValueError(f"task must be approved before queueing: {task_id}")
        queued = self.transition_task(task_id, "queued", actor="paperclip", details={"queue": "sqlite"})
        queued_at = utcnow()
        self.db.enqueue_task(task_id, correlation_id, queued_at, max_attempts=self.queue_max_attempts)
        self.db.add_audit_event(task_id, "task_enqueued", "paperclip", {"correlation_id": correlation_id}, queued_at)
        return queued

    def _queue_backoff_seconds(self, attempt_count: int) -> int:
        return self.queue_backoff_seconds * (2 ** max(0, attempt_count - 1))

    def claim_queue_item(self, task_id: str, worker_id: str, now: datetime | None = None) -> dict:
        queue_item = self.db.get_queue_item(task_id)
        if queue_item is None:
            raise KeyError(task_id)
        now = now or datetime.now(timezone.utc)
        lease_expires_at = queue_item.get("lease_expires_at")
        current_worker = queue_item.get("worker_id")
        if current_worker and lease_expires_at:
            lease_deadline = datetime.fromisoformat(lease_expires_at.replace("Z", "+00:00"))
            if lease_deadline > now and current_worker != worker_id:
                raise ValueError(f"queue item already leased by {current_worker}")
        updated_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        new_lease_expires_at = (now + timedelta(seconds=self.queue_lease_seconds)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        self.db.claim_queue_item(task_id, worker_id, new_lease_expires_at, updated_at)
        self.db.add_audit_event(task_id, "task_claimed", worker_id, {"lease_expires_at": new_lease_expires_at}, updated_at)
        return self.get_task(task_id)

    def process_queue(self, task_id: str, now: datetime | None = None, worker_id: str | None = None) -> dict:
        queue_item = self.db.get_queue_item(task_id)
        if queue_item is None:
            raise KeyError(task_id)
        if queue_item["status"] != "queued":
            return self.get_task(task_id)
        now = now or datetime.now(timezone.utc)
        next_attempt_at = queue_item.get("next_attempt_at")
        if next_attempt_at:
            scheduled = datetime.fromisoformat(next_attempt_at.replace("Z", "+00:00"))
            if scheduled > now:
                return self.get_task(task_id)
        if worker_id is not None:
            self.claim_queue_item(task_id, worker_id=worker_id, now=now)
            queue_item = self.db.get_queue_item(task_id)
        try:
            return self.dispatch_task(task_id, correlation_id=queue_item.get("correlation_id"), worker_id=worker_id)
        except Exception as exc:
            attempt_count = int(queue_item.get("attempt_count", 0)) + 1
            updated_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
            if attempt_count >= int(queue_item.get("max_attempts", self.queue_max_attempts)):
                self.db.mark_queue_dead_letter(task_id, attempt_count, str(exc), updated_at)
                self.transition_task(task_id, "failed", actor="paperclip", details={"reason": "dead_letter", "error": str(exc)})
                self.db.add_audit_event(
                    task_id,
                    "task_dead_lettered",
                    "paperclip",
                    {"attempt_count": attempt_count, "error": str(exc)},
                    updated_at,
                )
                return self.get_task(task_id)
            self.db.update_task_state(task_id, "queued", utcnow())
            backoff_seconds = self._queue_backoff_seconds(attempt_count)
            next_retry_at = (now + timedelta(seconds=backoff_seconds)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            self.db.mark_queue_retry(task_id, attempt_count, next_retry_at, str(exc), updated_at)
            self.db.add_audit_event(
                task_id,
                "task_retry_scheduled",
                "paperclip",
                {"attempt_count": attempt_count, "next_attempt_at": next_retry_at, "error": str(exc)},
                updated_at,
            )
            return self.get_task(task_id)

    def dispatch_task(self, task_id: str, correlation_id: str | None = None, worker_id: str | None = None) -> dict:
        task = self.db.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        if task["state"] == "approved":
            self.enqueue_task(task_id, correlation_id=correlation_id)
            task = self.db.get_task(task_id)
        if task is None or task["state"] != "queued":
            raise ValueError(f"task must be queued before dispatch: {task_id}")
        queue_item = self.db.get_queue_item(task_id)
        if worker_id is not None and (queue_item is None or queue_item.get("worker_id") != worker_id):
            raise ValueError(f"task must be leased by worker before dispatch: {task_id}")
        self.transition_task(task_id, "running", actor="paperclip", details={"dispatch": "hermes"})
        started_at = utcnow()
        timeout_at = (datetime.fromisoformat(started_at.replace("Z", "+00:00")) + timedelta(seconds=self.queue_timeout_seconds)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        self.db.mark_queue_running(task_id, started_at, timeout_at, started_at)
        self.db.mark_queue_dispatched(task_id, utcnow())
        trace_id = correlation_id or task["request_payload"].get("trace", {}).get("trace_id")
        if trace_id:
            self.traces.record(trace_id, "paperclip", "task_dispatched", task_id=task_id)
        self.dispatch_client.submit(task["request_payload"], correlation_id=trace_id)
        return self.get_task(task_id)

    def record_result(self, task_id: str, result: dict) -> dict:
        existing_result = self.db.get_result(task_id)
        if existing_result is not None:
            existing_task = self.get_task(task_id)
            if existing_task is None:
                raise KeyError(task_id)
            return existing_task

        task = self.db.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        if task["state"] == "cancelled":
            self.db.add_audit_event(task_id, "result_ignored_after_cancellation", "paperclip", {"run_status": result.get("run", {}).get("status")}, utcnow())
            existing_task = self.get_task(task_id)
            if existing_task is None:
                raise KeyError(task_id)
            return existing_task

        status = result["run"]["status"]
        target_state = "succeeded" if status == "succeeded" else "failed"
        memory_provenance = extract_memory_provenance(result)
        transition_details = {"run_status": status}
        if memory_provenance is not None:
            transition_details["memory_provenance"] = memory_provenance
        self.transition_task(task_id, target_state, actor="hermes", details=transition_details)
        created_at = utcnow()
        self.db.store_result_with_audit(task_id, result, status, created_at)
        if memory_provenance is not None:
            self.db.add_audit_event(task_id, "memory_provenance_recorded", "paperclip", memory_provenance, created_at)
        self.storage.persist_result(task_id, result)
        trace_id = (result.get("trace") or {}).get("trace_id")
        if trace_id:
            self.traces.record(trace_id, "paperclip", "result_recorded", task_id=task_id, status=status)
        return self.get_task(task_id)

    def cancel_task(self, task_id: str, actor: str = "operator", reason: str = "cancelled") -> dict | None:
        task = self.db.get_task(task_id)
        if task is None:
            return None
        if task["state"] == "cancelled":
            return self.get_task(task_id)
        if task["state"] in {"succeeded", "failed", "rejected"}:
            raise ValueError(f"task cannot be cancelled from terminal state: {task['state']}")

        updated_at = utcnow()
        queue_item = self.db.get_queue_item(task_id)
        self.db.update_task_state(task_id, "cancelled", updated_at)
        if queue_item is not None:
            self.db.mark_queue_cancelled(task_id, updated_at, last_error=reason)
        self.db.add_audit_event(task_id, "task_cancelled", actor, {"reason": reason, "previous_state": task["state"]}, updated_at)
        return self.get_task(task_id)

    def list_tasks_for_tenant(self, tenant_id: str) -> list[dict]:
        tasks = []
        for task in self.db.list_tasks():
            if task.get("tenant_id") != tenant_id:
                continue
            hydrated = self.get_task(task["id"])
            if hydrated is not None:
                tasks.append(hydrated)
        return tasks

    def get_task(self, task_id: str) -> dict | None:
        task = self.db.get_task(task_id)
        if task is None:
            return None
        result = self.db.get_result(task_id)
        response = {
            "id": task["id"],
            "schema_version": task["schema_version"],
            "type": task["type"],
            "title": task["title"],
            "description": task["description"],
            "priority": task["priority"],
            "risk_level": task["risk_level"],
            "requester": {
                "id": task["requester_id"],
                "display_name": task["requester_display_name"],
            },
            "tenant": {
                "tenant_id": task["tenant_id"],
                "org_id": task["org_id"],
                "client_id": task["client_id"],
            },
            "state": task["state"],
            "approval_status": task["approval_status"],
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
        }
        if result is not None:
            response["result"] = result["payload"]
        return response

    def get_audit(self, task_id: str) -> list[dict]:
        return self.db.get_audit_events(task_id)

    def list_recoverable_stuck_jobs(self, now: datetime | None = None) -> list[dict]:
        now = now or datetime.now(timezone.utc)
        recoverable: list[dict] = []
        for item in self.db.list_queue_items(status="running"):
            worker_id = item.get("worker_id")
            lease_expires_at = item.get("lease_expires_at")
            if not worker_id or not lease_expires_at:
                continue
            deadline = datetime.fromisoformat(lease_expires_at.replace("Z", "+00:00"))
            if deadline <= now:
                recoverable.append(
                    {
                        "task_id": item["task_id"],
                        "worker_id": worker_id,
                        "lease_expires_at": lease_expires_at,
                    }
                )
        return recoverable

    def recover_stuck_job(self, task_id: str, actor: str = "operator", now: datetime | None = None) -> dict | None:
        task = self.db.get_task(task_id)
        queue_item = self.db.get_queue_item(task_id)
        if task is None or queue_item is None:
            return None
        now = now or datetime.now(timezone.utc)
        lease_expires_at = queue_item.get("lease_expires_at")
        worker_id = queue_item.get("worker_id")
        if not worker_id or not lease_expires_at:
            return None
        deadline = datetime.fromisoformat(lease_expires_at.replace("Z", "+00:00"))
        if deadline > now:
            return None
        updated_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        self.db.reset_queue_to_queued(task_id, updated_at)
        self.db.update_task_state(task_id, "queued", updated_at)
        self.db.add_audit_event(task_id, "task_recovered_from_stuck", actor, {"previous_worker_id": worker_id}, updated_at)
        return self.get_task(task_id)

    def enforce_timeouts(self, now: datetime | None = None) -> list[dict]:
        now = now or datetime.now(timezone.utc)
        timed_out: list[dict] = []
        for item in self.db.list_queue_items(status="running"):
            timeout_at = item.get("timeout_at")
            if not timeout_at:
                continue
            deadline = datetime.fromisoformat(timeout_at.replace("Z", "+00:00"))
            if deadline <= now:
                updated_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
                self.db.mark_queue_timed_out(item["task_id"], "queue timeout exceeded", updated_at)
                self.transition_task(item["task_id"], "failed", actor="paperclip", details={"reason": "timeout"})
                self.db.add_audit_event(item["task_id"], "task_timed_out", "paperclip", {"timeout_at": timeout_at}, updated_at)
                timed_out.append({"task_id": item["task_id"], "timeout_at": timeout_at})
        return timed_out

    def get_queue(self, status: str | None = None) -> list[dict]:
        return self.db.list_queue_items(status=status)

    def list_retention_candidates(self, older_than: datetime) -> list[dict]:
        candidates: list[dict] = []
        for task in self.db.list_tasks():
            created_at = datetime.fromisoformat(task["created_at"].replace("Z", "+00:00"))
            if created_at <= older_than and task["state"] in {"succeeded", "failed", "rejected"}:
                candidates.append(
                    {
                        "task_id": task["id"],
                        "state": task["state"],
                        "created_at": task["created_at"],
                    }
                )
        return candidates

    def delete_task(self, task_id: str, actor: str = "operator") -> bool:
        task = self.db.get_task(task_id)
        if task is None:
            return False
        self.db.delete_task_data(task_id)
        self.storage.delete_task_storage(task_id)
        return True

    def get_approval_audit(self, task_id: str) -> list[dict]:
        return [
            event
            for event in self.db.get_audit_events(task_id)
            if event["event_type"] in {"approval_requested", "approval_granted", "approval_rejected", "approval_expired"}
        ]

    def find_expired_approvals(self, now: datetime | None = None) -> list[dict]:
        now = now or datetime.now(timezone.utc)
        expired: list[dict] = []
        for task in self.db.list_tasks():
            if task["state"] != "pending_approval":
                continue
            updated_at = datetime.fromisoformat(task["updated_at"].replace("Z", "+00:00"))
            if updated_at + timedelta(seconds=self.approval_ttl_seconds) <= now:
                expired.append(
                    {
                        "task_id": task["id"],
                        "state": task["state"],
                        "approval_status": task.get("approval_status") or "unknown",
                        "updated_at": task["updated_at"],
                    }
                )
                self.db.add_audit_event(task["id"], "approval_expired", "paperclip", {"updated_at": task["updated_at"]}, now.isoformat().replace("+00:00", "Z"))
        return expired

    def reconcile_approval_status(self) -> list[dict]:
        mismatches: list[dict] = []
        for task in self.db.list_tasks():
            state = task["state"]
            approval_status = task.get("approval_status") or "unknown"
            ok = True
            if state == "pending_approval":
                ok = approval_status == "pending"
            elif state == "approved":
                ok = approval_status in {"approved", "not_required"}
            elif state == "rejected":
                ok = approval_status == "rejected"
            if not ok:
                mismatches.append(
                    {
                        "task_id": task["id"],
                        "state": state,
                        "approval_status": approval_status,
                    }
                )
        return mismatches

    def list_stuck_approval_tasks(self, now: datetime | None = None) -> list[dict]:
        by_task_id = {}
        for item in self.reconcile_approval_status():
            by_task_id[item["task_id"]] = {**item, "reason": "state_mismatch"}
        for item in self.find_expired_approvals(now=now):
            by_task_id[item["task_id"]] = {**item, "reason": "expired_pending_approval"}
        return list(by_task_id.values())

    def recover_stuck_approval(self, task_id: str, actor: str = "operator") -> dict | None:
        task = self.db.get_task(task_id)
        if task is None:
            return None
        updated_at = utcnow()
        self.db.update_task_state(task_id, "pending_approval", updated_at, approval_status="pending")
        self.db.add_audit_event(task_id, "approval_recovery_reset_pending", actor, {"from_state": task["state"], "from_approval_status": task.get("approval_status")}, updated_at)
        return self.get_task(task_id)


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    service = PaperclipService(root / "data" / "paperclip.sqlite3")
    payload = json.loads((root / "fixtures" / "task_request_valid.json").read_text())
    task = service.submit_task(payload)
    print(json.dumps(task, indent=2))
    print(json.dumps(service.get_audit(task["id"]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
