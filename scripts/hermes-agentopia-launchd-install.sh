#!/usr/bin/env bash
set -euo pipefail
LABEL="ai.hermes.gateway.agentopia"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
HERMES_BIN="$(python3 - <<'PY'
import os, shutil
p = shutil.which('hermes')
print(os.path.realpath(p) if p else '')
PY
)"
if [ -z "$HERMES_BIN" ]; then
  echo "hermes binary not found" >&2
  exit 1
fi
if [ -z "${API_SERVER_KEY:-}" ]; then
  echo "API_SERVER_KEY must be exported before installing the launchd service." >&2
  exit 1
fi
mkdir -p "$HOME/.hermes-agentopia/logs"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>export HERMES_HOME="$HOME/.hermes-agentopia" API_SERVER_ENABLED=true API_SERVER_KEY="$API_SERVER_KEY" API_SERVER_PORT=8742; exec "$HERMES_BIN" gateway run --replace</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/.hermes-agentopia/logs/launchd.out.log</string>
  <key>StandardErrorPath</key><string>$HOME/.hermes-agentopia/logs/launchd.err.log</string>
</dict>
</plist>
PLIST
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"
launchctl kickstart -k "gui/$(id -u)/${LABEL}" || true
echo "Installed ${LABEL} -> $PLIST"
