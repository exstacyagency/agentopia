#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService
from scripts.contracts import validate_payload

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class IntegrationFlowTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_approved_task_runs_end_to_end_through_hermes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", hermes_root=ROOT)
            task = service.submit_task(self.load_fixture("task_request_valid.json"))
            self.assertEqual(task["state"], "succeeded")
            self.assertIn("result", task)
            errors = validate_payload("task_result_v1.json", task["result"])
            self.assertEqual(errors, [])
            audit = service.get_audit("task_123")
            event_types = [event["event_type"] for event in audit]
            self.assertIn("result_recorded", event_types)

    def test_pending_approval_does_not_dispatch_until_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", hermes_root=ROOT)
            payload = self.load_fixture("task_request_valid.json")
            payload["task"]["id"] = "task_pending"
            payload["execution_policy"]["approval"] = {"required": True, "status": "pending"}
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "pending_approval")
            self.assertNotIn("result", task)
            service.transition_task("task_pending", "approved", actor="human", details={"action": "approve"})
            updated = service.dispatch_task("task_pending")
            self.assertEqual(updated["state"], "succeeded")
            self.assertIn("result", updated)


if __name__ == "__main__":
    unittest.main()
