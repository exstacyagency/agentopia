# MemPalace Runtime Integration

This document describes how MemPalace now participates in real Hermes execution context.

## Current behavior

At execution time, Hermes now builds a MemPalace-backed wakeup context using the task title and description.

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

## Important boundary

This integration changes retrieval/context behavior.
It does **not** replace:
- Paperclip issue history
- approvals
- runs
- Hermes execution persistence
- Agentopia audit/state records
