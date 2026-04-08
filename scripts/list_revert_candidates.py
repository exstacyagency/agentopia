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
    file_write = metadata.get("file_write") or {}
    if metadata.get("task_type") != "file_write":
        continue
    if run.get("status") != "succeeded":
        continue
    if not file_write.get("path"):
        continue
    items.append(
        {
            "task_id": envelope.get("task_id"),
            "run_id": run.get("run_id"),
            "path": file_write.get("path"),
            "previous_sha256": file_write.get("previous_sha256"),
            "new_sha256": file_write.get("new_sha256"),
            "change_preview": file_write.get("change_preview"),
            "previous_bytes": file_write.get("previous_bytes"),
            "existed_before": file_write.get("existed_before"),
            "changed": file_write.get("changed"),
            "revertable": file_write.get("previous_bytes") is not None,
        }
    )

print(json.dumps(items[:30], indent=2))
