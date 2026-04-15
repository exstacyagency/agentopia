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


class FakeDispatchClient:
    def __init__(self, result: dict):
        self.result = result
        self.calls = 0
        self.service: PaperclipService | None = None

    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        self.calls += 1
        assert self.service is not None
        self.service.record_result(payload["task"]["id"], self.result)
        return self.result


class IdempotentTaskSubmissionTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_repeated_submission_with_same_idempotency_key_returns_original_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dispatch = FakeDispatchClient(SUCCESS_RESULT)
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=dispatch)
            dispatch.service = service
            payload = self.load_fixture("task_request_valid.json")
            first = service.submit_task(payload, idempotency_key="idem-123")
            second = service.submit_task(payload, idempotency_key="idem-123")
            self.assertEqual(first["id"], second["id"])
            self.assertEqual(dispatch.calls, 1)
            queue_items = service.get_queue()
            self.assertEqual(len(queue_items), 1)


if __name__ == "__main__":
    unittest.main()
