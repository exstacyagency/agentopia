#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

base = Path(__file__).resolve().parent.parent / "var" / "hermes" / "runs"
if not base.exists():
    print("[]")
    raise SystemExit(0)

items = []
for path in sorted(base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
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
    row = {
        "file": path.name,
        "task_id": envelope.get("task_id"),
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "task_type": task_type,
        "policy_mode": policy.get("mode"),
        "policy_reason": policy.get("reason"),
        "summary": result.get("summary"),
        "trace_id": (envelope.get("trace") or {}).get("trace_id"),
    }
    if task_type == "file_write":
        row["write"] = metadata.get("file_write")
    if task_type == "repo_write":
        row["write"] = metadata.get("repo_write")
    if result.get("error"):
        row["error"] = result.get("error")
    items.append(row)

print(json.dumps(items[:30], indent=2))
