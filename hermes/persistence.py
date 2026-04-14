from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes.redaction import redact_value


class HermesPersistence:
    def __init__(self, root: Path):
        self.root = root
        self.base = self.root / "var" / "hermes"
        self.runs_dir = self.base / "runs"
        self.callbacks_dir = self.base / "callbacks"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.callbacks_dir.mkdir(parents=True, exist_ok=True)

    def persist_result(self, result: dict[str, Any]) -> Path:
        task_id = result.get("task_id", "unknown-task")
        run_id = (result.get("run") or {}).get("run_id", f"run_{task_id}")
        path = self.runs_dir / f"{task_id}__{run_id}.json"
        payload = {
            "persisted_at": datetime.now(timezone.utc).isoformat(),
            "result": redact_value(result),
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")
        return path

    def record_callback_attempt(
        self,
        *,
        task_id: str,
        run_id: str,
        result_url: str,
        success: bool,
        status_code: int | None,
        error: str | None,
    ) -> Path:
        path = self.callbacks_dir / f"{task_id}__{run_id}.json"
        payload = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "run_id": run_id,
            "result_url": result_url,
            "success": success,
            "status_code": status_code,
            "error": error,
            "attempt_count": 1,
            "retryable": not success,
        }
        path.write_text(json.dumps(redact_value(payload), indent=2) + "\n")
        return path
