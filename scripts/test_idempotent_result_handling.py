#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService

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


class IdempotentResultHandlingTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_repeated_result_recording_returns_existing_task_without_reapplying(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3")
            payload = self.load_fixture("task_request_valid.json")
            payload["task"]["id"] = "task_result_idem"
            payload["execution_policy"]["approval"] = {"required": True, "status": "pending"}
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "pending_approval")
            service.transition_task("task_result_idem", "approved", actor="human", details={"action": "approve"})
            service.transition_task("task_result_idem", "queued", actor="paperclip", details={"queue": "sqlite"})
            service.transition_task("task_result_idem", "running", actor="paperclip", details={"dispatch": "hermes"})

            first = service.record_result("task_result_idem", SUCCESS_RESULT)
            second = service.record_result("task_result_idem", SUCCESS_RESULT)

            self.assertEqual(first["state"], "succeeded")
            self.assertEqual(second["state"], "succeeded")
            audit = service.get_audit("task_result_idem")
            result_events = [event for event in audit if event["event_type"] == "result_recorded"]
            self.assertEqual(len(result_events), 1)


if __name__ == "__main__":
    unittest.main()
