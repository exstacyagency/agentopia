# Tenant-Scoped Memory Boundaries

This document defines the current memory surface in Agentopia and the required tenant boundary contract for making it safe for multi-tenant use.

## Why this document exists

Agentopia already exposes real memory behavior through Hermes and MemPalace integration.
Before enforcing tenant-scoped memory isolation, the platform must identify every memory touchpoint and define what tenant scope is required at each boundary.

This document started as the inventory and contract step.
The current enforcement baseline now also requires tenant scope on the Hermes memory service API and partitions tenant config/status persistence paths.
Full memory isolation is still not complete until all runtime memory retrieval paths and internal endpoint contracts are consistently tenant-scoped.

## Current memory surface inventory

### 1. Hermes internal memory endpoints

Current endpoints in `hermes/app.py`:

- `GET /internal/memory/config`
- `POST /internal/memory/config`
- `GET /internal/memory/status`
- `POST /internal/memory/status`
- `POST /internal/memory/search`
- `POST /internal/memory/wakeup`
- `POST /internal/memory/mine`
- `POST /internal/memory/reindex`

Current state:

- these are internal-only endpoints
- they do not currently require an explicit tenant identifier in the request body or path
- they operate against a singleton `MemPalaceService()` instance
- they are therefore currently platform-global, not tenant-scoped

### 2. Hermes memory service layer

Current service in `hermes/memory/service.py`:

- `get_config()`
- `set_config()`
- `status()`
- `search()`
- `wakeup()`
- `run_operation("mine")`
- `run_operation("reindex")`

Current state:

- the service reads one config source
- it writes one status file under `var/hermes/memory/`
- it does not currently accept tenant scope in method signatures
- configuration and status are effectively shared across all tenants

### 3. MemPalace config and storage surface

Current files in `hermes/memory/config.py` and `hermes/memory/service.py`:

- `var/hermes/memory/mempalace-config.json`
- `var/hermes/memory/mempalace-status.json`

Current state:

- these are singleton filesystem paths
- there is no tenant partitioning in config or status persistence
- company-specific or tenant-specific memory settings are not yet represented

### 4. Runtime execution memory enrichment

Current docs already describe runtime memory enrichment:

- `docs/mempalace-runtime-integration.md`

Current state:

- Hermes execution can attach memory metadata such as:
  - `memory.memory_mode`
  - `memory.memory_source`
  - `memory.memory_hits`
- this means memory retrieval already affects execution context and output metadata
- there is currently no explicit tenant-boundary contract guaranteeing those hits come only from the requesting tenant scope

### 5. Permission-level memory flag

Current execution policy already includes:

- `execution_policy.permissions.allow_memory`

Current state:

- this is an execution permission gate
- it is not itself a tenant isolation boundary
- allowing memory today does not define which tenant memory is allowed

## Current risk summary

The main risk is not that memory exists, but that memory behavior is currently:

- singleton-oriented
- config-global
- status-global
- retrieval-global by contract
- not explicitly scoped to tenant, org, or client identity

In a paying multi-tenant environment, this creates unacceptable ambiguity around:

- search results
- wakeup context
- mining and reindex operations
- memory config changes
- runtime memory metadata

## Required tenant boundary contract

Before tenant-scoped memory boundaries can be marked complete, the platform must enforce all of the following.

### A. Explicit tenant scope on memory operations

Every memory operation must resolve an explicit scope object, at minimum:

```json
{
  "tenant_id": "tenant-a",
  "org_id": "org-a",
  "client_id": "client-a"
}
```

At minimum, the authoritative isolation key should be:

- `tenant_id`

### B. Tenant-aware method signatures

Memory service operations should move from singleton-style calls such as:

- `search(query)`
- `wakeup(issue_title, issue_description)`
- `set_config(payload)`

To tenant-aware calls such as:

- `search(scope, query)`
- `wakeup(scope, issue_title, issue_description)`
- `set_config(scope, payload)`
- `status(scope)`
- `run_operation(scope, operation)`

### C. Tenant-partitioned persistence

The following must become tenant-partitioned before completion:

- memory config
- memory status
- any local cache or persisted memory artifacts
- any configured MemPalace path or source mapping

### D. Tenant-aware HTTP contract

Internal memory endpoints must not rely on implicit singleton state.
They should require either:

- tenant scope in authenticated request context, or
- an explicit tenant identifier in the request contract, validated against caller permissions

### E. Tenant-safe runtime enrichment

When Hermes attaches memory metadata to execution context or result metadata:

- the retrieval source must be tenant-scoped
- the metadata must be attributable to the same tenant scope as the task
- cross-tenant memory hits must be impossible by contract

## Minimum implementation sequence

Recommended implementation order:

1. add tenant scope to the memory service contract
2. partition config and status storage by tenant
3. require tenant scope in internal memory endpoints
4. propagate tenant context from Paperclip task ownership into Hermes memory calls
5. add tests proving cross-tenant memory config or retrieval cannot leak

## Current enforcement baseline

The current code now enforces these tenant-boundary basics:

- memory service methods require tenant scope
- tenant config paths are partitioned under tenant-specific directories
- tenant status paths are partitioned under tenant-specific directories

## What is not complete yet

This is closer, but tenant-scoped memory boundaries are only truly complete when all live runtime memory retrieval and endpoint usage is consistently tenant-scoped end to end.

Remaining gap areas include:

- stricter request-contract enforcement on every internal memory endpoint path
- verified tenant propagation from Paperclip-owned task context into Hermes runtime memory retrieval
- proof that runtime execution memory hits cannot cross tenant boundaries

## Verification for this slice

Review alongside:

- `hermes/app.py`
- `hermes/memory/service.py`
- `docs/mempalace-runtime-integration.md`
- `docs/memory-roadmap.md`
