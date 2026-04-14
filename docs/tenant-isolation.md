# Client, Org, and Tenant Isolation

This document defines the current minimal tenant isolation baseline for Paperclip.

## Goals

- bind client API keys to a tenant identity
- stamp tasks with tenant ownership at creation time
- reject cross-tenant task reads and audit access

## Current model

A file-based client API key may now carry:

- `tenant_id`
- `org_id`
- `client_id`

Paperclip records tenant ownership on each task and uses the authenticated key identity to enforce access.

## Current enforcement

- `POST /tasks`
  - requires authenticated client auth
  - stamps the task with the caller tenant metadata
- `GET /tasks/<id>`
  - allowed only when the authenticated tenant matches the task tenant
- `GET /tasks/<id>/audit`
  - allowed only when the authenticated tenant matches the task tenant

## Registry example

```json
{
  "keys": [
    {
      "id": "tenant_a_submitter",
      "role": "submitter",
      "tenant_id": "tenant_a",
      "org_id": "org_a",
      "client_id": "client_a",
      "key": "tenant-a-secret",
      "status": "active"
    }
  ]
}
```

## Behavior

If a request tries to access another tenant's task:

- Paperclip returns HTTP `403`
- request handling stops

## Verification

Run:

```bash
./.venv/bin/python scripts/test_tenant_isolation.py
```

## Notes

This is the first tenant boundary only. It does not yet include:

- tenant-aware approval workflows
n- tenant-specific rate limits
- tenant-scoped memory boundaries
- full org hierarchy semantics beyond simple ownership tags
