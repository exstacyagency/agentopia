from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentopiaTaskEnvelope:
    schema_version: str
    task_id: str
    task_type: str
    title: str
    description: str
    priority: str
    risk_level: str
    requester_id: str
    requester_display_name: str
    company_id: str
    project_id: str | None
    goal_id: str | None
    approval_required: bool
    approval_status: str
    max_cost_usd: float
    max_runtime_minutes: int
    allow_network: bool
    allow_memory: bool
    allow_tools: bool
    allowed_tool_classes: list[str]
    output_format: str
    output_length: str
    callback_url: str
    trace_id: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class PaperclipIssueCreate:
    company_id: str
    title: str
    description: str
    priority: str
    project_id: str | None
    goal_id: str | None
    status: str = "backlog"
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class PaperclipIssueRecord:
    id: str
    identifier: str | None
    issue_number: int | None
    company_id: str
    project_id: str | None
    project_workspace_id: str | None
    goal_id: str | None
    parent_id: str | None
    title: str
    description: str | None
    status: str
    priority: str
    assignee_agent_id: str | None
    assignee_user_id: str | None
    checkout_run_id: str | None
    execution_run_id: str | None
    execution_agent_name_key: str | None
    execution_locked_at: str | None
    created_by_agent_id: str | None
    created_by_user_id: str | None
    origin_kind: str | None
    origin_id: str | None
    origin_run_id: str | None
    request_depth: int
    billing_code: str | None
    assignee_adapter_overrides: dict[str, Any] | None
    execution_workspace_id: str | None
    execution_workspace_preference: str | None
    execution_workspace_settings: dict[str, Any] | None
    started_at: str | None
    completed_at: str | None
    cancelled_at: str | None
    hidden_at: str | None
    labels: list[dict[str, Any]]
    label_ids: list[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class PaperclipApprovalCreate:
    company_id: str
    approval_type: str
    payload: dict[str, Any]
    linked_issue_ids: list[str]


@dataclass(frozen=True)
class PaperclipExecutionTrigger:
    agent_id: str
    source: str
    trigger_detail: str
    payload: dict[str, Any]
