from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes.memory.config import (
    load_mempalace_config,
    mempalace_config_dict,
    save_mempalace_config,
)
from hermes.memory.mempalace_client import MemPalaceClient

ROOT = Path(__file__).resolve().parent.parent.parent
STATUS_PATH = ROOT / "var" / "hermes" / "memory" / "mempalace-status.json"


class MemPalaceService:
    def __init__(self) -> None:
        self._reload()

    def _reload(self) -> None:
        self.config = load_mempalace_config()
        self.client = MemPalaceClient(self.config)

    def _read_status_file(self) -> dict[str, Any]:
        if STATUS_PATH.exists():
            try:
                import json
                return json.loads(STATUS_PATH.read_text())
            except Exception:
                return {}
        return {}

    def _write_status_file(self, payload: dict[str, Any]) -> None:
        import json
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text(json.dumps(payload, indent=2) + "\n")

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

        persisted = self._read_status_file()
        return {
            "config": self.get_config(),
            "command_found": command_found,
            "error": command_error,
            "memory_mode": self.config.memory_mode,
            "last_operation": persisted.get("last_operation"),
            "last_synced_at": persisted.get("last_synced_at"),
            "last_error": persisted.get("last_error"),
        }

    def run_operation(self, operation: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        if not self.config.enabled:
            result = {
                "ok": False,
                "reason": "mempalace_disabled",
                "operation": operation,
            }
            self._write_status_file({
                "last_operation": operation,
                "last_synced_at": None,
                "last_error": result["reason"],
            })
            return result
        try:
            subprocess.run([self.config.command, operation], check=True, capture_output=True, text=True)
            self._write_status_file({
                "last_operation": operation,
                "last_synced_at": now,
                "last_error": None,
            })
            return {
                "ok": True,
                "reason": f"mempalace_{operation}_ok",
                "operation": operation,
                "completed_at": now,
            }
        except FileNotFoundError:
            self._write_status_file({
                "last_operation": operation,
                "last_synced_at": None,
                "last_error": "mempalace_command_not_found",
            })
            return {
                "ok": False,
                "reason": "mempalace_command_not_found",
                "operation": operation,
            }
        except subprocess.CalledProcessError as exc:
            self._write_status_file({
                "last_operation": operation,
                "last_synced_at": None,
                "last_error": exc.stderr,
            })
            return {
                "ok": False,
                "reason": f"mempalace_{operation}_failed",
                "operation": operation,
                "stderr": exc.stderr,
            }

    def search(self, query: str) -> dict[str, Any]:
        return {
            "config": self.get_config(),
            "memory_mode": self.config.memory_mode,
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
            "memory_mode": self.config.memory_mode,
            "wakeup_context": {
                "issue_title": issue_title,
                "issue_description": issue_description,
                "memory_hits": search_result.get("results") or [],
                "memory_source": ("mempalace" if self.config.memory_mode in {"augment", "prefer_mempalace"} else "native_only"),
            },
        }
