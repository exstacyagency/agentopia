#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT/docker-compose.hermes-openwebui.yml"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
  echo "OPENAI_API_KEY is not set. Set it to match Hermes API_SERVER_KEY." >&2
  exit 1
fi

if [ -z "${OPENAI_API_BASE_URL:-}" ]; then
  export OPENAI_API_BASE_URL="http://host.docker.internal:8642/v1"
fi

echo "Starting Open WebUI..."
docker compose -f "$COMPOSE_FILE" up -d

echo
echo "Open WebUI should be available at: http://localhost:3000"
echo "Expected Hermes API base: $OPENAI_API_BASE_URL"
