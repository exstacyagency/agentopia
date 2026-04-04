from __future__ import annotations

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "received": {"validating", "cancelled"},
    "validating": {"pending_approval", "approved", "cancelled"},
    "pending_approval": {"approved", "rejected", "cancelled"},
    "approved": {"queued", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"succeeded", "failed", "cancelled"},
    "succeeded": set(),
    "failed": set(),
    "rejected": set(),
    "cancelled": set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def assert_transition(current: str, target: str) -> None:
    if not can_transition(current, target):
        raise ValueError(f"invalid state transition: {current} -> {target}")
