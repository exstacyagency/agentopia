#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

./scripts/validate.sh
./scripts/doctor.sh
./scripts/contract-demo.sh

grep -q '^services:$' docker-compose.yml
grep -q '^  paperclip:$' docker-compose.yml
grep -q '^  hermes:$' docker-compose.yml

echo "smoke ok"
