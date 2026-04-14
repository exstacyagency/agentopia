#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BASE_ENV="config/environments/production.env"
SECRETS_ENV="config/environments/production.secrets.env"
OUTPUT_ENV="config/environments/production.rendered.env"

if [ ! -f "$BASE_ENV" ]; then
  echo "missing base env: $BASE_ENV" >&2
  exit 1
fi

if [ ! -f "$SECRETS_ENV" ]; then
  echo "missing secrets env: $SECRETS_ENV" >&2
  exit 1
fi

cat "$BASE_ENV" "$SECRETS_ENV" > "$OUTPUT_ENV"

echo "rendered production env: $OUTPUT_ENV"
python3 scripts/env-validator.py --env-file "$OUTPUT_ENV"
