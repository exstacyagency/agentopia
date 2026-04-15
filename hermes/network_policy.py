from __future__ import annotations


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


def enforce_network_policy(task_request: dict, command: str) -> None:
    allow_network = bool(task_request.get("execution_policy", {}).get("permissions", {}).get("allow_network", False))
    if not allow_network and command_uses_network(command):
        raise NetworkEgressDeniedError(f"network egress denied for command: {command}")
