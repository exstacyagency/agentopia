# Preparing Agentopia as a Clean Base Repo

This guide explains how to copy Agentopia into a new repository as a clean foundation for another project.

## Goal

The goal is not to ship Agentopia unchanged.
The goal is to use Agentopia as the production-ready platform base and remove or rewrite the parts that are too specific to Agentopia itself.

## What is safe to keep

You can usually keep these parts largely as-is:

- Paperclip control-plane structure
- Hermes execution boundary
- auth and tenant model
- durable queue and runtime behavior
- Postgres + migrations
- sandbox and safety controls
- memory safety baseline
- metrics, logging, alerts, and runbooks
- customer API surface as a starting point

## What should be changed early

You should change these near the start of the new repo:

- project name and service identity
- domain-specific task types
- examples and fixtures
- product docs and onboarding language
- sample configs and environment descriptions
- any repo-specific branding in scripts and docs

## Clean transfer steps

### 1. Create the new repository

- create the new destination repo
- copy or fork Agentopia into it
- keep full git history if you want implementation traceability
- or copy a clean snapshot if you want a fresh product history

### 2. Rename the product surface

Update:

- `README.md`
- docs that mention Agentopia as the product name
- any script/help text that is product-branded
- example payloads and fixture copy

### 3. Reset environment expectations

Review and replace:

- `.env`
- `.env.example`
- `env.agentopia.template`
- environment-specific config files
- client key examples
- internal auth tokens
- any sample or local-only paths

### 4. Re-scope task contracts

Review:

- request schemas
- result schemas
- supported Hermes task types
- customer API docs
- public contract docs

Remove task types you do not want exposed in the new product.
Add only the ones your new domain actually needs.

### 5. Re-audit docs for transfer noise

Rewrite or remove docs that are too Agentopia-specific.
Keep the platform docs that still describe real behavior.

Good candidates to rewrite first:

- customer API docs
- onboarding/setup docs
- any UI/dashboard docs
- any product-positioning language in the README

### 6. Replace secrets and key material

Do not carry forward operational secrets from the source repo.

Rotate or replace:

- internal auth tokens
- client API key registries
- provider API keys
- local env defaults

### 7. Verify the new repo baseline

Before calling the new repo ready, verify:

- migrations run cleanly
- Postgres selection still works
- task submission works end to end
- tenant boundaries still hold
- safety controls still block dangerous paths
- customer docs match the new project name and task model

## Recommended first files to update in the new repo

- `README.md`
- `docs/customer-api-docs.md`
- `docs/onboarding-and-setup.md`
- `docs/public-api-contract.md`
- `fixtures/task_request_valid.json`
- `fixtures/task_result_valid.json`
- `schemas/task_request_v1.json`
- `schemas/task_result_v1.json`
- `env.agentopia.template`

## Recommended verification after transfer

Run at minimum:

```bash
./scripts/validate-suite.sh core
```

Then run the most relevant focused tests for your changed task model.

## Final rule

Treat Agentopia as a platform base, not a frozen template.
Keep the hardened infrastructure spine, but rewrite the product-facing layer early so the new repo feels intentional instead of inherited.
