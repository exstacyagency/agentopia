# Hermes Boundary Rules

This document defines how Agentopia and Hermes should evolve without pushing core product logic into upstream Hermes updates.

## Agentopia owns
- execution semantics
- policy gating
- write safety and overwrite controls
- semantic action labels and production reasons
- callback persistence and retry behavior
- approval linkage and reconciliation
- operator summaries and review tooling

## Hermes owns
- runtime execution substrate
- model/runtime access
- provider/runtime compatibility
- transport/config mechanics required to run Hermes itself

## Enforcement rule

If a proposed change affects behavior or business logic, it must land in Agentopia first.

That includes changes to:
- execution behavior
- safety semantics
- approval behavior
- write behavior
- labeling and explanations
- reconciliation logic
- operator review surfaces

Hermes-side changes should only:
- translate
- integrate
- expose runtime capabilities
- preserve compatibility with upstream Hermes/runtime changes

## Preferred update pattern
1. absorb upstream Hermes/runtime changes at compatibility seams
2. keep Agentopia behavior stable
3. rerun the Hermes validation checklist before accepting the update
