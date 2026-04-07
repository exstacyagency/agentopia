from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from hermes.paperclip_mapping import PaperclipTaskContext


def build_task_request(
    *,
    task_id: str,
    task_type: str,
    title: str,
    description: str,
    requester_id: str,
    requester_name: str,
    priority: str,
    risk_level: str,
    context: PaperclipTaskContext,
    execution_policy: dict[str, Any],
    callback_url: str,
) -> dict[str, Any]:
    submitted_at = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": "v1",
        "task": {
            "id": task_id,
            "type": task_type,
            "title": title,
            "description": description,
            "priority": priority,
            "risk_level": risk_level,
            "requester": {
                "id": requester_id,
                "display_name": requester_name,
            },
            "context": context.to_dict(),
            "created_at": submitted_at,
        },
        "execution_policy": execution_policy,
        "routing": {
            "source": "paperclip",
            "destination": "hermes",
            "callback": {
                "result_url": callback_url,
                "auth_mode": "shared_token",
            },
        },
        "trace": {
            "trace_id": f"paperclip-{task_id}",
            "submitted_at": submitted_at,
        },
    }
