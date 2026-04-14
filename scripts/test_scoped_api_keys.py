#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from importlib import reload
from pathlib import Path
from unittest.mock import patch

import paperclip.app as paperclip_app

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
SUCCESS_RESULT = {
    "schema_version": "v1",
    "task_id": "task_123",
    "run": {
        "run_id": "run_task_123",
        "status": "succeeded",
        "started_at": "2026-04-04T18:00:00Z",
        "finished_at": "2026-04-04T18:00:00Z",
        "runtime_seconds": 0,
    },
    "result": {
        "summary": "ok",
        "output_format": "markdown",
        "output": "# ok",
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
        "trace_id": "trace_abc123",
        "reported_at": "2026-04-04T18:00:00Z",
    },
}


class ScopedApiKeyTests(unittest.TestCase):
    def _run_request(self, token: str | None) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PAPERCLIP_DB_PATH"] = str(Path(tmp) / "paperclip.sqlite3")
            reload(paperclip_app)
            server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            time.sleep(0.1)

            conn = HTTPConnection("127.0.0.1", server.server_address[1])
            payload = FIXTURES.joinpath("task_request_valid.json").read_bytes()
            headers = {"Content-Type": "application/json", "Content-Length": str(len(payload))}
            if token is not None:
                headers["Authorization"] = f"Bearer {token}"
            with patch.object(paperclip_app.SERVICE.dispatch_client, "submit", return_value=SUCCESS_RESULT):
                conn.request("POST", "/tasks", body=payload, headers=headers)
                response = conn.getresponse()
                body = response.read().decode()
                status = response.status
            conn.close()
            server.server_close()
            thread.join(timeout=2)
            return status, body

    def test_scoped_key_with_tasks_write_scope_is_accepted(self) -> None:
        os.environ["PAPERCLIP_CLIENT_API_KEYS"] = "tasks.write:scoped-write-key"
        os.environ.pop("PAPERCLIP_CLIENT_API_KEY", None)
        status, body = self._run_request("scoped-write-key")
        self.assertEqual(status, 201)
        self.assertIn("task_", body)

    def test_scoped_key_without_required_scope_is_rejected(self) -> None:
        os.environ["PAPERCLIP_CLIENT_API_KEYS"] = "tasks.read:scoped-read-key"
        os.environ.pop("PAPERCLIP_CLIENT_API_KEY", None)
        status, body = self._run_request("scoped-read-key")
        self.assertEqual(status, 401)
        self.assertIn("unauthorized", body)


if __name__ == "__main__":
    unittest.main()
