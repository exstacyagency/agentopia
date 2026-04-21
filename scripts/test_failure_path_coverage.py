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


class FailingDispatchClient:
    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        raise RuntimeError("dispatch failed")


class NoopDispatchClient:
    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        return {"accepted": True}


class FailurePathCoverageTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_dispatch_failure_schedules_retry_and_preserves_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=FailingDispatchClient())
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "queued")
            queue_item = service.db.get_queue_item(task["id"])
            self.assertEqual(queue_item["status"], "queued")
            self.assertEqual(queue_item["attempt_count"], 1)
            self.assertEqual(queue_item["last_error"], "dispatch failed")

    def test_cannot_cancel_terminal_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=NoopDispatchClient())
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            service.record_result(task["id"], SUCCESS_RESULT)
            with self.assertRaises(ValueError):
                service.cancel_task(task["id"], actor="operator", reason="too late")

    def test_http_cancel_of_missing_task_returns_task_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
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

            server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()
            time.sleep(0.05)

            body = json.dumps({"reason": "missing"}).encode()
            conn = HTTPConnection("127.0.0.1", server.server_address[1])
            conn.request(
                "POST",
                "/tasks/missing-task/cancel",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                    "Authorization": "Bearer tenant-a-key",
                },
            )
            response = conn.getresponse()
            payload = json.loads(response.read().decode())
            self.assertEqual(response.status, 404)
            self.assertEqual(payload["error"]["code"], "task_not_found")
            conn.close()

            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
