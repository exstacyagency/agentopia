from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MemPalaceConfig:
    enabled: bool
    command: str


def load_mempalace_config() -> MemPalaceConfig:
    return MemPalaceConfig(
        enabled=os.environ.get("MEMPALACE_ENABLED", "0") == "1",
        command=os.environ.get("MEMPALACE_COMMAND", "mempalace"),
    )
