#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PAPERCLIP_DIR="${PAPERCLIP_DIR:-$HOME/.openclaw/workspace/upstream-paperclip}"

echo "Preparing Paperclip dev checkout..."
"$ROOT/scripts/bootstrap-paperclip-dev.sh"

echo
echo "Start these in separate terminals:"
echo
echo "1) Paperclip"
echo "   cd $PAPERCLIP_DIR && pnpm dev"
echo
echo "2) Isolated Hermes"
echo "   cd $ROOT && export API_SERVER_KEY='<your-local-secret>' && ./scripts/hermes-agentopia-start.sh"
echo
echo "3) Isolated Open WebUI"
echo "   cd $ROOT && export API_SERVER_KEY='<your-local-secret>' && ./scripts/hermes-agentopia-openwebui-up.sh"
echo
echo "Expected URLs:"
echo "- Paperclip: http://127.0.0.1:3100 or the port it prints"
echo "- Hermes Open WebUI: http://localhost:3001"
