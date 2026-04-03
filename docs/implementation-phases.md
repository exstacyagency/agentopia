# Implementation Phases

This is the working checklist for moving from scaffold to real integration.

## Phase 1 — Contract layer

**Goal:** define and validate the request/result handoff between Paperclip and Hermes.

**Done when:**

- the request schema is represented in code
- the result schema is represented in code
- invalid inputs fail fast
- the contract demo runs against repo-local artifacts
- the task runner writes structured output
- output models exist in code

## Phase 2 — Runtime wiring

**Goal:** make the repo boot a meaningful local stack.

**Done when:**

- `docker-compose.yml` uses real service targets or clearly documented local equivalents
- startup order and health checks are meaningful
- the runtime can be exercised locally without manual guessing

## Phase 3 — Real execution path

**Goal:** run an end-to-end flow from Paperclip to Hermes.

**Done when:**

- a task enters the system through Paperclip
- Hermes executes the task through a real path
- Paperclip records audit information
- a sample output is produced and stored

## Phase 4 — Secrets and configuration

**Goal:** connect runtime settings to real secret handling.

**Done when:**

- `.env.example` matches the actual required values
- secrets are not stored in the repo
- config validation catches missing or invalid runtime values

## Phase 5 — Operations

**Goal:** make the system maintainable.

**Done when:**

- setup, validation, smoke, and doctor scripts cover the real boot path
- docs explain how to run and troubleshoot the stack
- update/upgrade steps are documented

## Phase 6 — Production path

**Goal:** define where this goes once the local stack works.

**Done when:**

- deployment topology is chosen
- upgrade and rollback strategy is documented
- real runtime targets are pinned and repeatable
