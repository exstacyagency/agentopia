#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/hermes-agentopia-env.sh"
echo "HERMES_HOME=$HERMES_HOME"
echo "API_SERVER_PORT=$API_SERVER_PORT"
hermes gateway status || true
echo
curl -fsS "http://127.0.0.1:${API_SERVER_PORT}/health" || true
echo
curl -fsS "http://127.0.0.1:${API_SERVER_PORT}/v1/models" || true
echo
