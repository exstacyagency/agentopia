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


class NoopDispatchClient:
    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        return {"accepted": True}


class WorkerLeasingTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_second_worker_cannot_claim_active_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=NoopDispatchClient())
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "running")
            queue_item = service.db.get_queue_item(task["id"])
            service.db.update_task_state(task["id"], "queued", queue_item["updated_at"])
            now = datetime.now(timezone.utc)
            service.claim_queue_item(task["id"], "worker-a", now=now)
            with self.assertRaises(ValueError):
                service.claim_queue_item(task["id"], "worker-b", now=now + timedelta(seconds=1))

    def test_expired_lease_can_be_reclaimed_by_new_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=NoopDispatchClient())
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            queue_item = service.db.get_queue_item(task["id"])
            service.db.update_task_state(task["id"], "queued", queue_item["updated_at"])
            first_claim_time = datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)
            service.claim_queue_item(task["id"], "worker-a", now=first_claim_time)
            reclaimed = service.claim_queue_item(task["id"], "worker-b", now=first_claim_time + timedelta(seconds=120))
            self.assertEqual(reclaimed["id"], task["id"])
            queue_item = service.db.get_queue_item(task["id"])
            self.assertEqual(queue_item["worker_id"], "worker-b")


if __name__ == "__main__":
    unittest.main()
