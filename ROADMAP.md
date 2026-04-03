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
9. Define implementation phases
10. Validate request/result contracts in code
11. Validate runtime env requirements in code
12. Move contract demo to repo-local artifacts and tests
13. Add unit tests for the contract runner
14. Split runner logic into a reusable module
15. Add a Makefile with one-command workflow wrappers
16. Add sample task artifact creation

## Next passes

- replace placeholder images or settings once the actual services are confirmed
- wire real Paperclip/Hermes execution paths
- replace the contract demo with real code paths
- add a minimal smoke test for the compose stack
- tighten compose health checks once real services are available
- add real task execution tests instead of runner-only checks

## Deferred

- real business logic
- real agent skill packs
- production deployment topology
- secrets management integration beyond `.env` placeholders
