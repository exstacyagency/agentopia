#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p artifacts
TEMPLATE="${1:-repo-summary}"
TEMPLATE_PATH="artifacts/templates/${TEMPLATE}.json"
if [ ! -f "$TEMPLATE_PATH" ]; then
  echo "unknown template: $TEMPLATE" >&2
  exit 1
fi

cp "$TEMPLATE_PATH" artifacts/request.json
echo "sample task written: $TEMPLATE"
