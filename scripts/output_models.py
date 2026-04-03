from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HandoffPolicy:
    budget_usd: int
    runtime_minutes: int
    approval_required: bool


@dataclass(frozen=True)
class TaskOutput:
    task_id: str
    title: str
    priority: str
    handoff_from: str = "paperclip"
    handoff_to: str = "hermes"
    policy: HandoffPolicy = field(default_factory=lambda: HandoffPolicy(0, 0, False))
    status: str = "success"
    summary: str = ""
    notes: tuple[str, ...] = ()
