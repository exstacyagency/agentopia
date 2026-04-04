#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService
from scripts.contracts import validate_payload

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
SUCCESS_RESULT = {
    "schema_version": "v1",
    "task_id": "task_123",
    "run": {
        "run_id": "run_task_123",
        "status": "succeeded",
        "started_at": "2026-04-04T18:00:00Z",
        "finished_at": "2026-04-04T18:00:00Z",
        "runtime_seconds": 0,
    },
    "result": {
        "summary": "ok",
        "output_format": "markdown",
        "output": "# ok",
        "notes": [],
        "error": None,
    },
    "artifacts": [],
    "usage": {
        "actual_cost_usd": 0.0,
        "model_provider": "local",
        "model_name": "test",
        "tool_calls": 0,
    },
    "trace": {
        "trace_id": "trace_abc123",
        "reported_at": "2026-04-04T18:00:00Z",
    },
}


class FakeDispatchClient:
    def __init__(self, result: dict):
        self.result = result
        self.service: PaperclipService | None = None

    def submit(self, payload: dict) -> dict:
        assert self.service is not None
        self.service.record_result(payload["task"]["id"], self.result)
        return self.result


class IntegrationFlowTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def make_service(self, db_path: Path) -> PaperclipService:
        dispatch = FakeDispatchClient(SUCCESS_RESULT)
        service = PaperclipService(db_path, dispatch_client=dispatch)
        dispatch.service = service
        return service

    def test_approved_task_runs_end_to_end_through_dispatch_client(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self.make_service(Path(tmp) / "paperclip.sqlite3")
            task = service.submit_task(self.load_fixture("task_request_valid.json"))
            self.assertEqual(task["state"], "succeeded")
            self.assertIn("result", task)
            errors = validate_payload("task_result_v1.json", task["result"])
            self.assertEqual(errors, [])
            audit = service.get_audit("task_123")
            event_types = [event["event_type"] for event in audit]
            self.assertIn("result_recorded", event_types)

    def test_pending_approval_does_not_dispatch_until_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self.make_service(Path(tmp) / "paperclip.sqlite3")
            payload = self.load_fixture("task_request_valid.json")
            payload["task"]["id"] = "task_pending"
            payload["execution_policy"]["approval"] = {"required": True, "status": "pending"}
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "pending_approval")
            self.assertNotIn("result", task)
            service.transition_task("task_pending", "approved", actor="human", details={"action": "approve"})
            updated = service.dispatch_task("task_pending")
            self.assertEqual(updated["state"], "succeeded")
            self.assertIn("result", updated)


if __name__ == "__main__":
    unittest.main()
