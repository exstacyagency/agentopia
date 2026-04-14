from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from hermes.build_info import BUILD_STAMP, RUNTIME_FEATURES
from hermes.callback_store import HermesCallbackStore
from hermes.dashboard_state import build_operator_queue_state
from hermes.executor import HermesExecutor
from hermes.issue_actions import handle_issue_action
from hermes.memory.service import MemPalaceService
from hermes.paperclip_comments import PaperclipCommentPoster
from hermes.persistence import HermesPersistence
from hermes.postback_store import HermesPostbackStore
from hermes.runtime_checks import summarize_runtime_guards
from scripts.input_validation import InputValidationError, validate_strings
from scripts.rate_limit import InMemoryRateLimiter

ROOT = os.path.dirname(os.path.dirname(__file__))
EXECUTOR = HermesExecutor(os.path.abspath(ROOT))
PERSISTENCE = HermesPersistence(os.path.abspath(ROOT))
CALLBACK_STORE = HermesCallbackStore(os.path.abspath(ROOT))
POSTBACK_STORE = HermesPostbackStore(os.path.abspath(ROOT))
COMMENT_POSTER = PaperclipCommentPoster()
MEMPALACE = MemPalaceService()
PAPERCLIP_RESULT_URL = os.environ.get("PAPERCLIP_RESULT_URL", "http://127.0.0.1:3200/internal/tasks/{task_id}/result")
MAX_REQUEST_BYTES = int(os.environ.get("HERMES_MAX_REQUEST_BYTES", str(1024 * 1024)))
RATE_LIMIT_COUNT = int(os.environ.get("HERMES_RATE_LIMIT_COUNT", "30"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("HERMES_RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMITER = InMemoryRateLimiter(RATE_LIMIT_COUNT, RATE_LIMIT_WINDOW_SECONDS)


class HermesHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _client_ip(self) -> str:
        return self.client_address[0] if self.client_address else "unknown"

    def _enforce_rate_limit(self) -> bool:
        if RATE_LIMITER.allow(self._client_ip()):
            return True
        self._send(429, {"error": "rate limit exceeded", "limit": RATE_LIMIT_COUNT, "window_seconds": RATE_LIMIT_WINDOW_SECONDS})
        return False

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_REQUEST_BYTES:
            self._send(413, {"error": "request body too large", "max_bytes": MAX_REQUEST_BYTES})
            raise ValueError("request_too_large")
        raw = self.rfile.read(length) if length else b"{}"
        body = json.loads(raw.decode() or "{}")
        validate_strings(body)
        return body

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send(
                200,
                {
                    "ok": True,
                    "service": "hermes",
                    "runtime": summarize_runtime_guards(getattr(COMMENT_POSTER, "base_url", None)),
                    "build": {
                        "stamp": BUILD_STAMP,
                        "features": RUNTIME_FEATURES,
                    },
                },
            )
            return
        if parsed.path == "/internal/dashboard-state":
            self._send(200, build_operator_queue_state(os.path.abspath(ROOT)))
            return
        if parsed.path == "/internal/memory/config":
            self._send(200, {"config": MEMPALACE.get_config()})
            return
        if parsed.path == "/internal/memory/status":
            self._send(200, MEMPALACE.status())
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if not self._enforce_rate_limit():
            return
        try:
            body = self._read_json_body()
        except InputValidationError as exc:
            self._send(400, {"error": str(exc)})
            return
        except ValueError as exc:
            if str(exc) == "request_too_large":
                return
            raise

        if parsed.path.startswith("/internal/tasks/") and parsed.path.endswith("/result"):
            task_id = parsed.path.split("/")[3]
            stored = CALLBACK_STORE.store(task_id, body)
            self._send(200, {"ok": True, "task_id": task_id, "stored_path": str(stored)})
            return

        if parsed.path == "/internal/issue-action":
            response = handle_issue_action(body)
            self._send(200 if response.get("ok") else 400, response)
            return

        if parsed.path == "/internal/memory/search":
            query = body.get("query", "")
            self._send(200, MEMPALACE.search(query))
            return

        if parsed.path == "/internal/memory/wakeup":
            issue_title = body.get("issue_title", "")
            issue_description = body.get("issue_description", "")
            self._send(200, MEMPALACE.wakeup(issue_title, issue_description))
            return

        if parsed.path == "/internal/memory/config":
            self._send(200, {"config": MEMPALACE.set_config(body)})
            return

        if parsed.path == "/internal/memory/status":
            self._send(200, MEMPALACE.status())
            return

        if parsed.path == "/internal/memory/mine":
            self._send(200, MEMPALACE.run_operation("mine"))
            return

        if parsed.path == "/internal/memory/reindex":
            self._send(200, MEMPALACE.run_operation("reindex"))
            return

        if parsed.path != "/internal/execute":
            self._send(404, {"error": "not found"})
            return

        result = EXECUTOR.execute(body)
        persisted_path = PERSISTENCE.persist_result(result)
        result["persistence"] = {"result_path": str(persisted_path)}

        metadata = (result.get("result") or {}).get("metadata") or {}
        issue_id = metadata.get("paperclip_issue_id")
        if issue_id:
            try:
                comment_result = COMMENT_POSTER.post_execution_summary(issue_id, result)
                result["persistence"]["paperclip_comment"] = {
                    "success": True,
                    "comment_id": comment_result.get("id"),
                }
                postback_path = POSTBACK_STORE.record(
                    issue_id=issue_id,
                    run_id=result["run"]["run_id"],
                    postback_type="comment",
                    success=True,
                    error=None,
                    payload={
                        **result["persistence"]["paperclip_comment"],
                        "body": COMMENT_POSTER.build_execution_comment_body(result),
                    },
                )
                result["persistence"]["paperclip_comment"]["postback_path"] = str(postback_path)
            except Exception as exc:
                postback_path = POSTBACK_STORE.record(
                    issue_id=issue_id,
                    run_id=result["run"]["run_id"],
                    postback_type="comment",
                    success=False,
                    error=str(exc),
                    payload={
                        "issue_id": issue_id,
                        "body": COMMENT_POSTER.build_execution_comment_body(result),
                    },
                )
                result["persistence"]["paperclip_comment"] = {
                    "success": False,
                    "error": str(exc),
                    "issue_id": issue_id,
                    "postback_path": str(postback_path),
                }
            try:
                dashboard_result = COMMENT_POSTER.publish_issue_dashboard(issue_id, result)
                result["persistence"]["paperclip_dashboard"] = {
                    "success": True,
                    "document_id": dashboard_result.get("id"),
                    "key": dashboard_result.get("key"),
                }
                dashboard_doc = COMMENT_POSTER.build_issue_dashboard_document(result)
                postback_path = POSTBACK_STORE.record(
                    issue_id=issue_id,
                    run_id=result["run"]["run_id"],
                    postback_type="dashboard",
                    success=True,
                    error=None,
                    payload={
                        **result["persistence"]["paperclip_dashboard"],
                        **dashboard_doc,
                    },
                )
                result["persistence"]["paperclip_dashboard"]["postback_path"] = str(postback_path)
            except Exception as exc:
                dashboard_doc = COMMENT_POSTER.build_issue_dashboard_document(result)
                postback_path = POSTBACK_STORE.record(
                    issue_id=issue_id,
                    run_id=result["run"]["run_id"],
                    postback_type="dashboard",
                    success=False,
                    error=str(exc),
                    payload={
                        "issue_id": issue_id,
                        **dashboard_doc,
                    },
                )
                result["persistence"]["paperclip_dashboard"] = {
                    "success": False,
                    "error": str(exc),
                    "issue_id": issue_id,
                    "postback_path": str(postback_path),
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
