# MemPalace Memory Modes

This document defines how MemPalace integrates with the platform memory model.

## Principle

MemPalace augments or becomes the preferred retrieval backend for memory context.
It does **not** replace system-of-record data such as:
- Paperclip issues/comments/approvals/runs
- Hermes execution records
- Agentopia persistence and audit data

## Supported modes

### `off`
- MemPalace is not used for retrieval
- native platform records remain the only context source

### `augment`
- MemPalace memory hits are added to native context
- this is the recommended default mode

### `prefer_mempalace`
- MemPalace becomes the preferred long-term retrieval source
- native platform records still remain the source of truth for operational state and auditability

## Why this matters

This keeps the architecture clean:
- MemPalace overrides retrieval behavior
- it does not override system-of-record behavior
