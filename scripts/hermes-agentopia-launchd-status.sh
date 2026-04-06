#!/usr/bin/env bash
set -euo pipefail
LABEL="ai.hermes.gateway.agentopia"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
ls -l "$PLIST"
launchctl print "gui/$(id -u)/${LABEL}" || true
echo
echo '--- health ---'
curl -fsS http://127.0.0.1:8742/health || true
echo
echo '--- models ---'
curl -fsS -H 'Authorization: Bearer agentopia-secret' http://127.0.0.1:8742/v1/models || true
echo
