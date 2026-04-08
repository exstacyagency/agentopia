# Paperclip ↔ Hermes Integration Handoff

This document is the GitHub handoff/source-of-truth for ongoing Agentopia work integrating Paperclip and Hermes. Update this file in every relevant PR so another agent can resume without reconstructing context from chat.

## Goal

Connect Agentopia to a real locally running Paperclip control plane and isolated Hermes runtime so work can flow through:

1. Agentopia task/request
2. Paperclip issue creation
3. Paperclip approval creation when required
4. Paperclip-native execution trigger through agent wakeup / heartbeat run
5. Hermes execution in the isolated Agentopia runtime
6. Result, artifact, and run linkage back into Agentopia
7. Durable callback delivery and operator inspection

## Repo boundary rule

- **Agentopia is the only repo to update/push/PR for this integration work.**
- **Paperclip changes remain local-only dependency/runtime patches unless the user explicitly says otherwise.**
- Treat the upstream/local Paperclip checkout as a patched local control-plane dependency for Agentopia development, not as a repo to operationalize through GitHub by default.

## Non-negotiable constraints

- Refer to the orchestration repo/product as **Paperclip** in user-facing discussion.
- Do **not** interfere with the shared Hermes / trading-bot environment under `~/.hermes`.
- Agentopia Hermes isolation target:
  - `HERMES_HOME=/Users/work/.hermes-agentopia`
  - `API_SERVER_PORT=8742`
  - Open WebUI on `3001`
- Do not bake in secrets/default API keys; require explicit local secrets.

## Current state

### Agentopia repo

Implemented and validated already:
- Step 1 findings/docs for Paperclip API surface
- Step 2 adapter skeleton
- Step 3 HTTP client layer
- isolation helpers and docs for isolated Hermes + Open WebUI
- Paperclip issue creation aligned to real live issue shapes
- approval route alignment in the Agentopia client/service layer
- Paperclip-native execution trigger via `POST /api/agents/{agentId}/wakeup`
- Paperclip ↔ Hermes bridge envelope and task mapping contract
- expanded Hermes executor task support
- live-validated routes:
  - `file_analysis`
  - `text_generation`
  - `structured_extract`
  - `repo_change_plan`
  - `implementation_draft`
- result persistence under `var/hermes/runs/`
- callback attempt recording under `var/hermes/callbacks/`
- callback retry tooling
- callback sink acceptance under `var/hermes/callback-results/`
- lightweight operator inspection scripts for recent runs and callback results

Important current files in Agentopia:
- `hermes/app.py`
- `hermes/executor.py`
- `hermes/paperclip_mapping.py`
- `hermes/paperclip_bridge.py`
- `hermes/persistence.py`
- `hermes/callback_store.py`
- `schemas/task_request_v1.json`
- `docs/paperclip-hermes-result-contract.md`
- `docs/paperclip-task-mapping-contract.md`
- `docs/paperclip-step4-live-integration.md`
- `docs/paperclip-hermes-runbook.md`
- `docs/paperclip-hermes-inspector.md`
- `docs/paperclip-upstream-dependency.md`
- `docs/agentopia-local-stack.md`
- `scripts/bootstrap-paperclip-dev.sh`
- `scripts/start-agentopia-stack.sh`
- `scripts/check-paperclip-live-ready.sh`
- `scripts/test_paperclip_live_probe.py`
- `scripts/list_failed_callbacks.py`
- `scripts/retry_failed_callbacks.py`
- `scripts/list_recent_runs.py`
- `scripts/list_callback_results.py`
- `scripts/hermes-agentopia-env.sh`
- `scripts/hermes-agentopia-guard.sh`
- `scripts/hermes-agentopia-start.sh`
- `scripts/hermes-agentopia-status.sh`
- `scripts/hermes-agentopia-openwebui-up.sh`
- `scripts/hermes-agentopia-openwebui-down.sh`
- `scripts/hermes-agentopia-launchd-install.sh`
- `scripts/hermes-agentopia-launchd-status.sh`
- `scripts/hermes-agentopia-launchd-uninstall.sh`

