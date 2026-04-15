from __future__ import annotations

from hermes.runner import CommandRequest


class NetworkEgressDeniedError(RuntimeError):
    pass


NETWORK_COMMAND_HINTS = (
    "curl ",
    "wget ",
    "http://",
    "https://",
    "nc ",
    "ping ",
)


def command_uses_network(command: str) -> bool:
    lowered = command.lower()
    return any(hint in lowered for hint in NETWORK_COMMAND_HINTS)


def allow_network_for(task_request: dict) -> bool:
    return bool(task_request.get("execution_policy", {}).get("permissions", {}).get("allow_network", False))


def enforce_network_policy(task_request: dict, command: str) -> None:
    if not allow_network_for(task_request) and command_uses_network(command):
        raise NetworkEgressDeniedError(f"network egress denied for command: {command}")


def network_enabled_request(task_request: dict, command: str, cwd) -> CommandRequest:
    if not allow_network_for(task_request):
        raise NetworkEgressDeniedError(f"network-enabled execution denied for command: {command}")
    runtime_minutes = task_request.get("execution_policy", {}).get("budget", {}).get("max_runtime_minutes", 0)
    max_runtime_seconds = max(1, int(runtime_minutes * 60)) if runtime_minutes else None
    return CommandRequest(command=command, cwd=cwd, max_runtime_seconds=max_runtime_seconds)
