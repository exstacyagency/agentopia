from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes.redaction import redact_value


class HermesAuditLogger:
    def __init__(self, root: Path):
        self.path = root / "var" / "hermes" / "audit.log"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, payload: dict[str, Any]) -> Path:
        entry = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": redact_value(payload),
        }
        with self.path.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
        return self.path
