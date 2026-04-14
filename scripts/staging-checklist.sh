#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Agentopia staging checklist =="
echo

echo "1) Validate staging config"
python3 scripts/env-validator.py --env-file config/environments/staging.env

echo
echo "2) Validate tracked environment templates"
./scripts/validate-environment-configs.sh

echo
echo "3) Recommended staging bring-up commands"
echo "   docker compose --profile runtime pull"
echo "   docker compose --profile runtime up -d"

echo
echo "4) Post-staging verification"
echo "   scripts/agentopia status"
echo "   scripts/agentopia runtime-check"
echo "   scripts/agentopia smoke"

echo
echo "Staging checklist completed successfully."
