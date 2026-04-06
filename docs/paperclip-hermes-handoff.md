# Paperclip ↔ Hermes Integration Handoff

This document is the GitHub handoff/source-of-truth for ongoing Agentopia work integrating Paperclip and Hermes. Update this file as progress happens so another agent can resume work without reconstructing context from chat.

## Goal

Connect Agentopia to a real locally running Paperclip control plane and isolated Hermes runtime so work can flow through:

1. Agentopia task/request
2. Paperclip issue creation
3. Paperclip approval creation when required
4. Paperclip-native execution trigger (agent wakeup / heartbeat run path)
5. Hermes execution in the isolated Agentopia runtime
6. Result / artifact / run linkage back into Agentopia

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

Implemented already:
- Step 1 findings/docs for Paperclip API surface
- Step 2 adapter skeleton
- Step 3 HTTP client layer
- isolation helpers and docs for isolated Hermes + Open WebUI
- docs/bootstrap guidance making Agentopia the operational source of truth for local stack bring-up

Important files already added in Agentopia:
- `docs/paperclip-api-surface.md`
- `docs/paperclip-hermes-step1-findings.md`
- `docs/paperclip-step2-adapter.md`
- `docs/paperclip-step3-http-client.md`
- `docs/paperclip-upstream-dependency.md`
- `docs/agentopia-local-stack.md`
- `scripts/bootstrap-paperclip-dev.sh`
- `scripts/start-agentopia-stack.sh`
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

Local boot/unblock work already done there:
- added local workspace Hermes adapter package under `packages/adapters/hermes-local/`
- rewired server/ui dependency resolution from missing external adapter package to workspace package
- fixed frontend/runtime issues that blocked local UI boot
- fixed visible Paperclip user-facing branding in the frontend so the app/tab no longer shows Seiko locally

Important note:
- local commit exists on branch `feature/paperclip-hermes-local-adapter-and-ui-fixes`
- push to upstream `paperclipai/paperclip` failed with HTTP 403 due to missing permission
- do **not** assume an upstream PR exists unless one is actually created by an account with access

## Verified environment

### Isolated Hermes
- home: `~/.hermes-agentopia`
- health: `curl http://127.0.0.1:8742/health`
- models: `curl -H 'Authorization: Bearer <key>' http://127.0.0.1:8742/v1/models`
- Open WebUI: `http://localhost:3001`
- launchd label: `ai.hermes.gateway.agentopia`

### Paperclip dev
- local UI/API currently boots from upstream checkout
- backend health verified previously at `http://127.0.0.1:3100/api/health`
- adapter-related endpoints verified previously:
  - `GET /api/companies/dev/adapters/hermes_local/models`
  - `GET /api/companies/dev/adapters/hermes_local/detect-model`

## Key architectural conclusion

Paperclip’s real orchestration model is not a generic `/tasks` flow. The key native objects are:
- issues
- approvals
- agents
- heartbeat runs / wakeups

Agentopia integration should map onto that model directly.

## What is blocked right now

Authenticated live Paperclip object creation is still blocked on obtaining/using a valid local board-auth + company context in the running dev environment.

Anonymous probing is insufficient because relevant routes depend on board/company access.

## Remaining implementation plan

### 1. Finish authenticated live Paperclip validation
- establish valid board/company session in Paperclip local dev UI/API
- list or create target company context
- create a real issue
- create a real approval
- identify exact execution trigger path and returned object shapes

### 2. Implement real issue creation in Agentopia
- replace shape assumptions with live request/response shapes
- return/persist Paperclip issue IDs
- add tests around real object parsing

### 3. Implement approval flow in Agentopia
- create approval when required
- link approval to issue
- return/persist approval IDs

### 4. Implement Paperclip-native execution trigger
- determine whether trigger path is agent wakeup, issue transition, heartbeat run start, or a combination
- wire Agentopia to the actual Paperclip execution entrypoint
- return/persist run linkage fields

### 5. Bind execution to isolated Hermes only
- ensure all execution targets `~/.hermes-agentopia`
- ensure no leakage into shared `~/.hermes`
- verify runtime path/port/profile explicitly

### 6. Add run/result/artifact tracking
- status polling or event capture
- run IDs / heartbeat run IDs / timestamps / outputs / artifacts
- tie everything back to Agentopia task envelope

### 7. Harden policy and observability
- approval/policy matrix by task risk
- end-to-end tracing fields
- debugging docs for failures

### 8. Add one canonical end-to-end acceptance flow
- Agentopia request → Paperclip issue → optional approval → execution trigger → isolated Hermes run → result tracking

## Recommended next action for the next agent

The immediate next task should be:

**Get authenticated local Paperclip issue creation working and capture the exact request/response shape.**

That is the shortest path to unblocking the rest of the integration.

### Suggested concrete sequence
1. boot local Paperclip from `~/.openclaw/workspace/upstream-paperclip`
2. establish board-auth in the browser/dev session
3. inspect existing company context or create a local dev company
4. create a real issue through the authenticated API/UI
5. capture the returned JSON shape
6. update Agentopia `paperclip_adapter/http_client.py` and `paperclip_adapter/service.py` to match reality
7. update this handoff doc with findings

## Update policy for this file

From this point forward, whenever progress is made on Paperclip ↔ Hermes integration in Agentopia, update this document as part of the change so future agents can resume cleanly.
