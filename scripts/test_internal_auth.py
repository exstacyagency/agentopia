#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import threading
import time
import types
import unittest
from http.client import HTTPConnection

from paperclip.dispatch import HermesDispatchClient


class InternalAuthTests(unittest.TestCase):
    def test_dispatch_client_sends_bearer_token(self) -> None:
        captured = {}

        class DummyResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"{}"

        def fake_urlopen(req):
            captured["authorization"] = req.headers.get("Authorization")
            return DummyResponse()

        client = HermesDispatchClient("http://127.0.0.1:3200", auth_token="shared-token")
        from unittest.mock import patch

        with patch("paperclip.dispatch.request.urlopen", fake_urlopen):
            client.submit({"task": {"id": "task_123"}})

        self.assertEqual(captured["authorization"], "Bearer shared-token")

    def test_paperclip_internal_result_requires_auth(self) -> None:
        os.environ["AGENTOPIA_INTERNAL_AUTH_TOKEN"] = "shared-token"
        from importlib import reload
        import paperclip.app as paperclip_app

        reload(paperclip_app)
        server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        time.sleep(0.1)

        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        payload = json.dumps({"run": {"status": "succeeded"}}).encode()
        conn.request("POST", "/internal/tasks/task_123/result", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
        response = conn.getresponse()
        body = response.read().decode()
        self.assertEqual(response.status, 401)
        self.assertIn("unauthorized", body)
        conn.close()
        server.server_close()
        thread.join(timeout=2)

    def test_hermes_execute_requires_auth(self) -> None:
        os.environ["AGENTOPIA_INTERNAL_AUTH_TOKEN"] = "shared-token"
        sys.modules.setdefault("hermes.build_info", types.SimpleNamespace(BUILD_STAMP="test", RUNTIME_FEATURES=[]))
        sys.modules.setdefault("hermes.dashboard_state", types.SimpleNamespace(build_operator_queue_state=lambda root: {}))
        sys.modules.setdefault("hermes.callback_store", types.SimpleNamespace(HermesCallbackStore=lambda root: object()))
        sys.modules.setdefault("hermes.postback_store", types.SimpleNamespace(HermesPostbackStore=lambda root: object()))
        sys.modules.setdefault("hermes.issue_actions", types.SimpleNamespace(handle_issue_action=lambda body: {"ok": True}))
        sys.modules.setdefault("hermes.runtime_checks", types.SimpleNamespace(summarize_runtime_guards=lambda base_url: {}))

        class _DummyPersistence:
            def __init__(self, root):
                pass

            def persist_result(self, result):
                return None

        class _DummyCommentPoster:
            base_url = None

        class _DummyMemPalace:
            def get_config(self):
                return {}

            def status(self):
                return {}

            def search(self, query):
                return {}

            def wakeup(self, issue_title, issue_description):
                return {}

            def set_config(self, body):
                return {}

            def run_operation(self, name):
                return {}

        sys.modules.setdefault("hermes.persistence", types.SimpleNamespace(HermesPersistence=_DummyPersistence))
        sys.modules.setdefault("hermes.paperclip_comments", types.SimpleNamespace(PaperclipCommentPoster=_DummyCommentPoster))
        sys.modules.setdefault("hermes.memory.service", types.SimpleNamespace(MemPalaceService=_DummyMemPalace))

        from importlib import reload
        import hermes.app as hermes_app

        reload(hermes_app)
        server = hermes_app.ThreadingHTTPServer(("127.0.0.1", 0), hermes_app.HermesHandler)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        time.sleep(0.1)

        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        payload = json.dumps({"task": {"title": "ok"}}).encode()
        conn.request("POST", "/internal/execute", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
        response = conn.getresponse()
        body = response.read().decode()
        self.assertEqual(response.status, 401)
        self.assertIn("unauthorized", body)
        conn.close()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
