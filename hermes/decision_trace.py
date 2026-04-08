from __future__ import annotations

from typing import Any


def build_decision_trace(task: dict[str, Any], policy_mode: str, policy_reason: str, context: dict[str, Any]) -> dict[str, Any]:
    task_type = task.get("type")
    approval_required = ((context or {}).get("paperclip_approval_id") is not None) or bool(task_type in {"file_write", "repo_write", "file_revert"})
    target_paths: list[str] = []
    if context.get("file_path"):
        target_paths.append(context.get("file_path"))
    for change in context.get("changes") or []:
        if change.get("file_path"):
            target_paths.append(change.get("file_path"))

    return {
        "requested_intent": task.get("description"),
        "mapped_task_type": task_type,
        "policy_evaluation": {
            "mode": policy_mode,
            "reason": policy_reason,
        },
        "approval": {
            "required": approval_required,
            "paperclip_approval_id": context.get("paperclip_approval_id"),
            "paperclip_approval_status": context.get("paperclip_approval_status"),
        },
        "target_paths": target_paths,
        "issue_id": context.get("issue_id"),
        "paperclip_run_id": context.get("paperclip_run_id"),
        "agent_id": context.get("agent_id"),
        "decision_summary": f"{task_type} resolved with policy mode {policy_mode} because {policy_reason}",
    }
