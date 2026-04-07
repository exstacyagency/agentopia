from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


class FileWriteError(Exception):
    pass


@dataclass(frozen=True)
class FileWriteResult:
    path: Path
    bytes_written: int
    existed_before: bool
    changed: bool
    previous_bytes: int
    previous_sha256: str | None
    new_sha256: str
    change_preview: str


def resolve_workspace_path(root: Path, relative_path: str) -> Path:
    if not relative_path:
        raise FileWriteError("file_path is required")
    workspace_root = root.resolve()
    candidate = (workspace_root / relative_path).resolve()
    if candidate == workspace_root or workspace_root not in candidate.parents:
        raise FileWriteError("target path is outside workspace scope")
    return candidate


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def preview_change(previous: str, new: str) -> str:
    if previous == new:
        return "no content change"
    prev_preview = previous[:80].replace("\n", "\\n")
    new_preview = new[:80].replace("\n", "\\n")
    return f"prev='{prev_preview}' -> new='{new_preview}'"


def write_workspace_file(root: Path, relative_path: str, content: str, overwrite: bool = False) -> FileWriteResult:
    target = resolve_workspace_path(root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = content or ""
    existed_before = target.exists()
    previous = target.read_text() if existed_before else ""
    previous_bytes = len(previous.encode())

    if existed_before and not overwrite and previous != data:
        raise FileWriteError("target file exists and overwrite is false")

    target.write_text(data)
    return FileWriteResult(
        path=target,
        bytes_written=len(data.encode()),
        existed_before=existed_before,
        changed=(previous != data),
        previous_bytes=previous_bytes,
        previous_sha256=(short_hash(previous) if existed_before else None),
        new_sha256=short_hash(data),
        change_preview=preview_change(previous, data),
    )
