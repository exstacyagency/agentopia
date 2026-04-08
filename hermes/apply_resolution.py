from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def resolve_issue_apply_candidates(root: Path, issue_id: str) -> list[dict[str, Any]]:
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
        repo_write = metadata.get("repo_write") or {}
        if metadata.get("task_type") != "repo_write":
            continue
        if metadata.get("paperclip_issue_id") != issue_id:
            continue
        if run.get("status") != "succeeded":
            continue
        if not repo_write.get("preview_only"):
            continue
        files = repo_write.get("files") or []
        changes = []
        for item in files:
            path_value = item.get("path")
            if not path_value:
                continue
            changes.append(
                {
                    "file_path": path_value,
                    "content": item.get("content") or "",
                    "overwrite": item.get("overwrite", False),
                    "overwrite_approved": item.get("overwrite_approved", False),
                }
            )
        items.append(
            {
                "task_id": envelope.get("task_id"),
                "run_id": run.get("run_id"),
                "file_count": repo_write.get("file_count"),
                "files": files,
                "apply_payload": {
                    "source_run_id": run.get("run_id"),
                    "changes": changes,
                    "apply": True,
                },
            }
        )
    return items
