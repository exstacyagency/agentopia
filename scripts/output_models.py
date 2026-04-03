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
        data["task"] = {
            "id": data.pop("task_id"),
            "title": data.pop("title"),
            "priority": data.pop("priority"),
        }
        data["handoff"] = {
            "from": data.pop("handoff_from"),
            "to": data.pop("handoff_to"),
            "policy": data.pop("policy"),
        }
        data["execution"] = {
            "status": data.pop("status"),
            "summary": data.pop("summary"),
            "notes": list(data.pop("notes")),
        }
        return data
