#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/bootstrap-venv.sh
./.venv/bin/python -m pip install 'pip-audit>=2.7.3,<3'
./.venv/bin/python -m pip_audit -r requirements.lock
