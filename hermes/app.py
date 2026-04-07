from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import request
from urllib.parse import urlparse

from hermes.executor import HermesExecutor
from hermes.persistence import HermesPersistence
from hermes.callback_store import HermesCallbackStore

ROOT = Path(__file__).resolve().parent.parent
EXECUTOR = HermesExecutor(ROOT)
PERSISTENCE = HermesPersistence(ROOT)
CALLBACK_STORE = HermesCallbackStore(ROOT)
PAPERCLIP_RESULT_URL = os.environ.get("PAPERCLIP_RESULT_URL", "http://127.0.0.1:3100/internal/tasks/{task_id}/result")


class HermesHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(200, """<!doctype html>
<html>
  <head><meta charset=\"utf-8\"><title>Hermes</title></head>
  <body>
    <h1>Hermes</h1>
    <p>Status: healthy</p>
    <p>Role: execution plane</p>
    <h2>Available endpoints</h2>
    <ul>
      <li><code>GET /health</code></li>
      <li><code>POST /internal/execute</code></li>
    </ul>
  </body>
</html>""")
            return
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
        persisted_path = PERSISTENCE.persist_result(result)
        result.setdefault("persistence", {})["result_path"] = str(persisted_path)
        result_url = PAPERCLIP_RESULT_URL.format(task_id=result["task_id"])
        req = request.Request(
            result_url,
            data=json.dumps(result).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        callback_success = False
        callback_status = None
        callback_error = None
        try:
            with request.urlopen(req) as response:
                callback_status = getattr(response, "status", None)
                response.read()
                callback_success = True
        except Exception as exc:
            callback_error = str(exc)
        callback_path = PERSISTENCE.record_callback_attempt(
            task_id=result["task_id"],
            run_id=result["run"]["run_id"],
            result_url=result_url,
            success=callback_success,
            status_code=callback_status,
            error=callback_error,
        )
        result["persistence"]["callback_path"] = str(callback_path)
        result["persistence"]["callback"] = {
            "success": callback_success,
            "status_code": callback_status,
            "error": callback_error,
        }
        status = 200 if result["run"]["status"] == "succeeded" else 400
        self._send(status, result)


def main() -> int:
    port = int(os.environ.get("HERMES_PORT", "3200"))
    server = ThreadingHTTPServer(("0.0.0.0", port), HermesHandler)
    print(f"hermes listening on http://0.0.0.0:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
