#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hermes.persistence import HermesPersistence
from paperclip.service import PaperclipService


class AuditLoggingTests(unittest.TestCase):
    def test_hermes_persistence_writes_audit_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            persistence = HermesPersistence(root)
            persistence.persist_result(
                {
                    "task_id": "task_123",
                    "run": {"run_id": "run_123"},
                    "result": {"summary": "ok"},
                }
            )
            audit_path = root / "var" / "hermes" / "audit.log"
            self.assertTrue(audit_path.exists())
            lines = audit_path.read_text().strip().splitlines()
            self.assertGreaterEqual(len(lines), 1)
            entry = json.loads(lines[-1])
            self.assertEqual(entry["event_type"], "persist_result")
            self.assertEqual(entry["payload"]["task_id"], "task_123")

    def test_paperclip_audit_events_remain_queryable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3")
            payload = {
                "schema_version": "v1",
                "task": {
                    "id": "task_audit",
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
                "trace": {"trace_id": "trace_audit", "submitted_at": "2026-04-03T18:01:05Z"},
            }
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "pending_approval")
            audit = service.get_audit("task_audit")
            self.assertGreaterEqual(len(audit), 2)
            event_types = [event["event_type"] for event in audit]
            self.assertIn("task_received", event_types)


if __name__ == "__main__":
    unittest.main()
