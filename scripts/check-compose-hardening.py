#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "docker-compose.yml"

REQUIRED_SNIPPETS = [
    "init: true",
    "read_only: true",
    "no-new-privileges:true",
    "cap_drop:",
    "- ALL",
    "tmpfs:",
    'max-size: "10m"',
    'max-file: "3"',
    ":ro",
]


def main() -> int:
    text = COMPOSE.read_text()
    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in text]
    if missing:
        for item in missing:
            print(f"missing hardening snippet: {item}")
        return 1
    print("compose hardening ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
