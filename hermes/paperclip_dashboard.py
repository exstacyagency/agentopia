from __future__ import annotations

from typing import Any


def build_issue_dashboard_document(result: dict[str, Any]) -> dict[str, str]:
    result_payload = result.get("result") or {}
    metadata = result_payload.get("metadata") or {}
    policy = metadata.get("policy") or {}
    decision_trace = metadata.get("decision_trace") or {}
    error = result_payload.get("error") or {}
    run = result.get("run") or {}

    lines = [
        "# Agentopia Review Dashboard Snapshot",
        "",
        "## Action",
        f"- Action label: {metadata.get('action_label')}",
        f"- Category: {metadata.get('action_category')}",
        f"- Operator summary: {metadata.get('operator_summary')}",
        f"- Action reason: {metadata.get('action_reason')}",
        "",
        "## Policy",
        f"- Mode: {policy.get('mode')}",
        f"- Reason: {policy.get('reason')}",
        f"- Run status: {run.get('status')}",
        "",
        "## Decision trace",
        f"- Requested intent: {decision_trace.get('requested_intent')}",
        f"- Mapped task type: {decision_trace.get('mapped_task_type')}",
        f"- Decision summary: {decision_trace.get('decision_summary')}",
        f"- Target paths: {decision_trace.get('target_paths')}",
        "",
        "## Approval",
        f"- Required: {(decision_trace.get('approval') or {}).get('required')}",
        f"- Approval id: {(decision_trace.get('approval') or {}).get('paperclip_approval_id')}",
        f"- Approval status: {(decision_trace.get('approval') or {}).get('paperclip_approval_status')}",
    ]

    if error:
        lines.extend([
            "",
            "## Error",
            f"- Code: {error.get('code')}",
            f"- Message: {error.get('message')}",
        ])

    return {
        "key": "agentopia-review-dashboard",
        "title": "Agentopia Review Dashboard",
        "body": "\n".join(lines),
    }
