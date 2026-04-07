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

STRUCTURED_EXTRACT_HINTS = (
    "extract",
    "pull out",
    "list",
    "identify",
    "requirements",
    "steps",
    "config keys",
    "checklist",
    "into json",
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

CHANGE_PLAN_HINTS = (
    "plan the changes",
    "change plan",
    "implementation plan",
    "plan the implementation",
    "what needs to change",
    "impacted files",
    "rollback",
    "acceptance checks",
)

IMPLEMENTATION_DRAFT_HINTS = (
    "draft the implementation",
    "implementation draft",
    "proposed edits",
    "patch outline",
    "pseudo diff",
    "edit sketch",
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

    if any(hint in text for hint in STRUCTURED_EXTRACT_HINTS):
        return MappedTask(
            task_type="structured_extract",
            context={
                "source": extracted_path or fallback_repo,
                "extraction_goal": description or title or "Extract structured information",
                "output_schema": ["items", "notes"],
            },
        )

    if any(hint in text for hint in IMPLEMENTATION_DRAFT_HINTS):
        return MappedTask(
            task_type="implementation_draft",
            context={
                "goal": description or title or "Draft the implementation",
                "impacted_files": ["TBD"],
                "validation_checks": ["Run targeted tests", "Review edge cases"],
            },
        )

    if any(hint in text for hint in IMPLEMENTATION_DRAFT_HINTS):
        return MappedTask(
            task_type="implementation_draft",
            context={
                "goal": description or title or "Draft the implementation",
                "impacted_files": ["TBD"],
                "validation_checks": ["Run targeted tests", "Review edge cases"],
            },
        )

    if any(hint in text for hint in CHANGE_PLAN_HINTS):
        return MappedTask(
            task_type="repo_change_plan",
            context={
                "repo": fallback_repo,
                "goal": description or title or "Plan the repo change",
                "impacted_files": ["TBD"],
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
