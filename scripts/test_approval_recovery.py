#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from paperclip.service import PaperclipService


class ApprovalRecoveryTests(unittest.TestCase):
    def test_lists_and_recovers_stuck_approval_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PAPERCLIP_APPROVAL_TTL_SECONDS"] = "60"
            db_path = Path(tmp) / "paperclip.sqlite3"
            service = PaperclipService(db_path)
            payload = {
                "schema_version": "v1",
                "task": {
                    "id": "task_stuck",
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
                "trace": {"trace_id": "trace_stuck", "submitted_at": "2026-04-03T18:01:05Z"},
            }
            service.submit_task(payload)
            service.db.update_task_state("task_stuck", "approved", "2026-04-03T18:00:00Z", approval_status="pending")
            stuck = service.list_stuck_approval_tasks(now=datetime(2026, 4, 3, 18, 2, 0, tzinfo=timezone.utc))
            self.assertEqual(len(stuck), 1)
            self.assertEqual(stuck[0]["task_id"], "task_stuck")

            recovered = service.recover_stuck_approval("task_stuck")
            self.assertIsNotNone(recovered)
            self.assertEqual(recovered["state"], "pending_approval")
            self.assertEqual(recovered["approval_status"], "pending")


if __name__ == "__main__":
    unittest.main()
