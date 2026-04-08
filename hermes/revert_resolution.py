from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def resolve_issue_revert_candidates(root: Path, issue_id: str) -> list[dict[str, Any]]:
    runs_base = root / "var" / "hermes" / "runs"
    if not runs_base.exists() or not issue_id:
        return []

    items: list[dict[str, Any]] = []
    for path in sorted(runs_base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        envelope = data.get("result") or {}
        run = envelope.get("run") or {}
        result = envelope.get("result") or {}
        metadata = result.get("metadata") or {}
        if metadata.get("task_type") != "file_write":
            continue
        if run.get("status") != "succeeded":
            continue
        if metadata.get("paperclip_issue_id") != issue_id:
            continue
        write = metadata.get("file_write") or {}
        path_value = write.get("path")
        if not path_value:
            continue
        items.append(
            {
                "task_id": envelope.get("task_id"),
                "run_id": run.get("run_id"),
                "file_path": path_value,
                "previous_bytes": write.get("previous_bytes"),
                "previous_sha256": write.get("previous_sha256"),
                "new_sha256": write.get("new_sha256"),
                "change_preview": write.get("change_preview"),
                "revert_payload": {
                    "source_run_id": run.get("run_id"),
                    "file_path": path_value,
                    "previous_content": write.get("previous_content") or "",
                },
            }
        )
    return items
