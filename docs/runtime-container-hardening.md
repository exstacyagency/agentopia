# Runtime and Container Hardening

This document defines the minimum runtime and container hardening posture for Agentopia in its current scaffold state.

## Goals

- reduce container privilege by default
- make writable paths explicit
- limit accidental privilege escalation
- keep hardening expectations visible in deployment workflows

## Minimum hardening posture

For runtime services, prefer:

- read-only root filesystems where practical
- explicit writable temp storage
- dropped Linux capabilities
- `no-new-privileges`
- `init: true` for better signal and process handling
- bounded log size to reduce noisy disk growth

## Current compose hardening baseline

The compose runtime should:

- mount config read-only
- use tmpfs for temporary writable paths
- enable `security_opt: ["no-new-privileges:true"]`
- drop all Linux capabilities by default
- set `read_only: true`
- use `init: true`
- define bounded json-file log rotation

## Operational caveat

This is still scaffold-level hardening, not a full production container security posture.

It improves default safety, but does not replace:

- image provenance checks
- secret handling
- network policy
- sandboxing inside Hermes actions
- host-level hardening

## Verification

Review compose config and confirm:

- no unexpected writable host mounts exist
- config mounts are read-only
- log rotation is enabled
- services still pass readiness checks after hardening

## Definition of done for this item

This repo can consider runtime/container hardening minimally defined when:

- hardening expectations are documented
- compose runtime defaults are hardened
- verification steps are documented
