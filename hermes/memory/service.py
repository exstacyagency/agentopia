from __future__ import annotations

from typing import Any

from hermes.memory.config import load_mempalace_config
from hermes.memory.mempalace_client import MemPalaceClient


class MemPalaceService:
    def __init__(self) -> None:
        self.config = load_mempalace_config()
        self.client = MemPalaceClient(self.config)

    def search(self, query: str) -> dict[str, Any]:
        return {
            "config": {
                "enabled": self.config.enabled,
                "command": self.config.command,
            },
            **self.client.search(query),
        }

    def wakeup(self, issue_title: str, issue_description: str) -> dict[str, Any]:
        query = "\n\n".join(part for part in [issue_title, issue_description] if part).strip()
        search_result = self.search(query)
        return {
            "config": search_result.get("config", {}),
            "ok": search_result.get("ok", False),
            "reason": search_result.get("reason"),
            "query": query,
            "wakeup_context": {
                "issue_title": issue_title,
                "issue_description": issue_description,
                "memory_hits": search_result.get("results") or [],
            },
        }
