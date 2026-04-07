from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hermes.file_ops import FileWriteError, write_workspace_file


@dataclass(frozen=True)
class RepoWriteFileResult:
    path: str
    bytes_written: int
    existed_before: bool
    changed: bool
    previous_bytes: int
    previous_sha256: str | None
    new_sha256: str
    change_preview: str
    overwrite: bool


@dataclass(frozen=True)
class RepoWriteResult:
    files: list[RepoWriteFileResult]


def apply_repo_write(root: Path, changes: list[dict]) -> RepoWriteResult:
    if not changes:
        raise FileWriteError("repo_write requires at least one change")

    results: list[RepoWriteFileResult] = []
    for change in changes:
        file_path = change.get("file_path") or ""
        content = change.get("content") or ""
        overwrite = bool(change.get("overwrite", False))
        written = write_workspace_file(root, file_path, content, overwrite=overwrite)
        results.append(
            RepoWriteFileResult(
                path=str(written.path.relative_to(root)),
                bytes_written=written.bytes_written,
                existed_before=written.existed_before,
                changed=written.changed,
                previous_bytes=written.previous_bytes,
                previous_sha256=written.previous_sha256,
                new_sha256=written.new_sha256,
                change_preview=written.change_preview,
                overwrite=overwrite,
            )
        )

    return RepoWriteResult(files=results)
