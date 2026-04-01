#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

missing=0
for f in .env.example .gitignore README.md docker-compose.yml scripts/setup.sh scripts/update.sh config/paperclip/paperclip.yml config/hermes/hermes.yml; do
  if [ ! -f "$f" ]; then
    echo "missing: $f"
    missing=1
  fi
done

if [ "$missing" -ne 0 ]; then
  exit 1
fi

echo "validation ok"
