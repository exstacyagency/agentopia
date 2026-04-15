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


class AlwaysFailDispatchClient:
    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        raise RuntimeError("permanent hermes failure")


class DeadLetterHandlingTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_queue_item_moves_to_dead_letter_after_max_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=AlwaysFailDispatchClient())
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "queued")
            queue_item = service.db.get_queue_item(task["id"])
            scheduled = datetime.fromisoformat(queue_item["next_attempt_at"].replace("Z", "+00:00"))
            service.process_queue(task["id"], now=scheduled + timedelta(seconds=1))
            queue_item = service.db.get_queue_item(task["id"])
            scheduled = datetime.fromisoformat(queue_item["next_attempt_at"].replace("Z", "+00:00"))
            final = service.process_queue(task["id"], now=scheduled + timedelta(seconds=1))
            self.assertEqual(final["state"], "failed")
            queue_item = service.db.get_queue_item(task["id"])
            self.assertEqual(queue_item["status"], "dead_letter")
            self.assertEqual(queue_item["attempt_count"], 3)


if __name__ == "__main__":
    unittest.main()
