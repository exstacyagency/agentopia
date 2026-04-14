#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Agentopia deployment checklist =="
echo

echo "1) Validate environment"
python3 scripts/env-validator.py

echo
echo "2) Verify local validation suite"
./scripts/bootstrap-venv.sh
./.venv/bin/python scripts/test_contract_schemas.py
./.venv/bin/python scripts/test_paperclip_service.py
./.venv/bin/python scripts/test_hermes_executor.py
./.venv/bin/python scripts/test_integration_flow.py
./.venv/bin/python scripts/test_runtimes.py

echo
echo "3) Recommended runtime bring-up commands"
echo "   docker compose --profile runtime pull"
echo "   docker compose --profile runtime up -d"

echo
echo "4) Post-deploy verification"
echo "   scripts/agentopia status"
echo "   scripts/agentopia runtime-check"
echo "   scripts/agentopia smoke"

echo
echo "Deployment checklist completed successfully."
