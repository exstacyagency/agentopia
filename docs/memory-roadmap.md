# Memory Roadmap

This document captures later-phase memory features that can be added after the current MemPalace integration baseline.

## Current baseline

Already implemented:
- memory config
- memory status
- search test
- wakeup preview
- mine/reindex controls
- memory modes
- runtime memory context enrichment in Hermes execution metadata

## Next-phase candidate features

### 1. Memory provenance in operator surfaces
- show memory source in review panel
- show memory hit counts in queue/dashboard
- show whether MemPalace contributed to a specific execution

### 2. Richer status/health
- indexed source counts
- last successful search time
- last successful wakeup-context generation time
- operation duration and richer mine/reindex details

### 3. Company-specific memory isolation
- company-specific palace path
- company-specific include/exclude rules
- company-specific source mapping
- company-specific mining scopes

### 4. Mining governance
- manual-only vs scheduled mining
- stale-memory thresholds
- who can trigger mine/reindex
- source freshness policy

### 5. Memory-aware decision trace
- include memory contribution summaries in decision trace
- show which retrieval mode was active for an action
- show a compact summary of which memories influenced execution

### 6. Memory-aware wakeup integration in Paperclip
- use memory context in real Paperclip wakeup flows
- show wakeup preview directly next to execution controls

### 7. Better Memory tab UX
- cards instead of raw JSON
- richer search result rendering
- operation history
- inline health warnings and troubleshooting guidance

### 8. Advanced retrieval modes later
- more experimental MemPalace modes if they prove stable
- contradiction/consistency tooling if worth the complexity

## Guiding principle

MemPalace should continue to:
- override retrieval behavior
- augment runtime context

It should not replace:
- issue history
- approvals
- execution records
- audit/state persistence
