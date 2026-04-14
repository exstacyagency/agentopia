from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from paperclip.dispatch import HermesDispatchClient
from paperclip.service import PaperclipService
from scripts.api_keys import configured_client_api_keys, configured_client_api_keys_file, resolve_api_key_identity, resolve_api_key_identity_from_file, role_allows_scope
from scripts.correlation import CORRELATION_HEADER, get_or_create_correlation_id
from scripts.input_validation import InputValidationError, validate_strings
from scripts.metrics import MetricsRegistry
from scripts.rate_limit import InMemoryRateLimiter
from scripts.structured_logging import log_event

ROOT = Path(__file__).resolve().parent.parent
PAPERCLIP_DB_PATH = Path(os.environ.get("PAPERCLIP_DB_PATH", str(ROOT / "data" / "paperclip.sqlite3")))
HERMES_BASE_URL = os.environ.get("HERMES_BASE_URL", "http://127.0.0.1:3200")
INTERNAL_AUTH_TOKEN = os.environ.get("AGENTOPIA_INTERNAL_AUTH_TOKEN", "")
CLIENT_API_TOKEN = os.environ.get("PAPERCLIP_CLIENT_API_KEY", "")
CLIENT_API_KEYS = configured_client_api_keys()
CLIENT_API_KEYS_FILE = configured_client_api_keys_file()
SERVICE = PaperclipService(PAPERCLIP_DB_PATH, dispatch_client=HermesDispatchClient(HERMES_BASE_URL, auth_token=INTERNAL_AUTH_TOKEN))
MAX_REQUEST_BYTES = int(os.environ.get("PAPERCLIP_MAX_REQUEST_BYTES", str(1024 * 1024)))
RATE_LIMIT_COUNT = int(os.environ.get("PAPERCLIP_RATE_LIMIT_COUNT", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("PAPERCLIP_RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMITER = InMemoryRateLimiter(RATE_LIMIT_COUNT, RATE_LIMIT_WINDOW_SECONDS)
METRICS = MetricsRegistry()


class PaperclipHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode()
        correlation_id = getattr(self, "correlation_id", None)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if correlation_id:
            self.send_header(CORRELATION_HEADER, correlation_id)
        self.end_headers()
        self.wfile.write(body)
        METRICS.inc("paperclip_responses_sent_total")
        log_event("paperclip", "response_sent", status=status, path=self.path, correlation_id=correlation_id)

    def _client_ip(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _enforce_rate_limit(self) -> bool:
        if RATE_LIMITER.allow(self._client_ip()):
            return True
        self._send(429, {"error": "rate limit exceeded", "limit": RATE_LIMIT_COUNT, "window_seconds": RATE_LIMIT_WINDOW_SECONDS})
        return False

    def _require_internal_auth(self) -> bool:
        expected = INTERNAL_AUTH_TOKEN
        provided = self.headers.get("Authorization", "")
        if expected and provided == f"Bearer {expected}":
            return True
        self._send(401, {"error": "unauthorized"})
        return False

    def _require_client_auth(self) -> bool:
        provided = self.headers.get("Authorization", "")
        identity = resolve_api_key_identity_from_file(provided, CLIENT_API_KEYS_FILE)
        if identity is not None:
            if identity.status != "active":
                self._send(401, {"error": "unauthorized", "reason": "api_key_revoked"})
                return False
            if identity.scope == "tasks.write" or role_allows_scope(identity.role, "tasks.write"):
                self.client_api_identity = {
                    "key_id": identity.key_id,
                    "scope": identity.scope or "tasks.write",
                    "role": identity.role,
                    "source": "file",
                }
                return True
        identity = resolve_api_key_identity(provided, CLIENT_API_KEYS)
        if identity is not None and identity.scope == "tasks.write":
            self.client_api_identity = {"key_id": identity.key_id, "scope": identity.scope, "source": "env"}
            return True
        expected = CLIENT_API_TOKEN
        if expected and provided == f"Bearer {expected}":
            self.client_api_identity = {"key_id": "legacy-client-key", "scope": "tasks.write", "source": "legacy"}
            return True
        self._send(401, {"error": "unauthorized"})
        return False

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_REQUEST_BYTES:
            self._send(413, {"error": "request body too large", "max_bytes": MAX_REQUEST_BYTES})
            raise ValueError("request_too_large")
        raw = self.rfile.read(length) if length else b"{}"
        body = json.loads(raw.decode())
        validate_strings(body)
        return body

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
        if parsed.path == "/metrics":
            body = METRICS.render().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/health":
            dependencies = {
                "db_path_exists": PAPERCLIP_DB_PATH.parent.exists(),
                "internal_auth_configured": bool(INTERNAL_AUTH_TOKEN),
                "client_api_keys_file_exists": CLIENT_API_KEYS_FILE.exists(),
            }
            ok = all(dependencies.values())
            self._send(200 if ok else 503, {"ok": ok, "service": "paperclip", "dependencies": dependencies})
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
        self.correlation_id = get_or_create_correlation_id(self.headers)
        METRICS.inc("paperclip_requests_received_total")
        self.client_api_identity = None
        log_event("paperclip", "request_received", method="POST", path=parsed.path, correlation_id=self.correlation_id)
        if not self._enforce_rate_limit():
            METRICS.inc("paperclip_requests_rejected_total")
            log_event("paperclip", "request_rejected", reason="rate_limit", path=parsed.path, correlation_id=self.correlation_id)
            return
        try:
            body = self._read_json_body()
            if parsed.path == "/tasks":
                if not self._require_client_auth():
                    return
                task = SERVICE.submit_task(body)
                log_event(
                    "paperclip",
                    "client_api_authenticated",
                    path=parsed.path,
                    correlation_id=self.correlation_id,
                    api_key=self.client_api_identity,
                )
                self._send(201, task)
                return
            if len(parts) == 4 and parts[0] == "internal" and parts[1] == "tasks" and parts[3] == "result":
                if not self._require_internal_auth():
                    return
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
        except InputValidationError as exc:
            self._send(400, {"error": str(exc)})
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
    log_event("paperclip", "service_start", port=port)
    print(f"paperclip listening on http://0.0.0.0:{port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
