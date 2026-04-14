#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from paperclip.service import PaperclipService


class ApprovalAuditTrailTests(unittest.TestCase):
    def test_approval_events_are_recorded_and_filterable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PAPERCLIP_APPROVAL_TTL_SECONDS"] = "60"
            db_path = Path(tmp) / "paperclip.sqlite3"
            service = PaperclipService(db_path)
            base_payload = {
                "schema_version": "v1",
                "task": {
                    "id": "task_approval_audit",
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
                "trace": {"trace_id": "trace_approval_audit", "submitted_at": "2026-04-03T18:01:05Z"},
            }
            pending_payload = dict(base_payload)
            pending_payload["task"] = dict(base_payload["task"])
            pending_payload["task"]["id"] = "task_approval_expired"
            pending_payload["trace"] = dict(base_payload["trace"])
            pending_payload["trace"]["trace_id"] = "trace_approval_expired"
            service.submit_task(pending_payload)
            service.db.update_task_state("task_approval_expired", "pending_approval", "2026-04-03T18:00:00Z", approval_status="pending")
            service.find_expired_approvals(now=datetime(2026, 4, 3, 18, 2, 0, tzinfo=timezone.utc))

            approved_payload = dict(base_payload)
            approved_payload["task"] = dict(base_payload["task"])
            approved_payload["task"]["id"] = "task_approval_granted"
            approved_payload["trace"] = dict(base_payload["trace"])
            approved_payload["trace"]["trace_id"] = "trace_approval_granted"
            service.submit_task(approved_payload)
            service.transition_task("task_approval_granted", "approved", actor="operator", details={"reason": "approved"})

            expired_events = service.get_approval_audit("task_approval_expired")
            granted_events = service.get_approval_audit("task_approval_granted")
            expired_types = [event["event_type"] for event in expired_events]
            granted_types = [event["event_type"] for event in granted_events]
            self.assertIn("approval_requested", expired_types)
            self.assertIn("approval_expired", expired_types)
            self.assertIn("approval_requested", granted_types)
            self.assertIn("approval_granted", granted_types)


if __name__ == "__main__":
    unittest.main()
