#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
runs_base = root / "var" / "hermes" / "runs"
state_file = root / "var" / "hermes" / "approval-status.json"

if not runs_base.exists():
    print("[]")
    raise SystemExit(0)

current_state = {}
if state_file.exists():
    try:
        current_state = json.loads(state_file.read_text())
    except Exception:
        current_state = {}

items = []
for path in sorted(runs_base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
    try:
        data = json.loads(path.read_text())
    except Exception:
        continue
    envelope = data.get("result") or {}
    result = envelope.get("result") or {}
    metadata = result.get("metadata") or {}
    approval_id = metadata.get("paperclip_approval_id")
    stored_status = metadata.get("paperclip_approval_status")
    if not approval_id:
        continue
    current_status = current_state.get(approval_id)
    items.append(
        {
            "task_id": envelope.get("task_id"),
            "task_type": metadata.get("task_type"),
            "approval_id": approval_id,
            "stored_status": stored_status,
            "current_status": current_status,
            "status_match": stored_status == current_status if current_status is not None else None,
        }
    )

print(json.dumps(items[:30], indent=2))
