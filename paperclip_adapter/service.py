from __future__ import annotations

from typing import Any

from paperclip_adapter.client import PaperclipAdapter
from paperclip_adapter.http_client import PaperclipClientConfig, PaperclipHttpClient


class PaperclipAdapterService:
    def __init__(self, http_client: PaperclipHttpClient):
        self.http_client = http_client
        self.adapter = PaperclipAdapter()

    def submit_task(
        self,
        payload: dict[str, Any],
        *,
        company_id: str,
        execution_agent_id: str,
        project_id: str | None = None,
        goal_id: str | None = None,
    ) -> dict[str, Any]:
        plan = self.adapter.build_plan(
            payload,
            company_id=company_id,
            project_id=project_id,
            goal_id=goal_id,
            execution_agent_id=execution_agent_id,
        )
        issue = self.http_client.create_issue_obj(plan["issue_create"])
        approval = None
        if plan["approval_create"]:
            approval = self.http_client.create_approval_obj(plan["approval_create"] | {"linked_issue_ids": [issue["id"]]})
        wake = self.http_client.wake_agent_obj(plan["execution_trigger"] | {"payload": plan["execution_trigger"]["payload"] | {"issueId": issue["id"]}})
        return {
            "issue": issue,
            "approval": approval,
            "wake": wake,
        }


def build_http_client(base_url: str, bearer_token: str | None = None) -> PaperclipHttpClient:
    return PaperclipHttpClient(PaperclipClientConfig(base_url=base_url, bearer_token=bearer_token))
