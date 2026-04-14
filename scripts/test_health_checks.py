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


class HealthCheckTests(unittest.TestCase):
    def test_paperclip_health_reports_missing_internal_auth(self) -> None:
        os.environ.pop("AGENTOPIA_INTERNAL_AUTH_TOKEN", None)
        from importlib import reload
        import paperclip.app as paperclip_app

        reload(paperclip_app)
        server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
        thread = threading.Thread(target=server.handle_request)
        thread.start()
        time.sleep(0.1)

        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        conn.request("GET", "/health")
        response = conn.getresponse()
        payload = json.loads(response.read().decode())
        self.assertEqual(response.status, 503)
        self.assertFalse(payload["ok"])
        self.assertFalse(payload["dependencies"]["internal_auth_configured"])
        conn.close()
        server.server_close()
        thread.join(timeout=2)

    def test_hermes_health_reports_ready_dependencies(self) -> None:
        os.environ["AGENTOPIA_INTERNAL_AUTH_TOKEN"] = "shared-token"
        os.environ["PAPERCLIP_RESULT_URL"] = "http://127.0.0.1:3100/internal/tasks/{task_id}/result"
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
        conn.request("GET", "/health")
        response = conn.getresponse()
        payload = json.loads(response.read().decode())
        self.assertEqual(response.status, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["dependencies"]["internal_auth_configured"])
        self.assertTrue(payload["dependencies"]["paperclip_result_url_configured"])
        conn.close()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
