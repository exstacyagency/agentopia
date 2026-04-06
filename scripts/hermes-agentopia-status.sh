#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hermes-agentopia-env.sh"
source "$SCRIPT_DIR/hermes-agentopia-guard.sh"
LABEL="ai.hermes.gateway.agentopia"
echo "HERMES_HOME=$HERMES_HOME"
echo "API_SERVER_PORT=$API_SERVER_PORT"
launchctl print "gui/$(id -u)/${LABEL}" || true
echo
curl -fsS "http://127.0.0.1:${API_SERVER_PORT}/health" || true
echo
curl -fsS -H "Authorization: Bearer ${API_SERVER_KEY}" "http://127.0.0.1:${API_SERVER_PORT}/v1/models" || true
echo
