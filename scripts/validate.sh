#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

required_files=(
  .env.example
  .gitignore
  README.md
  docker-compose.yml
  scripts/setup.sh
  scripts/update.sh
  scripts/validate.sh
  config/paperclip/paperclip.yml
  config/hermes/hermes.yml
)

missing=0
for f in "${required_files[@]}"; do
  if [ ! -f "$f" ]; then
    echo "missing: $f"
    missing=1
  fi
done

for d in config/paperclip config/hermes memory skills; do
  if [ ! -d "$d" ]; then
    echo "missing dir: $d"
    missing=1
  fi
done

if [ "$missing" -ne 0 ]; then
  exit 1
fi

echo "validation ok"
