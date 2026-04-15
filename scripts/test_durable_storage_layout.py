#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from paperclip.service import PaperclipService

SUCCESS_RESULT = {
    "schema_version": "v1",
    "task_id": "task_storage",
    "run": {
        "run_id": "run_task_storage",
        "status": "succeeded",
        "started_at": "2026-04-15T15:00:00Z",
        "finished_at": "2026-04-15T15:00:01Z",
        "runtime_seconds": 1,
    },
    "result": {
        "summary": "stored",
        "output_format": "markdown",
        "output": "# stored",
        "notes": [],
        "error": None,
    },
    "artifacts": [],
    "usage": {
        "actual_cost_usd": 0.0,
        "model_provider": "local",
        "model_name": "test",
        "tool_calls": 0,
    },
    "trace": {
        "trace_id": "trace_storage",
        "reported_at": "2026-04-15T15:00:01Z",
    },
}


class DurableStorageLayoutTests(unittest.TestCase):
    def test_result_is_persisted_to_task_storage_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "data" / "paperclip.sqlite3"
            service = PaperclipService(db_path)
            service.db.create_task(
                {
                    "id": "task_storage",
                    "schema_version": "v1",
                    "type": "repo_summary",
                    "title": "storage",
                    "description": "storage",
                    "priority": "medium",
                    "risk_level": "low",
                    "requester_id": "u1",
                    "requester_display_name": "u1",
                    "tenant_id": "",
                    "org_id": "",
                    "client_id": "",
                    "state": "running",
                    "approval_status": "approved",
                    "request_payload": {"trace": {"trace_id": "trace_storage"}},
                    "created_at": "2026-04-15T15:00:00Z",
                    "updated_at": "2026-04-15T15:00:00Z",
                }
            )
            service.record_result("task_storage", SUCCESS_RESULT)
            result_path = Path(tmp) / "var" / "paperclip" / "tasks" / "task_storage" / "result.json"
            artifacts_dir = Path(tmp) / "var" / "paperclip" / "tasks" / "task_storage" / "artifacts"
            self.assertTrue(result_path.exists())
            self.assertTrue(artifacts_dir.is_dir())
            self.assertEqual(json.loads(result_path.read_text()), SUCCESS_RESULT)


if __name__ == "__main__":
    unittest.main()
