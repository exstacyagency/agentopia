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

### Phase: formal approval contract linkage

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
- approval linkage is now formalized in the mapping/bridge/result-contract docs and code

Immediate focus:
- keep this handoff doc updated in every relevant PR
- preserve the now-working durable callback and inspection path
- ensure approval linkage is consistently carried by the bridge contract, not just opportunistically through context
- validate mapped bridge-generated envelopes preserve approval linkage end to end

After that, choose between:
1. add deeper Paperclip approval object reconciliation/status sync
2. add a third narrow write-capable route

## Recommended next action for the next agent

The immediate next task should be:

**Validate a bridge-generated task envelope preserves approval linkage end to end.**

### Suggested concrete sequence
1. construct a task request through `hermes/paperclip_bridge.py` using `PaperclipTaskContext`
2. include `paperclip_approval_id` and `paperclip_approval_status`
3. execute it through Hermes
4. confirm those fields survive into persisted result metadata and `scripts/list_write_actions.py`
5. update this handoff doc again in the same PR with the validation result

## Working rule from here on

From this point forward, whenever progress is made on Paperclip ↔ Hermes integration in Agentopia, update this document in the same PR. Do not let the handoff doc lag behind the real current state.
