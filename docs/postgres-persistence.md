# Postgres Persistence

This document defines the current minimal Postgres persistence baseline for Paperclip.

## Goals

- add a production-oriented database option beyond SQLite
- keep local development and tests working with SQLite by default
- make Postgres selection explicit through config

## Current config

- `PAPERCLIP_DATABASE_URL`

If `PAPERCLIP_DATABASE_URL` uses a Postgres scheme:

- `postgres://`
- `postgresql://`

Paperclip will initialize a Postgres-backed DB implementation.

If it is unset:

- Paperclip continues using the SQLite path for local/dev flows

## Current scope

This is the first Postgres slice.

It provides:

- Postgres DB selection
- Postgres connection bootstrap
- dependency setup for psycopg

It does not yet provide:

- full parity of every DB helper method
- production migration execution against Postgres
- deployment wiring for managed Postgres

## Verification

Run:

```bash
./.venv/bin/python scripts/test_postgres_persistence.py
```
