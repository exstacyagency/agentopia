from __future__ import annotations


class ToolPermissionError(RuntimeError):
    pass


TASK_TOOL_CLASS = {
    "repo_summary": "repo_read",
    "text_generation": "local_exec",
    "file_write": "file_write",
    "repo_write": "repo_write",
    "file_revert": "file_write",
    "shell_command": "local_exec",
}


def required_tool_class(task_type: str) -> str:
    return TASK_TOOL_CLASS.get(task_type, "unknown")


def enforce_tool_permission(task_request: dict) -> None:
    task_type = task_request.get("task", {}).get("type", "")
    required = required_tool_class(task_type)
    allowed = task_request.get("execution_policy", {}).get("permissions", {}).get("allowed_tool_classes", [])
    if required not in allowed:
        raise ToolPermissionError(f"tool class not allowed for task type {task_type}: {required}")
