from __future__ import annotations

from dataclasses import asdict
from typing import Any

from paperclip_adapter.mapping import (
    map_issue_to_execution_trigger,
    map_task_to_approval,
    map_task_to_issue,
    parse_agentopia_task,
)


class PaperclipAdapter:
    """Step-2 skeleton adapter.

    This adapter does not yet perform real HTTP I/O. It formalizes the mapping from
    the Agentopia task envelope into the Paperclip-native orchestration object model.
    """

    def build_plan(
        self,
        payload: dict[str, Any],
        *,
        company_id: str,
        project_id: str | None = None,
        goal_id: str | None = None,
        execution_agent_id: str,
        issue_id: str = "PAPERCLIP_ISSUE_ID_PLACEHOLDER",
    ) -> dict[str, Any]:
        task = parse_agentopia_task(payload, company_id=company_id, project_id=project_id, goal_id=goal_id)
        issue = map_task_to_issue(task)
        approval = map_task_to_approval(task, issue_id=issue_id)
        trigger = map_issue_to_execution_trigger(task, issue_id=issue_id, agent_id=execution_agent_id)
        return {
            "task": asdict(task),
            "issue_create": asdict(issue),
            "approval_create": asdict(approval) if approval else None,
            "execution_trigger": asdict(trigger),
        }
