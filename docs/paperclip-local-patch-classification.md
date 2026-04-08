# Paperclip Local Patch Classification

This document classifies the current local-only Paperclip patch surface by purpose, durability, and ownership.

## Current observed local patch files

From the local Paperclip working tree, the active patch surface currently includes:
- `packages/adapters/hermes-local/package.json`
- `packages/adapters/hermes-local/src/ui/index.ts`
- `pnpm-lock.yaml`
- `server/package.json`
- `server/src/routes/agents.ts`
- `tsconfig.json`
- `ui/package.json`
- `ui/src/components/IssueReviewPanel.tsx`
- `ui/src/pages/Dashboard.tsx`
- `ui/src/api/issueActions.ts`
- `ui/src/api/operatorQueue.ts`

## Classification

### A. Required runtime/integration patches

These are necessary for the local Paperclip ↔ Hermes stack to function at all or to propagate the correct execution context.

- `server/src/routes/agents.ts`
  - purpose: wakeup context propagation / issue identity correctness
  - status: required runtime fix
  - ownership: local Paperclip bridge surface

- `packages/adapters/hermes-local/package.json`
- `server/package.json`
- `ui/package.json`
- `pnpm-lock.yaml`
  - purpose: local adapter workspace/install/runtime wiring
  - status: required runtime fix
  - ownership: local-only dependency/runtime shim

- `tsconfig.json`
  - purpose: local build unblock / stale path cleanup
  - status: required build fix
  - ownership: local-only build hygiene

### B. Operator UI enhancement patches

These improve or enable native Paperclip operator surfaces, but are not strictly required for the underlying orchestration/execution loop.

- `ui/src/components/IssueReviewPanel.tsx`
  - purpose: native issue-level review panel and controls
  - status: operator enhancement
  - ownership: Paperclip UI surfacing only

- `ui/src/pages/Dashboard.tsx`
  - purpose: queue-level operator overview section
  - status: operator enhancement
  - ownership: Paperclip UI surfacing only

- `ui/src/api/issueActions.ts`
  - purpose: issue-level UI command bridge
  - status: operator enhancement
  - ownership: Paperclip UI surfacing only

- `ui/src/api/operatorQueue.ts`
  - purpose: queue-level dashboard bridge
  - status: operator enhancement
  - ownership: Paperclip UI surfacing only

### C. Adapter UI compatibility patches

- `packages/adapters/hermes-local/src/ui/index.ts`
  - purpose: Hermes adapter UI registration/compatibility
  - status: compatibility patch
  - ownership: local adapter compatibility layer

## Durability guidance

### Must-keep local for now
- runtime wiring patches
- issue-id propagation fixes
- local adapter compatibility patches

### Candidate to upstream later
- generic build fixes if they are broadly valid
- generic issue-context propagation fixes if they are not Agentopia-specific
- UI null-safety/runtime crash guards if they are broadly correct

### Keep Agentopia-owned, not upstreamed into Paperclip semantics
- review logic
- decision-trace semantics
- operator-state meaning
- apply/revert/review control semantics

Paperclip should only surface these, not own them.

## Validation checklist

Before trusting the local Paperclip runtime, verify:
1. local patched branch is checked out
2. `pnpm build` or relevant UI/server typecheck passes
3. wakeup path uses real issue ids, not run ids
4. issue comments and dashboard docs land on the real issue
5. review panel and queue page render without crashing

## Why this exists

The platform is now functionally real, so patch ambiguity is one of the biggest remaining operational risks. This classification keeps the local patch surface explicit and easier to reason about.
