#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from paperclip_adapter.http_client import PaperclipClientConfig, PaperclipHttpClient
from paperclip_adapter.models import PaperclipApprovalCreate, PaperclipExecutionTrigger, PaperclipIssueCreate


class FakePaperclipHandler(BaseHTTPRequestHandler):
    calls = []

    def _send(self, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode())
        FakePaperclipHandler.calls.append((self.path, payload, dict(self.headers)))
        if self.path.endswith("/issues"):
            self._send({"id": "ISSUE-123", "ok": True})
            return
        if self.path.endswith("/approvals"):
            self._send({"id": "APPROVAL-123", "ok": True})
            return
        if self.path.endswith("/wakeup"):
            self._send({"id": "WAKE-123", "ok": True})
            return
        self._send({"ok": True})


class PaperclipHttpClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), FakePaperclipHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def setUp(self):
        FakePaperclipHandler.calls.clear()
        self.client = PaperclipHttpClient(PaperclipClientConfig(base_url=f"http://127.0.0.1:{self.port}", bearer_token="token-123"))

    def test_create_issue_posts_expected_payload(self):
        response = self.client.create_issue(PaperclipIssueCreate(
            company_id="company_123",
            title="Issue title",
            description="Issue body",
            priority="medium",
            project_id="project_123",
            goal_id="goal_123",
            metadata={"agentopia": {"task_id": "task_123"}},
        ))
        self.assertEqual(response["id"], "ISSUE-123")
        path, payload, headers = FakePaperclipHandler.calls[-1]
        self.assertEqual(path, "/companies/company_123/issues")
        self.assertEqual(payload["projectId"], "project_123")
        self.assertEqual(headers["Authorization"], "Bearer token-123")

    def test_create_approval_and_wakeup_post_expected_payloads(self):
        approval = self.client.create_approval(PaperclipApprovalCreate(
            company_id="company_123",
            approval_type="agentopia_task_execution",
            payload={"issueId": "ISSUE-123"},
            linked_issue_ids=["ISSUE-123"],
        ))
        wake = self.client.wake_agent(PaperclipExecutionTrigger(
            agent_id="agent_123",
            source="agentopia",
            trigger_detail="paperclip_issue_execution",
            payload={"issueId": "ISSUE-123"},
        ))
        self.assertEqual(approval["id"], "APPROVAL-123")
        self.assertEqual(wake["id"], "WAKE-123")
        self.assertEqual(FakePaperclipHandler.calls[0][0], "/companies/company_123/approvals")
        self.assertEqual(FakePaperclipHandler.calls[1][0], "/agents/agent_123/wakeup")


if __name__ == "__main__":
    unittest.main()
