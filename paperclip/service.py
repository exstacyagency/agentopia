from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from paperclip.db import PaperclipDB
from paperclip.state_machine import assert_transition
from scripts.contracts import validate_payload


def utcnow() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PaperclipService:
    def __init__(self, db_path: Path):
        self.db = PaperclipDB(db_path)

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
                "request_payload": payload,
                "created_at": created_at,
                "updated_at": created_at,
            }
        )
        self.db.add_audit_event(task["id"], "task_received", "paperclip", {"state": initial_state}, created_at)

        self.transition_task(task["id"], "validating", actor="paperclip", details={"schema_version": payload["schema_version"]})
        next_state = "pending_approval" if approval["required"] and approval["status"] != "approved" else "approved"
        self.transition_task(task["id"], next_state, actor="paperclip", details={"approval_status": approval["status"]})
        return self.get_task(task["id"])

    def transition_task(self, task_id: str, target_state: str, actor: str, details: dict | None = None) -> dict:
        task = self.db.get_task(task_id)
        if task is None:
            raise KeyError(task_id)
        assert_transition(task["state"], target_state)
        updated_at = utcnow()
        self.db.update_task_state(task_id, target_state, updated_at)
        self.db.add_audit_event(
            task_id,
            f"state_changed:{task['state']}->{target_state}",
            actor,
            details or {},
            updated_at,
        )
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> dict | None:
        task = self.db.get_task(task_id)
        if task is None:
            return None
        return {
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
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
        }

    def get_audit(self, task_id: str) -> list[dict]:
        return self.db.get_audit_events(task_id)


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
