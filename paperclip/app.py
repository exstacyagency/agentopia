from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from paperclip.service import PaperclipService

ROOT = Path(__file__).resolve().parent.parent
SERVICE = PaperclipService(ROOT / "data" / "paperclip.sqlite3")


class PaperclipHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
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
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        body = json.loads(raw.decode())
        try:
            if parsed.path == "/tasks":
                task = SERVICE.submit_task(body)
                self._send(201, task)
                return
            if len(parts) == 3 and parts[0] == "tasks" and parts[2] in {"approve", "reject"}:
                target_state = "approved" if parts[2] == "approve" else "rejected"
                task = SERVICE.transition_task(parts[1], target_state, actor="human", details={"action": parts[2]})
                self._send(200, task)
                return
        except KeyError:
            self._send(404, {"error": "task not found"})
            return
        except ValueError as exc:
            self._send(400, {"error": str(exc)})
            return
        self._send(404, {"error": "not found"})


def main() -> int:
    server = HTTPServer(("0.0.0.0", 3100), PaperclipHandler)
    print("paperclip listening on http://0.0.0.0:3100")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
