#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from paperclip.service import PaperclipService


class RetentionDeletionWorkflowTests(unittest.TestCase):
    def test_lists_terminal_tasks_as_retention_candidates_and_deletes_all_task_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "data" / "paperclip.sqlite3"
            service = PaperclipService(db_path)
            service.db.create_task(
                {
                    "id": "task_retention",
                    "schema_version": "v1",
                    "type": "repo_summary",
                    "title": "retention",
                    "description": "retention",
                    "priority": "medium",
                    "risk_level": "low",
                    "requester_id": "u1",
                    "requester_display_name": "u1",
                    "tenant_id": "",
                    "org_id": "",
                    "client_id": "",
                    "state": "succeeded",
                    "approval_status": "approved",
                    "request_payload": {"trace": {"trace_id": "trace_retention"}},
                    "created_at": "2026-04-10T12:00:00Z",
                    "updated_at": "2026-04-10T12:00:00Z",
                }
            )
            service.db.add_audit_event("task_retention", "task_received", "paperclip", {}, "2026-04-10T12:00:00Z")
            service.db.store_result_with_audit(
                "task_retention",
                {"run": {"status": "succeeded"}, "trace": {"trace_id": "trace_retention"}},
                "succeeded",
                "2026-04-10T12:01:00Z",
            )
            service.storage.persist_result("task_retention", {"result": "persisted"})

            candidates = service.list_retention_candidates(datetime(2026, 4, 11, 0, 0, 0, tzinfo=timezone.utc))
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["task_id"], "task_retention")

            deleted = service.delete_task("task_retention")
            self.assertTrue(deleted)
            self.assertIsNone(service.db.get_task("task_retention"))
            self.assertIsNone(service.db.get_result("task_retention"))
            self.assertEqual(service.db.get_audit_events("task_retention"), [])
            self.assertFalse((Path(tmp) / "var" / "paperclip" / "tasks" / "task_retention").exists())


if __name__ == "__main__":
    unittest.main()
