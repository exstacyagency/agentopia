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


class MetricsTests(unittest.TestCase):
    def test_paperclip_metrics_endpoint_exposes_counters(self) -> None:
        os.environ["PAPERCLIP_RATE_LIMIT_COUNT"] = "100"
        from importlib import reload
        import paperclip.app as paperclip_app

        reload(paperclip_app)
        server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
        thread = threading.Thread(target=lambda: [server.handle_request(), server.handle_request()])
        thread.start()
        time.sleep(0.1)

        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        payload = json.dumps({"bad": "payload"}).encode()
        conn.request("POST", "/tasks", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload))})
        response = conn.getresponse()
        response.read()
        conn.close()

        conn2 = HTTPConnection("127.0.0.1", server.server_address[1])
        conn2.request("GET", "/metrics")
        response2 = conn2.getresponse()
        body = response2.read().decode()
        self.assertEqual(response2.status, 200)
        self.assertIn("paperclip_requests_received_total", body)
        self.assertIn("paperclip_responses_sent_total", body)
        conn2.close()
        server.server_close()
        thread.join(timeout=2)

    def test_hermes_metrics_endpoint_exposes_counters(self) -> None:
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
        thread = threading.Thread(target=lambda: [server.handle_request(), server.handle_request()])
        thread.start()
        time.sleep(0.1)

        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        payload = json.dumps({"task": {"title": "ok"}}).encode()
        conn.request("POST", "/internal/execute", body=payload, headers={"Content-Type": "application/json", "Content-Length": str(len(payload)), "Authorization": "Bearer shared-token"})
        response = conn.getresponse()
        response.read()
        conn.close()

        conn2 = HTTPConnection("127.0.0.1", server.server_address[1])
        conn2.request("GET", "/metrics")
        response2 = conn2.getresponse()
        body = response2.read().decode()
        self.assertEqual(response2.status, 200)
        self.assertIn("hermes_requests_received_total", body)
        self.assertIn("hermes_responses_sent_total", body)
        conn2.close()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
