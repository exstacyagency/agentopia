from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from hermes.executor import HermesExecutor

ROOT = Path(__file__).resolve().parent.parent
EXECUTOR = HermesExecutor(ROOT)


class HermesHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send(200, {"ok": True, "service": "hermes"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/internal/execute":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        body = json.loads(raw.decode())
        result = EXECUTOR.execute(body)
        status = 200 if result["run"]["status"] == "succeeded" else 400
        self._send(status, result)


def main() -> int:
    server = HTTPServer(("0.0.0.0", 3200), HermesHandler)
    print("hermes listening on http://0.0.0.0:3200")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
