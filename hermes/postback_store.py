from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HermesPostbackStore:
    def __init__(self, root: Path):
        self.base = root / "var" / "hermes" / "postbacks"
        self.base.mkdir(parents=True, exist_ok=True)

    def record(self, *, issue_id: str, run_id: str, postback_type: str, success: bool, error: str | None, payload: dict[str, Any] | None = None) -> Path:
        path = self.base / f"{run_id}__{postback_type}.json"
        data = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "issue_id": issue_id,
            "run_id": run_id,
            "postback_type": postback_type,
            "success": success,
            "error": error,
            "retryable": not success,
            "payload": payload or {},
        }
        path.write_text(json.dumps(data, indent=2) + "\n")
        return path
