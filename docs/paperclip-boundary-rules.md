# Paperclip Boundary Rules

This document defines how Agentopia and Paperclip should evolve without coupling core logic to local Paperclip patches.

## Agentopia owns
- task mapping and bridge semantics
- policy gating
- write-capable route safety
- semantic action labels and production reasons
- callback persistence and retry
- approval linkage and reconciliation
- operator summaries and review tooling

## Paperclip owns
- issue objects
- approval objects
- agents
- heartbeat runs / wakeups
- Paperclip-visible issue history and UI surfacing

## Preferred integration pattern
1. Keep execution logic in Agentopia.
2. Keep Paperclip-specific API details inside thin adapter/client/service layers.
3. Surface results back into Paperclip via comments or native objects when useful.
4. Treat local Paperclip patches as temporary compatibility shims, not as the permanent home of core features.

## Why this matters

This keeps Paperclip replaceable and lets Agentopia absorb upstream Paperclip changes at the boundary instead of rewriting core logic.
