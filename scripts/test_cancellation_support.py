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


class HangingDispatchClient:
    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        return {"accepted": True}


class CancellationSupportTests(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text())

    def test_service_can_cancel_running_task_and_ignore_late_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = PaperclipService(Path(tmp) / "paperclip.sqlite3", dispatch_client=HangingDispatchClient())
            payload = self.load_fixture("task_request_valid.json")
            task = service.submit_task(payload)
            self.assertEqual(task["state"], "running")

            cancelled = service.cancel_task(task["id"], actor="operator", reason="user requested")
            self.assertEqual(cancelled["state"], "cancelled")
            queue_item = service.db.get_queue_item(task["id"])
            self.assertEqual(queue_item["status"], "cancelled")

            late = service.record_result(task["id"], SUCCESS_RESULT)
            self.assertEqual(late["state"], "cancelled")
            self.assertIsNone(service.db.get_result(task["id"]))

    def test_http_cancel_endpoint_cancels_tenant_owned_task(self) -> None:
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
            os.environ.pop("PAPERCLIP_CLIENT_API_KEYS", None)
            os.environ.pop("PAPERCLIP_CLIENT_API_KEY", None)
            reload(paperclip_app)
            paperclip_app.SERVICE = PaperclipService(tmp_path / "paperclip.sqlite3", dispatch_client=HangingDispatchClient())

            server = paperclip_app.ThreadingHTTPServer(("127.0.0.1", 0), paperclip_app.PaperclipHandler)
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()
            time.sleep(0.05)

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
                },
            )
            response = conn.getresponse()
            body = json.loads(response.read().decode())
            self.assertEqual(response.status, 201)
            task_id = body["id"]
            conn.close()

            cancel_body = json.dumps({"reason": "user requested"}).encode()
            cancel_conn = HTTPConnection("127.0.0.1", server.server_address[1])
            cancel_conn.request(
                "POST",
                f"/tasks/{task_id}/cancel",
                body=cancel_body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(cancel_body)),
                    "Authorization": "Bearer tenant-a-key",
                },
            )
            cancel_response = cancel_conn.getresponse()
            cancelled = json.loads(cancel_response.read().decode())
            self.assertEqual(cancel_response.status, 200)
            self.assertEqual(cancelled["state"], "cancelled")
            cancel_conn.close()

            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
