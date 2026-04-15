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

This slice now provides a Postgres-backed implementation for the Paperclip DB helper surface used by the current service layer.

It provides:

- Postgres DB selection
- Postgres connection bootstrap
- helper parity for task, audit, queue, idempotency, and result operations
- dependency setup for psycopg

Still not included:

- production migration execution against Postgres itself
- deployment wiring for managed Postgres
- a live integration test against a running Postgres instance in this repo

## Verification

Run:

```bash
./.venv/bin/python scripts/test_postgres_persistence.py
```
