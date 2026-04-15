# Migrations

This document defines the current minimal schema migration baseline for Paperclip.

## Goals

- stop relying on inline schema bootstrap alone
- make schema evolution explicit and replayable
- track applied versions in the database

## Current model

Paperclip now applies SQL migrations from:

- `migrations/`

Applied versions are recorded in:

- `schema_migrations`

Current initial migration:

- `001_initial_schema.sql`

## Current behavior

On database initialization:

- Paperclip applies unapplied SQL migrations in order
- each applied migration is recorded exactly once

## Verification

Run:

```bash
./.venv/bin/python scripts/test_migrations.py
```

## Notes

This is the first migration slice. It does not yet include:

- rollback migrations
- branching migration safeguards
- Postgres-specific migration tooling
