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
    if task_type == "file_write":
        approval = payload.get("execution_policy", {}).get("approval", {})
        permissions = payload.get("execution_policy", {}).get("permissions", {})
        target_path = task.get("context", {}).get("file_path", "")
        if approval.get("required") and approval.get("status") == "approved" and permissions.get("write_scope") == "workspace_scoped" and target_path:
            return PolicyDecision(True, "explicit_file_write_approval", "allow")
        return PolicyDecision(False, "write_capable_requires_explicit_policy", "deny")
    if task_type in WRITE_CAPABLE_TASK_TYPES:
        return PolicyDecision(False, "write_capable_requires_explicit_policy", "deny")
    return PolicyDecision(False, "unsupported_task_type", "deny")
