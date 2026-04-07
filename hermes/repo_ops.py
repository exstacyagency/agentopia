from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hermes.file_ops import FileWriteError, resolve_workspace_path, short_hash, preview_change, write_workspace_file


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
    overwrite_approved: bool


@dataclass(frozen=True)
class RepoWriteResult:
    files: list[RepoWriteFileResult]
    applied: bool


def inspect_repo_change(root: Path, change: dict) -> RepoWriteFileResult:
    file_path = change.get("file_path") or ""
    content = change.get("content") or ""
    overwrite = bool(change.get("overwrite", False))
    overwrite_approved = bool(change.get("overwrite_approved", False))
    target = resolve_workspace_path(root, file_path)
    existed_before = target.exists()
    previous = target.read_text() if existed_before else ""
    previous_bytes = len(previous.encode())
    return RepoWriteFileResult(
        path=str(target.relative_to(root)),
        bytes_written=len(content.encode()),
        existed_before=existed_before,
        changed=(previous != content),
        previous_bytes=previous_bytes,
        previous_sha256=(short_hash(previous) if existed_before else None),
        new_sha256=short_hash(content),
        change_preview=preview_change(previous, content),
        overwrite=overwrite,
        overwrite_approved=overwrite_approved,
    )


def apply_repo_write(root: Path, changes: list[dict]) -> RepoWriteResult:
    if not changes:
        raise FileWriteError("repo_write requires at least one change")

    results: list[RepoWriteFileResult] = []
    for change in changes:
        inspected = inspect_repo_change(root, change)
        written = write_workspace_file(root, change.get("file_path") or "", change.get("content") or "", overwrite=inspected.overwrite)
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
                overwrite=inspected.overwrite,
                overwrite_approved=inspected.overwrite_approved,
            )
        )

    return RepoWriteResult(files=results, applied=True)


def preview_repo_write(root: Path, changes: list[dict]) -> RepoWriteResult:
    if not changes:
        raise FileWriteError("repo_write requires at least one change")
    return RepoWriteResult(files=[inspect_repo_change(root, change) for change in changes], applied=False)
