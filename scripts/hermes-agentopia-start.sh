#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hermes-agentopia-env.sh"
source "$SCRIPT_DIR/hermes-agentopia-guard.sh"
cd "$HERMES_HOME"
echo "Starting isolated Hermes Agentopia instance"
echo "HERMES_HOME=$HERMES_HOME"
echo "API_SERVER_PORT=$API_SERVER_PORT"
exec hermes gateway run --replace
