#!/usr/bin/env bash
set -euo pipefail
EXPECTED_HOME="$HOME/.hermes-agentopia"
CURRENT_HOME="${HERMES_HOME:-}"
if [ -z "$CURRENT_HOME" ]; then
  echo "Refusing to continue: HERMES_HOME is not set." >&2
  echo "Expected: $EXPECTED_HOME" >&2
  exit 1
fi
if [ "$CURRENT_HOME" != "$EXPECTED_HOME" ]; then
  echo "Refusing to continue: HERMES_HOME points to $CURRENT_HOME" >&2
  echo "Expected isolated home: $EXPECTED_HOME" >&2
  exit 1
fi
if [ "$CURRENT_HOME" = "$HOME/.hermes" ]; then
  echo "Refusing to continue: shared Hermes home is forbidden for Agentopia scripts." >&2
  exit 1
fi
