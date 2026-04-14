from __future__ import annotations

import json
import os
from urllib import request
from urllib.error import HTTPError


class HermesDispatchClient:
    def __init__(self, base_url: str = "http://127.0.0.1:3200", auth_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token if auth_token is not None else os.environ.get("AGENTOPIA_INTERNAL_AUTH_TOKEN", "")

    def submit(self, payload: dict, correlation_id: str | None = None) -> dict:
        data = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        req = request.Request(
            f"{self.base_url}/internal/execute",
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            body = exc.read().decode()
            if body:
                return json.loads(body)
            raise
