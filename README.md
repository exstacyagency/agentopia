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

- `config/paperclip/` — governance and org config
- `config/hermes/` — agent/runtime config
- `docs/` — architecture, example flow, and runbook notes
- `scripts/` — bootstrap, update, validation, and smoke helpers
- `docker-compose.yml` — local stack wiring
- `.env.example` — documented env vars
- `CONTRIBUTING.md` — branch and PR norms
- `ROADMAP.md` — current and upcoming work

## Current scaffold

- `config/paperclip/paperclip.yml`
- `config/hermes/hermes.yml`
- `scripts/setup.sh`
- `scripts/update.sh`
- `scripts/validate.sh`
- `scripts/doctor.sh`
- `scripts/smoke.sh`
- `docs/architecture.md`
- `docs/example-flow.md`
- `docs/runbook.md`

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
./scripts/setup.sh
./scripts/validate.sh
./scripts/doctor.sh
./scripts/smoke.sh
```

## Notes

- Do not commit secrets.
- Keep changes small and reviewable.
- Prefer additive changes over rewrites.
