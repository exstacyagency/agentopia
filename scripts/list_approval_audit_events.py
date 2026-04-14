#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from paperclip.service import PaperclipService

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: list_approval_audit_events.py <task_id>")
        return 2
    task_id = sys.argv[1]
    service = PaperclipService(ROOT / "data" / "paperclip.sqlite3")
    events = service.get_approval_audit(task_id)
    for event in events:
        print(event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
