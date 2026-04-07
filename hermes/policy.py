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


def evaluate_task_policy(task_type: str) -> PolicyDecision:
    if task_type in SAFE_TASK_TYPES:
        return PolicyDecision(True, "allowed_read_only", "allow")
    if task_type in WRITE_CAPABLE_TASK_TYPES:
        return PolicyDecision(False, "write_capable_requires_explicit_policy", "deny")
    return PolicyDecision(False, "unsupported_task_type", "deny")
