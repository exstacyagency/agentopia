#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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


class FlakyDispatchClient:
    def __init__(self):
        self.calls = 0
        self.service: PaperclipService | None = None

    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary hermes outage")
        assert self.service is not None
        self.service.record_result(payload["task"]["id"], SUCCESS_RESULT)
        return SUCCESS_RESULT


class RetryBackoffTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_failed_dispatch_schedules_retry_with_backoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dispatch = FlakyDispatchClient()
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=dispatch)
            dispatch.service = service
            task = service.submit_task(self.load_fixture("task_request_valid.json"))
            self.assertEqual(task["state"], "queued")
            queue_item = service.db.get_queue_item(task["id"])
            self.assertEqual(queue_item["attempt_count"], 1)
            self.assertEqual(queue_item["status"], "queued")
            self.assertEqual(queue_item["last_error"], "temporary hermes outage")
            self.assertIsNotNone(queue_item["next_attempt_at"])

    def test_retry_process_succeeds_after_backoff_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dispatch = FlakyDispatchClient()
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=dispatch)
            dispatch.service = service
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "queued")
            queue_item = service.db.get_queue_item("task_123")
            scheduled = datetime.fromisoformat(queue_item["next_attempt_at"].replace("Z", "+00:00"))
            retried = service.process_queue("task_123", now=scheduled + timedelta(seconds=1))
            self.assertEqual(retried["state"], "succeeded")
            queue_item = service.db.get_queue_item("task_123")
            self.assertEqual(queue_item["status"], "dispatched")
            self.assertEqual(dispatch.calls, 2)


if __name__ == "__main__":
    unittest.main()
