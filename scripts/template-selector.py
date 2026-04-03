#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "artifacts" / "templates"
REQUEST_PATH = ROOT / "artifacts" / "request.json"

ALLOWED = {"repo-summary", "budget-check"}


def main() -> int:
    template = sys.argv[1] if len(sys.argv) > 1 else "repo-summary"
    if template not in ALLOWED:
        print(f"unknown template: {template}", file=sys.stderr)
        return 1

    template_path = TEMPLATES / f"{template}.json"
    if not template_path.exists():
        print(f"missing template file: {template_path}", file=sys.stderr)
        return 1

    REQUEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    request = json.loads(template_path.read_text())
    REQUEST_PATH.write_text(json.dumps(request, indent=2) + "\n")
    print(f"sample task written: {template}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
