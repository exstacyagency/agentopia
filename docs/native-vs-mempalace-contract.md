# Native Memory vs MemPalace Contract

This document defines the canonical memory contract for Agentopia.

## Purpose

Agentopia now has both:

- native platform records and execution context
- MemPalace-backed retrieval and memory enrichment

This contract makes their roles explicit so future memory work does not blur the boundary.

## The two memory layers

### 1. Native memory

Native memory means platform-owned records and state that already exist inside Agentopia and Paperclip.

Examples include:

- Paperclip task records
- approval state
- audit events
- execution results
- queue state
- operator-visible run history
- tenant ownership and task metadata

Native memory is the system of record for:

- governance
- approvals
- lifecycle state
- auditability
- durable execution history

### 2. MemPalace memory

MemPalace memory means retrieval-oriented contextual memory used to enrich execution.

Examples include:

- search hits
- wakeup context
- mined memory sources
- retrieval augmentation for Hermes execution

MemPalace is **not** the system of record for:

- approvals
- task state
- queue state
- audit events
- execution persistence
- tenant ownership

## Core contract

### Native memory is authoritative for platform state

Paperclip and Agentopia native records remain authoritative for:

- what happened
- who approved what
- what state a task is in
- what result was recorded
- what tenant owns the work

### MemPalace is a retrieval subsystem

MemPalace may:

- augment execution context
- supply relevant memory hits
- influence model context and operator understanding

MemPalace must not:

- silently replace native records
- override approvals or task state
- mutate lifecycle semantics
- become the source of truth for governance or audit

## Memory modes

### `off`

- MemPalace is not used for retrieval
- only native platform records and context are in effect

### `augment`

- native platform records remain primary
- MemPalace contributes additional retrieval context
- execution may include MemPalace hits alongside native context

### `prefer_mempalace`

- MemPalace becomes the preferred retrieval backend for long-term contextual recall
- native records still remain authoritative for governance, lifecycle, and audit
- this mode changes retrieval preference, not source-of-truth ownership

## Runtime contract

At Hermes execution time:

- native task/request context enters first
- MemPalace may add retrieval context when allowed
- memory provenance should identify when MemPalace contributed
- tenant boundaries must still apply to retrieval scope

## Operator contract

Operator-facing surfaces should treat native and MemPalace data differently.

### Native surfaces

Use native records for:

- approval history
- task lifecycle state
- queue visibility
- durable results
- audit trails

### Memory surfaces

Use MemPalace-derived context for:

- retrieval hints
- wakeup summaries
- contextual recall during execution
- optional provenance summaries

## Non-goals

This contract does not imply:

- MemPalace deletion semantics are complete
- fallback behavior is complete
- all memory UI surfaces are finished

Those remain separate checklist items.

## Implementation expectation

Any new memory-facing feature should answer these questions explicitly:

1. Is this native memory or MemPalace retrieval?
2. Is it authoritative state or contextual enrichment?
3. Can it cross tenant boundaries? (answer should be no)
4. Does it affect audit/state semantics? (if yes, native records must remain authoritative)

## Practical rule

If the question is:

- "what actually happened?" -> native records win
- "what prior context may help with this execution?" -> MemPalace may contribute
