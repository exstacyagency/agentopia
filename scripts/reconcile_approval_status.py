#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

from paperclip_adapter.http_client import PaperclipHttpClient

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

paperclip_base_url = os.environ.get("PAPERCLIP_BASE_URL", "http://127.0.0.1:3100")
paperclip_company_id = os.environ.get("PAPERCLIP_COMPANY_ID")
client = PaperclipHttpClient(base_url=paperclip_base_url)


def resolve_current_status(approval_id: str) -> tuple[str | None, str]:
    if paperclip_company_id:
        try:
            approval = client.get_approval(paperclip_company_id, approval_id)
            return approval.get("status"), "paperclip_live"
        except Exception:
            pass
    return current_state.get(approval_id), "local_fallback"


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
    current_status, source = resolve_current_status(approval_id)
    items.append(
        {
            "task_id": envelope.get("task_id"),
            "task_type": metadata.get("task_type"),
            "approval_id": approval_id,
            "stored_status": stored_status,
            "current_status": current_status,
            "status_source": source,
            "status_match": stored_status == current_status if current_status is not None else None,
        }
    )

print(json.dumps(items[:30], indent=2))
