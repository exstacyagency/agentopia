from __future__ import annotations

from pathlib import Path


class FileWriteError(Exception):
    pass


def resolve_workspace_path(root: Path, relative_path: str) -> Path:
    if not relative_path:
        raise FileWriteError("file_path is required")
    workspace_root = root.resolve()
    candidate = (workspace_root / relative_path).resolve()
    if candidate == workspace_root or workspace_root not in candidate.parents:
        raise FileWriteError("target path is outside workspace scope")
    return candidate


def write_workspace_file(root: Path, relative_path: str, content: str) -> tuple[Path, int]:
    target = resolve_workspace_path(root, relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = content or ""
    target.write_text(data)
    return target, len(data.encode())
