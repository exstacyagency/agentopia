# MemPalace Runtime Integration

This document describes how MemPalace now participates in real Hermes execution context.

## Current behavior

At execution time, Hermes now builds a MemPalace-backed wakeup context using the task title and description.
When tenant context is present on the task, runtime memory enrichment is now scoped to that tenant boundary before memory metadata is attached to the execution result.

The resulting memory metadata is attached to execution context and result metadata as:
- `memory.memory_mode`
- `memory.memory_source`
- `memory.memory_hits`

## Interpretation

### `off`
No MemPalace-backed retrieval should be considered active.

### `augment`
MemPalace contributes memory hits alongside the native issue/execution context.

### `prefer_mempalace`
MemPalace is treated as the preferred long-term retrieval source, while native platform records remain the system of record.

## Tenant boundary

Runtime memory enrichment should only occur when:

- `execution_policy.permissions.allow_memory` is true
- task tenant context is present

The runtime memory metadata should carry the same tenant identity as the task that requested execution.

## Important boundary

This integration changes retrieval/context behavior.
It does **not** replace:
- Paperclip issue history
- approvals
- runs
- Hermes execution persistence
- Agentopia audit/state records
