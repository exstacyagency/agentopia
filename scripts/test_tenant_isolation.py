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


class TenantIsolationTests(unittest.TestCase):
    def test_cross_tenant_task_read_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            registry_path = tmp_path / "client_api_keys.json"
            registry_path.write_text(json.dumps({
                "keys": [
                    {"id": "tenant-a", "role": "submitter", "tenant_id": "tenant-a", "org_id": "org-a", "client_id": "client-a", "key": "tenant-a-key", "status": "active"},
                    {"id": "tenant-b", "role": "submitter", "tenant_id": "tenant-b", "org_id": "org-b", "client_id": "client-b", "key": "tenant-b-key", "status": "active"},
                ]
            }))
            os.environ["PAPERCLIP_DB_PATH"] = str(tmp_path / "paperclip.sqlite3")
            os.environ["PAPERCLIP_CLIENT_API_KEYS_FILE"] = str(registry_path)
            os.environ.pop("PAPERCLIP_CLIENT_API_KEYS", None)
            os.environ.pop("PAPERCLIP_CLIENT_API_KEY", None)
            reload(paperclip_app)

            server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
            thread = threading.Thread(target=server.handle_request)
            thread.start()
            time.sleep(0.1)

            payload = FIXTURES.joinpath("task_request_valid.json").read_bytes()
            with patch.object(paperclip_app.SERVICE.dispatch_client, "submit", return_value=SUCCESS_RESULT):
                submit_conn = HTTPConnection("127.0.0.1", server.server_address[1])
                submit_conn.request(
                    "POST",
                    "/tasks",
                    body=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Content-Length": str(len(payload)),
                        "Authorization": "Bearer tenant-a-key",
                    },
                )
                submit_response = submit_conn.getresponse()
                submit_body = json.loads(submit_response.read().decode())
                submit_conn.close()

            task_id = submit_body["id"]

            read_server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
            read_thread = threading.Thread(target=read_server.handle_request)
            read_thread.start()
            time.sleep(0.1)
            read_conn = HTTPConnection("127.0.0.1", read_server.server_address[1])
            read_conn.request("GET", f"/tasks/{task_id}", headers={"Authorization": "Bearer tenant-b-key"})
            read_response = read_conn.getresponse()
            read_body = read_response.read().decode()
            self.assertEqual(read_response.status, 403)
            self.assertIn("tenant_mismatch", read_body)
            read_conn.close()
            read_server.server_close()
            read_thread.join(timeout=2)

            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
