#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

root = Path(__file__).resolve().parent.parent
runs_base = root / "var" / "hermes" / "runs"
state_file = root / "var" / "hermes" / "approval-status.json"

if not runs_base.exists():
    print("{}")
    raise SystemExit(0)

current_state = {}
if state_file.exists():
    try:
        current_state = json.loads(state_file.read_text())
    except Exception:
        current_state = {}


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
    if task_type not in {"file_write", "repo_write"}:
        continue
    policy = metadata.get("policy") or {}
    error = result.get("error")
    approval_id = metadata.get("paperclip_approval_id")
    stored_status = metadata.get("paperclip_approval_status")
    current_status = current_state.get(approval_id) if approval_id else None
    status_match = stored_status == current_status if approval_id and current_status is not None else None
    items.append(
        {
            "task_id": envelope.get("task_id"),
            "run_id": run.get("run_id"),
            "task_type": task_type,
            "operator_status": operator_status(run.get("status"), policy.get("mode"), error),
            "action_label": metadata.get("action_label"),
            "action_category": metadata.get("action_category"),
            "operator_summary": metadata.get("operator_summary"),
            "action_reason": metadata.get("action_reason"),
            "policy_mode": policy.get("mode"),
            "policy_reason": policy.get("reason"),
            "paperclip_issue_id": metadata.get("paperclip_issue_id"),
            "paperclip_approval_id": approval_id,
            "paperclip_approval_status": stored_status,
            "current_approval_status": current_status,
            "approval_status_match": status_match,
            "error": error,
        }
    )

output = {
    "pending_previews": [x for x in items if x["operator_status"] == "preview"],
    "blocked_actions": [x for x in items if x["operator_status"] in {"blocked_policy", "blocked_scope"}],
    "applied_writes": [x for x in items if x["operator_status"] == "approved_write"],
    "approval_mismatches": [x for x in items if x["approval_status_match"] is False],
}

print(json.dumps(output, indent=2))
