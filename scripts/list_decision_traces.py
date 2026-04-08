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
    trace = metadata.get("decision_trace")
    if not trace:
        continue
    items.append(
        {
            "task_id": envelope.get("task_id"),
            "run_id": run.get("run_id"),
            "task_type": metadata.get("task_type"),
            "action_label": metadata.get("action_label"),
            "operator_summary": metadata.get("operator_summary"),
            "decision_trace": trace,
        }
    )

print(json.dumps(items[:30], indent=2))
