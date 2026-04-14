# Operator Runbooks for Common Failures

This document defines the minimum operator runbook baseline for Agentopia in its current scaffold state.

## Goals

- make common failure handling faster and less ad hoc
- point operators to the right validation and recovery commands
- connect deploy, rollback, auth, and health workflows into one troubleshooting guide

## Common failure scenarios

### 1. Health endpoint returns unhealthy

Symptoms:
- `/health` returns `503`
- readiness checks fail

Check:
```bash
scripts/agentopia runtime-check
./.venv/bin/python scripts/test_health_checks.py
```

Look for:
- missing internal auth token
- missing Paperclip result URL
- env/config drift

### 2. Internal auth failures

Symptoms:
- internal endpoints return `401`
- Paperclip cannot dispatch to Hermes
- result callbacks fail

Check:
```bash
./.venv/bin/python scripts/test_internal_auth.py
python3 scripts/check-secret-handling.py
```

Look for:
- missing `AGENTOPIA_INTERNAL_AUTH_TOKEN`
- mismatch between service configs
- stale rendered production env file

### 3. Request rejection at the edge

Symptoms:
- HTTP `413`, `429`, or `400`

Check:
```bash
./.venv/bin/python scripts/test_request_limits.py
./.venv/bin/python scripts/test_rate_limits.py
./.venv/bin/python scripts/test_input_validation.py
```

Look for:
- oversized payloads
- repeated requests from one client IP
- control-character input

### 4. Deployment readiness unclear

Check:
```bash
./scripts/deploy-checklist.sh
./scripts/staging-checklist.sh
./scripts/validate-environment-configs.sh
```

Look for:
- invalid environment config
- non-digest production refs
- missing rollback target

### 5. Need to revert a bad rollout

Check:
```bash
./scripts/rollback-checklist.sh
```

Look for:
- known-good previous image refs
- restored config values
- readiness and smoke recovery after rollback

### 6. Security hygiene verification

Check:
```bash
./scripts/run-dependency-scan.sh
python3 scripts/check-provenance.py
python3 scripts/check-secret-handling.py
python3 scripts/check-compose-hardening.py
```

Look for:
- vulnerable dependencies
- non-pinned provenance inputs
- bad secret handling
- compose hardening drift

## Recommended operator flow

When unsure, use this sequence:

```bash
./scripts/bootstrap-venv.sh
scripts/agentopia validate
scripts/agentopia doctor
scripts/agentopia runtime-check
scripts/agentopia status
scripts/agentopia smoke
```

Then move to the scenario-specific checks above.

## Definition of done for this item

This repo can consider operator runbooks minimally defined when:

- common failure scenarios are documented
- each scenario points to concrete validation or recovery commands
- the runbook ties together the existing deployment, rollback, and verification tooling
