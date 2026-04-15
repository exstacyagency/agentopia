# Backup and Restore Plan

This document defines the current minimal backup and restore baseline for Agentopia.

## Goals

- identify what must be backed up
- define a repeatable restore path
- make verification part of the backup story

## Current backup scope

Minimum backup targets:

- Paperclip database
  - SQLite path by default
  - Postgres database when configured
- rendered production environment files or equivalent deployment config artifacts
- operator deployment metadata

## Current backup frequency

Minimum recommendation:

- before production-like deployments
- daily for active environments
- before schema changes or migration rollouts

## SQLite backup path

Example:

```bash
cp data/paperclip.sqlite3 var/backups/paperclip-$(date +%Y%m%d-%H%M%S).sqlite3
```

## Postgres backup path

Example:

```bash
pg_dump "$PAPERCLIP_DATABASE_URL" > var/backups/paperclip-$(date +%Y%m%d-%H%M%S).sql
```

## Restore path

### SQLite restore

1. stop writes to Paperclip
2. copy the selected backup file into the active DB path
3. start Paperclip again
4. verify readiness and smoke checks

### Postgres restore

1. stop writes to Paperclip
2. restore the selected SQL dump into the target database
3. run migrations if required by the selected restore point
4. start Paperclip again
5. verify readiness and smoke checks

## Restore verification

After restore, verify at minimum:

- migrations are applied
- health/readiness checks pass
- expected task and audit records are readable
- queue metadata is present if runtime recovery is needed

## Verification helper

Run:

```bash
./scripts/backup-restore-checklist.sh
```

## Notes

This slice does not yet include:

- automated scheduled backups
- encrypted backup transport/storage setup
- retention enforcement automation
- point-in-time recovery
