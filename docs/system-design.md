# Agentopia Architecture and Build Plan

## Purpose

Agentopia is a two-layer agent system:

- **Paperclip** handles orchestration, governance, approvals, budgets, and audit.
- **Hermes** handles execution, tools, memory, and result generation.

The goal is to move the repo from a scaffold/demo state into a real working system with a clear boundary between control-plane and worker-plane responsibilities.

---

## High-Level Architecture

### 1. Paperclip — Control Plane

Paperclip is the policy and orchestration layer.

**Responsibilities**
- Accept inbound task requests
- Validate request schema
- Evaluate policy and risk
- Check budget limits
- Enforce approval requirements
- Route approved tasks to Hermes
- Track task lifecycle state
- Record audit events
- Store final outputs and metadata

**Core idea**
Paperclip decides **whether** work may happen, under what constraints, and how it should be tracked.

---

### 2. Hermes — Execution Plane

Hermes is the runtime worker.

**Responsibilities**
- Receive approved tasks from Paperclip
- Load task constraints and execution permissions
- Use tools, memory, and skills to perform work
- Produce structured outputs
- Return status, logs, and artifacts
- Report execution metadata back to Paperclip

**Core idea**
Hermes decides **how** the approved work gets done, but does not own governance.

---

### 3. Shared System Boundary

The Paperclip↔Hermes boundary should be explicit and versioned.

**Shared concerns**
- Request schema
- Result schema
- Task state transitions
- Error and retry model
- Artifact references
- Audit metadata
- Authentication between services

This boundary is the most important part of the system. It should be treated like an API contract, not an informal convention.

---

## Proposed Runtime Flow

### Step 1 — Task Intake
A task enters Paperclip through an API endpoint or other ingress path.

Paperclip stores:
- task id
- requester identity
- task body
- priority
- constraints
- requested budget
- approval state
- timestamps
- schema version

### Step 2 — Policy Evaluation
Paperclip evaluates:
- whether the task is in scope
- whether it is allowed
- whether it exceeds budget
- whether it requires approval
- what execution permissions Hermes should receive

### Step 3 — Approval Gate
If approval is required:
- task moves to `pending_approval`
- approval metadata is stored
- human or policy action resolves it

If no approval is required:
- task moves to `approved`

### Step 4 — Dispatch to Hermes
Paperclip sends Hermes:
- the approved task payload
- execution constraints
- tool/network/memory permissions
- budget/runtime ceilings
- callback/result routing metadata

### Step 5 — Execution
Hermes:
- accepts the task
- executes with the allowed tools/skills
- captures logs/notes/artifacts
- produces structured output
- returns final result or failure state

### Step 6 — Audit and Completion
Paperclip:
- records result metadata
- stores audit trail
- marks task complete/failed/rejected
- exposes task history and outputs

---

## Ownership Boundaries

### Paperclip owns
- task intake
- task state machine
- policy engine
- budget checks
- approval logic
- audit events
- routing decisions
- persistence of control-plane state

### Hermes owns
- execution runtime
- skill/tool loading
- memory access
- execution logs
- artifact generation
- structured result generation
- retries/internal runtime handling

### Agentopia repo owns
- local development topology
- service definitions
- shared schemas
- config surfaces
- scripts and operational tooling
- tests and documentation

---

## Recommended Initial Deployment Model

For the first real implementation, keep it simple.

### Suggested stack
- **Paperclip service**: small HTTP API
- **Hermes service**: small worker/API process
- **Database**: SQLite for local dev, Postgres later
- **Compose**: local orchestration for all services
- **Artifacts**: local filesystem first, object storage later

### Why this works
- Minimizes moving parts
- Allows real end-to-end testing quickly
- Avoids premature infra complexity
- Gives a clean upgrade path to production later

---

## Minimal Data Model

A real implementation needs persistence.

### Core tables/collections

#### `tasks`
- id
- schema_version
- title
- description
- priority
- requester_id
- requester_display_name
- state
- risk_level
- created_at
- updated_at

#### `task_constraints`
- task_id
- output_format
- output_length
- allow_network
- allow_tools
- allow_memory
- max_runtime_minutes
- max_cost_usd

#### `approvals`
- id
- task_id
- required
- status
- decided_by
- decided_at
- reason

#### `budgets`
- task_id
- max_cost_usd
- estimated_cost_usd
- actual_cost_usd
- budget_status

#### `runs`
- id
- task_id
- hermes_run_id
- status
- started_at
- finished_at
- runtime_seconds
- model_provider
- model_name

#### `audit_events`
- id
- task_id
- event_type
- actor
- payload_json
- created_at

#### `artifacts`
- id
- task_id
- artifact_type
- path_or_uri
- content_type
- created_at

---

## Versioned API Contract

The current repo has demo contract validation, but this needs to become a formal interface.

### Task request envelope
Should include:
- schema version
- task id
- requester
- title/description
- priority/risk
- budget policy
- approval policy
- routing info
- callback info
- trace/correlation id

### Result envelope
Should include:
- schema version
- task id
- run id
- status
- summary
- structured output
- artifacts
- audit metadata
- runtime metadata
- error details if failed

### Why versioning matters
Without a versioned contract:
- Paperclip and Hermes will drift
- changes will silently break workflows
- tests will remain shallow
- integrations will become brittle

---

## Task State Machine

Define this explicitly in code.

### Suggested states
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

### Suggested transitions
- `received -> validating`
- `validating -> pending_approval`
- `validating -> approved`
- `pending_approval -> approved`
- `pending_approval -> rejected`
- `approved -> queued`
- `queued -> running`
- `running -> succeeded`
- `running -> failed`
- `approved/queued/running -> cancelled`

Paperclip should own these transitions.

