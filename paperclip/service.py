from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from paperclip.db import PaperclipDB
from paperclip.dispatch import HermesDispatchClient
from paperclip.state_machine import assert_transition
from scripts.contracts import validate_payload
from scripts.trace_log import TraceLogger


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PaperclipService:
    def __init__(self, db_path: Path, dispatch_client: HermesDispatchClient | None = None):
        self.db = PaperclipDB(db_path)
        self.dispatch_client = dispatch_client or HermesDispatchClient()
        self.traces = TraceLogger(db_path.parent.parent if db_path.parent.name == 'data' else db_path.parent)
        self.approval_ttl_seconds = int(os.environ.get("PAPERCLIP_APPROVAL_TTL_SECONDS", "3600"))

    def submit_task(self, payload: dict) -> dict:
        errors = validate_payload("task_request_v1.json", payload)
        if errors:
            raise ValueError("; ".join(errors))

        task = payload["task"]
        approval = payload["execution_policy"]["approval"]
        created_at = utcnow()
        initial_state = "received"
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
                "state": initial_state,
                "approval_status": approval["status"],
                "request_payload": payload,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
        self.db.add_audit_event(task["id"], "task_received", "paperclip", {"state": initial_state}, created_at)
        self.traces.record(payload["trace"]["trace_id"], "paperclip", "task_submitted", task_id=task["id"], state=initial_state)

        self.transition_task(task["id"], "validating", actor="paperclip", details={"schema_version": payload["schema_version"]})
        next_state = "pending_approval" if approval["required"] and approval["status"] != "approved" else "approved"
        self.transition_task(task["id"], next_state, actor="paperclip", details={"approval_status": approval["status"]})
        if next_state == "approved":
            self.dispatch_task(task["id"], correlation_id=payload.get("trace", {}).get("trace_id"))
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
        self.db.update_task_state(task_id, target_state, updated_at, approval_status=approval_status)
        self.db.add_audit_event(
            task_id,
            f"state_changed:{task['state']}->{target_state}",
            actor,
            details or {},
            updated_at,
        )
        return self.get_task(task_id)

    def dispatch_task(self, task_id: str, correlation_id: str | None = None) -> dict:
        task = self.db.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        if task["state"] != "approved":
            raise ValueError(f"task must be approved before dispatch: {task_id}")
        self.transition_task(task_id, "queued", actor="paperclip", details={"dispatch": "hermes"})
        self.transition_task(task_id, "running", actor="paperclip", details={"dispatch": "hermes"})
        trace_id = correlation_id or task["request_payload"].get("trace", {}).get("trace_id")
        if trace_id:
            self.traces.record(trace_id, "paperclip", "task_dispatched", task_id=task_id)
        self.dispatch_client.submit(task["request_payload"], correlation_id=trace_id)
        return self.get_task(task_id)

    def record_result(self, task_id: str, result: dict) -> dict:
        status = result["run"]["status"]
        target_state = "succeeded" if status == "succeeded" else "failed"
        self.transition_task(task_id, target_state, actor="hermes", details={"run_status": status})
        created_at = utcnow()
        self.db.store_result(task_id, result, created_at)
        self.db.add_audit_event(task_id, "result_recorded", "paperclip", {"status": status}, created_at)
        trace_id = (result.get("trace") or {}).get("trace_id")
        if trace_id:
            self.traces.record(trace_id, "paperclip", "result_recorded", task_id=task_id, status=status)
        return self.get_task(task_id)

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

    def find_expired_approvals(self, now: datetime | None = None) -> list[dict]:
        now = now or datetime.now(timezone.utc)
        expired: list[dict] = []
        for task in self.db.list_tasks():
            if task["state"] != "pending_approval":
                continue
            updated_at = datetime.fromisoformat(task["updated_at"].replace("Z", "+00:00"))
            if updated_at + timedelta(seconds=self.approval_ttl_seconds) < now:
                expired.append(
                    {
                        "task_id": task["id"],
                        "state": task["state"],
                        "approval_status": task.get("approval_status") or "unknown",
                        "updated_at": task["updated_at"],
                    }
                )
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
