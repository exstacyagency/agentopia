# Stronger Service-to-Service Authentication

This document defines the minimum service-to-service authentication baseline for Agentopia in its current scaffold state.

## Goals

- ensure internal execution calls are authenticated
- ensure result callbacks are authenticated
- keep the auth path explicit and testable

## Current baseline

Paperclip and Hermes should share an internal auth token.

Config:

- `AGENTOPIA_INTERNAL_AUTH_TOKEN`

Expected usage:

- Paperclip includes `Authorization: Bearer <token>` when dispatching to Hermes
- Hermes includes `Authorization: Bearer <token>` when posting results back to Paperclip
- Paperclip and Hermes reject internal endpoints when the bearer token is missing or incorrect

## Current protected endpoints

### Hermes
- `POST /internal/execute`

### Paperclip
- `POST /internal/tasks/<id>/result`

## Expected behavior

If auth is missing or invalid:

- return HTTP `401`
- return a small JSON error payload
- do not continue request handling

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_internal_auth.py
```

## Definition of done for this item

This repo can consider stronger service-to-service authentication minimally defined when:

- internal dispatch and result endpoints require a shared auth token
- the dispatch client sends the token
- protected endpoints reject unauthenticated requests
- behavior is documented and tested
