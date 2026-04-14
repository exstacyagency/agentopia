from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TraceLogger:
    def __init__(self, root: Path):
        self.root = root
        self.dir = self.root / "var" / "traces"
        self.dir.mkdir(parents=True, exist_ok=True)

    def record(self, trace_id: str, service: str, event: str, **fields: Any) -> Path:
        path = self.dir / f"trace-{trace_id}.jsonl"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": trace_id,
            "service": service,
            "event": event,
            **fields,
        }
        with path.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")
        return path
