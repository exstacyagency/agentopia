# Agentopia v1 System Contract

## Purpose

This contract defines the boundary between:

- **Paperclip**: orchestration, governance, approvals, budgets, audit
- **Hermes**: execution, tools, memory, task completion, structured output

This is the first thing to lock down before building the services.

---

# 1. Design Principles

1. **Paperclip owns control**
   - intake
   - policy
   - approvals
   - budgets
   - lifecycle state

2. **Hermes owns execution**
   - runtime behavior
   - tools
   - memory
   - work output
   - execution metadata

3. **The boundary is explicit**
   - Paperclip sends approved tasks
   - Hermes returns structured results
   - neither side guesses the other’s internal state

4. **Everything is versioned**
   - every envelope includes `schema_version`

---

# 2. Core Entities

## Task
A unit of work submitted into the system.

## Run
A single Hermes execution attempt for a task.

## Approval
A decision required before certain work can proceed.

## Audit Event
An immutable record of an important state transition or action.

## Artifact
A file or structured output produced during execution.

---

# 3. Task Lifecycle

Paperclip owns the lifecycle state machine.

## Allowed task states
- `received`
- `validating`
- `pending_approval`
- `approved`
- `queued`
- `running`
- `succeeded`
- `failed`
- `rejected`
- `cancelled`

## Allowed transitions
- `received -> validating`
- `validating -> pending_approval`
- `validating -> approved`
- `pending_approval -> approved`
- `pending_approval -> rejected`
- `approved -> queued`
- `queued -> running`
- `running -> succeeded`
- `running -> failed`
- `received|validating|pending_approval|approved|queued|running -> cancelled`

Hermes does **not** own task state semantics. Hermes reports execution status; Paperclip applies state transitions.

---

# 4. Request Envelope: Paperclip → Hermes

This is the payload Hermes receives after approval/policy checks.

## Required top-level fields

```json
{
  "schema_version": "v1",
  "task": {},
  "execution_policy": {},
  "routing": {},
  "trace": {}
}
```

---

## 4.1 `task`

```json
{
  "id": "task_123",
  "type": "repo_summary",
  "title": "Summarize repository changes",
  "description": "Analyze recent repository changes and return a concise summary.",
  "priority": "medium",
  "risk_level": "low",
  "requester": {
    "id": "user_001",
    "display_name": "xtcagent"
  },
  "context": {
    "repo": "exstacyagency/agentopia",
    "branch": "main"
  },
  "created_at": "2026-04-03T18:00:00Z"
}
```

## Required fields
- `id`
- `type`
- `title`
- `description`
- `priority`
- `risk_level`
- `requester`
- `created_at`

## Allowed `priority`
- `low`
- `medium`
- `high`
- `urgent`

## Allowed `risk_level`
- `low`
- `medium`
- `high`

---

## 4.2 `execution_policy`

```json
{
  "budget": {
    "max_cost_usd": 5.0,
    "max_runtime_minutes": 15,
    "max_output_bytes": 65536
  },
  "approval": {
    "required": false,
    "status": "approved",
    "approved_by": "paperclip",
    "approved_at": "2026-04-03T18:01:00Z"
  },
  "permissions": {
    "allow_network": false,
    "allow_memory": true,
    "allow_tools": true,
    "allowed_tool_classes": ["repo_read", "local_exec"],
    "write_scope": "artifacts_only"
  },
  "output_requirements": {
    "format": "markdown",
    "length": "short",
    "include_artifacts": true
  }
}
```

## Required fields
- `budget`
- `approval`
- `permissions`
- `output_requirements`

### `budget` required
- `max_cost_usd`
- `max_runtime_minutes`

### `budget` optional
- `max_output_bytes`

### `approval` required
- `required`
- `status`

### Allowed `approval.status`
- `not_required`
- `pending`
- `approved`
- `rejected`

### `permissions` required
- `allow_network`
- `allow_memory`
- `allow_tools`
- `allowed_tool_classes`
- `write_scope`

### Allowed `write_scope`
- `none`
- `artifacts_only`
- `workspace_scoped`

### `output_requirements` required
- `format`
- `length`
- `include_artifacts`

### Allowed `format`
- `markdown`
- `json`
- `text`

### Allowed `length`
- `short`
- `medium`
- `long`

---

## 4.3 `routing`

```json
{
  "source": "paperclip",
  "destination": "hermes",
  "callback": {
    "result_url": "http://paperclip:3100/internal/tasks/task_123/result",
    "auth_mode": "shared_token"
  }
}
```

## Required fields
- `source`
- `destination`
- `callback`

### `callback` required
- `result_url`
- `auth_mode`

---

## 4.4 `trace`

```json
{
  "trace_id": "trace_abc123",
  "submitted_at": "2026-04-03T18:01:05Z"
}
```

## Required fields
- `trace_id`
- `submitted_at`

---

# 5. Result Envelope: Hermes → Paperclip

This is the payload Hermes returns after execution.

## Required top-level fields

```json
{
  "schema_version": "v1",
  "task_id": "task_123",
  "run": {},
  "result": {},
  "artifacts": [],
  "usage": {},
  "trace": {}
}
```

---

## 5.1 `run`

```json
{
  "run_id": "run_001",
  "status": "succeeded",
  "started_at": "2026-04-03T18:01:10Z",
  "finished_at": "2026-04-03T18:01:21Z",
  "runtime_seconds": 11
}
```

## Required fields
- `run_id`
- `status`
- `started_at`
- `finished_at`
- `runtime_seconds`

