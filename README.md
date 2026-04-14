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

## Python environment

Use a local virtualenv and install the repo in editable mode with pinned dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
```

## Continuous integration

GitHub Actions now validates the repo in a clean environment by creating a virtualenv, installing from `pyproject.toml`, and running the core test suite.

## Container image policy

Runtime image refs should use explicit version tags or immutable digests. Avoid floating tags like `latest`, `main`, `master`, `dev`, and `nightly`.

See `docs/container-image-versioning.md`.

## Release promotion policy

Release and staging-to-production promotion criteria are documented in `docs/release-promotion-criteria.md`.

## Deployment process

Use `docs/deployment-process.md` for the repeatable deployment flow and `scripts/deploy-checklist.sh` for the current deployment validation checklist.

## Environment config validation

Use `scripts/validate-environment-configs.sh` to validate the tracked environment templates in `config/environments/`.

Production-like configs should use digest-pinned image refs, while development and staging can use explicit non-floating tags.

## Staging environment

Use `docs/staging-environment.md` for the minimum staging definition and `scripts/staging-checklist.sh` for the staging preflight checklist.

## Production secret injection

Use `docs/production-secret-injection.md` for the secret injection policy and `scripts/render-production-env.sh` to build a validated production runtime env from tracked templates plus untracked secrets.

## Secret storage and handling

Use `docs/secret-storage-handling.md` for the current secret handling baseline and `python3 scripts/check-secret-handling.py` to verify obvious repo-level secret handling rules.

## Service-to-service authentication

Use `docs/service-to-service-auth.md` for the internal auth baseline. Protected internal endpoints now use a shared bearer token via `AGENTOPIA_INTERNAL_AUTH_TOKEN`.

## Runtime and container hardening

Use `docs/runtime-container-hardening.md` for the hardening baseline and `python3 scripts/check-compose-hardening.py` to verify the compose file still includes the expected safeguards.

## Dependency and vulnerability scanning

Use `docs/dependency-vulnerability-scanning.md` for the scan policy and `scripts/run-dependency-scan.sh` to run the local dependency audit path.

## Image and dependency provenance

Use `docs/image-dependency-provenance.md` for provenance expectations and `python3 scripts/check-provenance.py` to verify the current baseline.

## Artifact access and redaction

Use `docs/artifact-access-redaction.md` for the current artifact handling baseline. Persisted results are internal-only by default and now redact obvious secret-bearing values before writing.

## Request size limits

Use `docs/request-size-limits.md` for the current request body limit policy. Paperclip and Hermes both enforce configurable max request sizes.

## Input validation and sanitization

Use `docs/input-validation-sanitization.md` for the current safer input validation baseline. Paperclip and Hermes both reject request payload strings containing unsafe control characters.

## Rate limiting and abuse protection

Use `docs/rate-limiting-abuse-protection.md` for the current abuse-control baseline. Paperclip and Hermes both enforce configurable per-IP request limits.

## Audit logging

Use `docs/audit-logging.md` for the current audit logging baseline. Paperclip keeps audit events in SQLite, and Hermes now writes structured audit records for persistence-side events.

## Structured logging

Use `docs/structured-logging.md` for the current service-log baseline. Paperclip and Hermes now emit JSON log lines for key service events.

## Correlation IDs

Use `docs/correlation-ids.md` for the current request correlation baseline. Paperclip and Hermes now propagate or generate `X-Correlation-ID` values across internal requests and responses.

## Dependency-aware health checks

Use `docs/dependency-aware-health-checks.md` for the current health baseline. Paperclip and Hermes health endpoints now report required dependency/config readiness, not just process liveness.

## Rollback process

Use `docs/rollback-process.md` for rollback guidance and `scripts/rollback-checklist.sh` for the current rollback verification checklist.

## How to start

```bash
cp .env.example .env
scripts/agentopia start
```

## Hermes browser UI

Hermes does not currently ship a Paperclip-style native board UI in this repo.
The supported browser path is **Hermes API server + Open WebUI**.

For a machine that already has a shared Hermes instance, use the isolated Agentopia setup instead of the shared default home.

See:
- `docs/hermes-openwebui.md`
- `docs/hermes-agentopia-isolation.md`
- `docker-compose.hermes-openwebui.yml`
- `scripts/hermes-openwebui-up.sh`
- `scripts/hermes-openwebui-down.sh`
- `scripts/hermes-agentopia-*.sh`

## Notes

- Do not commit secrets.
- Keep changes small and reviewable.
- Prefer additive changes over rewrites.
