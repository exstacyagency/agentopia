# Memory Provenance

This document defines the current memory provenance baseline for Agentopia execution and audit surfaces.

## Goals

- make memory contribution visible in execution results
- surface compact memory provenance into Paperclip audit history
- preserve tenant identity on memory contribution summaries

## Current behavior

Hermes execution results may include memory metadata under:

- `result.metadata.memory`

Paperclip now extracts a compact provenance summary from that metadata and records it into audit surfaces.

Current provenance fields:

- `tenant_id`
- `org_id`
- `client_id`
- `memory_mode`
- `memory_source`
- `memory_hit_count`

## Audit behavior

When a Hermes result includes memory metadata, Paperclip records:

- memory provenance in the state-transition details for result processing
- a dedicated audit event:
  - `memory_provenance_recorded`

## Notes

This slice focuses on compact provenance summaries in execution and audit surfaces.
It does not yet add:

- richer operator UI rendering
- per-hit provenance display in dashboards
- deletion workflows for memory-backed context

## Verification

Run:

```bash
./.venv/bin/python scripts/test_memory_provenance.py
```
