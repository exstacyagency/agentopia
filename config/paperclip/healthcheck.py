#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from runtimes import RuntimeTargets

ROOT = Path('/app')


def main() -> int:
    targets = RuntimeTargets.from_env(ROOT / 'config' / 'paperclip' / '.env')
    data = {
        'service': 'paperclip',
        'ok': bool(targets.paperclip_image and targets.paperclip_url and targets.paperclip_api_key),
        'missing': [
            key for key, value in {
                'PAPERCLIP_IMAGE': targets.paperclip_image,
                'PAPERCLIP_URL': targets.paperclip_url,
                'PAPERCLIP_API_KEY': targets.paperclip_api_key,
            }.items() if not value
        ],
    }
    print(json.dumps(data, indent=2))
    return 0 if data['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
