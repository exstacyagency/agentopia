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
