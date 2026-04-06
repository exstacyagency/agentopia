from __future__ import annotations

from typing import Any

from paperclip_adapter.models import (
    AgentopiaTaskEnvelope,
    PaperclipApprovalCreate,
    PaperclipExecutionTrigger,
    PaperclipIssueCreate,
)


PRIORITY_MAP = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "urgent": "urgent",
}


APPROVAL_TYPE = "agentopia_task_execution"


def parse_agentopia_task(payload: dict[str, Any], company_id: str, project_id: str | None = None, goal_id: str | None = None) -> AgentopiaTaskEnvelope:
    task = payload["task"]
    policy = payload["execution_policy"]
    permissions = policy["permissions"]
    output_requirements = policy["output_requirements"]
    routing = payload["routing"]
    trace = payload["trace"]
    requester = task["requester"]
    approval = policy["approval"]
    budget = policy["budget"]
    return AgentopiaTaskEnvelope(
        schema_version=payload["schema_version"],
        task_id=task["id"],
        task_type=task["type"],
        title=task["title"],
        description=task["description"],
        priority=task["priority"],
        risk_level=task["risk_level"],
        requester_id=requester["id"],
        requester_display_name=requester["display_name"],
        company_id=company_id,
        project_id=project_id,
        goal_id=goal_id,
        approval_required=approval["required"],
        approval_status=approval["status"],
        max_cost_usd=float(budget["max_cost_usd"]),
        max_runtime_minutes=int(budget["max_runtime_minutes"]),
        allow_network=bool(permissions["allow_network"]),
        allow_memory=bool(permissions["allow_memory"]),
        allow_tools=bool(permissions["allow_tools"]),
        allowed_tool_classes=list(permissions["allowed_tool_classes"]),
        output_format=output_requirements["format"],
        output_length=output_requirements["length"],
        callback_url=routing["callback"]["result_url"],
        trace_id=trace["trace_id"],
        raw_payload=payload,
    )


def map_task_to_issue(task: AgentopiaTaskEnvelope) -> PaperclipIssueCreate:
    metadata = {
        "agentopia": {
            "schema_version": task.schema_version,
            "task_id": task.task_id,
            "task_type": task.task_type,
            "risk_level": task.risk_level,
            "requester_id": task.requester_id,
            "requester_display_name": task.requester_display_name,
            "approval_required": task.approval_required,
            "approval_status": task.approval_status,
            "execution_constraints": {
                "max_cost_usd": task.max_cost_usd,
                "max_runtime_minutes": task.max_runtime_minutes,
                "allow_network": task.allow_network,
                "allow_memory": task.allow_memory,
                "allow_tools": task.allow_tools,
                "allowed_tool_classes": task.allowed_tool_classes,
                "output_format": task.output_format,
                "output_length": task.output_length,
            },
            "callback_url": task.callback_url,
            "trace_id": task.trace_id,
        }
    }
    return PaperclipIssueCreate(
        company_id=task.company_id,
        title=task.title,
        description=task.description,
        priority=PRIORITY_MAP.get(task.priority, "medium"),
        project_id=task.project_id,
        goal_id=task.goal_id,
        metadata=metadata,
    )


def map_task_to_approval(task: AgentopiaTaskEnvelope, issue_id: str) -> PaperclipApprovalCreate | None:
    if not task.approval_required:
        return None
    return PaperclipApprovalCreate(
        company_id=task.company_id,
        approval_type=APPROVAL_TYPE,
        payload={
            "issueId": issue_id,
            "taskId": task.task_id,
            "title": task.title,
            "riskLevel": task.risk_level,
            "maxCostUsd": task.max_cost_usd,
            "maxRuntimeMinutes": task.max_runtime_minutes,
            "traceId": task.trace_id,
        },
        linked_issue_ids=[issue_id],
    )


def map_issue_to_execution_trigger(task: AgentopiaTaskEnvelope, issue_id: str, agent_id: str) -> PaperclipExecutionTrigger:
    return PaperclipExecutionTrigger(
        agent_id=agent_id,
        source="agentopia",
        trigger_detail="paperclip_issue_execution",
        payload={
            "issueId": issue_id,
            "taskId": task.task_id,
            "traceId": task.trace_id,
            "callbackUrl": task.callback_url,
            "taskType": task.task_type,
        },
    )
