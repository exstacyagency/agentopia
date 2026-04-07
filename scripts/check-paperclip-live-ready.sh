#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:3102}"

echo "Checking Paperclip live readiness at: $BASE_URL"
if curl -fsS "$BASE_URL/api/health" >/dev/null; then
  echo "PASS: Paperclip health endpoint responded"
else
  echo "FAIL: Paperclip health endpoint is unavailable at $BASE_URL/api/health" >&2
  exit 1
fi
