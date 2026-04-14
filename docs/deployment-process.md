# Repeatable Deployment Process

This document defines the minimum repeatable deployment process for Agentopia in its current scaffold state.

## Goals

- make deployments predictable
- reduce operator guesswork
- tie deployment steps to validated image refs and runtime config
- make rollback preparation part of the deployment path

## Deployment assumptions

Current repo state:

- local/dev workflow is script-driven
- runtime configuration comes from `.env`
- runtime validation is available through `scripts/env-validator.py`
- tracked environment templates live in `config/environments/`
- image refs should already follow `docs/container-image-versioning.md`
- promotion decisions should already follow `docs/release-promotion-criteria.md`

## Minimum deployment inputs

Before deployment, have all of the following ready:

- target environment name
- intended commit or PR reference
- `PAPERCLIP_IMAGE` ref
- `HERMES_IMAGE` ref
- environment-specific `.env` values
- rollback target image refs

For staging, use `config/environments/staging.env` as the tracked baseline and `scripts/staging-checklist.sh` as the preflight checklist.

## Repeatable deployment flow

### 1. Prepare environment config

Set or update the environment config with explicit image refs and required runtime values.

Validate:

```bash
python3 scripts/env-validator.py
```

Do not continue if env validation fails.

For tracked environment templates, also run:

```bash
./scripts/validate-environment-configs.sh
```

### 2. Verify the repo state

Use the validated branch or merged `main` state intended for deployment.

Recommended checks:

```bash
git rev-parse HEAD
./scripts/bootstrap-venv.sh
./.venv/bin/python scripts/test_contract_schemas.py
./.venv/bin/python scripts/test_paperclip_service.py
./.venv/bin/python scripts/test_hermes_executor.py
./.venv/bin/python scripts/test_integration_flow.py
./.venv/bin/python scripts/test_runtimes.py
```

### 3. Record deployment metadata

Record at minimum:

- commit SHA
- branch or PR
- target environment
- Paperclip image ref
- Hermes image ref
- rollback target

### 4. Start or update runtime services

For the current compose-based scaffold:

```bash
docker compose --profile runtime pull
docker compose --profile runtime up -d
```

If using the local Hermes isolation workflow, follow the relevant startup scripts in `scripts/` and capture the exact runtime refs used.

### 5. Verify service readiness

Run:

```bash
scripts/agentopia status
scripts/agentopia runtime-check
scripts/agentopia smoke
```

Do not mark deployment complete until readiness checks pass.

### 6. Record completion

Capture:

- deployment timestamp
- operator
- final image refs
- readiness/smoke result
- any follow-up actions

## Rollback preparation

Every deployment should identify a rollback target before rollout.

Minimum rollback data:

- previous Paperclip image ref
- previous Hermes image ref
- prior known-good config state
- operator note for why rollback might be needed

See `docs/rollback-process.md` and `scripts/rollback-checklist.sh` for the rollback path.

## Deployment anti-patterns

Do not deploy when:

- image refs use floating tags
- env validation is failing
- the operator cannot identify the intended commit
- rollback target is unknown
- smoke or readiness checks are failing

## Definition of done for this item

This repo can consider the deployment process minimally repeatable when:

- deployment steps are documented
- required inputs are documented
- validation steps are included before runtime startup
- post-deploy verification steps are included
- rollback preparation is part of the process
