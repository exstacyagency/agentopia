#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent / "var" / "hermes"
results_base = root / "callback-results"
callbacks_base = root / "callbacks"
items = []

if results_base.exists():
    for path in sorted(results_base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
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
                "source": "accepted_callback",
                "file": path.name,
                "task_id": payload.get("task_id"),
                "run_id": run.get("run_id"),
                "status": run.get("status"),
                "summary": result.get("summary"),
                "task_type": metadata.get("task_type"),
                "stored_at": data.get("stored_at"),
            }
        )

if callbacks_base.exists() and not items:
    for path in sorted(callbacks_base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        items.append(
            {
                "source": "callback_attempt",
                "file": path.name,
                "task_id": data.get("task_id"),
                "run_id": data.get("run_id"),
                "success": data.get("success"),
                "status_code": data.get("status_code"),
                "error": data.get("error"),
                "attempt_count": data.get("attempt_count"),
                "recorded_at": data.get("recorded_at"),
            }
        )

print(json.dumps(items[:20], indent=2))
