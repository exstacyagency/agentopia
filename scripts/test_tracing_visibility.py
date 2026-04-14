#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService


class TracingVisibilityTests(unittest.TestCase):
    def test_paperclip_trace_log_records_submission_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            class DummyDispatch:
                def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
                    return {"ok": True}

            service = PaperclipService(root / "data" / "paperclip.sqlite3", dispatch_client=DummyDispatch())
            payload = {
                "schema_version": "v1",
                "task": {
                    "id": "task_trace",
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
                    "approval": {"required": False, "status": "approved"},
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
                "trace": {"trace_id": "trace_visible", "submitted_at": "2026-04-03T18:01:05Z"},
            }
            service.submit_task(payload)
            service.record_result(
                "task_trace",
                {
                    "schema_version": "v1",
                    "task_id": "task_trace",
                    "run": {"run_id": "run_task_trace", "status": "succeeded", "started_at": "2026-04-03T18:01:05Z", "finished_at": "2026-04-03T18:01:06Z", "runtime_seconds": 1},
                    "result": {"summary": "ok", "output_format": "markdown", "output": "# ok", "notes": [], "error": None},
                    "artifacts": [],
                    "usage": {"actual_cost_usd": 0.0, "model_provider": "local", "model_name": "test", "tool_calls": 0},
                    "trace": {"trace_id": "trace_visible", "reported_at": "2026-04-03T18:01:06Z"},
                },
            )
            trace_path = root / "var" / "traces" / "trace-trace_visible.jsonl"
            self.assertTrue(trace_path.exists())
            events = [json.loads(line)["event"] for line in trace_path.read_text().splitlines() if line.strip()]
            self.assertIn("task_submitted", events)
            self.assertIn("task_dispatched", events)
            self.assertIn("result_recorded", events)


if __name__ == "__main__":
    unittest.main()
