#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService


class FakeDispatchClient:
    def __init__(self, result: dict):
        self.result = result
        self.service: PaperclipService | None = None

    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        assert self.service is not None
        self.service.record_result(payload["task"]["id"], self.result)
        return self.result

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


class PaperclipServiceTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def make_service(self, db_path: Path) -> PaperclipService:
        dispatch = FakeDispatchClient(SUCCESS_RESULT)
        service = PaperclipService(db_path, dispatch_client=dispatch)
        dispatch.service = service
        return service

    def test_submit_task_persists_and_runs_to_succeeded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self.make_service(Path(tmp) / "paperclip.sqlite3")
            task = service.submit_task(self.load_fixture("task_request_valid.json"))
            self.assertEqual(task["id"], "task_123")
            self.assertEqual(task["state"], "succeeded")
            self.assertIn("result", task)
            audit = service.get_audit("task_123")
            self.assertGreaterEqual(len(audit), 6)

    def test_invalid_payload_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self.make_service(Path(tmp) / "paperclip.sqlite3")
            with self.assertRaises(ValueError):
                service.submit_task(self.load_fixture("task_request_invalid.json"))

    def test_pending_approval_can_be_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = self.make_service(Path(tmp) / "paperclip.sqlite3")
            payload = self.load_fixture("task_request_valid.json")
            payload["task"]["id"] = "task_approval"
            payload["execution_policy"]["approval"] = {
                "required": True,
                "status": "pending"
            }
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "pending_approval")
            updated = service.transition_task("task_approval", "approved", actor="human", details={"action": "approve"})
            self.assertEqual(updated["state"], "approved")


if __name__ == "__main__":
    unittest.main()
