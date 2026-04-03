#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from runtimes import RuntimeTargets

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    targets = RuntimeTargets.from_env(ROOT / ".env")
    print(targets.dashboard())
    print(targets.report())
    print(targets.report_json(), end="")
    if not targets.ok():
        return 1
    print("env validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
