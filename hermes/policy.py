from __future__ import annotations

from dataclasses import dataclass

SAFE_TASK_TYPES = {
    "repo_summary",
    "file_analysis",
    "text_generation",
    "structured_extract",
    "repo_change_plan",
    "implementation_draft",
}

WRITE_CAPABLE_TASK_TYPES = {
    "repo_write",
    "file_write",
    "file_revert",
    "shell_command",
}


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    mode: str


def evaluate_task_policy(payload: dict) -> PolicyDecision:
    task = payload["task"]
    task_type = task["type"]
    if task_type in SAFE_TASK_TYPES:
        return PolicyDecision(True, "allowed_read_only", "allow")

    approval = payload.get("execution_policy", {}).get("approval", {})
    permissions = payload.get("execution_policy", {}).get("permissions", {})
    context = task.get("context", {})

    if task_type == "file_write":
        target_path = context.get("file_path", "")
        overwrite = bool(context.get("overwrite", False))
        overwrite_approved = bool(context.get("overwrite_approved", False))
        if approval.get("required") and approval.get("status") == "approved" and permissions.get("write_scope") == "workspace_scoped" and target_path:
            if overwrite:
                if overwrite_approved:
                    return PolicyDecision(True, "explicit_file_write_overwrite_approval", "allow")
                return PolicyDecision(False, "overwrite_requires_explicit_approval", "deny")
            return PolicyDecision(True, "explicit_file_write_approval", "allow")
        return PolicyDecision(False, "write_capable_requires_explicit_policy", "deny")

    if task_type == "repo_write":
        changes = context.get("changes") or []
        apply_changes = bool(context.get("apply", False))
        if not approval.get("required") or approval.get("status") != "approved" or permissions.get("write_scope") != "workspace_scoped" or not changes:
            return PolicyDecision(False, "repo_write_requires_explicit_approval", "deny")
        if not apply_changes:
            return PolicyDecision(True, "repo_write_preview", "preview")
        overwrite_needed = any(bool(change.get("overwrite", False)) for change in changes)
        overwrite_approved = all(bool(change.get("overwrite_approved", False)) for change in changes if bool(change.get("overwrite", False)))
        if overwrite_needed and not overwrite_approved:
            return PolicyDecision(False, "repo_write_overwrite_requires_explicit_approval", "deny")
        return PolicyDecision(True, "explicit_repo_write_approval", "allow")

    if task_type == "file_revert":
        target_path = context.get("file_path", "")
        previous_content = context.get("previous_content")
        if approval.get("required") and approval.get("status") == "approved" and permissions.get("write_scope") == "workspace_scoped" and target_path and previous_content is not None:
            return PolicyDecision(True, "explicit_file_revert_approval", "allow")
        return PolicyDecision(False, "file_revert_requires_explicit_approval", "deny")

    if task_type in WRITE_CAPABLE_TASK_TYPES:
        return PolicyDecision(False, "write_capable_requires_explicit_policy", "deny")
    return PolicyDecision(False, "unsupported_task_type", "deny")
