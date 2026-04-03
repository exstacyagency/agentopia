from __future__ import annotations

from dataclasses import dataclass, field, asdict


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

    def to_dict(self) -> dict:
        data = asdict(self)
        data["task_id"] = data.pop("task_id")
        data["handoff_from"] = data.pop("handoff_from")
        data["handoff_to"] = data.pop("handoff_to")
        data["policy"] = data["policy"]
        data["notes"] = list(data["notes"])
        return data
