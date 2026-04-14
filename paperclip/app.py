from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from paperclip.dispatch import HermesDispatchClient
from paperclip.service import PaperclipService

ROOT = Path(__file__).resolve().parent.parent
PAPERCLIP_DB_PATH = Path(os.environ.get("PAPERCLIP_DB_PATH", str(ROOT / "data" / "paperclip.sqlite3")))
HERMES_BASE_URL = os.environ.get("HERMES_BASE_URL", "http://127.0.0.1:3200")
SERVICE = PaperclipService(PAPERCLIP_DB_PATH, dispatch_client=HermesDispatchClient(HERMES_BASE_URL))
MAX_REQUEST_BYTES = int(os.environ.get("PAPERCLIP_MAX_REQUEST_BYTES", str(1024 * 1024)))


class PaperclipHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_REQUEST_BYTES:
            self._send(413, {"error": "request body too large", "max_bytes": MAX_REQUEST_BYTES})
            raise ValueError("request_too_large")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode())

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.path == "/":
            self._send_html(200, """<!doctype html>
<html>
  <head><meta charset=\"utf-8\"><title>Paperclip</title></head>
  <body>
    <h1>Paperclip</h1>
    <p>Status: healthy</p>
    <p>Role: control plane</p>
    <h2>Available endpoints</h2>
    <ul>
      <li><code>GET /health</code></li>
      <li><code>POST /tasks</code></li>
      <li><code>GET /tasks/&lt;id&gt;</code></li>
      <li><code>GET /tasks/&lt;id&gt;/audit</code></li>
      <li><code>POST /internal/tasks/&lt;id&gt;/result</code></li>
    </ul>
  </body>
</html>""")
            return
        if parsed.path == "/health":
            self._send(200, {"ok": True, "service": "paperclip"})
            return
        if len(parts) == 2 and parts[0] == "tasks":
            task = SERVICE.get_task(parts[1])
            if task is None:
                self._send(404, {"error": "task not found"})
                return
            self._send(200, task)
            return
        if len(parts) == 3 and parts[0] == "tasks" and parts[2] == "audit":
            self._send(200, {"events": SERVICE.get_audit(parts[1])})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        try:
            body = self._read_json_body()
            if parsed.path == "/tasks":
                task = SERVICE.submit_task(body)
                self._send(201, task)
                return
            if len(parts) == 4 and parts[0] == "internal" and parts[1] == "tasks" and parts[3] == "result":
                task = SERVICE.record_result(parts[2], body)
                self._send(200, task)
                return
            if len(parts) == 3 and parts[0] == "tasks" and parts[2] in {"approve", "reject"}:
                target_state = "approved" if parts[2] == "approve" else "rejected"
                task = SERVICE.transition_task(parts[1], target_state, actor="human", details={"action": parts[2]})
                if target_state == "approved":
                    task = SERVICE.dispatch_task(parts[1])
                self._send(200, task)
                return
        except ValueError as exc:
            if str(exc) == "request_too_large":
                return
            self._send(400, {"error": str(exc)})
            return
        except KeyError:
            self._send(404, {"error": "task not found"})
            return
        self._send(404, {"error": "not found"})


def main() -> int:
    port = int(os.environ.get("PAPERCLIP_PORT", "3100"))
    server = ThreadingHTTPServer(("0.0.0.0", port), PaperclipHandler)
    print(f"paperclip listening on http://0.0.0.0:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
