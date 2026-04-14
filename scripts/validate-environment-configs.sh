#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

for env_file in config/environments/*.env; do
  echo "Validating $env_file"
  python3 scripts/env-validator.py --env-file "$env_file"
done
