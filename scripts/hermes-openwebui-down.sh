#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT/docker-compose.hermes-openwebui.yml"

docker compose -f "$COMPOSE_FILE" down
