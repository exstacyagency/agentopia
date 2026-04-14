# Scoped API Keys

This document defines the current scoped client API key baseline for Agentopia.

## Goals

- replace a single flat client token with explicit per-key scopes
- keep the first supported scope small and enforceable
- preserve backward compatibility briefly while the auth surface evolves

## Current configuration

Paperclip supports a scoped client key list via:

- `PAPERCLIP_CLIENT_API_KEYS`

Format:

- comma-separated entries
- each entry is `scope:key`

Example:

```bash
PAPERCLIP_CLIENT_API_KEYS="tasks.write:client-write-key"
```

Legacy fallback still exists for:

- `PAPERCLIP_CLIENT_API_KEY`

## Current supported scope

- `tasks.write`

A key with `tasks.write` can call:

- `POST /tasks`

## Behavior

If the bearer token maps to a known scoped key with the required scope:

- Paperclip accepts the request
- Paperclip records a non-secret key fingerprint in logs

If the token is missing, invalid, or lacks the required scope:

- Paperclip returns HTTP `401`
- request handling stops before task submission

## Verification

Run:

```bash
./.venv/bin/python scripts/test_scoped_api_keys.py
```

## Notes

This scoped-key baseline now pairs with `docs/api-key-rotation-revocation.md` for active/revoked registry handling and overlapping key rotation windows.

Still not included:

- management APIs for issuing keys
- per-tenant isolation
