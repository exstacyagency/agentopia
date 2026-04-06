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
    metadata: dict[str, Any]


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
