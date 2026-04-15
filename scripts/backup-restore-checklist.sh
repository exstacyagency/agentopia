#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB_PATH="${PAPERCLIP_DB_PATH:-$ROOT/data/paperclip.sqlite3}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/var/backups}"
DATABASE_URL="${PAPERCLIP_DATABASE_URL:-}"

mkdir -p "$BACKUP_DIR"

echo "backup_restore_checklist"
echo "  db_path: $DB_PATH"
echo "  backup_dir: $BACKUP_DIR"

if [[ -n "$DATABASE_URL" ]]; then
  echo "  backend: postgres"
  if command -v pg_dump >/dev/null 2>&1; then
    echo "  pg_dump: available"
  else
    echo "  pg_dump: missing"
  fi
else
  echo "  backend: sqlite"
  if [[ -f "$DB_PATH" ]]; then
    echo "  sqlite_db: present"
  else
    echo "  sqlite_db: missing"
  fi
fi

echo "  restore_verification_steps:"
echo "    - apply migrations if needed"
echo "    - verify health checks"
echo "    - verify task and audit reads"
echo "    - verify queue metadata if recovery is needed"
