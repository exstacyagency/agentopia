#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-core}"

CORE_TESTS=(
  "scripts/test_contract_schemas.py"
  "scripts/test_paperclip_service.py"
  "scripts/test_hermes_executor.py"
  "scripts/test_integration_flow.py"
)

FULL_TESTS=(
  "scripts/test_runtimes.py"
  "scripts/test_env_validator.py"
  "scripts/test_render_production_env.py"
  "scripts/check-compose-hardening.py"
  "scripts/run-dependency-scan.sh"
  "scripts/test_check_provenance.py"
  "scripts/check-provenance.py"
  "scripts/test_persistence_redaction.py"
  "scripts/test_request_limits.py"
  "scripts/test_input_validation.py"
  "scripts/test_rate_limits.py"
  "scripts/test_audit_logging.py"
  "scripts/test_secret_handling.py"
  "scripts/check-secret-handling.py"
  "scripts/test_internal_auth.py"
  "scripts/test_structured_logging.py"
  "scripts/test_correlation_ids.py"
  "scripts/test_health_checks.py"
  "scripts/test_metrics.py"
  "scripts/test_tracing_visibility.py"
  "scripts/test_alerts.py"
  "scripts/test_approval_reconciliation.py"
  "scripts/test_approval_expiration.py"
  "scripts/test_approval_audit_trail.py"
)

run_item() {
  local item="$1"
  if [[ "$item" == *.sh ]]; then
    echo "→ $item"
    "./$item"
  else
    echo "→ $item"
    ./.venv/bin/python "$item"
  fi
}

echo "Bootstrapping virtualenv"
./scripts/bootstrap-venv.sh

echo "Running validation mode: $MODE"
for item in "${CORE_TESTS[@]}"; do
  run_item "$item"
done

case "$MODE" in
  core)
    ;;
  full)
    for item in "${FULL_TESTS[@]}"; do
      run_item "$item"
    done
    ;;
  *)
    echo "usage: ./scripts/validate-suite.sh [core|full]" >&2
    exit 2
    ;;
esac

echo "Validation complete: $MODE"
