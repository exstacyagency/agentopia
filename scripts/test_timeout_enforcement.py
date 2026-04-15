#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from paperclip.service import PaperclipService

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class HangingDispatchClient:
    def __init__(self):
        self.calls = 0

    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        self.calls += 1
        return {"accepted": True}


class TimeoutEnforcementTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_running_queue_item_times_out_after_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dispatch = HangingDispatchClient()
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=dispatch)
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "running")
            queue_item = service.db.get_queue_item(task["id"])
            self.assertEqual(queue_item["status"], "dispatched")
            service.db.mark_queue_running(task["id"], queue_item["created_at"], queue_item["timeout_at"], queue_item["updated_at"])
            timed_out = service.enforce_timeouts(
                now=datetime.fromisoformat(queue_item["timeout_at"].replace("Z", "+00:00")) + timedelta(seconds=1)
            )
            self.assertEqual(timed_out[0]["task_id"], task["id"])
            updated = service.get_task(task["id"])
            self.assertEqual(updated["state"], "failed")
            queue_item = service.db.get_queue_item(task["id"])
            self.assertEqual(queue_item["status"], "timed_out")


if __name__ == "__main__":
    unittest.main()