---

## Security and Governance Model

### Paperclip enforcement
Paperclip should decide:
- whether network is allowed
- whether tool execution is allowed
- whether memory access is allowed
- whether approval is required
- what budget ceiling applies

### Hermes enforcement
Hermes should receive explicit execution permissions and must not exceed them.

### Minimum auth model
- service-to-service auth token
- per-request trace id
- signed/internal-only task dispatch
- no secrets committed to repo

### Later improvements
- secret store integration
- scoped tokens
- per-tenant/org policy
- immutable audit event store

---

## Observability Requirements

A real system needs visibility.

### Minimum observability
- Paperclip logs task lifecycle events
- Hermes logs run lifecycle events
- correlation id across both services
- task/run status endpoints
- structured JSON logs

### Nice next step
- metrics:
  - tasks received
  - tasks approved/rejected
  - queue latency
  - run duration
  - failure rate
- traces later if needed

---

## What the Repo Already Has

Useful foundation already present:
- architecture docs
- implementation-phase docs
- config stubs
- demo request/result validation
- workflow wrapper scripts
- output model demo
- local compose skeleton

This is useful scaffolding, but it is not yet the implementation.

---

## What Needs to Be Built

## Phase 1 — Freeze the Contract
Build first:
- formal request schema
- formal result schema
- schema version field
- shared validation package/module
- fixtures for valid/invalid cases
- contract tests for both sides

**Done when**
- both services consume the same schema definitions
- breaking changes are caught in tests
- request/result format is no longer “demo only”

---

## Phase 2 — Build Minimal Paperclip
Build:
- HTTP API for task intake
- persistent task storage
- policy evaluation module
- approval state handling
- budget validation
- task lifecycle state machine
- audit event writer

**Suggested endpoints**
- `POST /tasks`
- `GET /tasks/:id`
- `POST /tasks/:id/approve`
- `POST /tasks/:id/reject`
- `GET /tasks/:id/audit`

**Done when**
- Paperclip can accept a task and move it through real states

---

## Phase 3 — Build Minimal Hermes
Build:
- task consumer or worker API
- execution permission loader
- simple executor
- structured result emitter
- result callback/submission to Paperclip
- run metadata tracking

**First supported task type**
Keep it tiny:
- repo summary
- markdown generation
- file analysis
Something deterministic and easy to test.

**Done when**
- Hermes can execute one real approved task end-to-end

---

## Phase 4 — Real Dispatch Path
Build:
- Paperclip→Hermes dispatch mechanism
- Hermes→Paperclip result reporting
- retry/error handling
- idempotency behavior
- timeout behavior

**Dispatch options**
- simplest: direct HTTP call
- later: queue/event bus if needed

For now, use direct HTTP. Don’t over-engineer it.

**Done when**
- a task submitted to Paperclip actually gets executed by Hermes

---

## Phase 5 — Persistence and Audit
Build:
- task persistence
- run persistence
- approval persistence
- artifact metadata persistence
- append-only audit events

**Done when**
- you can inspect task history after the fact
- you can answer who approved what, what ran, and what was produced

---

## Phase 6 — Compose and Local Dev Become Real
Build:
- real service definitions in `docker-compose.yml`
- meaningful health endpoints
- startup sequencing based on actual service readiness
- sample seed data or demo task flow

**Health should prove**
- Paperclip can start, read config, and talk to DB
- Hermes can start and reach Paperclip
- a demo task can be submitted and completed

**Done when**
- local boot is an actual working system, not just script/demo validation

---

## Phase 7 — Operational Hardening
Build:
- upgrade/update docs
- failure-mode docs
- retry policy docs
- troubleshooting docs
- log/metric conventions
- config validation against real runtime needs

**Done when**
- someone else can boot, debug, and operate the stack without guessing

---

## Current Gaps in the Existing Repo

These are the major missing pieces right now:
- no real Paperclip service
- no real Hermes service
- no persistent datastore
- no actual routing between services
- no real approvals/budgets engine
- no real health endpoints
- no real end-to-end execution path
- no formal shared API spec
- no real artifact lifecycle
- no deep integration tests

Also worth noting:
- the current task runner writes local JSON artifacts and simulates success
- the workflow still depends on pre-existing local artifacts in places
- the compose file is a shell around env-configured images, not a verified system

---

## Recommended Implementation Order

If you want the shortest path to “real”:

1. Define versioned request/result schemas
2. Add SQLite-backed Paperclip service
3. Add minimal Hermes worker
4. Connect them with direct HTTP dispatch
5. Persist task/runs/audit/artifact metadata
6. Add one real end-to-end task type
7. Make compose boot and prove the whole loop
8. Add tests and operational polish

That sequence gets you to a working system fastest.

---

## Definition of Done for v1

Agentopia v1 exists when:
- a task can be submitted to Paperclip
- Paperclip validates policy/budget/approval
- approved work is dispatched to Hermes
- Hermes executes one real task type
- results return to Paperclip
- audit trail is persisted
- task status is queryable
- local compose boots the system reliably
- docs match reality

---

## Suggested Immediate Repo Work Items

### Must-do next
- add `docs/system-design.md` or similar with the architecture above
- define shared schemas in code
- choose runtime implementation language/framework for the services
- create Paperclip service skeleton
- create Hermes service skeleton
- choose SQLite/Postgres abstraction
- add state-machine tests

### Immediately after
- implement task intake
- implement approval flow
- implement dispatch
- implement one executor path
- implement result callback
- implement persistence and audit

---

## Final Take

The repo is in a good “planning scaffold” state.
The next step is not more wrappers or more placeholder docs — it is to create the first real control-plane service, the first real worker, and a narrow but fully functional end-to-end path between them.
