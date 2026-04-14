#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService


class ApprovalReconciliationTests(unittest.TestCase):
    def test_reconciliation_detects_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "paperclip.sqlite3"
            service = PaperclipService(db_path)
            payload = {
                "schema_version": "v1",
                "task": {
                    "id": "task_reconcile",
                    "type": "repo_summary",
                    "title": "Title",
                    "description": "Desc",
                    "priority": "medium",
                    "risk_level": "low",
                    "requester": {"id": "user_1", "display_name": "user"},
                    "created_at": "2026-04-03T18:00:00Z",
                },
                "execution_policy": {
                    "budget": {"max_cost_usd": 1.0, "max_runtime_minutes": 5},
                    "approval": {"required": True, "status": "pending"},
                    "permissions": {
                        "allow_network": False,
                        "allow_memory": True,
                        "allow_tools": True,
                        "allowed_tool_classes": ["repo_read"],
                        "write_scope": "artifacts_only",
                    },
                    "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": True},
                },
                "routing": {"source": "paperclip", "destination": "hermes", "callback": {"result_url": "http://paperclip/result", "auth_mode": "shared_token"}},
                "trace": {"trace_id": "trace_reconcile", "submitted_at": "2026-04-03T18:01:05Z"},
            }
            service.submit_task(payload)
            service.db.update_task_state("task_reconcile", "approved", "2026-04-03T18:02:00Z", approval_status="pending")
            mismatches = service.reconcile_approval_status()
            self.assertEqual(len(mismatches), 1)
            self.assertEqual(mismatches[0]["task_id"], "task_reconcile")


if __name__ == "__main__":
    unittest.main()
