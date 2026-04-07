#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

base = Path(__file__).resolve().parent.parent / "var" / "hermes" / "runs"
if not base.exists():
    print("[]")
    raise SystemExit(0)


def operator_status(status: str | None, policy_mode: str | None, error: dict | None) -> str:
    if policy_mode == "preview":
        return "preview"
    if error:
        code = error.get("code")
        if code == "POLICY_BLOCKED":
            return "blocked_policy"
        if code == "WRITE_SCOPE_VIOLATION":
            return "blocked_scope"
        return "failed"
    if status == "succeeded" and policy_mode == "allow":
        return "approved_write"
    return status or "unknown"


def normalize_file_write(write: dict | None) -> tuple[dict | None, bool]:
    if not write:
        return None, True
    normalized = {
        "path": write.get("path"),
        "bytes_written": write.get("bytes_written"),
        "existed_before": write.get("existed_before"),
        "changed": write.get("changed"),
        "previous_bytes": write.get("previous_bytes"),
        "previous_sha256": write.get("previous_sha256"),
        "new_sha256": write.get("new_sha256"),
        "change_preview": write.get("change_preview"),
        "overwrite": write.get("overwrite"),
    }
    legacy = any(key not in write for key in ["existed_before", "changed", "previous_bytes", "previous_sha256", "new_sha256", "change_preview", "overwrite"])
    return normalized, legacy


def normalize_repo_write(write: dict | None) -> tuple[dict | None, bool]:
    if not write:
        return None, True
    files = []
    legacy = False
    for item in write.get("files") or []:
        files.append(
            {
                "path": item.get("path"),
                "bytes_written": item.get("bytes_written"),
                "existed_before": item.get("existed_before"),
                "changed": item.get("changed"),
                "previous_bytes": item.get("previous_bytes"),
                "previous_sha256": item.get("previous_sha256"),
                "new_sha256": item.get("new_sha256"),
                "change_preview": item.get("change_preview"),
                "overwrite": item.get("overwrite"),
                "overwrite_approved": item.get("overwrite_approved"),
            }
        )
        if any(key not in item for key in ["existed_before", "changed", "previous_bytes", "previous_sha256", "new_sha256", "change_preview", "overwrite", "overwrite_approved"]):
            legacy = True
    normalized = {
        "preview_only": write.get("preview_only"),
        "file_count": write.get("file_count"),
        "files": files,
    }
    if "preview_only" not in write:
        legacy = True
    return normalized, legacy


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
    error = result.get("error")
    row = {
        "file": path.name,
        "task_id": envelope.get("task_id"),
        "run_id": run.get("run_id"),
        "status": run.get("status"),
        "task_type": task_type,
        "policy_mode": policy.get("mode"),
        "policy_reason": policy.get("reason"),
        "operator_status": operator_status(run.get("status"), policy.get("mode"), error),
        "summary": result.get("summary"),
        "trace_id": (envelope.get("trace") or {}).get("trace_id"),
        "paperclip_approval": {
            "id": metadata.get("paperclip_approval_id"),
            "status": metadata.get("paperclip_approval_status"),
        },
    }
    if task_type == "file_write":
        row["write"], legacy = normalize_file_write(metadata.get("file_write"))
        row["legacy_result_shape"] = legacy
    if task_type == "repo_write":
        row["write"], legacy = normalize_repo_write(metadata.get("repo_write"))
        row["legacy_result_shape"] = legacy
    if error:
        row["error"] = error
    items.append(row)

print(json.dumps(items[:30], indent=2))
