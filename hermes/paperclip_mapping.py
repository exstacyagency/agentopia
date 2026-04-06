from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MappedTask:
    task_type: str
    context: dict[str, Any]


FILE_ANALYSIS_HINTS = (
    "file",
    "filepath",
    "path",
    "analyze file",
    "inspect file",
    "read file",
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".md",
    ".json",
    ".yaml",
    ".yml",
)

TEXT_GENERATION_HINTS = (
    "write",
    "draft",
    "generate",
    "compose",
    "summarize this text",
    "announcement",
    "email",
    "message",
    "post",
)

REPO_SUMMARY_HINTS = (
    "repo",
    "repository",
    "codebase",
    "project overview",
    "summarize repo",
    "summarize repository",
    "overview",
)


def _combined_text(title: str | None, description: str | None) -> str:
    return f"{title or ''}\n{description or ''}".strip().lower()


def _extract_path(text: str) -> str | None:
    for token in text.replace("`", " ").replace("\n", " ").split():
        cleaned = token.strip(" .,()[]{}<>\"'")
        if "/" in cleaned or cleaned.endswith((".py", ".ts", ".tsx", ".js", ".md", ".json", ".yaml", ".yml")):
            return cleaned
    return None


def map_paperclip_issue_to_task(title: str | None, description: str | None, *, fallback_repo: str = "paperclip-runtime-workspace") -> MappedTask:
    text = _combined_text(title, description)
    extracted_path = _extract_path(text)

    if extracted_path or any(hint in text for hint in FILE_ANALYSIS_HINTS):
        return MappedTask(
            task_type="file_analysis",
            context={
                "file_path": extracted_path or "unknown-file",
                "objective": description or title or "Analyze the referenced file",
            },
        )

    if any(hint in text for hint in TEXT_GENERATION_HINTS):
        return MappedTask(
            task_type="text_generation",
            context={
                "prompt": description or title or "Generate text",
                "audience": "general",
                "tone": "neutral",
            },
        )

    if any(hint in text for hint in REPO_SUMMARY_HINTS):
        return MappedTask(
            task_type="repo_summary",
            context={
                "repo": fallback_repo,
                "branch": "unknown-branch",
            },
        )

    return MappedTask(
        task_type="repo_summary",
        context={
            "repo": fallback_repo,
            "branch": "unknown-branch",
        },
    )
