# Client-Facing API Authentication

This document defines the minimum client-facing API authentication baseline for Agentopia in its current scaffold state.

## Goals

- require authentication on client-facing Paperclip task submission endpoints
- keep internal endpoint auth separate from client API auth
- make client auth behavior explicit and testable

## Current baseline

Paperclip should require a bearer token on client-facing task submission requests.

Config:

- `PAPERCLIP_CLIENT_API_KEY`

Expected usage:

- clients send `Authorization: Bearer <token>` to Paperclip
- Paperclip rejects unauthenticated task submission requests
- internal endpoints continue using `AGENTOPIA_INTERNAL_AUTH_TOKEN`

## Current protected endpoints

- `POST /tasks`

## Expected behavior

If auth is missing or invalid:

- return HTTP `401`
- return a small JSON error payload
- do not continue request handling

## Local verification

Run:

```bash
./.venv/bin/python scripts/test_client_api_auth.py
```

## Definition of done for this item

This repo can consider client-facing API authentication minimally defined when:

- client task submission requires a configured bearer token
- internal auth remains separate from client auth
- behavior is documented and tested
