# Memory Deletion Workflows

This document defines the current tenant-scoped memory deletion workflow for Agentopia.

## Goals

- support explicit deletion of tenant-partitioned memory state
- ensure one tenant deletion does not remove another tenant's memory state
- make deletion behavior durable and operator-usable

## Current behavior

Agentopia now supports tenant-scoped memory deletion through the Hermes memory service.

Current deletion target:

- tenant-partitioned memory directory under `var/hermes/memory/<tenant_id>/`

This currently removes tenant-scoped:

- MemPalace config
- MemPalace status
- other tenant-local memory files under that tenant directory

## Internal workflow

Hermes now supports:

- `POST /internal/memory/delete`

Required request scope:

```json
{
  "tenant_id": "tenant-a"
}
```

## Safety properties

- deletion is tenant-scoped
- deletion for tenant A does not remove tenant B state
- deleting an already-absent tenant memory directory returns a clean success response

## Notes

This slice covers the current tenant-partitioned memory state managed by Hermes.
It does not yet imply:

- deletion of external MemPalace backend data outside the managed tenant directory
- UI-level deletion workflows
- retention scheduling for memory cleanup

## Verification

Run:

```bash
./.venv/bin/python scripts/test_memory_deletion_workflows.py
```
