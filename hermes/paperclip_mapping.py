from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PaperclipTaskContext:
    issue_id: str | None = None
    paperclip_run_id: str | None = None
    agent_id: str | None = None
    paperclip_approval_id: str | None = None
    paperclip_approval_status: str | None = None
    extras: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.issue_id is not None:
            payload["issue_id"] = self.issue_id
        if self.paperclip_run_id is not None:
            payload["paperclip_run_id"] = self.paperclip_run_id
        if self.agent_id is not None:
            payload["agent_id"] = self.agent_id
        if self.paperclip_approval_id is not None:
            payload["paperclip_approval_id"] = self.paperclip_approval_id
        if self.paperclip_approval_status is not None:
            payload["paperclip_approval_status"] = self.paperclip_approval_status
        if self.extras:
            payload.update(self.extras)
        return payload
