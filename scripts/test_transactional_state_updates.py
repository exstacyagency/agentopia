#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService


class TransactionalStateUpdateTests(unittest.TestCase):
    def test_result_record_and_audit_are_transactional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3")
            service.db.create_task(
                {
                    "id": "task_txn",
                    "schema_version": "v1",
                    "type": "repo_summary",
                    "title": "txn",
                    "description": "txn",
                    "priority": "medium",
                    "risk_level": "low",
                    "requester_id": "u1",
                    "requester_display_name": "u1",
                    "tenant_id": "",
                    "org_id": "",
                    "client_id": "",
                    "state": "running",
                    "approval_status": "approved",
                    "request_payload": {"trace": {"trace_id": "trace_txn"}},
                    "created_at": "2026-04-15T15:00:00Z",
                    "updated_at": "2026-04-15T15:00:00Z",
                }
            )

            original_add_audit = service.db.add_audit_event

            def failing_add_audit(*args, **kwargs):
                raise RuntimeError("boom")

            service.db.add_audit_event = failing_add_audit
            with self.assertRaises(RuntimeError):
                service.db.store_result_with_audit(
                    "task_txn",
                    {"run": {"status": "succeeded"}, "trace": {"trace_id": "trace_txn"}},
                    "succeeded",
                    "2026-04-15T15:01:00Z",
                )
            service.db.add_audit_event = original_add_audit

            self.assertIsNone(service.db.get_result("task_txn"))
            self.assertEqual(service.db.get_audit_events("task_txn"), [])


if __name__ == "__main__":
    unittest.main()
