#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/hermes-agentopia-env.sh"
cd "$HERMES_HOME"
echo "Starting isolated Hermes Agentopia instance"
echo "HERMES_HOME=$HERMES_HOME"
echo "API_SERVER_PORT=$API_SERVER_PORT"
exec hermes gateway run --replace
