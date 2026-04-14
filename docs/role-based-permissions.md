# Role-Based Permissions

This document defines the current minimal role-based permission baseline for Paperclip client API access.

## Goals

- assign permissions through named roles instead of one-off key-by-key scope logic
- keep the role model explicit and small at first
- enforce roles at request time using existing API key identity data

## Current roles

- `submitter`
  - grants `tasks.write`
- `viewer`
  - grants no current write permissions

## Current enforcement

Paperclip resolves client access in this order:

1. file-based API key registry
2. env-based scoped key list
3. legacy single token

For file-based keys, a key may define either:

- `scope`, or
- `role`

If a role is present, Paperclip maps it to allowed scopes before authorizing the request. File-based keys may also carry `tenant_id`, `org_id`, and `client_id` metadata that is used by the tenant isolation layer.

## Current protected behavior

- `POST /tasks` requires `tasks.write`
- a `submitter` role is sufficient for `POST /tasks`
- a `viewer` role is rejected for `POST /tasks`

## Registry example

```json
{
  "keys": [
    {
      "id": "customer_submitter",
      "role": "submitter",
      "key": "submitter-secret",
      "status": "active"
    },
    {
      "id": "customer_viewer",
      "role": "viewer",
      "key": "viewer-secret",
      "status": "active"
    }
  ]
}
```

## Verification

Run:

```bash
./.venv/bin/python scripts/test_role_permissions.py
```

## Notes

This is the first role layer only. It does not yet include:

- tenant-specific role assignment
- human user identities
- approval-specific roles
- external role management APIs
