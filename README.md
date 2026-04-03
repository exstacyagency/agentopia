# agentopia

Agentopia is the current repo for the infrastructure plan: a lightweight scaffold for orchestrating agent runtime, governance, and future business logic.

## Goals

- keep the repo incremental and non-destructive
- separate orchestration from execution
- preserve secrets outside the repo
- make it easy to wire in Paperclip and Hermes later

## First implementation pass

1. document the current shape of the repo
2. add config folders for paperclip and hermes
3. make setup/update scripts idempotent
4. define env variables in `.env.example`
5. keep the stack runnable from the existing repo

## Repo layout

- `artifacts/` — contract demo inputs/outputs
- `artifacts/templates/` — reusable sample task inputs
- `config/paperclip/` — governance and org config
- `config/paperclip/healthcheck.py` — runtime health check helper
- `config/hermes/` — agent/runtime config
- `config/hermes/healthcheck.py` — runtime health check helper
- `docs/` — architecture, example flow, implementation phases, and runbook notes
- `scripts/` — bootstrap, update, validation, smoke, contract, env helpers, and contract tests
- `docker-compose.yml` — local stack wiring
- `Makefile` — compatibility wrapper for common commands
- `scripts/agentopia` — canonical single entrypoint for common commands
- `.env.example` — documented env vars
- `CONTRIBUTING.md` — branch and PR norms
- `ROADMAP.md` — current and upcoming work

## Current scaffold

- `config/paperclip/paperclip.yml`
- `config/paperclip/healthcheck.py`
- `config/hermes/hermes.yml`
- `config/hermes/healthcheck.py`
- `scripts/setup.sh`
- `scripts/update.sh`
- `scripts/validate.sh`
- `scripts/doctor.sh`
- `scripts/smoke.sh`
- `scripts/sample-task.sh`
- `scripts/template-selector.py`
- `scripts/contract-runner.py`
- `scripts/task-runner.py`
- `scripts/contract-demo.sh`
- `scripts/contract_runner.py`
- `scripts/env-validator.py`
- `scripts/test_contract_runner.py`
- `scripts/output_models.py`
- `scripts/output_fixture.json`
- `scripts/agentopia`
- `scripts/runtimes.py`
- `docs/architecture.md`
- `docs/example-flow.md`
- `docs/implementation-phases.md`
- `docs/runbook.md`

## Quick flow

```bash
scripts/agentopia boot
```

That runs:

- `setup`
- `validate`
- `doctor`
- `runtime-check`
- `smoke`
- `sample-task`
- `contract-demo`
- `test-contract`
- `template-check`
- `task-run`

## Preferred command surface

Use `scripts/agentopia <command>` for the common workflow actions.

## Runtime targets

The runtime stack now expects the following env vars to be set in `.env`:

- `PAPERCLIP_IMAGE`
- `HERMES_IMAGE`
- `PAPERCLIP_URL`
- `PAPERCLIP_API_KEY`
- `HERMES_MODEL_PROVIDER`
- `HERMES_MODEL`
- `HERMES_API_KEY`

## How to start

```bash
cp .env.example .env
scripts/agentopia boot
```

## Notes

- Do not commit secrets.
- Keep changes small and reviewable.
- Prefer additive changes over rewrites.
