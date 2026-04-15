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


class PublicApiContractTests(unittest.TestCase):
    def start_server(self):
        server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        time.sleep(0.05)
        return server, thread

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        tmp_path = Path(self.tmpdir.name)
        registry_path = tmp_path / "client_api_keys.json"
        registry_path.write_text(json.dumps({
            "keys": [
                {"id": "tenant-a", "role": "submitter", "tenant_id": "tenant-a", "org_id": "org-a", "client_id": "client-a", "key": "tenant-a-key", "status": "active"},
                {"id": "tenant-b", "role": "submitter", "tenant_id": "tenant-b", "org_id": "org-b", "client_id": "client-b", "key": "tenant-b-key", "status": "active"},
            ]
        }))
        os.environ["PAPERCLIP_DB_PATH"] = str(tmp_path / "paperclip.sqlite3")
        os.environ["PAPERCLIP_CLIENT_API_KEYS_FILE"] = str(registry_path)
        os.environ["AGENTOPIA_INTERNAL_AUTH_TOKEN"] = "internal-token"
        os.environ.pop("PAPERCLIP_CLIENT_API_KEYS", None)
        os.environ.pop("PAPERCLIP_CLIENT_API_KEY", None)
        reload(paperclip_app)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_submit_fetch_and_audit_match_public_contract(self) -> None:
        server, thread = self.start_server()
        payload = FIXTURES.joinpath("task_request_valid.json").read_bytes()

        with patch.object(paperclip_app.SERVICE.dispatch_client, "submit", return_value=SUCCESS_RESULT):
            conn = HTTPConnection("127.0.0.1", server.server_address[1])
            conn.request(
                "POST",
                "/tasks",
                body=payload,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(payload)),
                    "Authorization": "Bearer tenant-a-key",
                    "Idempotency-Key": "idem-public-contract",
                },
            )
            response = conn.getresponse()
            body = json.loads(response.read().decode())
            self.assertEqual(response.status, 201)
            self.assertEqual(body["schema_version"], "v1")
            self.assertEqual(body["requester"]["display_name"], "xtcagent")
            self.assertEqual(body["tenant"]["tenant_id"], "tenant-a")
            task_id = body["id"]
            conn.close()

        fetch_conn = HTTPConnection("127.0.0.1", server.server_address[1])
        fetch_conn.request("GET", f"/tasks/{task_id}", headers={"Authorization": "Bearer tenant-a-key"})
        fetch_response = fetch_conn.getresponse()
        fetch_body = json.loads(fetch_response.read().decode())
        self.assertEqual(fetch_response.status, 200)
        self.assertEqual(fetch_body["id"], task_id)
        self.assertIn("state", fetch_body)
        self.assertIn("approval_status", fetch_body)
        fetch_conn.close()

        audit_conn = HTTPConnection("127.0.0.1", server.server_address[1])
        audit_conn.request("GET", f"/tasks/{task_id}/audit", headers={"Authorization": "Bearer tenant-a-key"})
        audit_response = audit_conn.getresponse()
        audit_body = json.loads(audit_response.read().decode())
        self.assertEqual(audit_response.status, 200)
        self.assertIn("events", audit_body)
        self.assertGreater(len(audit_body["events"]), 0)
        audit_conn.close()

        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    def test_cross_tenant_fetch_is_forbidden(self) -> None:
        server, thread = self.start_server()
        payload = FIXTURES.joinpath("task_request_valid.json").read_bytes()

        with patch.object(paperclip_app.SERVICE.dispatch_client, "submit", return_value=SUCCESS_RESULT):
            conn = HTTPConnection("127.0.0.1", server.server_address[1])
            conn.request(
                "POST",
                "/tasks",
                body=payload,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(payload)),
                    "Authorization": "Bearer tenant-a-key",
                },
            )
            response = conn.getresponse()
            task = json.loads(response.read().decode())
            conn.close()

        fetch_conn = HTTPConnection("127.0.0.1", server.server_address[1])
        fetch_conn.request("GET", f"/tasks/{task['id']}", headers={"Authorization": "Bearer tenant-b-key"})
        fetch_response = fetch_conn.getresponse()
        fetch_body = fetch_response.read().decode()
        self.assertEqual(fetch_response.status, 403)
        self.assertIn("tenant_mismatch", fetch_body)
        fetch_conn.close()

        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
