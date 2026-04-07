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
    result = data.get("result") or {}
    run = result.get("run") or {}
    metadata = ((result.get("result") or {}).get("metadata") or {})
    items.append(
        {
            "file": path.name,
            "task_id": result.get("task_id"),
            "run_id": run.get("run_id"),
            "status": run.get("status"),
            "summary": (result.get("result") or {}).get("summary"),
            "task_type": metadata.get("task_type"),
            "trace_id": (result.get("trace") or {}).get("trace_id"),
        }
    )
print(json.dumps(items[:20], indent=2))
