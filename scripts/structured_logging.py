from __future__ import annotations

import json
from datetime import datetime, timezone


def log_event(service: str, event: str, **fields) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": service,
        "event": event,
        **fields,
    }
    print(json.dumps(payload), flush=True)
