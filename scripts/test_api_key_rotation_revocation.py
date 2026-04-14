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


class ApiKeyRotationRevocationTests(unittest.TestCase):
    def _run_request(self, registry: dict, token: str) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "client_api_keys.json"
            registry_path.write_text(json.dumps(registry))
            os.environ["PAPERCLIP_DB_PATH"] = str(tmp_path / "paperclip.sqlite3")
            os.environ["PAPERCLIP_CLIENT_API_KEYS_FILE"] = str(registry_path)
            os.environ.pop("PAPERCLIP_CLIENT_API_KEYS", None)
            os.environ.pop("PAPERCLIP_CLIENT_API_KEY", None)
            reload(paperclip_app)

            server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            time.sleep(0.1)

            conn = HTTPConnection("127.0.0.1", server.server_address[1])
            payload = FIXTURES.joinpath("task_request_valid.json").read_bytes()
            headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
                "Authorization": f"Bearer {token}",
            }
            with patch.object(paperclip_app.SERVICE.dispatch_client, "submit", return_value=SUCCESS_RESULT):
                conn.request("POST", "/tasks", body=payload, headers=headers)
                response = conn.getresponse()
                body = response.read().decode()
                status = response.status
            conn.close()
            server.server_close()
            thread.join(timeout=2)
            return status, body

    def test_rotation_allows_old_and_new_active_keys_during_cutover(self) -> None:
        registry = {
            "keys": [
                {"id": "old-primary", "scope": "tasks.write", "key": "old-key", "status": "active"},
                {"id": "new-primary", "scope": "tasks.write", "key": "new-key", "status": "active"},
            ]
        }
        old_status, _ = self._run_request(registry, "old-key")
        new_status, _ = self._run_request(registry, "new-key")
        self.assertEqual(old_status, 201)
        self.assertEqual(new_status, 201)

    def test_revoked_key_is_rejected(self) -> None:
        registry = {
            "keys": [
                {"id": "old-primary", "scope": "tasks.write", "key": "old-key", "status": "revoked"},
            ]
        }
        status, body = self._run_request(registry, "old-key")
        self.assertEqual(status, 401)
        self.assertIn("api_key_revoked", body)


if __name__ == "__main__":
    unittest.main()
