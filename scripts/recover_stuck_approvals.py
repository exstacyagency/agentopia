#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from paperclip.service import PaperclipService

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--reset-pending", action="store_true")
    args = parser.parse_args()

    service = PaperclipService(ROOT / "data" / "paperclip.sqlite3")

    if args.list:
        items = service.list_stuck_approval_tasks()
        for item in items:
            print(item)
        return 0

    if args.task_id and args.reset_pending:
        result = service.recover_stuck_approval(args.task_id)
        if result is None:
            print({"error": "task not found", "task_id": args.task_id})
            return 1
        print(result)
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
