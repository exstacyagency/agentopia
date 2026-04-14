# Image and Dependency Provenance Checks

This document defines the minimum provenance checks for Agentopia in its current scaffold state.

## Goals

- prefer verifiable runtime image references
- make dependency source expectations explicit
- fail fast on obviously weak provenance inputs

## Current provenance baseline

### Runtime images
Production image refs should already be digest-pinned.

Minimum provenance expectation:

- production env uses `@sha256:` image refs
- staging/dev use explicit non-floating tags
- runtime validation rejects floating tags

### Python dependencies
Current dependency provenance baseline is limited but explicit:

- dependencies are pinned in `requirements.lock`
- package installs come from the configured Python package index during environment setup
- the repo should fail validation if `requirements.lock` contains unpinned dependency lines

## Current repo-level provenance checks

Minimum checks now enforced:

- production image refs must be digest-pinned
- `requirements.lock` entries must be exact `==` pins
- comments, blanks, and editable/path installs are not allowed in `requirements.lock`

## Limits of current provenance checks

This is not full supply-chain attestation.

It does **not** yet prove:

- signed container provenance
- signed Python package attestations
- registry trust policy
- SBOM verification

It does provide a stronger baseline than free-form refs and loosely specified dependencies.

## Local usage

Run:

```bash
python3 scripts/check-provenance.py
```

## Definition of done for this item

This repo can consider image and dependency provenance checks minimally defined when:

- provenance expectations are documented
- runtime image digest requirements are already enforced for production
- dependency lockfile entries are checked for exact pins
- a local provenance check command exists
