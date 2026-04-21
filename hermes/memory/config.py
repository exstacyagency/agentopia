from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY_ROOT = ROOT / "var" / "hermes" / "memory"


@dataclass(frozen=True)
class MemPalaceConfig:
    enabled: bool
    command: str
    palace_path: str | None
    memory_mode: str


@dataclass(frozen=True)
class MemoryScope:
    tenant_id: str
    org_id: str = ""
    client_id: str = ""


def require_memory_scope(payload: dict[str, Any] | None) -> MemoryScope:
    payload = payload or {}
    tenant_id = str(payload.get("tenant_id") or "").strip()
    if not tenant_id:
        raise ValueError("tenant_id is required for memory operations")
    return MemoryScope(
        tenant_id=tenant_id,
        org_id=str(payload.get("org_id") or "").strip(),
        client_id=str(payload.get("client_id") or "").strip(),
    )


def tenant_memory_dir(scope: MemoryScope) -> Path:
    return MEMORY_ROOT / scope.tenant_id


def tenant_config_path(scope: MemoryScope) -> Path:
    return tenant_memory_dir(scope) / "mempalace-config.json"


def tenant_status_path(scope: MemoryScope) -> Path:
    return tenant_memory_dir(scope) / "mempalace-status.json"


def _env_config() -> MemPalaceConfig:
    return MemPalaceConfig(
        enabled=os.environ.get("MEMPALACE_ENABLED", "0") == "1",
        command=os.environ.get("MEMPALACE_COMMAND", "mempalace"),
        palace_path=os.environ.get("MEMPALACE_PATH"),
        memory_mode=os.environ.get("MEMPALACE_MEMORY_MODE", "augment"),
    )


def load_mempalace_config(scope: MemoryScope) -> MemPalaceConfig:
    config_path = tenant_config_path(scope)
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text())
            return MemPalaceConfig(
                enabled=bool(data.get("enabled", False)),
                command=str(data.get("command") or "mempalace"),
                palace_path=data.get("palace_path"),
                memory_mode=str(data.get("memory_mode") or "augment"),
            )
        except Exception:
            pass
    return _env_config()


def save_mempalace_config(scope: MemoryScope, payload: dict[str, Any]) -> MemPalaceConfig:
    config = MemPalaceConfig(
        enabled=bool(payload.get("enabled", False)),
        command=str(payload.get("command") or "mempalace"),
        palace_path=payload.get("palace_path"),
        memory_mode=str(payload.get("memory_mode") or "augment"),
    )
    config_path = tenant_config_path(scope)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(asdict(config), indent=2) + "\n")
    return config


def mempalace_config_dict(config: MemPalaceConfig) -> dict[str, Any]:
    return asdict(config)


def memory_scope_dict(scope: MemoryScope) -> dict[str, Any]:
    return asdict(scope)
