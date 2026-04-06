from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any
from urllib import request

from paperclip_adapter.models import PaperclipApprovalCreate, PaperclipExecutionTrigger, PaperclipIssueCreate


@dataclass(frozen=True)
class PaperclipClientConfig:
    base_url: str
    bearer_token: str | None = None


class PaperclipHttpClient:
    def __init__(self, config: PaperclipClientConfig):
        self.config = config

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"
        return headers

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode()
        req = request.Request(
            f"{self.config.base_url.rstrip('/')}{path}",
            data=body,
            headers=self._headers(),
            method=method,
        )
        with request.urlopen(req) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}

    def create_issue(self, issue: PaperclipIssueCreate) -> dict[str, Any]:
        payload = {
            "title": issue.title,
            "description": issue.description,
            "priority": issue.priority,
            "projectId": issue.project_id,
            "goalId": issue.goal_id,
            "metadata": issue.metadata,
        }
        return self._request("POST", f"/companies/{issue.company_id}/issues", payload)

    def create_issue_obj(self, issue: dict[str, Any]) -> dict[str, Any]:
        return self.create_issue(PaperclipIssueCreate(**issue))

    def create_approval(self, approval: PaperclipApprovalCreate) -> dict[str, Any]:
        payload = {
            "approvalType": approval.approval_type,
            "payload": approval.payload,
            "linkedIssueIds": approval.linked_issue_ids,
        }
        return self._request("POST", f"/companies/{approval.company_id}/approvals", payload)

    def create_approval_obj(self, approval: dict[str, Any]) -> dict[str, Any]:
        return self.create_approval(PaperclipApprovalCreate(**approval))

    def wake_agent(self, trigger: PaperclipExecutionTrigger) -> dict[str, Any]:
        payload = {
            "source": trigger.source,
            "triggerDetail": trigger.trigger_detail,
            "payload": trigger.payload,
        }
        return self._request("POST", f"/agents/{trigger.agent_id}/wakeup", payload)

    def wake_agent_obj(self, trigger: dict[str, Any]) -> dict[str, Any]:
        return self.wake_agent(PaperclipExecutionTrigger(**trigger))
