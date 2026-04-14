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
        self.calls: list[dict] = []
        self.service: PaperclipService | None = None

    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        self.calls.append({"task_id": payload["task"]["id"], "correlation_id": correlation_id})
        assert self.service is not None
        self.service.record_result(payload["task"]["id"], self.result)
        return self.result


class DurableQueueTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_approved_task_is_persisted_in_queue_before_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dispatch = FakeDispatchClient(SUCCESS_RESULT)
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=dispatch)
            dispatch.service = service
            task = service.submit_task(self.load_fixture("task_request_valid.json"))
            queue_item = service.db.get_queue_item(task["id"])
            self.assertIsNotNone(queue_item)
            self.assertEqual(queue_item["status"], "dispatched")
            self.assertEqual(dispatch.calls[0]["task_id"], task["id"])

    def test_pending_queue_items_are_listable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dispatch = FakeDispatchClient(SUCCESS_RESULT)
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=dispatch)
            dispatch.service = service
            payload = self.load_fixture("task_request_valid.json")
            payload["task"]["id"] = "task_queue_only"
            service.db.create_task(
                {
                    "id": payload["task"]["id"],
                    "schema_version": payload["schema_version"],
                    "type": payload["task"]["type"],
                    "title": payload["task"]["title"],
                    "description": payload["task"]["description"],
                    "priority": payload["task"]["priority"],
                    "risk_level": payload["task"]["risk_level"],
                    "requester_id": payload["task"]["requester"]["id"],
                    "requester_display_name": payload["task"]["requester"]["display_name"],
                    "tenant_id": "",
                    "org_id": "",
                    "client_id": "",
                    "state": "approved",
                    "approval_status": "approved",
                    "request_payload": payload,
                    "created_at": "2026-04-04T18:00:00Z",
                    "updated_at": "2026-04-04T18:00:00Z",
                }
            )
            service.enqueue_task("task_queue_only", correlation_id="trace_queue")
            queued = service.get_queue(status="queued")
            self.assertEqual(len(queued), 1)
            self.assertEqual(queued[0]["task_id"], "task_queue_only")
            self.assertEqual(queued[0]["correlation_id"], "trace_queue")


if __name__ == "__main__":
    unittest.main()
