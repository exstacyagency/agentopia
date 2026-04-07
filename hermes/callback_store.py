from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HermesCallbackStore:
    def __init__(self, root: Path):
        self.root = root
        self.base = self.root / "var" / "hermes" / "callback-results"
        self.base.mkdir(parents=True, exist_ok=True)

    def store(self, task_id: str, payload: dict[str, Any]) -> Path:
        path = self.base / f"{task_id}.json"
        wrapped = {
            "stored_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        path.write_text(json.dumps(wrapped, indent=2) + "\n")
        return path
