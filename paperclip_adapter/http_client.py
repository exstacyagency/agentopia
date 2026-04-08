from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request

from paperclip_adapter.models import (
    PaperclipApprovalCreate,
    PaperclipExecutionTrigger,
    PaperclipIssueCreate,
    PaperclipIssueRecord,
)


@dataclass(frozen=True)
class PaperclipClientConfig:
    base_url: str
    bearer_token: str | None = None


class PaperclipHttpClient:
    def __init__(self, config: PaperclipClientConfig):
        self.config = config

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
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
        try:
            with request.urlopen(req) as response:
                raw = response.read().decode()
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            raise RuntimeError(f"paperclip_http_error status={exc.code} method={method} path={path} body={raw}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"paperclip_connection_error method={method} path={path} reason={exc.reason}") from exc

    def create_issue(self, issue: PaperclipIssueCreate) -> dict[str, Any]:
        payload = {
            "title": issue.title,
            "description": issue.description,
            "priority": issue.priority,
            "projectId": issue.project_id,
            "goalId": issue.goal_id,
            "status": issue.status,
        }
        return self._request("POST", f"/api/companies/{issue.company_id}/issues", payload)

    def create_issue_obj(self, issue: dict[str, Any]) -> dict[str, Any]:
        return self.create_issue(PaperclipIssueCreate(**issue))

    def normalize_issue(self, issue: dict[str, Any]) -> PaperclipIssueRecord:
        return PaperclipIssueRecord(
            id=issue["id"],
            identifier=issue.get("identifier"),
            issue_number=issue.get("issueNumber"),
            company_id=issue["companyId"],
            project_id=issue.get("projectId"),
            project_workspace_id=issue.get("projectWorkspaceId"),
            goal_id=issue.get("goalId"),
            parent_id=issue.get("parentId"),
            title=issue["title"],
            description=issue.get("description"),
            status=issue["status"],
            priority=issue["priority"],
            assignee_agent_id=issue.get("assigneeAgentId"),
            assignee_user_id=issue.get("assigneeUserId"),
            checkout_run_id=issue.get("checkoutRunId"),
            execution_run_id=issue.get("executionRunId"),
            execution_agent_name_key=issue.get("executionAgentNameKey"),
            execution_locked_at=issue.get("executionLockedAt"),
            created_by_agent_id=issue.get("createdByAgentId"),
            created_by_user_id=issue.get("createdByUserId"),
            origin_kind=issue.get("originKind"),
            origin_id=issue.get("originId"),
            origin_run_id=issue.get("originRunId"),
            request_depth=issue.get("requestDepth", 0),
            billing_code=issue.get("billingCode"),
            assignee_adapter_overrides=issue.get("assigneeAdapterOverrides"),
            execution_workspace_id=issue.get("executionWorkspaceId"),
            execution_workspace_preference=issue.get("executionWorkspacePreference"),
            execution_workspace_settings=issue.get("executionWorkspaceSettings"),
            started_at=issue.get("startedAt"),
            completed_at=issue.get("completedAt"),
            cancelled_at=issue.get("cancelledAt"),
            hidden_at=issue.get("hiddenAt"),
            labels=issue.get("labels", []),
            label_ids=issue.get("labelIds", []),
            created_at=issue["createdAt"],
            updated_at=issue["updatedAt"],
        )

    def create_approval(self, approval: PaperclipApprovalCreate) -> dict[str, Any]:
        payload = {
            "type": approval.approval_type,
            "payload": approval.payload,
            "issueIds": approval.linked_issue_ids,
        }
        return self._request("POST", f"/api/companies/{approval.company_id}/approvals", payload)

    def create_approval_obj(self, approval: dict[str, Any]) -> dict[str, Any]:
        return self.create_approval(PaperclipApprovalCreate(**approval))

    def get_approval(self, company_id: str, approval_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/companies/{company_id}/approvals/{approval_id}")

    def create_issue_comment(self, issue_id: str, body: str, reopen: bool | None = None, interrupt: bool | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"body": body}
        if reopen is not None:
            payload["reopen"] = reopen
        if interrupt is not None:
            payload["interrupt"] = interrupt
        return self._request("POST", f"/api/issues/{issue_id}/comments", payload)

    def upsert_issue_document(self, issue_id: str, key: str, title: str, body: str) -> dict[str, Any]:
        payload = {
            "title": title,
            "format": "markdown",
            "body": body,
            "baseRevisionId": None,
        }
        return self._request("PUT", f"/api/issues/{issue_id}/documents/{key}", payload)

    def wake_agent(self, trigger: PaperclipExecutionTrigger) -> dict[str, Any]:
        payload = {
            "source": trigger.source,
            "triggerDetail": trigger.trigger_detail,
            "payload": trigger.payload,
        }
        return self._request("POST", f"/api/agents/{trigger.agent_id}/wakeup", payload)

    def wake_agent_obj(self, trigger: dict[str, Any]) -> dict[str, Any]:
        return self.wake_agent(PaperclipExecutionTrigger(**trigger))
