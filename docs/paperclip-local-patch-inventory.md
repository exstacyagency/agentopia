# Paperclip Local Patch Inventory

This document tracks the local-only Paperclip changes required for the Agentopia ↔ Paperclip ↔ Hermes integration.

## Purpose

Keep the Paperclip patch surface small, explicit, and disposable.

## Categories

### Boot/build fixes
Local changes required only to get the upstream Paperclip checkout to install, build, or serve locally.

Examples in current local setup:
- local workspace Hermes adapter package under `packages/adapters/hermes-local/`
- namespace/import updates needed to match current `@paperclipai/*` package names
- root `tsconfig.json` cleanup for stale adapter references
- current Hermes adapter type-shape fixes for server/UI build compatibility

### Runtime integration shims
Local changes required for live local bridge execution but not intended to become Agentopia’s long-term system of record.

Examples in current local setup:
- wakeup context propagation patch so the Hermes adapter receives issue/task context
- local Hermes adapter routing/mirroring used for live validation

### User-facing Paperclip patches
Local browser-facing Paperclip changes used to make the local UI usable.

Examples in current local setup:
- visible Paperclip branding fixes in local frontend/browser surfaces

## Boundary rule

Keep these local-only Paperclip patches minimal.

Do not move Agentopia-owned logic into Paperclip. In particular, the following stay Agentopia-owned:
- policy gating
- write safety and overwrite controls
- semantic labels and action reasoning
- callback durability
- approval reconciliation
- operator summaries and inspectors

Paperclip should primarily provide:
- issue / approval / agent / heartbeat-run orchestration
- local UI visibility
- comments / visible history surfacing

## Working rule

When a new Paperclip patch is added locally, document:
- file(s) touched
- category
- reason
- whether it is required for boot, runtime, or UI surfacing
