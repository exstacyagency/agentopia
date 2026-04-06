#!/usr/bin/env bash
set -euo pipefail

PAPERCLIP_DIR="${PAPERCLIP_DIR:-$HOME/.openclaw/workspace/upstream-paperclip}"

if [ ! -d "$PAPERCLIP_DIR/.git" ]; then
  echo "FAIL: local Paperclip checkout not found at $PAPERCLIP_DIR" >&2
  exit 1
fi

cd "$PAPERCLIP_DIR"

check_file() {
  local path="$1"
  if [ ! -e "$path" ]; then
    echo "FAIL: missing expected local Paperclip patch file: $path" >&2
    exit 1
  fi
}

check_file packages/adapters/hermes-local/package.json
check_file packages/adapters/hermes-local/src/index.ts
check_file packages/adapters/hermes-local/src/server/index.ts
check_file packages/adapters/hermes-local/src/ui/index.ts

if ! grep -q 'workspace:\*' server/package.json; then
  echo "FAIL: server/package.json does not appear to use the local workspace Hermes adapter" >&2
  exit 1
fi

if ! grep -q 'workspace:\*' ui/package.json; then
  echo "FAIL: ui/package.json does not appear to use the local workspace Hermes adapter" >&2
  exit 1
fi

echo "OK: local Paperclip patch state looks present"
echo "- repo: $PAPERCLIP_DIR"
echo "- hermes adapter workspace files present"
echo "- server/ui appear wired to workspace adapter"
