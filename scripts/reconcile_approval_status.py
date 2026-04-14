#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from paperclip.service import PaperclipService

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    service = PaperclipService(ROOT / "data" / "paperclip.sqlite3")
    mismatches = service.reconcile_approval_status()
    if not mismatches:
        print("approval reconciliation ok")
        return 0
    for mismatch in mismatches:
        print(mismatch)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