### Upstream Paperclip local repo

Local repo path:
- `~/.openclaw/workspace/upstream-paperclip`

Local-only Paperclip work already done there:
- added local workspace Hermes adapter package under `packages/adapters/hermes-local/`
- rewired server/ui dependency resolution from missing external adapter package to workspace package
- fixed frontend/runtime issues that blocked local UI boot
- patched visible user-facing Paperclip branding locally
- patched wakeup context propagation so the Hermes adapter receives the correct issue/task context
- patched local Hermes adapter routing/mirroring needed for live validation

Important note:
- Paperclip remains a local-only patched dependency/runtime for this integration work unless the user explicitly requests upstream PR work

## Verified environment

### Isolated Hermes
- home: `~/.hermes-agentopia`
- health: `curl http://127.0.0.1:8742/health`
- models: `curl -H 'Authorization: Bearer <key>' http://127.0.0.1:8742/v1/models`
- Open WebUI: `http://localhost:3001`
- launchd label: `ai.hermes.gateway.agentopia`

### Paperclip dev
- local UI/API boots from upstream checkout
- backend health: `http://127.0.0.1:3100/api/health`
- adapter-related endpoints verified:
  - `GET /api/companies/dev/adapters/hermes_local/models`
  - `GET /api/companies/dev/adapters/hermes_local/detect-model`
- issue creation works live
- execution trigger works live through agent wakeup / heartbeat run

## Key architectural conclusions

Paperclip’s real orchestration model is not a generic `/tasks` flow. The key native objects are:
- issues
- approvals
- agents
- heartbeat runs / wakeups

Agentopia integration should map onto that model directly.

A second important conclusion is that the bridge proof threshold has already been reached. The current phase is no longer “does it work?” but “is it durable, inspectable, and safe to extend?”

## Current validated bridge behavior

The local Paperclip ↔ Hermes path is now validated for:
- live Paperclip issue creation
- live Paperclip agent creation for isolated Hermes-backed agents
- live execution trigger through `POST /api/agents/{agentId}/wakeup`
- heartbeat run linkage captured back into Agentopia result metadata
- durable persisted results
- durable callback attempt records
- callback retry against persisted results
- direct callback sink acceptance when posting to `http://127.0.0.1:3200/internal/tasks/<task_id>/result`
- lightweight local inspection of recent runs and callback results

## Current operational gap

No fundamental architecture blocker remains for the safe-route bridge.

The main remaining gaps are now:
- align runtime callback target configuration with the working local sink, because Hermes is still posting to `http://127.0.0.1:3100/internal/tasks/{task_id}/result`
- clearer operator visibility over recent runs/callback state
- policy controls before riskier write-capable routes
- documentation discipline so the handoff doc stays current in every relevant PR

## Recommended next phase

### Phase: approval and review dashboard

Current validated state:
- write-capable actions already carry policy, approval, and semantic labeling metadata
- write-action summary and approval reconciliation exist as separate operator views
- a unified review dashboard script is now added to group pending previews, blocked actions, applied writes, and approval mismatches

Immediate focus:
- keep this handoff doc updated in every relevant PR
- preserve the now-working durable callback and Paperclip feedback loop
- make approval/deny review easier before building rollback
- validate the grouped review output against recent persisted runs
- explicitly mark legacy versus labeled result generations in the review output so operators can distinguish historical metadata gaps from real regressions

After that, choose between:
1. expand rollback/revert actions beyond file-level restore
2. enrich dashboard states and alerts further
3. surface revert summaries back into Paperclip issue history

### Boundary cleanup note

Before further live validation, keep the ownership boundary explicit:
- Agentopia owns core execution, policy, safety, labeling, reconciliation, and operator tooling
- Paperclip remains the orchestration/control-plane surface
- local Paperclip patches should stay thin, documented, and disposable
- Hermes runtime compatibility should remain distinct from Agentopia-owned execution semantics

Supporting docs added for this:
- `docs/paperclip-local-patch-inventory.md`
- `docs/paperclip-boundary-rules.md`
- `docs/hermes-boundary-rules.md`
- `docs/hermes-local-runtime-inventory.md`
- `docs/hermes-upgrade-validation-checklist.md`

