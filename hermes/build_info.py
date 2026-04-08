from __future__ import annotations

from datetime import datetime, timezone

BUILD_STAMP = datetime.now(timezone.utc).isoformat()
RUNTIME_FEATURES = [
    "issue_action_endpoint",
    "dashboard_state_endpoint",
    "runtime_guard_health",
    "paperclip_http_diagnostics",
]
