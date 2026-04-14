# API Key Rotation and Revocation

This document defines the current minimal rotation and revocation baseline for Paperclip client API keys.

## Goals

- support multiple concurrent client keys during rotation
- support explicit revocation without changing application code
- keep enforcement simple, local, and testable

## Configuration

Paperclip now supports a registry file:

- `PAPERCLIP_CLIENT_API_KEYS_FILE`

Default path:

- `config/paperclip/client_api_keys.json`

File format:

```json
{
  "keys": [
    {
      "id": "customer_a_primary",
      "scope": "tasks.write",
      "key": "secret-value",
      "status": "active"
    },
    {
      "id": "customer_a_old",
      "scope": "tasks.write",
      "key": "old-secret-value",
      "status": "revoked"
    }
  ]
}
```

## Rotation flow

1. add a new `active` key entry with the required scope
2. distribute the new key to the client
3. verify clients are using the new key
4. mark the old key as `revoked`
5. reload or restart Paperclip if needed in the current environment

This minimal implementation allows overlapping active keys during transition windows.

## Revocation behavior

If a key is marked `revoked`:

- Paperclip rejects requests using that key
- Paperclip returns HTTP `401`
- request handling stops before task submission

## Current supported scope

- `tasks.write`

## Compatibility

Current resolution order is:

1. file-based key registry via `PAPERCLIP_CLIENT_API_KEYS_FILE`
2. env-based scoped list via `PAPERCLIP_CLIENT_API_KEYS`
3. legacy single token via `PAPERCLIP_CLIENT_API_KEY`

## Verification

Run:

```bash
./.venv/bin/python scripts/test_api_key_rotation_revocation.py
```

## Notes

This slice does not yet include:

- automated issuance APIs
- expiration timestamps
- audit trails for key lifecycle changes
- tenant-aware key ownership rules