### Phase: automatic Paperclip comment feedback loop

Current validated state:
- allowed route live validation passed with `policy.mode = allow`
- blocked write-capable route live validation passed with `error.code = POLICY_BLOCKED`
- blocked route metadata correctly reports `policy.reason = write_capable_requires_explicit_policy`
- approved `file_write` live validation passed with `policy.reason = explicit_file_write_approval`
- `shell_command` remains blocked under deny-by-default policy
- real workspace-scoped `file_write` behavior is implemented and live-validated
- overwrite and change-tracking controls are implemented and live-validated
- overwrite-specific approval escalation and diff-preview metadata are implemented and live-validated
- constrained `repo_write` support is implemented and live-validated
- `repo_write` preview mode and per-change overwrite approval controls are implemented and live-validated
- an operator-facing write-action summary script is added and normalized
- Paperclip approval id/status linkage is validated in write-result metadata and operator summaries
- approval linkage is formalized in the mapping/bridge/result-contract docs and code
- approval reconciliation is implemented with local fallback and supports live Paperclip lookup
- semantic action labels and human-readable production reasons are implemented in result metadata and write summaries
- Paperclip issue-comment posting helpers are now implemented in the client/service layer
- automatic Paperclip execution-summary comment posting is now implemented in the Hermes app path
- boundary cleanup docs now explicitly describe Paperclip local patch inventory and ownership rules

Immediate focus:
- keep this handoff doc updated in every relevant PR
- preserve the now-working durable callback and inspection path
- automatically post semantic execution summaries back into Paperclip-visible issue history
- validate that a structured execution summary comment appears automatically in the Paperclip issue timeline

After that, choose between:
1. enrich mismatch handling and approval drift alerting
2. add richer Paperclip-native UI surfacing beyond comments

## Recommended next action for the next agent

The immediate next task should be:

**Validate the new issue-level action contract for future Paperclip review-panel controls.**

### Suggested concrete sequence
1. restart Hermes so it loads the issue-action endpoint
2. POST a sample `apply_preview` issue action to `/internal/issue-action`
3. POST a sample `file_revert` issue action to `/internal/issue-action`
4. confirm both return stable contract responses
5. update this handoff doc again in the same PR with the validation result

### Product note
The user explicitly said functionality matters more than polish right now.

Current priority:
- keep the review/approval/rollback/dashboard flow functional end to end
- defer UI look-and-feel polish until later

That means future work should prefer:
- correctness
- stable surfacing
- usable control flow

over:
- visual refinement
- styling polish
- presentation cleanup

### Practical next-phase order
The agreed sequencing from here is:
1. hardening / reliability pass
2. patch-discipline cleanup
3. operator UX cleanup until the system is stable to use
4. then evaluate MemPalace integration
5. after that, expand broader capabilities

MemPalace is therefore a phase-two enhancement, not part of the core Paperclip ↔ Hermes integration finish line.

### Hardening pass status
Current hardening work added:
- more explicit Paperclip HTTP error surfacing in the adapter client
- runtime guard visibility on `/health`
- richer persistence metadata when Paperclip comment or dashboard publish fails
- a lightweight platform hardening check script

Immediate hardening focus after this pass should remain:
- reload/restart discipline
- postback failure diagnosis and recovery
- local patch verification and reduction of runtime staleness surprises

Restart/reload discipline now includes:
- runtime build stamp surfaced on `/health`
- explicit runtime feature fingerprint surfaced on `/health`
- `scripts/check_runtime_reload.py` to confirm the running Hermes process actually loaded the expected feature set

Postback recovery now includes:
- durable postback records for comment and dashboard publishing under `var/hermes/postbacks/`
- `scripts/list_failed_postbacks.py`
- `scripts/retry_postbacks.py` with real replay logic for comment and dashboard postbacks

## Working rule from here on

From this point forward, whenever progress is made on Paperclip ↔ Hermes integration in Agentopia, update this document in the same PR. Do not let the handoff doc lag behind the real current state.
