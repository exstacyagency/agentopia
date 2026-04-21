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

import paperclip.app as paperclip_app

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"


class ApprovalReviewVisibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        tmp_path = Path(self.tmpdir.name)
        registry_path = tmp_path / "client_api_keys.json"
        registry_path.write_text(json.dumps({
            "keys": [
                {"id": "tenant-a", "role": "submitter", "tenant_id": "tenant-a", "org_id": "org-a", "client_id": "client-a", "key": "tenant-a-key", "status": "active"},
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

    def start_server(self):
        server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        time.sleep(0.05)
        return server, thread

    def test_task_detail_includes_approval_review_summary(self) -> None:
        server, thread = self.start_server()
        payload = json.loads(FIXTURES.joinpath("task_request_valid.json").read_text())
        payload["task"]["id"] = "task_review"
        payload["execution_policy"]["approval"] = {"required": True, "status": "pending"}
        body = json.dumps(payload).encode()

        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        conn.request(
            "POST",
            "/tasks",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "Authorization": "Bearer tenant-a-key",
            },
        )
        response = conn.getresponse()
        created = json.loads(response.read().decode())
        self.assertEqual(response.status, 201)
        conn.close()

        fetch = HTTPConnection("127.0.0.1", server.server_address[1])
        fetch.request("GET", f"/tasks/{created['id']}", headers={"Authorization": "Bearer tenant-a-key"})
        fetch_response = fetch.getresponse()
        task = json.loads(fetch_response.read().decode())
        self.assertEqual(fetch_response.status, 200)
        self.assertEqual(task["approval_review"]["approval_status"], "pending")
        self.assertTrue(task["approval_review"]["review_required"])
        self.assertEqual(task["approval_review"]["latest_review_event"]["event_type"], "approval_requested")
        fetch.close()

        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
