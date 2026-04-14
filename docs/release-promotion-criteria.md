# Release and Promotion Criteria

This document defines the minimum gate for promoting Agentopia changes from development work into staging-like validation and then toward production-like rollout.

## Goals

- make promotion decisions explicit
- reduce accidental drift between reviewed code and deployed runtime
- ensure runtime images, config, and test signals are captured together
- make rollback easier when a promotion fails

## Promotion model

### Development
Work happens on short-lived feature branches and lands through pull requests.

Minimum expectations:
- PR is focused on one change pass
- required CI checks pass
- production readiness checklist is updated when a readiness item is completed
- runtime/config/docs changes are included together when they change the same operational surface

### Staging
A change is eligible for staging promotion only if all of the following are true:

- merged into `main`
- required branch rules passed
- clean-environment CI passed
- runtime validation passes with explicit version tags or digests
- image refs to be promoted are recorded
- operator has a rollback target identified

### Production-like promotion
A staging-validated change is eligible for production-like rollout only if all of the following are true:

- staging validation completed without unresolved failures
- release notes or deployment notes include:
  - commit or PR reference
  - Paperclip image ref
  - Hermes image ref
  - key config differences
  - rollback target
- production uses digest-pinned image references where available
- operator confirms promotion window and rollback path

## Required evidence for promotion

Before promotion, capture:

- branch or commit being promoted
- PR link
- CI result
- `PAPERCLIP_IMAGE` ref
- `HERMES_IMAGE` ref
- env validation result
- rollback image refs or prior release target

## Minimum release checklist

### Before merge to main
- CI green
- review approved
- checklist/docs updated if readiness scope changed

### Before staging promotion
- `main` contains the exact change set
- image refs are explicit and recorded
- `scripts/env-validator.py` passes for intended config
- core validation suite passes

### Before production-like promotion
- staging validation completed
- deployment notes written
- digest refs selected for runtime images when available
- rollback target documented

## Promotion anti-patterns

Do not promote when:

- image refs still use floating tags
- CI is red or missing
- the change depends on undocumented manual steps
- runtime validation fails
- rollback target is unknown

## Recommended repo workflow

1. Merge feature PR to `main`
2. Record release candidate metadata
3. Validate with explicit image refs
4. Promote to staging-like environment
5. Verify behavior and logs
6. Promote with digest-pinned refs for production-like rollout
7. Record final deployed refs and rollback target

## Definition of done for this item

This repo can consider release and promotion criteria minimally defined when:

- promotion gates are documented
- required promotion evidence is documented
- staging and production-like expectations are distinct
- rollback expectations are part of the release path
