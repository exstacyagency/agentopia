from __future__ import annotations

import json
from urllib import request
from urllib.error import HTTPError


class HermesDispatchClient:
    def __init__(self, base_url: str = "http://127.0.0.1:3200"):
        self.base_url = base_url.rstrip("/")

    def submit(self, payload: dict) -> dict:
        data = json.dumps(payload).encode()
        req = request.Request(
            f"{self.base_url}/internal/execute",
            data=data,
            headers={"Content-Type": "application/json"},
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
