from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes.apply_resolution import resolve_issue_apply_candidates
from hermes.executor import HermesExecutor
from hermes.persistence import HermesPersistence
from hermes.revert_resolution import resolve_issue_revert_candidates

ROOT = Path(__file__).resolve().parent.parent
EXECUTOR = HermesExecutor(ROOT)
PERSISTENCE = HermesPersistence(ROOT)


def build_issue_action_response(action: str, issue_id: str, accepted: bool, reason: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ok": accepted,
        "issue_id": issue_id,
        "action": action,
        "reason": reason,
        "details": details or {},
    }


def execute_issue_file_revert(issue_id: str, context: dict[str, Any]) -> dict[str, Any]:
    submitted_at = datetime.now(timezone.utc).isoformat()
    source_run_id = context.get("source_run_id") or "unknown-run"
    payload = {
        "schema_version": "v1",
        "task": {
            "id": f"issue-revert-{source_run_id}",
            "type": "file_revert",
            "title": f"Revert issue write for {issue_id}",
            "description": f"Revert a previously applied file write for issue {issue_id}",
            "priority": "medium",
            "risk_level": "medium",
            "requester": {"id": "paperclip-ui", "display_name": "Paperclip UI"},
            "context": {
                "issue_id": issue_id,
                **context,
            },
            "created_at": submitted_at,
        },
        "execution_policy": {
            "budget": {"max_cost_usd": 5.0, "max_runtime_minutes": 15},
            "approval": {
                "required": True,
                "status": "approved",
                "approved_by": "paperclip-ui",
                "approved_at": submitted_at,
            },
            "permissions": {
                "allow_network": False,
                "allow_memory": True,
                "allow_tools": True,
                "allowed_tool_classes": ["local_exec"],
                "write_scope": "workspace_scoped",
            },
            "output_requirements": {
                "format": "markdown",
                "length": "short",
                "include_artifacts": True,
            },
        },
        "routing": {
            "source": "paperclip",
            "destination": "hermes",
            "callback": {
                "result_url": f"http://127.0.0.1:3200/internal/tasks/issue-revert-{source_run_id}/result",
                "auth_mode": "shared_token",
            },
        },
        "trace": {
            "trace_id": f"trace-issue-revert-{source_run_id}",
            "submitted_at": submitted_at,
        },
    }
    result = EXECUTOR.execute(payload)
    persisted_path = PERSISTENCE.persist_result(result)
    return build_issue_action_response(
        "file_revert",
        issue_id,
        result.get("run", {}).get("status") == "succeeded",
        "issue_revert_executed",
        {
            "result": result,
            "persisted_path": str(persisted_path),
        },
    )


def execute_issue_apply_preview(issue_id: str, context: dict[str, Any]) -> dict[str, Any]:
    submitted_at = datetime.now(timezone.utc).isoformat()
    source_run_id = context.get("source_run_id") or "unknown-run"
    payload = {
        "schema_version": "v1",
        "task": {
            "id": f"issue-apply-{source_run_id}",
            "type": "repo_write",
            "title": f"Apply preview for issue {issue_id}",
            "description": f"Apply a previously previewed repo write for issue {issue_id}",
            "priority": "medium",
            "risk_level": "medium",
            "requester": {"id": "paperclip-ui", "display_name": "Paperclip UI"},
            "context": {
                "issue_id": issue_id,
                **context,
            },
            "created_at": submitted_at,
        },
        "execution_policy": {
            "budget": {"max_cost_usd": 5.0, "max_runtime_minutes": 15},
            "approval": {
                "required": True,
                "status": "approved",
                "approved_by": "paperclip-ui",
                "approved_at": submitted_at,
            },
            "permissions": {
                "allow_network": False,
                "allow_memory": True,
                "allow_tools": True,
                "allowed_tool_classes": ["local_exec"],
                "write_scope": "workspace_scoped",
            },
            "output_requirements": {
                "format": "markdown",
                "length": "short",
                "include_artifacts": True,
            },
        },
        "routing": {
            "source": "paperclip",
            "destination": "hermes",
            "callback": {
                "result_url": f"http://127.0.0.1:3200/internal/tasks/issue-apply-{source_run_id}/result",
                "auth_mode": "shared_token",
            },
        },
        "trace": {
            "trace_id": f"trace-issue-apply-{source_run_id}",
            "submitted_at": submitted_at,
        },
    }
    result = EXECUTOR.execute(payload)
    persisted_path = PERSISTENCE.persist_result(result)
    return build_issue_action_response(
        "apply_preview",
        issue_id,
        result.get("run", {}).get("status") == "succeeded",
        "issue_apply_executed",
        {
            "result": result,
            "persisted_path": str(persisted_path),
        },
    )


def handle_issue_action(payload: dict[str, Any]) -> dict[str, Any]:
    issue_id = payload.get("issue_id") or ""
    action = payload.get("action") or ""
    context = payload.get("context") or {}

    if not issue_id:
        return build_issue_action_response(action or "unknown", issue_id, False, "issue_id_required")

    if action == "resolve_revert_candidates":
        candidates = resolve_issue_revert_candidates(ROOT, issue_id)
        return build_issue_action_response(
            action,
            issue_id,
            True,
            "revert_candidates_resolved",
            {"candidates": candidates},
        )

    if action == "resolve_apply_candidates":
        candidates = resolve_issue_apply_candidates(ROOT, issue_id)
        return build_issue_action_response(
            action,
            issue_id,
            True,
            "apply_candidates_resolved",
            {"candidates": candidates},
        )

    if action == "apply_preview":
        return execute_issue_apply_preview(issue_id, context)

    if action == "file_revert":
        return execute_issue_file_revert(issue_id, context)

    return build_issue_action_response(action, issue_id, False, "unsupported_issue_action")
