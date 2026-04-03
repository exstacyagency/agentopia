#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from runtimes import RuntimeTargets

ROOT = Path('/app')


def main() -> int:
    targets = RuntimeTargets.from_env(ROOT / 'config' / 'paperclip' / '.env')
    if not targets.paperclip_image or not targets.paperclip_url or not targets.paperclip_api_key:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
