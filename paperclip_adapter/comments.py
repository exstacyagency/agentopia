from __future__ import annotations

from typing import Any


def build_execution_summary_comment(result: dict[str, Any]) -> dict[str, Any]:
    metadata = ((result.get("result") or {}).get("metadata") or {})
    policy = metadata.get("policy") or {}
    approval_id = metadata.get("paperclip_approval_id")
    approval_status = metadata.get("paperclip_approval_status")

    lines = [
        "## Hermes Execution Summary",
        f"- Action: {metadata.get('action_label')}",
        f"- Category: {metadata.get('action_category')}",
        f"- Why: {metadata.get('action_reason')}",
        f"- Operator summary: {metadata.get('operator_summary')}",
        f"- Policy mode: {policy.get('mode')}",
        f"- Policy reason: {policy.get('reason')}",
    ]

    if approval_id:
        lines.append(f"- Approval id: {approval_id}")
    if approval_status:
        lines.append(f"- Approval status: {approval_status}")

    return {
        "body": "\n".join(lines),
    }
