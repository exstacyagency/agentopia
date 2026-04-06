#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/hermes-agentopia-env.sh"
if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required" >&2
  exit 1
fi
export OPENAI_API_BASE_URL="http://host.docker.internal:${API_SERVER_PORT}/v1"
export OPENAI_API_KEY="$API_SERVER_KEY"
docker run -d -p 3001:8080 \
  -e OPENAI_API_BASE_URL="$OPENAI_API_BASE_URL" \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui-agentopia:/app/backend/data \
  --name open-webui-agentopia \
  --restart always \
  ghcr.io/open-webui/open-webui:main

echo "Open WebUI for Agentopia should be at http://localhost:3001"
