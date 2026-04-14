#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import threading
import time
import unittest
from http.client import HTTPConnection


class ClientApiAuthTests(unittest.TestCase):
    def test_paperclip_task_submission_requires_client_auth(self) -> None:
        os.environ["PAPERCLIP_CLIENT_API_KEY"] = "client-token"
        from importlib import reload
        import paperclip.app as paperclip_app

        reload(paperclip_app)
        server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        time.sleep(0.1)

        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        payload = json.dumps({"schema_version": "v1"}).encode()
        conn.request("POST", "/tasks", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
        response = conn.getresponse()
        body = response.read().decode()
        self.assertEqual(response.status, 401)
        self.assertIn("unauthorized", body)
        conn.close()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
