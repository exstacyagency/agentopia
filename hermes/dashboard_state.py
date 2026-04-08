from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def operator_status(status: str | None, policy_mode: str | None, error: dict | None) -> str:
    if policy_mode == "preview":
        return "preview"
    if error:
        code = error.get("code")
        if code == "POLICY_BLOCKED":
            return "blocked_policy"
        if code == "WRITE_SCOPE_VIOLATION":
            return "blocked_scope"
        return "failed"
    if status == "succeeded" and policy_mode == "allow":
        return "approved_write"
    return status or "unknown"


def build_operator_queue_state(root: Path) -> dict[str, Any]:
    runs_base = root / "var" / "hermes" / "runs"
    if not runs_base.exists():
        return {
            "pending_previews": [],
            "blocked_actions": [],
            "completed_reverts": [],
            "approval_mismatches": [],
        }

    approval_state_path = root / "var" / "hermes" / "approval-status.json"
    current_state = {}
    if approval_state_path.exists():
        try:
            current_state = json.loads(approval_state_path.read_text())
        except Exception:
            current_state = {}

    items = []
    for path in sorted(runs_base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        envelope = data.get("result") or {}
        run = envelope.get("run") or {}
        result = envelope.get("result") or {}
        metadata = result.get("metadata") or {}
        task_type = metadata.get("task_type")
        if task_type not in {"file_write", "repo_write", "file_revert"}:
            continue
        policy = metadata.get("policy") or {}
        error = result.get("error")
        approval_id = metadata.get("paperclip_approval_id")
        stored_status = metadata.get("paperclip_approval_status")
        current_status = current_state.get(approval_id) if approval_id else None
        items.append(
            {
                "issue_id": metadata.get("paperclip_issue_id"),
                "task_id": envelope.get("task_id"),
                "run_id": run.get("run_id"),
                "task_type": task_type,
                "operator_status": operator_status(run.get("status"), policy.get("mode"), error),
                "operator_summary": metadata.get("operator_summary"),
                "policy_mode": policy.get("mode"),
                "policy_reason": policy.get("reason"),
                "approval_status_match": stored_status == current_status if approval_id and current_status is not None else None,
            }
        )

    return {
        "pending_previews": [x for x in items if x["operator_status"] == "preview"][:10],
        "blocked_actions": [x for x in items if x["operator_status"] in {"blocked_policy", "blocked_scope"}][:10],
        "completed_reverts": [x for x in items if x["task_type"] == "file_revert" and x["operator_status"] == "approved_write"][:10],
        "approval_mismatches": [x for x in items if x["approval_status_match"] is False][:10],
    }
