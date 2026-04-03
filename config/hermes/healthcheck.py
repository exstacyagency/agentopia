#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from runtimes import RuntimeTargets

ROOT = Path('/app')


def main() -> int:
    targets = RuntimeTargets.from_env(ROOT / 'config' / 'hermes' / '.env')
    if not targets.hermes_image or not targets.hermes_model_provider or not targets.hermes_model or not targets.hermes_api_key:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
