#!/usr/bin/env bash
set -euo pipefail

echo "Setting up agentopia..."

if [ -f .env ] && [ ! -f .env.backup ]; then
  cp .env .env.backup
fi

mkdir -p config/paperclip config/hermes

echo "Done. Add real config before starting services."
