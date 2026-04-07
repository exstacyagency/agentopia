#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

base = Path(__file__).resolve().parent.parent / "var" / "hermes" / "callback-results"
if not base.exists():
    print("[]")
    raise SystemExit(0)

items = []
for path in sorted(base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
    try:
        data = json.loads(path.read_text())
    except Exception:
        continue
    payload = data.get("payload") or {}
    run = payload.get("run") or {}
    result = payload.get("result") or {}
    metadata = result.get("metadata") or {}
    items.append(
        {
            "file": path.name,
            "task_id": payload.get("task_id"),
            "run_id": run.get("run_id"),
            "status": run.get("status"),
            "summary": result.get("summary"),
            "task_type": metadata.get("task_type"),
            "stored_at": data.get("stored_at"),
        }
    )
print(json.dumps(items[:20], indent=2))
