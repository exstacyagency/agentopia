# MemPalace Integration Plan

This document captures the recommended way to integrate MemPalace into the Paperclip ↔ Hermes ↔ Agentopia platform.

## Recommendation

Do **not** integrate MemPalace directly into Paperclip first.

Instead:
1. integrate MemPalace into Agentopia/Hermes as a memory service
2. expose configuration and status in Paperclip as a company-level **Memory** tab
3. then wire memory retrieval into Hermes execution and Paperclip agent wakeup flows

## Architecture

### Paperclip
Paperclip should remain the:
- control plane
- issue/approval/run UI
- operator surface
- company-level settings surface

### Hermes
Hermes should remain the:
- execution layer
- policy layer
- context consumer
- retrieval user during issue execution

### Agentopia
Agentopia should own:
- MemPalace integration
- memory config
- memory search
- wake-up context assembly
- memory status and mining orchestration

## Why this boundary is best

MemPalace is a memory/retrieval subsystem, not:
- an issue system
- an approvals engine
- an execution engine
- a policy engine

That makes it a natural fit under Agentopia/Hermes, not inside Paperclip core orchestration semantics.

## Proposed implementation order

### Phase 1: Agentopia/Hermes backend integration
Add a memory integration layer such as:
- `hermes/memory/mempalace_client.py`
- `hermes/memory/service.py`
- `hermes/memory/config.py`

Responsibilities:
- call MemPalace CLI or Python API
- search memory
- generate wake-up context
- manage per-company memory config
- expose a stable internal memory contract for the platform

### Proposed internal endpoints
- `GET /internal/memory/config?company_id=...`
- `POST /internal/memory/config`
- `POST /internal/memory/search`
- `POST /internal/memory/wakeup`
- `POST /internal/memory/mine`
- `GET /internal/memory/status`

## Phase 2: Hermes usage
Use MemPalace to augment Hermes context for:
- issue execution wakeup
- decision-history retrieval
- prior issue retrieval
- project/person memory lookup

Important rule:
MemPalace should **augment context**, not silently override policy or execution semantics.

## Phase 3: Paperclip company-level Memory tab
Add a **Memory** tab under the company header.

### What should live there

#### Settings
- enabled toggle
- palace path
- mining sources
- include/exclude paths
- company-to-palace mapping
- retrieval policy knobs
- mode selection

#### Status
- current mode
- indexing status
- last mine/sync time
- health/errors
- source counts

#### Tools
- test search box
- wake-up preview
- reindex/mine button
- optional memory-hit inspection

#### Governance
Controls for whether memory is used for:
- issue wakeup
- execution context
- review context
- operator search only

## Recommended initial MemPalace feature scope

### Use first
- raw mode search
- wake-up context generation
- project/person memory mining
- status/health

### Delay for later
- AAAK-heavy workflows
- contradiction-detection reliance
- aggressive autonomous mining
- other experimental repo features

Rationale:
MemPalace's raw mode appears to be the strongest and most honest path today. AAAK should be treated as experimental until proven otherwise in this platform context.

## Product framing for V1

### Memory tab first release
The first release should focus on:
- config
- status
- search
- wake-up preview
- raw mode only

This is the safest and clearest way to add MemPalace to the platform.

## Timing recommendation

MemPalace should be treated as a **phase-two enhancement**, after:
1. hardening / reliability pass
2. patch-discipline cleanup
3. operator UX cleanup until the system is stable to use

Only after that should the platform move into MemPalace integration work.

## Summary

Best implementation path:
- Agentopia/Hermes backend integration first
- Paperclip company-level Memory tab second
- memory-aware execution/wakeup third

This preserves boundaries cleanly:
- Agentopia owns semantics and memory behavior
- Hermes consumes memory during execution
- Paperclip presents settings and status in a native UI surface