### Allowed `run.status`
- `running`
- `succeeded`
- `failed`
- `cancelled`

For final result submission, `status` should normally be:
- `succeeded`
- `failed`
- `cancelled`

---

## 5.2 `result`

```json
{
  "summary": "Repository changes summarized successfully.",
  "output_format": "markdown",
  "output": "## Summary\n- Added contract runner\n- Added task output models\n- Added runtime validation",
  "notes": [
    "Validated request payload",
    "Read repository docs",
    "Generated short summary"
  ],
  "error": null
}
```

## Required fields
- `summary`
- `output_format`
- `output`
- `notes`
- `error`

### `error`
- `null` on success
- object on failure

Failure example:

```json
{
  "code": "EXECUTION_TIMEOUT",
  "message": "Task exceeded runtime budget.",
  "retryable": false
}
```

---

## 5.3 `artifacts`

```json
[
  {
    "type": "report",
    "path": "artifacts/output.md",
    "content_type": "text/markdown"
  },
  {
    "type": "structured_output",
    "path": "artifacts/output.json",
    "content_type": "application/json"
  }
]
```

Each artifact requires:
- `type`
- `path`
- `content_type`

---

## 5.4 `usage`

```json
{
  "estimated_cost_usd": 0.18,
  "actual_cost_usd": 0.21,
  "model_provider": "openrouter",
  "model_name": "gpt-5.4",
  "tool_calls": 4
}
```

## Required fields
- `actual_cost_usd`
- `model_provider`
- `model_name`
- `tool_calls`

Optional:
- `estimated_cost_usd`

---

## 5.5 `trace`

```json
{
  "trace_id": "trace_abc123",
  "reported_at": "2026-04-03T18:01:21Z"
}
```

## Required fields
- `trace_id`
- `reported_at`

---

# 6. Error Contract

Hermes should always return a structured error object on failure.

## Error shape

```json
{
  "code": "EXECUTION_FAILED",
  "message": "The task could not be completed.",
  "retryable": false
}
```

## Initial allowed error codes
- `VALIDATION_FAILED`
- `PERMISSION_DENIED`
- `APPROVAL_REQUIRED`
- `BUDGET_EXCEEDED`
- `EXECUTION_FAILED`
- `EXECUTION_TIMEOUT`
- `TOOL_FAILURE`
- `NETWORK_DISABLED`
- `INTERNAL_ERROR`

Paperclip should store these as part of audit and task history.

---

# 7. Minimal Task Types for v1

Don’t support everything at once.

## Supported initial task types
- `repo_summary`
- `file_analysis`
- `text_generation`

That’s enough to prove the architecture.

## Do not support in v1
- complex multi-agent workflows
- external side-effect-heavy tasks
- autonomous long-running plans
- broad plugin ecosystems
- production-grade tenancy

Keep v1 narrow.

---

# 8. Minimal API Surface

## Paperclip external/internal API

### Intake
- `POST /tasks`
  - create task
  - validate request
  - store task

### Status
- `GET /tasks/:id`
  - return task metadata and current state

### Approval
- `POST /tasks/:id/approve`
- `POST /tasks/:id/reject`

### Internal dispatch/result
- `POST /internal/tasks/:id/result`
  - Hermes submits final result

### Audit
- `GET /tasks/:id/audit`

---

## Hermes internal API or worker surface

Choose one of these patterns:

### Option A — direct HTTP execution
- `POST /internal/execute`

### Option B — worker poll
- Hermes polls Paperclip for approved queued tasks

For v1, I’d use **direct HTTP** because it’s simpler.

---

# 9. Audit Requirements

Paperclip should write immutable audit events for:
- task received
- validation passed/failed
- approval requested
- approved/rejected
- dispatched to Hermes
- Hermes started
- Hermes completed
- Hermes failed
- task cancelled

Each event should include:
- event id
- task id
- event type
- actor
- timestamp
- payload json

---

# 10. Persistence Requirements

Minimum persistent objects:
- tasks
- approvals
- runs
- audit_events
- artifacts

Use **SQLite** first unless there’s a hard reason not to.

That keeps local development simple and fast.

---

# 11. Enforcement Rules

## Paperclip must enforce
- no task reaches Hermes unless policy allows it
- budget/runtime ceilings are attached before dispatch
- approval state is explicit
- all tasks are auditable

## Hermes must enforce
- do not exceed execution permissions
- do not assume missing permissions
- return structured result format
- always report run status
- fail closed on invalid contract input

---

# 12. Definition of Done for Contract v1

This contract is “done” when:
- request schema exists in code
- result schema exists in code
- state machine exists in code
- fixtures exist for valid and invalid examples
- both services validate against the same definitions
- contract tests fail on breaking changes

---

# 13. Immediate Build Tasks From This Contract

## Step 1
Create:
- `docs/system-contract.md`
- `schemas/task_request_v1.json`
- `schemas/task_result_v1.json`

## Step 2
Create shared validation module:
- `shared/contracts.py` or equivalent

## Step 3
Add fixtures:
- `fixtures/task_request_valid.json`
- `fixtures/task_request_invalid.json`
- `fixtures/task_result_valid.json`
- `fixtures/task_result_invalid.json`

## Step 4
Build Paperclip against this contract

## Step 5
Build Hermes against this contract

---

# 14. Blunt Recommendation

The very next move should be:

1. write this contract into the repo
2. convert it into real schemas
3. write tests against it
4. only then start implementing Paperclip and Hermes
