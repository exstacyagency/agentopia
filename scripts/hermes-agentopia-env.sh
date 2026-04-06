#!/usr/bin/env bash
# Source this file to target the isolated Agentopia Hermes environment.
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes-agentopia}"
export API_SERVER_ENABLED="${API_SERVER_ENABLED:-true}"
export API_SERVER_PORT="${API_SERVER_PORT:-8742}"
export API_SERVER_KEY="${API_SERVER_KEY:-}"
if [ -z "$API_SERVER_KEY" ]; then
  echo "API_SERVER_KEY is not set. Export it before running Agentopia Hermes scripts." >&2
fi
