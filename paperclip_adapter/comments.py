from __future__ import annotations

from typing import Any


def build_execution_summary_comment(result: dict[str, Any]) -> dict[str, Any]:
    result_payload = result.get("result") or {}
    metadata = result_payload.get("metadata") or {}
    policy = metadata.get("policy") or {}
    approval_id = metadata.get("paperclip_approval_id")
    approval_status = metadata.get("paperclip_approval_status")
    error = result_payload.get("error") or {}
    run = result.get("run") or {}

    heading = "## Hermes Review Summary"
    if run.get("status") == "succeeded" and policy.get("mode") == "allow":
        heading = "## Hermes Execution Summary"
    elif policy.get("mode") == "preview":
        heading = "## Hermes Preview Summary"
    elif error:
        heading = "## Hermes Blocked Action Summary"

    lines = [
        heading,
        f"- Action: {metadata.get('action_label')}",
        f"- Category: {metadata.get('action_category')}",
        f"- Why: {metadata.get('action_reason')}",
        f"- Operator summary: {metadata.get('operator_summary')}",
        f"- Policy mode: {policy.get('mode')}",
        f"- Policy reason: {policy.get('reason')}",
        f"- Run status: {run.get('status')}",
    ]

    if approval_id:
        lines.append(f"- Approval id: {approval_id}")
    if approval_status:
        lines.append(f"- Approval status: {approval_status}")
    if error:
        lines.append(f"- Error code: {error.get('code')}")
        lines.append(f"- Error message: {error.get('message')}")

    return {
        "body": "\n".join(lines),
    }
