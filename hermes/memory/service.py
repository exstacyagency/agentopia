from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import Any

from hermes.memory.config import (
    MemoryScope,
    load_mempalace_config,
    memory_scope_dict,
    mempalace_config_dict,
    require_memory_scope,
    save_mempalace_config,
    tenant_status_path,
)
from hermes.memory.mempalace_client import MemPalaceClient


class MemPalaceService:
    def _client_for(self, scope: MemoryScope) -> tuple:
        config = load_mempalace_config(scope)
        return config, MemPalaceClient(config)

    def _read_status_file(self, scope: MemoryScope) -> dict[str, Any]:
        status_path = tenant_status_path(scope)
        if status_path.exists():
            try:
                import json
                return json.loads(status_path.read_text())
            except Exception:
                return {}
        return {}

    def _write_status_file(self, scope: MemoryScope, payload: dict[str, Any]) -> None:
        import json
        status_path = tenant_status_path(scope)
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(json.dumps(payload, indent=2) + "\n")

    def get_config(self, scope_payload: dict[str, Any]) -> dict[str, Any]:
        scope = require_memory_scope(scope_payload)
        config = load_mempalace_config(scope)
        return {"scope": memory_scope_dict(scope), **mempalace_config_dict(config)}

    def set_config(self, scope_payload: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        scope = require_memory_scope(scope_payload)
        config = save_mempalace_config(scope, payload)
        return {"scope": memory_scope_dict(scope), **mempalace_config_dict(config)}

    def status(self, scope_payload: dict[str, Any]) -> dict[str, Any]:
        scope = require_memory_scope(scope_payload)
        config, _client = self._client_for(scope)
        command_found = True
        command_error = None
        try:
            subprocess.run([config.command, "--help"], check=False, capture_output=True, text=True)
        except FileNotFoundError:
            command_found = False
            command_error = "mempalace_command_not_found"

        persisted = self._read_status_file(scope)
        return {
            "scope": memory_scope_dict(scope),
            "config": mempalace_config_dict(config),
            "command_found": command_found,
            "error": command_error,
            "memory_mode": config.memory_mode,
            "last_operation": persisted.get("last_operation"),
            "last_synced_at": persisted.get("last_synced_at"),
            "last_error": persisted.get("last_error"),
        }

    def run_operation(self, scope_payload: dict[str, Any], operation: str) -> dict[str, Any]:
        scope = require_memory_scope(scope_payload)
        config, _client = self._client_for(scope)
        now = datetime.now(timezone.utc).isoformat()
        if not config.enabled:
            result = {
                "ok": False,
                "reason": "mempalace_disabled",
                "operation": operation,
                "scope": memory_scope_dict(scope),
            }
            self._write_status_file(scope, {
                "last_operation": operation,
                "last_synced_at": None,
                "last_error": result["reason"],
            })
            return result
        try:
            subprocess.run([config.command, operation], check=True, capture_output=True, text=True)
            self._write_status_file(scope, {
                "last_operation": operation,
                "last_synced_at": now,
                "last_error": None,
            })
            return {
                "ok": True,
                "reason": f"mempalace_{operation}_ok",
                "operation": operation,
                "completed_at": now,
                "scope": memory_scope_dict(scope),
            }
        except FileNotFoundError:
            self._write_status_file(scope, {
                "last_operation": operation,
                "last_synced_at": None,
                "last_error": "mempalace_command_not_found",
            })
            return {
                "ok": False,
                "reason": "mempalace_command_not_found",
                "operation": operation,
                "scope": memory_scope_dict(scope),
            }
        except subprocess.CalledProcessError as exc:
            self._write_status_file(scope, {
                "last_operation": operation,
                "last_synced_at": None,
                "last_error": exc.stderr,
            })
            return {
                "ok": False,
                "reason": f"mempalace_{operation}_failed",
                "operation": operation,
                "stderr": exc.stderr,
                "scope": memory_scope_dict(scope),
            }

    def search(self, scope_payload: dict[str, Any], query: str) -> dict[str, Any]:
        scope = require_memory_scope(scope_payload)
        config, client = self._client_for(scope)
        return {
            "scope": memory_scope_dict(scope),
            "config": mempalace_config_dict(config),
            "memory_mode": config.memory_mode,
            **client.search(query),
        }

    def wakeup(self, scope_payload: dict[str, Any], issue_title: str, issue_description: str) -> dict[str, Any]:
        scope = require_memory_scope(scope_payload)
        query = "\n\n".join(part for part in [issue_title, issue_description] if part).strip()
        search_result = self.search(memory_scope_dict(scope), query)
        memory_mode = search_result.get("memory_mode") or "augment"
        fallback_reason = None
        memory_source = "native_only"
        if search_result.get("ok", False):
            memory_source = "mempalace" if memory_mode in {"augment", "prefer_mempalace"} else "native_only"
        else:
            fallback_reason = search_result.get("reason") or "mempalace_unavailable"
            memory_source = "native_only"
        return {
            "scope": memory_scope_dict(scope),
            "config": search_result.get("config", {}),
            "ok": search_result.get("ok", False),
            "reason": search_result.get("reason"),
            "query": query,
            "memory_mode": memory_mode,
            "fallback_reason": fallback_reason,
            "wakeup_context": {
                "issue_title": issue_title,
                "issue_description": issue_description,
                "memory_hits": search_result.get("results") or [],
                "memory_source": memory_source,
            },
        }
