#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from http.client import HTTPConnection
from urllib.parse import urlparse


class PaperclipClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _request(self, method: str, path: str, body: dict | None = None, headers: dict | None = None) -> tuple[int, dict | str]:
        parsed = urlparse(self.base_url)
        conn = HTTPConnection(parsed.hostname, parsed.port or 80)
        payload = json.dumps(body).encode() if body is not None else None
        request_headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
            request_headers["Content-Length"] = str(len(payload))
        if headers:
            request_headers.update(headers)
        conn.request(method, path, body=payload, headers=request_headers)
        response = conn.getresponse()
        raw = response.read().decode()
        conn.close()
        try:
            return response.status, json.loads(raw)
        except Exception:
            return response.status, raw

    def submit_task(self, payload: dict, *, idempotency_key: str | None = None, webhook_url: str | None = None):
        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if webhook_url:
            headers["X-Webhook-Url"] = webhook_url
        return self._request("POST", "/tasks", body=payload, headers=headers)

    def get_task(self, task_id: str):
        return self._request("GET", f"/tasks/{task_id}")

    def wait_for_terminal_state(self, task_id: str, *, timeout_seconds: int = 30, poll_interval_seconds: float = 1.0):
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            status, payload = self.get_task(task_id)
            if status != 200:
                return status, payload
            if payload.get("state") in {"succeeded", "failed", "rejected", "cancelled"}:
                return status, payload
            time.sleep(poll_interval_seconds)
        return 408, {"error": {"code": "client_timeout", "message": "Timed out waiting for terminal state", "status": 408}}
