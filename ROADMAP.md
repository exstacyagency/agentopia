# Roadmap

## Current focus

1. Scaffold repo structure
2. Add config stubs for Paperclip and Hermes
3. Add setup, validation, and doctor checks
4. Document contribution and branching norms
5. Document architecture, runbook, and example flow
6. Add a contract demo for request/result handoff
7. Add a tiny runnable contract runner
8. Connect the contract runner to repo artifacts

## Next passes

- tighten Docker Compose to match the real runtime targets
- replace placeholder images or settings once the actual services are confirmed
- wire real Paperclip/Hermes execution paths
- replace the contract demo with real code paths
- add a minimal smoke test for the compose stack

## Deferred

- real business logic
- real agent skill packs
- production deployment topology
- secrets management integration beyond `.env` placeholders
