from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "var" / "hermes" / "memory" / "mempalace-config.json"


@dataclass(frozen=True)
class MemPalaceConfig:
    enabled: bool
    command: str
    palace_path: str | None


def _env_config() -> MemPalaceConfig:
    return MemPalaceConfig(
        enabled=os.environ.get("MEMPALACE_ENABLED", "0") == "1",
        command=os.environ.get("MEMPALACE_COMMAND", "mempalace"),
        palace_path=os.environ.get("MEMPALACE_PATH"),
    )


def load_mempalace_config() -> MemPalaceConfig:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text())
            return MemPalaceConfig(
                enabled=bool(data.get("enabled", False)),
                command=str(data.get("command") or "mempalace"),
                palace_path=data.get("palace_path"),
            )
        except Exception:
            pass
    return _env_config()


def save_mempalace_config(payload: dict[str, Any]) -> MemPalaceConfig:
    config = MemPalaceConfig(
        enabled=bool(payload.get("enabled", False)),
        command=str(payload.get("command") or "mempalace"),
        palace_path=payload.get("palace_path"),
    )
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(asdict(config), indent=2) + "\n")
    return config


def mempalace_config_dict(config: MemPalaceConfig) -> dict[str, Any]:
    return asdict(config)
