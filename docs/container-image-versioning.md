# Container Image Versioning Strategy

This repo should not treat runtime image references as free-form values.

## Goals

- avoid hidden runtime drift
- make deployments reproducible
- make rollback targets explicit
- prevent accidental use of floating image references in production-like environments

## Allowed image reference policy

### Production
Prefer immutable digests:

```text
ghcr.io/hermes-agent/hermes@sha256:<digest>
paperclipai/paperclip@sha256:<digest>
```

Production should not rely on floating tags.

### Staging and development
Explicit version tags are allowed:

```text
ghcr.io/hermes-agent/hermes:1.4.2
paperclipai/paperclip:2026.04.1
```

Avoid floating tags even outside production when possible.

### Disallowed
Do not use floating references such as:

```text
:latest
:main
:master
:dev
:nightly
```

These values make it difficult to reproduce behavior or roll back safely.

## Repo policy

- `PAPERCLIP_IMAGE` and `HERMES_IMAGE` must use either:
  - an immutable digest reference, or
  - an explicit non-floating tag
- `.env.example` should demonstrate explicit tags, not `latest`
- runtime validation should fail on known floating tags
- production deployments should prefer digest-pinned references

## Validation behavior

The runtime validator should:

- fail if either image is missing
- fail if either image uses a known floating tag
- accept digest references
- accept explicit non-floating tags

## Rollout guidance

1. Use explicit tags in local and staging environments
2. Promote tested images by digest for production
3. Record deployed image refs in release notes or deployment metadata
4. Roll back by reusing the previously known-good digest
