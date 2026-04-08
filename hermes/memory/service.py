from __future__ import annotations

import subprocess
from typing import Any

from hermes.memory.config import (
    load_mempalace_config,
    mempalace_config_dict,
    save_mempalace_config,
)
from hermes.memory.mempalace_client import MemPalaceClient


class MemPalaceService:
    def __init__(self) -> None:
        self._reload()

    def _reload(self) -> None:
        self.config = load_mempalace_config()
        self.client = MemPalaceClient(self.config)

    def get_config(self) -> dict[str, Any]:
        return mempalace_config_dict(self.config)

    def set_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        config = save_mempalace_config(payload)
        self._reload()
        return mempalace_config_dict(config)

    def status(self) -> dict[str, Any]:
        command_found = True
        command_error = None
        try:
            subprocess.run([self.config.command, "--help"], check=False, capture_output=True, text=True)
        except FileNotFoundError:
            command_found = False
            command_error = "mempalace_command_not_found"

        return {
            "config": self.get_config(),
            "command_found": command_found,
            "error": command_error,
        }

    def search(self, query: str) -> dict[str, Any]:
        return {
            "config": self.get_config(),
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
