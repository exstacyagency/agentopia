# MemPalace Fallback Behavior

This document defines the current fallback behavior when MemPalace is unavailable.

## Goals

- keep Hermes execution working when MemPalace is disabled or unavailable
- fall back to native-only memory context instead of failing execution
- make fallback behavior explicit in execution metadata

## Current behavior

When memory use is allowed but MemPalace is unavailable, Hermes now falls back to:

- `memory_source: native_only`
- empty `memory_hits`
- explicit `fallback_reason`

Current fallback reasons may include:

- `mempalace_disabled`
- `mempalace_command_not_found`
- other MemPalace search failure reasons returned by the memory service

## Runtime contract

Fallback should not:

- fail the Hermes execution by itself
- remove tenant identity from memory metadata
- pretend MemPalace contributed when it did not

Instead, the runtime result should show that:

- memory was allowed
- MemPalace was unavailable
- execution continued with native-only context

## Verification

Run:

```bash
./.venv/bin/python scripts/test_memory_fallback.py
```
