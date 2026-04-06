#!/usr/bin/env bash
set -euo pipefail
docker rm -f open-webui-agentopia >/dev/null 2>&1 || true
echo "Stopped open-webui-agentopia"
