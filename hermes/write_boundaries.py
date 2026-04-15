from __future__ import annotations

from pathlib import Path

from hermes.file_ops import FileWriteError, resolve_workspace_path


class WriteBoundaryError(RuntimeError):
    pass


def ensure_within_write_boundary(root: Path, relative_path: str) -> Path:
    try:
        return resolve_workspace_path(root, relative_path)
    except (ValueError, FileWriteError) as exc:
        raise WriteBoundaryError(str(exc)) from exc


def validate_repo_changes(root: Path, changes: list[dict]) -> None:
    for change in changes:
        path = change.get("path") or change.get("relative_path")
        if not path:
            raise WriteBoundaryError("repo change is missing path")
        ensure_within_write_boundary(root, path)
