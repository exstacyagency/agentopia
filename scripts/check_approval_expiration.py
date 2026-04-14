#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from paperclip.service import PaperclipService

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    service = PaperclipService(ROOT / "data" / "paperclip.sqlite3")
    expired = service.find_expired_approvals()
    if not expired:
        print("approval expiration ok")
        return 0
    for item in expired:
        print(item)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
