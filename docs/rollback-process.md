# Rollback Process

This document defines the minimum rollback process for Agentopia in its current scaffold state.

## Goals

- make rollback steps explicit before incidents happen
- reduce time to recover from bad deployments
- ensure rollback targets are identified before rollout
- preserve enough deployment metadata to revert safely

## When rollback should be considered

Rollback should be considered when any of the following happen after a deployment:

- readiness or smoke checks fail
- runtime validation reveals an incorrect config or image ref
- a deployment introduces a blocking regression
- operator cannot restore service health quickly by fixing forward
- an image or config change is known to be unsafe

## Required rollback inputs

Before a rollout, record:

- previous known-good `PAPERCLIP_IMAGE`
- previous known-good `HERMES_IMAGE`
- previous known-good config state or env snapshot
- deployment commit SHA
- deployment timestamp
- operator name or identifier

A deployment should not be considered ready if these rollback inputs are unknown.

## Minimum rollback flow

### 1. Confirm the rollback target

Identify the last known-good runtime state:

- Paperclip image ref
- Hermes image ref
- matching config state

### 2. Restore the prior runtime refs and config

Update the runtime environment to the previous known-good values.

At minimum, restore:

- `PAPERCLIP_IMAGE`
- `HERMES_IMAGE`
- any config values changed in the failed deployment

### 3. Re-run validation before restarting

Run:

```bash
python3 scripts/env-validator.py
```

Do not proceed if the rollback target itself fails validation.

### 4. Re-apply the previous runtime state

For the current compose-based scaffold:

```bash
docker compose --profile runtime pull
docker compose --profile runtime up -d
```

### 5. Verify recovery

Run:

```bash
scripts/agentopia status
scripts/agentopia runtime-check
scripts/agentopia smoke
```

Recovery is not complete until these checks pass.

### 6. Record rollback completion

Capture:

- rollback timestamp
- rollback operator
- restored image refs
- restored config notes
- reason for rollback
- follow-up remediation needed

## Rollback anti-patterns

Do not attempt rollback when:

- the prior known-good refs are unknown
- the rollback config does not match the prior runtime state
- validation is failing and ignored
- the operator cannot identify what changed in the failed deployment

## Recommended rollback checklist

1. Stop and assess the failed rollout
2. Identify the last known-good runtime refs
3. Restore prior config values
4. Run env validation
5. Re-apply the known-good runtime state
6. Run readiness and smoke checks
7. Record what happened and what still needs follow-up

## Definition of done for this item

This repo can consider rollback minimally defined when:

- rollback inputs are documented
- rollback steps are documented
- validation is required before re-applying runtime state
- post-rollback verification is documented
- rollback recording is part of the process
