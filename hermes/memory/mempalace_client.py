from __future__ import annotations

import json
import subprocess
from typing import Any

from hermes.memory.config import MemPalaceConfig


class MemPalaceClient:
    def __init__(self, config: MemPalaceConfig):
        self.config = config

    def search(self, query: str) -> dict[str, Any]:
        if not self.config.enabled:
            return {
                "ok": False,
                "reason": "mempalace_disabled",
                "query": query,
                "results": [],
            }

        try:
            completed = subprocess.run(
                [self.config.command, "search", query, "--json"],
                check=True,
                capture_output=True,
                text=True,
            )
            raw = completed.stdout.strip()
            parsed = json.loads(raw) if raw else {}
            return {
                "ok": True,
                "reason": "mempalace_search_ok",
                "query": query,
                "results": parsed.get("results") if isinstance(parsed, dict) else parsed,
                "raw": parsed,
            }
        except FileNotFoundError:
            return {
                "ok": False,
                "reason": "mempalace_command_not_found",
                "query": query,
                "results": [],
            }
        except subprocess.CalledProcessError as exc:
            return {
                "ok": False,
                "reason": "mempalace_search_failed",
                "query": query,
                "results": [],
                "stderr": exc.stderr,
            }
        except json.JSONDecodeError:
            return {
                "ok": False,
                "reason": "mempalace_invalid_json",
                "query": query,
                "results": [],
                "stdout": completed.stdout if 'completed' in locals() else None,
            }
