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
from paperclip.service import PaperclipService

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


class CompletingDispatchClient:
    def __init__(self):
        self.service: PaperclipService | None = None

    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        assert self.service is not None
        result = dict(SUCCESS_RESULT)
        result["task_id"] = payload["task"]["id"]
        result["run"] = dict(SUCCESS_RESULT["run"])
        result["run"]["run_id"] = f"run_{payload['task']['id']}"
        self.service.record_result(payload["task"]["id"], result)
        return result


class HttpProcessE2ETests(unittest.TestCase):
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

        dispatch = CompletingDispatchClient()
        service = PaperclipService(tmp_path / "paperclip.sqlite3", dispatch_client=dispatch)
        dispatch.service = service
        paperclip_app.SERVICE = service

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def start_server(self):
        server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        time.sleep(0.05)
        return server, thread

    def test_public_http_flow_runs_task_to_completion_and_exposes_audit(self) -> None:
        server, thread = self.start_server()
        payload = FIXTURES.joinpath("task_request_valid.json").read_bytes()

        conn = HTTPConnection("127.0.0.1", server.server_address[1])
        conn.request(
            "POST",
            "/tasks",
            body=payload,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(payload)),
                "Authorization": "Bearer tenant-a-key",
                "Idempotency-Key": "e2e-001",
            },
        )
        response = conn.getresponse()
        created = json.loads(response.read().decode())
        self.assertEqual(response.status, 201)
        task_id = created["id"]
        conn.close()

        fetch = HTTPConnection("127.0.0.1", server.server_address[1])
        fetch.request("GET", f"/tasks/{task_id}", headers={"Authorization": "Bearer tenant-a-key"})
        fetch_response = fetch.getresponse()
        task = json.loads(fetch_response.read().decode())
        self.assertEqual(fetch_response.status, 200)
        self.assertEqual(task["state"], "succeeded")
        self.assertIn("result", task)
        fetch.close()

        audit = HTTPConnection("127.0.0.1", server.server_address[1])
        audit.request("GET", f"/tasks/{task_id}/audit", headers={"Authorization": "Bearer tenant-a-key"})
        audit_response = audit.getresponse()
        audit_body = json.loads(audit_response.read().decode())
        self.assertEqual(audit_response.status, 200)
        self.assertGreater(len(audit_body["events"]), 0)
        audit.close()

        history = HTTPConnection("127.0.0.1", server.server_address[1])
        history.request("GET", "/tasks", headers={"Authorization": "Bearer tenant-a-key"})
        history_response = history.getresponse()
        history_body = json.loads(history_response.read().decode())
        self.assertEqual(history_response.status, 200)
        self.assertEqual(len(history_body["tasks"]), 1)
        self.assertEqual(history_body["tasks"][0]["id"], task_id)
        history.close()

        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
