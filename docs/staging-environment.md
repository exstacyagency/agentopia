# Staging Environment

This document defines the minimum staging environment expectations for Agentopia.

## Goals

- provide a pre-production place to validate changes after merge
- exercise deployment, config, and runtime checks before production-like rollout
- keep staging config explicit and reviewable

## Minimum staging requirements

A staging environment should have:

- a dedicated staging config based on `config/environments/staging.env`
- explicit non-floating image refs
- the same validation path used for deployment readiness
- a known URL or runtime endpoint for Paperclip
- a known rollback target before promotion onward

## Current repo staging baseline

Tracked staging template:

- `config/environments/staging.env`

Recommended validation commands:

```bash
python3 scripts/env-validator.py --env-file config/environments/staging.env
./scripts/validate-environment-configs.sh
./scripts/deploy-checklist.sh
```

## Staging promotion expectations

Before considering staging ready:

- the change is merged to `main`
- CI is green
- staging env config validates cleanly
- image refs are explicit and recorded
- rollout notes include rollback target

## Staging verification

After bringing staging up, run:

```bash
scripts/agentopia status
scripts/agentopia runtime-check
scripts/agentopia smoke
```

Record:

- staging deployment timestamp
- image refs used
- validation results
- known issues, if any

## Anti-patterns

Do not treat staging as ready when:

- it is using floating tags
- config differs without documentation
- validation is skipped
- rollback target is unknown

## Definition of done for this item

This repo can consider staging minimally defined when:

- staging config is tracked
- staging validation steps are documented
- staging verification steps are documented
- staging is explicitly part of the promotion path
