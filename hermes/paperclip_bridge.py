from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hermes.paperclip_mapping import map_paperclip_issue_to_task


def build_paperclip_task_request(
    *,
    issue_id: str,
    issue_title: str,
    issue_description: str,
    paperclip_run_id: str,
    agent_id: str,
    fallback_repo: str = "paperclip-runtime-workspace",
    result_url: str | None = None,
) -> dict[str, Any]:
    mapped = map_paperclip_issue_to_task(issue_title, issue_description, fallback_repo=fallback_repo)
    submitted_at = datetime.now(timezone.utc).isoformat()

    context = dict(mapped.context)
    context.update(
        {
            "issue_id": issue_id,
            "paperclip_run_id": paperclip_run_id,
            "agent_id": agent_id,
        }
    )

    return {
        "schema_version": "v1",
        "task": {
            "id": issue_id,
            "type": mapped.task_type,
            "title": issue_title,
            "description": issue_description,
            "priority": "medium",
            "risk_level": "low",
            "requester": {"id": "paperclip", "display_name": "Paperclip"},
            "context": context,
            "created_at": submitted_at,
        },
        "execution_policy": {
            "budget": {"max_cost_usd": 5.0, "max_runtime_minutes": 10},
            "approval": {"required": False, "status": "not_required"},
            "permissions": {
                "allow_network": False,
                "allow_memory": False,
                "allow_tools": False,
                "allowed_tool_classes": [],
                "write_scope": "none",
            },
            "output_requirements": {"format": "markdown", "length": "short", "include_artifacts": True},
        },
        "routing": {
            "source": "paperclip",
            "destination": "hermes",
            "callback": {
                "result_url": result_url or f"http://127.0.0.1:3100/internal/tasks/{issue_id}/result",
                "auth_mode": "shared_token",
            },
        },
        "trace": {
            "trace_id": f"paperclip-{paperclip_run_id}",
            "submitted_at": submitted_at,
        },
    }
