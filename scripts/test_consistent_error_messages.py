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


class ConsistentErrorMessageTests(unittest.TestCase):
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

    def test_unauthorized_error_uses_consistent_shape(self) -> None:
        server, thread = self.start_server()
        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        conn.request("GET", "/tasks")
        response = conn.getresponse()
        body = json.loads(response.read().decode())
        self.assertEqual(response.status, 401)
        self.assertEqual(body["error"]["code"], "unauthorized")
        self.assertEqual(body["error"]["status"], 401)
        self.assertIn("message", body["error"])
        conn.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    def test_not_found_error_uses_consistent_shape(self) -> None:
        server, thread = self.start_server()
        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        conn.request("GET", "/nope", headers={"Authorization": "Bearer tenant-a-key"})
        response = conn.getresponse()
        body = json.loads(response.read().decode())
        self.assertEqual(response.status, 404)
        self.assertEqual(body["error"]["code"], "not_found")
        self.assertEqual(body["error"]["status"], 404)
        conn.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
