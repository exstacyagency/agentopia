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


class RateLimitTests(unittest.TestCase):
    def test_paperclip_rate_limits_repeated_requests(self) -> None:
        os.environ["PAPERCLIP_RATE_LIMIT_COUNT"] = "1"
        os.environ["PAPERCLIP_RATE_LIMIT_WINDOW_SECONDS"] = "60"
        from importlib import reload
        import paperclip.app as paperclip_app

        reload(paperclip_app)
        server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
        thread = threading.Thread(target=lambda: [server.handle_request(), server.handle_request()])
        thread.start()
        time.sleep(0.1)

        payload = json.dumps({"schema_version": "v1"}).encode()
        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        conn.request("POST", "/tasks", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
        first = conn.getresponse()
        first.read()
        conn.close()

        conn2 = HTTPConnection("127.0.0.1", server.server_address[1])
        conn2.request("POST", "/tasks", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
        second = conn2.getresponse()
        body = second.read().decode()
        self.assertEqual(second.status, 429)
        self.assertIn("rate limit exceeded", body)
        conn2.close()
        server.server_close()
        thread.join(timeout=2)

    def test_hermes_rate_limits_repeated_requests(self) -> None:
        os.environ["HERMES_RATE_LIMIT_COUNT"] = "1"
        os.environ["HERMES_RATE_LIMIT_WINDOW_SECONDS"] = "60"
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
        thread = threading.Thread(target=lambda: [server.handle_request(), server.handle_request()])
        thread.start()
        time.sleep(0.1)

        payload = json.dumps({"task": {"title": "ok"}}).encode()
        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        conn.request("POST", "/internal/execute", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
        first = conn.getresponse()
        first.read()
        conn.close()

        conn2 = HTTPConnection("127.0.0.1", server.server_address[1])
        conn2.request("POST", "/internal/execute", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
        second = conn2.getresponse()
        body = second.read().decode()
        self.assertEqual(second.status, 429)
        self.assertIn("rate limit exceeded", body)
        conn2.close()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
