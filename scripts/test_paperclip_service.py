#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class PaperclipServiceTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_submit_task_persists_and_advances_to_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3")
            task = service.submit_task(self.load_fixture("task_request_valid.json"))
            self.assertEqual(task["id"], "task_123")
            self.assertEqual(task["state"], "approved")
            audit = service.get_audit("task_123")
            self.assertGreaterEqual(len(audit), 3)

    def test_invalid_payload_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3")
            with self.assertRaises(ValueError):
                service.submit_task(self.load_fixture("task_request_invalid.json"))

    def test_pending_approval_can_be_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3")
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
