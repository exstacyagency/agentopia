from __future__ import annotations

from typing import Any


def summarize_runtime_guards(base_url: str | None) -> dict[str, Any]:
    warnings: list[str] = []
    if not base_url:
        warnings.append("paperclip_base_url_missing")
    return {
        "warnings": warnings,
        "paperclip_base_url": base_url,
    }
