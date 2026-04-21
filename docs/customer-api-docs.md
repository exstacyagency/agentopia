# Customer API Docs

These docs describe how a customer should use the current Agentopia Paperclip API.

## Base concept

Paperclip is the customer-facing control-plane API.
Customers submit tasks, fetch task state, inspect audit history, and cancel work through Paperclip.

## Authentication

Use a bearer token in the `Authorization` header.

Example:

```http
Authorization: Bearer tenant-a-key
```

Supported key sources are configured by the operator, but customers only need the issued API key.

## Submit a task

### Request

```bash
curl -X POST http://localhost:3100/tasks \
  -H 'Authorization: Bearer tenant-a-key' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: task-123-once' \
  --data @fixtures/task_request_valid.json
```

### Success response

- `201 Created`

Example response shape:

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
  "state": "queued",
  "approval_status": "approved",
  "created_at": "2026-04-21T14:00:00Z",
  "updated_at": "2026-04-21T14:00:00Z"
}
```

## Fetch task status

```bash
curl http://localhost:3100/tasks/task_123 \
  -H 'Authorization: Bearer tenant-a-key'
```

### Success response

- `200 OK`

This returns the current task record, including state, any stored result, and approval/review visibility when relevant.

The task response now includes an `approval_review` summary with fields like:

- `approval_status`
- `current_state`
- `review_required`
- `latest_review_event`

## Fetch task audit history

```bash
curl http://localhost:3100/tasks/task_123/audit \
  -H 'Authorization: Bearer tenant-a-key'
```

### Success response

- `200 OK`

Example response:

```json
{
  "events": [
    {
      "event_type": "task_received",
      "actor": "paperclip",
      "payload": {
        "state": "received"
      }
    }
  ]
}
```

## Cancel a task

```bash
curl -X POST http://localhost:3100/tasks/task_123/cancel \
  -H 'Authorization: Bearer tenant-a-key' \
  -H 'Content-Type: application/json' \
  --data '{"reason":"user requested"}'
```

### Success response

- `200 OK`

Cancellation is tenant-scoped and only applies to tasks owned by the authenticated tenant.

## Key management path

Customer keys are currently operator-issued through the file-based registry flow described in:

- `docs/key-management-path.md`

## Common errors

### `401 Unauthorized`

Returned when:

- the API key is missing
- the API key is invalid
- the API key is revoked

Example shape:

```json
{
  "error": {
    "code": "unauthorized",
    "message": "Unauthorized",
    "status": 401
  }
}
```

### `403 Forbidden`

Returned when:

- the authenticated tenant tries to read or cancel another tenant's task

### `404 Not Found`

Returned when:

- the task does not exist

Example shape:

```json
{
  "error": {
    "code": "task_not_found",
    "message": "Task not found",
    "status": 404
  }
}
```

### `413 Payload Too Large`

Returned when:

- the request body exceeds the configured request-size limit

### `429 Too Many Requests`

Returned when:

- rate limiting is triggered

## Practical workflow

Typical customer flow:

1. submit a task with `POST /tasks`
2. poll task state with `GET /tasks/<id>`
3. inspect audit history with `GET /tasks/<id>/audit` when needed
4. cancel with `POST /tasks/<id>/cancel` if work should stop

## Notes

These docs are customer-focused usage guidance layered on top of the stable public contract in:

- `docs/public-api-contract.md`
