#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

base = Path(__file__).resolve().parent.parent / "var" / "hermes" / "callbacks"
if not base.exists():
    print("[]")
    raise SystemExit(0)

items = []
for path in sorted(base.glob("*.json")):
    try:
        data = json.loads(path.read_text())
    except Exception:
        continue
    if not data.get("success"):
        items.append(
            {
                "file": path.name,
                "task_id": data.get("task_id"),
                "run_id": data.get("run_id"),
                "result_url": data.get("result_url"),
                "attempt_count": data.get("attempt_count", 1),
                "last_error": data.get("error"),
                "retryable": data.get("retryable", True),
            }
        )
print(json.dumps(items, indent=2))
