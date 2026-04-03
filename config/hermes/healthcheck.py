#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from runtimes import RuntimeTargets

ROOT = Path('/app')


def main() -> int:
    targets = RuntimeTargets.from_env(ROOT / 'config' / 'hermes' / '.env')
    data = {
        'service': 'hermes',
        'ok': bool(targets.hermes_image and targets.hermes_model_provider and targets.hermes_model and targets.hermes_api_key),
        'missing': [
            key for key, value in {
                'HERMES_IMAGE': targets.hermes_image,
                'HERMES_MODEL_PROVIDER': targets.hermes_model_provider,
                'HERMES_MODEL': targets.hermes_model,
                'HERMES_API_KEY': targets.hermes_api_key,
            }.items() if not value
        ],
    }
    print(json.dumps(data, indent=2))
    return 0 if data['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
