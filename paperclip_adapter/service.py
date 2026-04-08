from __future__ import annotations

from typing import Any

from paperclip_adapter.client import PaperclipAdapter
from paperclip_adapter.comments import build_execution_summary_comment
from paperclip_adapter.http_client import PaperclipClientConfig, PaperclipHttpClient


class PaperclipAdapterService:
    def __init__(self, http_client: PaperclipHttpClient):
        self.http_client = http_client
        self.adapter = PaperclipAdapter()

    def post_execution_summary_comment(self, company_id: str, issue_id: str, result: dict[str, Any]) -> dict[str, Any]:
        comment = build_execution_summary_comment(result)
        return self.http_client.create_issue_comment(company_id, issue_id, comment)

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
        raw_issue = self.http_client.create_issue_obj(plan["issue_create"])
        issue = self.http_client.normalize_issue(raw_issue)
        approval = None
        if plan["approval_create"]:
            approval = self.http_client.create_approval_obj(
                plan["approval_create"] | {"linked_issue_ids": [issue.id]}
            )
        wake = self.http_client.wake_agent_obj(
            plan["execution_trigger"]
            | {"payload": plan["execution_trigger"]["payload"] | {"issueId": issue.id, "issueIdentifier": issue.identifier}}
        )
        return {
            "issue": {
                "id": issue.id,
                "identifier": issue.identifier,
                "issue_number": issue.issue_number,
                "company_id": issue.company_id,
                "project_id": issue.project_id,
                "goal_id": issue.goal_id,
                "status": issue.status,
                "priority": issue.priority,
                "created_by_user_id": issue.created_by_user_id,
                "created_at": issue.created_at,
                "updated_at": issue.updated_at,
                "raw": raw_issue,
            },
            "approval": approval,
            "wake": wake,
        }


def build_http_client(base_url: str, bearer_token: str | None = None) -> PaperclipHttpClient:
    return PaperclipHttpClient(PaperclipClientConfig(base_url=base_url, bearer_token=bearer_token))
