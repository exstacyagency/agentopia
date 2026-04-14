# Runbook

## Local bootstrap

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
cp .env.example .env
scripts/agentopia setup
```

## Validation

```bash
scripts/agentopia validate
scripts/agentopia doctor
scripts/agentopia runtime-check
scripts/agentopia status
scripts/agentopia smoke
PYTHONPATH=. python3 scripts/test_contract_schemas.py
PYTHONPATH=. python3 scripts/test_paperclip_service.py
PYTHONPATH=. python3 scripts/test_hermes_executor.py
PYTHONPATH=. python3 scripts/test_integration_flow.py
```

## CI validation

GitHub Actions runs the same clean-environment validation suite on pushes and pull requests using a fresh virtualenv, pinned installs from `requirements.lock`, and an editable install from `pyproject.toml`.

## Release and promotion

Use `docs/release-promotion-criteria.md` as the minimum gate for moving changes from merged code to staging-like validation and then toward production-like rollout.

## Deployment process

Use `docs/deployment-process.md` for the repeatable deployment flow. Run `scripts/deploy-checklist.sh` before considering a deployment ready to execute.

## Environment config validation

Run `scripts/validate-environment-configs.sh` to validate the tracked development, staging, and production config templates.

## Staging environment

Use `docs/staging-environment.md` for the staging definition and run `scripts/staging-checklist.sh` before treating staging as ready.

## Production secret injection

Use `docs/production-secret-injection.md` for the secret injection path. Run `scripts/render-production-env.sh` after preparing the untracked production secrets file and before deployment.

## Secret storage and handling

Use `docs/secret-storage-handling.md` for the current handling baseline and run `python3 scripts/check-secret-handling.py` to verify repo-level secret handling rules.

## Service-to-service authentication

Use `docs/service-to-service-auth.md` for the internal auth baseline and run `./.venv/bin/python scripts/test_internal_auth.py` to verify protected internal endpoints reject unauthenticated requests.

## Runtime and container hardening

Use `docs/runtime-container-hardening.md` for the hardening baseline and run `python3 scripts/check-compose-hardening.py` after compose changes.

## Dependency and vulnerability scanning

Use `docs/dependency-vulnerability-scanning.md` for the scan policy and run `scripts/run-dependency-scan.sh` to audit pinned dependencies.

## Image and dependency provenance

Use `docs/image-dependency-provenance.md` for provenance expectations and run `python3 scripts/check-provenance.py` to verify the current baseline.

## Artifact access and redaction

Use `docs/artifact-access-redaction.md` for the current artifact handling baseline and run `./.venv/bin/python scripts/test_persistence_redaction.py` to verify redaction behavior.

## Request size limits

Use `docs/request-size-limits.md` for the current policy and run `./.venv/bin/python scripts/test_request_limits.py` to verify oversized requests are rejected.

## Input validation and sanitization

Use `docs/input-validation-sanitization.md` for the current baseline and run `./.venv/bin/python scripts/test_input_validation.py` to verify unsafe control-character payloads are rejected.

## Rate limiting and abuse protection

Use `docs/rate-limiting-abuse-protection.md` for the current baseline and run `./.venv/bin/python scripts/test_rate_limits.py` to verify repeated requests are limited.

## Audit logging

Use `docs/audit-logging.md` for the audit baseline and run `./.venv/bin/python scripts/test_audit_logging.py` to verify Paperclip and Hermes audit behavior.

## Rollback process

Use `docs/rollback-process.md` for the rollback path. Run `scripts/rollback-checklist.sh` after restoring the previous known-good image refs and config.

## Workflow commands

- `scripts/agentopia boot` — full repo workflow
- `scripts/agentopia demo` — alias for `boot`
- `scripts/agentopia sample-task` — generate the default task artifact
- `scripts/agentopia sample-task-budget` — generate the budget gate task artifact
- `scripts/agentopia task-run` — run the task runner directly
- `scripts/agentopia contract-demo` — run the contract demo
- `scripts/agentopia test-contract` — run the contract validation check
- `scripts/agentopia template-check` — verify template selection behavior
- `scripts/agentopia runtime-check` — validate runtime env targets and print a JSON status report
- `scripts/agentopia status` — quick runtime readiness check
- `scripts/agentopia start` — print a status report, then run the boot flow if readiness is OK

## Branching

- Create a new branch for each PR.
- Keep each PR focused on one pass.
- Prefer `scaffold-*` or `feature-*` branch names.

## Current limitations

- Compose services rely on `.env` runtime targets.
- Health checks are only stubs until real service probes are available.
- Secrets should live in `.env` or a secret store, never in the repo.
- Business logic is intentionally deferred.

## Concrete runtime targets

Set these values in `.env` before trying to boot the runtime stack:

- `PAPERCLIP_IMAGE`
- `HERMES_IMAGE`
- `PAPERCLIP_URL`
- `PAPERCLIP_API_KEY`
- `HERMES_MODEL_PROVIDER`
- `HERMES_MODEL`
- `HERMES_API_KEY`

For runtime images, use explicit version tags or immutable digests. Do not use floating tags like `latest`, `main`, `master`, `dev`, or `nightly`.

See `docs/container-image-versioning.md`.

## Troubleshooting

- If validation fails, check for missing files or directories.
- If runtime-check fails, it will print exactly which runtime targets are missing for each service, any invalid image refs, and a JSON report.
- If smoke fails, check the compose file for the expected service names and profiles.
- If a config file is blank, rerun `scripts/agentopia setup`.
- If runtime startup fails, confirm the real Paperclip and Hermes images or commands are correct.
- If promotion readiness is unclear, review `docs/release-promotion-criteria.md` and verify the image refs, validation output, and rollback target are recorded.
- If deployment readiness is unclear, run `scripts/deploy-checklist.sh` and review `docs/deployment-process.md`.
- If environment config readiness is unclear, run `scripts/validate-environment-configs.sh`.
- If staging readiness is unclear, run `scripts/staging-checklist.sh` and review `docs/staging-environment.md`.
- If production secret injection readiness is unclear, review `docs/production-secret-injection.md` and run `scripts/render-production-env.sh`.
- If secret handling readiness is unclear, review `docs/secret-storage-handling.md` and run `python3 scripts/check-secret-handling.py`.
- If service-to-service auth readiness is unclear, review `docs/service-to-service-auth.md` and run `./.venv/bin/python scripts/test_internal_auth.py`.
- If runtime/container hardening readiness is unclear, review `docs/runtime-container-hardening.md` and run `python3 scripts/check-compose-hardening.py`.
- If dependency scan readiness is unclear, review `docs/dependency-vulnerability-scanning.md` and run `scripts/run-dependency-scan.sh`.
- If provenance readiness is unclear, review `docs/image-dependency-provenance.md` and run `python3 scripts/check-provenance.py`.
- If artifact handling readiness is unclear, review `docs/artifact-access-redaction.md` and run `./.venv/bin/python scripts/test_persistence_redaction.py`.
- If request limit readiness is unclear, review `docs/request-size-limits.md` and run `./.venv/bin/python scripts/test_request_limits.py`.
- If input validation readiness is unclear, review `docs/input-validation-sanitization.md` and run `./.venv/bin/python scripts/test_input_validation.py`.
- If rate-limiting readiness is unclear, review `docs/rate-limiting-abuse-protection.md` and run `./.venv/bin/python scripts/test_rate_limits.py`.
- If audit logging readiness is unclear, review `docs/audit-logging.md` and run `./.venv/bin/python scripts/test_audit_logging.py`.
- If rollback readiness is unclear, run `scripts/rollback-checklist.sh` and review `docs/rollback-process.md`.
