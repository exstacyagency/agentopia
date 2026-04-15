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


class StuckJobRecoveryTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_expired_running_lease_can_be_recovered_to_queued(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=NoopDispatchClient())
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            queue_item = service.db.get_queue_item(task["id"])
            service.db.claim_queue_item(task["id"], "worker-a", "2026-04-15T11:00:00Z", "2026-04-15T10:59:00Z")
            service.db.mark_queue_running(task["id"], "2026-04-15T10:58:00Z", "2026-04-15T11:00:00Z", "2026-04-15T10:58:00Z")
            service.db.update_task_state(task["id"], "running", "2026-04-15T10:58:00Z")

            recoverable = service.list_recoverable_stuck_jobs(now=datetime(2026, 4, 15, 11, 1, 0, tzinfo=timezone.utc))
            self.assertEqual(recoverable[0]["task_id"], task["id"])

            recovered = service.recover_stuck_job(task["id"], now=datetime(2026, 4, 15, 11, 1, 0, tzinfo=timezone.utc))
            self.assertIsNotNone(recovered)
            self.assertEqual(recovered["state"], "queued")
            queue_item = service.db.get_queue_item(task["id"])
            self.assertEqual(queue_item["status"], "queued")
            self.assertIsNone(queue_item["worker_id"])


if __name__ == "__main__":
    unittest.main()
