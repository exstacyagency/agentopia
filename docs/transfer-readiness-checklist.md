# Transfer Readiness Checklist

Use this checklist before copying Agentopia into a new repository.

## Product identity

- [ ] Rename the product and service identity
- [ ] Rewrite product-facing README language
- [ ] Replace Agentopia-specific examples and fixtures

## Contracts and task model

- [ ] Review public API contract for the new domain
- [ ] Remove task types the new project should not expose
- [ ] Update request/result examples for the new product
- [ ] Decide whether any new task types are required

## Secrets and config

- [ ] Replace internal auth tokens
- [ ] Replace customer/client key examples
- [ ] Review `.env`, `.env.example`, and template files
- [ ] Verify environment-specific config matches the new deployment target

## Customer and operator surface

- [ ] Rewrite customer API docs
- [ ] Rewrite onboarding/setup docs
- [ ] Review runbook wording for old product references
- [ ] Review dashboard or approval docs for old product assumptions

## Safety and tenancy

- [ ] Verify tenant boundaries still match the new product model
- [ ] Verify sandbox and write/network controls still fit the new task set
- [ ] Re-run dangerous-path coverage after task-model changes

## Persistence and runtime

- [ ] Confirm Postgres and migrations still match the new repo
- [ ] Confirm storage layout still makes sense for the new domain
- [ ] Verify queue/retry/cancellation behavior still matches product expectations

## Pre-launch validation in the new repo

- [ ] Run `./scripts/validate-suite.sh core`
- [ ] Run focused tests for the changed API/task model
- [ ] Run at least one real end-to-end workflow in the new environment
- [ ] Check docs for stale Agentopia naming before launch
