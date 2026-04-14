#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Agentopia rollback checklist =="
echo

echo "Before running this checklist, restore your previous known-good image refs and config values."
echo

echo "1) Validate the rollback target environment"
python3 scripts/env-validator.py

echo
echo "2) Recommended runtime restore commands"
echo "   docker compose --profile runtime pull"
echo "   docker compose --profile runtime up -d"

echo
echo "3) Post-rollback verification"
echo "   scripts/agentopia status"
echo "   scripts/agentopia runtime-check"
echo "   scripts/agentopia smoke"

echo
echo "4) Record rollback metadata"
echo "   - rollback timestamp"
echo "   - operator"
echo "   - restored PAPERCLIP_IMAGE"
echo "   - restored HERMES_IMAGE"
echo "   - reason for rollback"
echo "   - follow-up remediation"

echo
echo "Rollback checklist completed successfully."
