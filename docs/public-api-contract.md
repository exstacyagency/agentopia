# Public API Contract

This document defines the stable client-facing Paperclip API surface for Agentopia v1.

## Scope

This contract covers the current client-usable HTTP endpoints exposed by Paperclip:

- `POST /tasks`
- `GET /tasks/<id>`
- `GET /tasks/<id>/audit`
- `GET /health`
- `GET /metrics`

It also distinguishes internal-only callbacks that are not part of the public contract:

- `POST /internal/tasks/<id>/result`

## Versioning

The current public contract version is `v1`.

For task submission and Hermes result payloads, `schema_version` must be `v1`.

## Authentication

### Client-facing endpoints

These endpoints require client authentication:

- `POST /tasks`
- `GET /tasks/<id>`
- `GET /tasks/<id>/audit`

Authentication uses a bearer token in the `Authorization` header.

Supported client key sources:

1. `PAPERCLIP_CLIENT_API_KEYS_FILE`
2. `PAPERCLIP_CLIENT_API_KEYS`
3. `PAPERCLIP_CLIENT_API_KEY`

### Internal-only endpoints

`POST /internal/tasks/<id>/result` is not public. It requires the internal service token:

- `AGENTOPIA_INTERNAL_AUTH_TOKEN`

## Public endpoints

### `POST /tasks`

Submit a task request.

#### Headers

- `Authorization: Bearer <client-api-key>`
- `Content-Type: application/json`
- `Idempotency-Key: <optional-key>`

#### Request body

The request body must match `schemas/task_request_v1.json`.

#### Success response

- `201 Created`
- JSON body containing the Paperclip task record

The task record includes:

- task identity and metadata
- requester
- tenant context
- current state
- approval status
- timestamps
- result, when available

#### Error responses

- `400 Bad Request` for invalid JSON/schema/input validation failures
- `401 Unauthorized` for missing, invalid, or revoked client keys
- `413 Payload Too Large` when the request exceeds `PAPERCLIP_MAX_REQUEST_BYTES`
- `429 Too Many Requests` when rate-limited

### `GET /tasks/<id>`

Fetch the current task record.

#### Headers

- `Authorization: Bearer <client-api-key>`

#### Success response

- `200 OK`
- JSON task record

#### Error responses

- `401 Unauthorized` for missing or invalid client auth
- `403 Forbidden` when the authenticated tenant does not own the task
- `404 Not Found` when the task does not exist

### `GET /tasks/<id>/audit`

Fetch audit events for a task.

#### Headers

- `Authorization: Bearer <client-api-key>`

#### Success response

- `200 OK`
- JSON object:

```json
{
  "events": []
}
```

#### Error responses

- `401 Unauthorized` for missing or invalid client auth
- `403 Forbidden` when the authenticated tenant does not own the task
- `404 Not Found` when the task does not exist

### `GET /health`

Dependency-aware health endpoint.

#### Success responses

- `200 OK` when dependencies are ready
- `503 Service Unavailable` when dependencies are not ready

#### Response body

```json
{
  "ok": true,
  "service": "paperclip",
  "dependencies": {
    "db_path_exists": true,
    "internal_auth_configured": true,
    "client_api_keys_file_exists": true
  }
}
```

### `GET /metrics`

Prometheus-style metrics endpoint.

#### Success response

- `200 OK`
- `text/plain; version=0.0.4`

## Public task record shape

The public task record returned by `POST /tasks` and `GET /tasks/<id>` currently includes:

```json
{
  "id": "task_123",
  "schema_version": "v1",
  "type": "repo_summary",
  "title": "Summarize repository changes",
  "description": "Analyze recent repository changes and return a concise summary.",
  "priority": "medium",
  "risk_level": "low",
  "requester": {
    "id": "user_001",
    "display_name": "xtcagent"
  },
  "tenant": {
    "tenant_id": "tenant-a",
    "org_id": "org-a",
    "client_id": "client-a"
  },
  "state": "succeeded",
  "approval_status": "approved",
  "created_at": "2026-04-03T18:01:05Z",
  "updated_at": "2026-04-03T18:01:05Z",
  "result": {}
}
```

## Guarantees

This public contract guarantees:

- the listed public endpoints are supported as documented
- the request payload for task submission is validated against `task_request_v1.json`
- Hermes result payloads are validated against `task_result_v1.json`
- tenant isolation is enforced on public task and audit reads
- internal callback endpoints are excluded from the client-facing contract

## Out of scope for this slice

This slice does not yet add:

- OpenAPI generation
- richer customer-facing tutorials
- status list/history collection endpoints beyond per-task fetch and audit
- approval dashboard UX
- SDKs or client helper libraries
