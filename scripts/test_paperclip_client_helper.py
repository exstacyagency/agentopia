#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
import unittest
from importlib import reload
from pathlib import Path

import paperclip.app as paperclip_app
from paperclip.service import PaperclipService
from scripts.paperclip_client_helper import PaperclipClient

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


class PaperclipClientHelperTests(unittest.TestCase):
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

    def test_helper_can_submit_and_wait_for_terminal_state(self) -> None:
        server, thread = self.start_server()
        client = PaperclipClient(f"http://127.0.0.1:{server.server_address[1]}", "tenant-a-key")
        payload = json.loads(FIXTURES.joinpath("task_request_valid.json").read_text())
        payload["task"]["id"] = "task_helper"

        status, created = client.submit_task(payload, idempotency_key="helper-001", webhook_url="https://example.com/webhook")
        self.assertEqual(status, 201)
        self.assertEqual(created["id"], "task_helper")

        status, task = client.wait_for_terminal_state("task_helper", timeout_seconds=5, poll_interval_seconds=0.1)
        self.assertEqual(status, 200)
        self.assertEqual(task["state"], "succeeded")

        audit = paperclip_app.SERVICE.get_audit("task_helper")
        webhook_events = [event for event in audit if event["event_type"] == "webhook_registered"]
        self.assertEqual(len(webhook_events), 1)

        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
