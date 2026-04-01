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
- `scripts/` — bootstrap and update helpers
- `docker-compose.yml` — local stack wiring
- `.env.example` — documented env vars

## Notes

- Do not commit secrets.
- Keep changes small and reviewable.
- Prefer additive changes over rewrites.
