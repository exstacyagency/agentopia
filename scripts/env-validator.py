#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_VARS = [
    "PAPERCLIP_URL",
    "PAPERCLIP_API_KEY",
    "HERMES_MODEL_PROVIDER",
    "HERMES_MODEL",
    "HERMES_API_KEY",
    "PAPERCLIP_IMAGE",
    "HERMES_IMAGE",
]


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> int:
    env = load_env_file(ROOT / ".env")
    missing = []
    for key in REQUIRED_VARS:
        value = os.environ.get(key, env.get(key, "")).strip()
        if not value:
            missing.append(key)
    if missing:
        print("missing runtime env vars:")
        for key in missing:
            print(f"- {key}")
        return 1
    print("env validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
