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
./scripts/validate-suite.sh core
./scripts/validate-suite.sh full
```

Use `core` for the default fast path and `full` for broad regression coverage.

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

## Client API authentication

Use `docs/client-api-authentication.md` for the client auth baseline and run `./.venv/bin/python scripts/test_client_api_auth.py` to verify client-facing task submission rejects unauthenticated requests.

## Scoped API keys

Use `docs/scoped-api-keys.md` for the scoped key baseline and run `./.venv/bin/python scripts/test_scoped_api_keys.py` to verify scope-aware client key enforcement.

## API key rotation and revocation

Use `docs/api-key-rotation-revocation.md` for the key lifecycle baseline and run `./.venv/bin/python scripts/test_api_key_rotation_revocation.py` to verify active-key rotation windows and revoked-key rejection.

## Role-based permissions

Use `docs/role-based-permissions.md` for the permission baseline and run `./.venv/bin/python scripts/test_role_permissions.py` to verify role-to-scope enforcement for client API keys.

## Client, org, and tenant isolation

Use `docs/tenant-isolation.md` for the current isolation baseline and run `./.venv/bin/python scripts/test_tenant_isolation.py` to verify cross-tenant task access is rejected.

## Durable queue

Use `docs/durable-queue.md` for the current queue baseline and run `./.venv/bin/python scripts/test_durable_queue.py` to verify queue persistence and inspection.

## Retries with backoff

Use `docs/retries-backoff.md` for the current retry baseline and run `./.venv/bin/python scripts/test_retries_backoff.py` to verify failed dispatches stay queued and reschedule the next attempt.

## Worker claiming and leasing

Use `docs/worker-claiming-leasing.md` for the current leasing baseline and run `./.venv/bin/python scripts/test_worker_leasing.py` to verify active claims block other workers until the lease expires.

## Idempotent task submission

Use `docs/idempotent-task-submission.md` for the current submission baseline and run `./.venv/bin/python scripts/test_idempotent_task_submission.py` to verify repeated submits with the same key do not create duplicate work.

## Idempotent result handling

Use `docs/idempotent-result-handling.md` for the current callback baseline and run `./.venv/bin/python scripts/test_idempotent_result_handling.py` to verify repeated result callbacks do not replay completion handling.

## Stuck job recovery

Use `docs/stuck-job-recovery.md` for the current recovery baseline and run `./.venv/bin/python scripts/test_stuck_job_recovery.py` to verify expired running leases can be reset to queued work.

## Dead-letter handling

Use `docs/dead-letter-handling.md` for the current terminal-failure baseline and run `./.venv/bin/python scripts/test_dead_letter_handling.py` to verify permanently failing queue items move into dead-letter state.

## Migrations

Use `docs/migrations.md` for the current schema migration baseline and run `./.venv/bin/python scripts/test_migrations.py` to verify ordered migration application and version tracking.

## Hermes executor dispatch boundary

Use `docs/hermes-executor-dispatch-boundary.md` for the current executor refactor baseline and run `./.venv/bin/python scripts/test_hermes_dispatch_boundary.py` plus `./.venv/bin/python scripts/test_hermes_executor.py` to verify the internal dispatch map while preserving the v1 result envelope.

## Hermes command runner boundary

Use `docs/sandbox-execution-runner.md` for the current deny-by-default command baseline and run `./.venv/bin/python scripts/test_hermes_runner_boundary.py` plus `./.venv/bin/python scripts/test_hermes_executor.py` to verify `shell_command` is denied by default unless an explicit runner is injected.

## Strict write boundaries

Use `docs/strict-write-boundaries.md` for the current workspace write-boundary baseline and run `./.venv/bin/python scripts/test_strict_write_boundaries.py` to verify path escapes are rejected before mutation helpers run.

## Per-tool permissions

Use `docs/per-tool-permissions.md` for the current permission baseline and run `./.venv/bin/python scripts/test_tool_permissions.py` to verify Hermes rejects task types whose required tool class is not allowed by policy.

## Resource and time limits

Use `docs/resource-time-limits.md` for the current execution-limit baseline and run `./.venv/bin/python scripts/test_execution_limits.py` to verify runner-backed shell commands fail when they exceed the configured runtime budget.

## Network egress controls

Use `docs/network-egress-controls.md` for the current network policy baseline and run `./.venv/bin/python scripts/test_network_egress_controls.py` to verify network-oriented shell commands are rejected when `allow_network` is false.

## Sandbox adapter

Use `docs/sandbox-adapter.md` for the current OS-level sandbox baseline and run `./.venv/bin/python scripts/test_sandbox_adapter.py` to verify sandboxed command execution can run through the OS sandbox while network access remains blocked.

## Safer shell execution layer

Use `docs/safer-shell-execution-layer.md` for the current shell-safety baseline and run `./.venv/bin/python scripts/test_shell_safety.py` to verify unsafe shell syntax and disallowed executables are rejected before runner execution.

## Resource and time limits

Use `docs/resource-time-limits.md` for the current Hermes execution-limit baseline and run `./.venv/bin/python scripts/test_execution_limits.py` to verify runtime enforcement now applies beyond the shell runner and that oversized execution payloads are rejected.

## Network egress controls

Use `docs/network-egress-controls.md` for the current Hermes network-control baseline and run `./.venv/bin/python scripts/test_network_egress_controls.py` to verify policy-level denial and macOS sandbox-profile network rules.

## Cancellation support

Use `docs/cancellation-support.md` for the current control-plane cancellation baseline and run `./.venv/bin/python scripts/test_cancellation_support.py` to verify queued or running tasks can be cancelled durably and that late results are ignored.

## Tenant-scoped memory boundaries

Use `docs/tenant-scoped-memory-boundaries.md` for the current memory-surface inventory and tenant-boundary contract before attempting enforcement work.

## Memory provenance

Use `docs/memory-provenance.md` for the current provenance baseline and run `./.venv/bin/python scripts/test_memory_provenance.py` to verify memory contribution is summarized into Paperclip audit surfaces.

## MemPalace fallback behavior

Use `docs/mempalace-fallback.md` for the current fallback baseline and run `./.venv/bin/python scripts/test_memory_fallback.py` to verify Hermes continues with native-only memory context when MemPalace is unavailable.

## Public API contract

Use `docs/public-api-contract.md` for the stable v1 Paperclip public endpoint contract and run `./.venv/bin/python scripts/test_public_api_contract.py` to verify submit, fetch, audit, and tenant-isolation behavior at the HTTP layer.

## Postgres persistence

Use `docs/postgres-persistence.md` for the current production DB baseline and run `./.venv/bin/python scripts/test_postgres_persistence.py` to verify Postgres backend selection through `PAPERCLIP_DATABASE_URL`.

## Transactional state updates

Use `docs/transactional-state-updates.md` for the current transactional baseline and run `./.venv/bin/python scripts/test_transactional_state_updates.py` to verify transactional rollback for coupled state/audit writes.

## Backup and restore plan

Use `docs/backup-restore-plan.md` for the current backup baseline and run `./scripts/backup-restore-checklist.sh` plus `./.venv/bin/python scripts/test_backup_restore_checklist.py` to verify backend-aware backup/restore checks.

## Durable storage layout

Use `docs/durable-storage-layout.md` for the current storage baseline and run `./.venv/bin/python scripts/test_durable_storage_layout.py` to verify task result files and artifact directories are materialized on disk.

## Retention and deletion workflows

Use `docs/retention-deletion-workflows.md` for the current cleanup baseline and run `./.venv/bin/python scripts/test_retention_deletion_workflows.py` to verify terminal tasks can be listed for retention and fully deleted from DB plus durable storage.

## Approval reconciliation

Use `docs/approval-reconciliation.md` for the current approval consistency baseline and run `./.venv/bin/python scripts/test_approval_reconciliation.py` to verify mismatch detection.

## Approval expiration

Use `docs/approval-expiration.md` for the stale-approval baseline and run `./.venv/bin/python scripts/test_approval_expiration.py` to verify expiration detection.

## Approval audit trail

Use `docs/approval-audit-trail.md` for the approval audit baseline and run `./.venv/bin/python scripts/test_approval_audit_trail.py` to verify approval-specific event recording.

## Approval recovery tools

Use `docs/approval-recovery-tools.md` for the stuck-approval recovery baseline and run `./.venv/bin/python scripts/test_approval_recovery.py` to verify recovery behavior.

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

## Structured logging

Use `docs/structured-logging.md` for the service logging baseline and run `./.venv/bin/python scripts/test_structured_logging.py` to verify JSON log output.

## Correlation IDs

Use `docs/correlation-ids.md` for the current correlation baseline and run `./.venv/bin/python scripts/test_correlation_ids.py` to verify propagation and response headers.

## Dependency-aware health checks

Use `docs/dependency-aware-health-checks.md` for the current health baseline and run `./.venv/bin/python scripts/test_health_checks.py` to verify healthy and unhealthy dependency states.

## Operator runbooks

Use `docs/operator-runbooks.md` for the common failure runbook baseline.

## Metrics

Use `docs/metrics.md` for the current metrics baseline and run `./.venv/bin/python scripts/test_metrics.py` to verify the metrics endpoints.

## Alerts

Use `docs/alerts.md` for the current alerting baseline and run `./.venv/bin/python scripts/test_alerts.py` to verify local alert evaluation behavior.

## Tracing and request/run visibility

Use `docs/tracing-visibility.md` for the current trace visibility baseline and run `./.venv/bin/python scripts/test_tracing_visibility.py` to verify per-trace logs.

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
- If client API auth readiness is unclear, review `docs/client-api-authentication.md` and run `./.venv/bin/python scripts/test_client_api_auth.py`.
- If scoped API key readiness is unclear, review `docs/scoped-api-keys.md` and run `./.venv/bin/python scripts/test_scoped_api_keys.py`.
- If API key rotation or revocation readiness is unclear, review `docs/api-key-rotation-revocation.md` and run `./.venv/bin/python scripts/test_api_key_rotation_revocation.py`.
- If role-based permission readiness is unclear, review `docs/role-based-permissions.md` and run `./.venv/bin/python scripts/test_role_permissions.py`.
- If tenant isolation readiness is unclear, review `docs/tenant-isolation.md` and run `./.venv/bin/python scripts/test_tenant_isolation.py`.
- If durable queue readiness is unclear, review `docs/durable-queue.md` and run `./.venv/bin/python scripts/test_durable_queue.py`.
- If retry readiness is unclear, review `docs/retries-backoff.md` and run `./.venv/bin/python scripts/test_retries_backoff.py`.
- If worker lease readiness is unclear, review `docs/worker-claiming-leasing.md` and run `./.venv/bin/python scripts/test_worker_leasing.py`.
- If idempotent submission readiness is unclear, review `docs/idempotent-task-submission.md` and run `./.venv/bin/python scripts/test_idempotent_task_submission.py`.
- If idempotent result readiness is unclear, review `docs/idempotent-result-handling.md` and run `./.venv/bin/python scripts/test_idempotent_result_handling.py`.
- If stuck-job recovery readiness is unclear, review `docs/stuck-job-recovery.md` and run `./.venv/bin/python scripts/test_stuck_job_recovery.py`.
- If dead-letter readiness is unclear, review `docs/dead-letter-handling.md` and run `./.venv/bin/python scripts/test_dead_letter_handling.py`.
- If migration readiness is unclear, review `docs/migrations.md` and run `./.venv/bin/python scripts/test_migrations.py`.
- If Hermes executor-boundary readiness is unclear, review `docs/hermes-executor-dispatch-boundary.md` and run `./.venv/bin/python scripts/test_hermes_dispatch_boundary.py` plus `./.venv/bin/python scripts/test_hermes_executor.py`.
- If Hermes command-runner readiness is unclear, review `docs/sandbox-execution-runner.md` and run `./.venv/bin/python scripts/test_hermes_runner_boundary.py` plus `./.venv/bin/python scripts/test_hermes_executor.py`.
- If strict write-boundary readiness is unclear, review `docs/strict-write-boundaries.md` and run `./.venv/bin/python scripts/test_strict_write_boundaries.py`.
- If per-tool permission readiness is unclear, review `docs/per-tool-permissions.md` and run `./.venv/bin/python scripts/test_tool_permissions.py`.
- If resource/time-limit readiness is unclear, review `docs/resource-time-limits.md` and run `./.venv/bin/python scripts/test_execution_limits.py`.
- If network-egress readiness is unclear, review `docs/network-egress-controls.md` and run `./.venv/bin/python scripts/test_network_egress_controls.py`.
- If sandbox-adapter readiness is unclear, review `docs/sandbox-adapter.md` and run `./.venv/bin/python scripts/test_sandbox_adapter.py`.
- If shell-safety readiness is unclear, review `docs/safer-shell-execution-layer.md` and run `./.venv/bin/python scripts/test_shell_safety.py`.
- If resource-limit readiness is unclear, review `docs/resource-time-limits.md` and run `./.venv/bin/python scripts/test_execution_limits.py`.
- If network-egress readiness is unclear, review `docs/network-egress-controls.md` and run `./.venv/bin/python scripts/test_network_egress_controls.py`.
- If cancellation readiness is unclear, review `docs/cancellation-support.md` and run `./.venv/bin/python scripts/test_cancellation_support.py`.
- If tenant-memory-boundary readiness is unclear, review `docs/tenant-scoped-memory-boundaries.md` and inspect `hermes/app.py` plus `hermes/memory/service.py`.
- If memory-provenance readiness is unclear, review `docs/memory-provenance.md` and run `./.venv/bin/python scripts/test_memory_provenance.py`.
- If mempalace fallback readiness is unclear, review `docs/mempalace-fallback.md` and run `./.venv/bin/python scripts/test_memory_fallback.py`.
- If public-API-contract readiness is unclear, review `docs/public-api-contract.md` and run `./.venv/bin/python scripts/test_public_api_contract.py`.
- If Postgres persistence readiness is unclear, review `docs/postgres-persistence.md` and run `./.venv/bin/python scripts/test_postgres_persistence.py`.
- If transactional state readiness is unclear, review `docs/transactional-state-updates.md` and run `./.venv/bin/python scripts/test_transactional_state_updates.py`.
- If backup/restore readiness is unclear, review `docs/backup-restore-plan.md`, run `./scripts/backup-restore-checklist.sh`, and run `./.venv/bin/python scripts/test_backup_restore_checklist.py`.
- If durable storage readiness is unclear, review `docs/durable-storage-layout.md` and run `./.venv/bin/python scripts/test_durable_storage_layout.py`.
- If retention/deletion readiness is unclear, review `docs/retention-deletion-workflows.md` and run `./.venv/bin/python scripts/test_retention_deletion_workflows.py`.
- If approval reconciliation readiness is unclear, review `docs/approval-reconciliation.md` and run `./.venv/bin/python scripts/test_approval_reconciliation.py`.
- If approval expiration readiness is unclear, review `docs/approval-expiration.md` and run `./.venv/bin/python scripts/test_approval_expiration.py`.
- If approval audit readiness is unclear, review `docs/approval-audit-trail.md` and run `./.venv/bin/python scripts/test_approval_audit_trail.py`.
- If stuck approval recovery readiness is unclear, review `docs/approval-recovery-tools.md` and run `./.venv/bin/python scripts/test_approval_recovery.py`.
- If runtime/container hardening readiness is unclear, review `docs/runtime-container-hardening.md` and run `python3 scripts/check-compose-hardening.py`.
- If dependency scan readiness is unclear, review `docs/dependency-vulnerability-scanning.md` and run `scripts/run-dependency-scan.sh`.
- If provenance readiness is unclear, review `docs/image-dependency-provenance.md` and run `python3 scripts/check-provenance.py`.
- If artifact handling readiness is unclear, review `docs/artifact-access-redaction.md` and run `./.venv/bin/python scripts/test_persistence_redaction.py`.
- If request limit readiness is unclear, review `docs/request-size-limits.md` and run `./.venv/bin/python scripts/test_request_limits.py`.
- If input validation readiness is unclear, review `docs/input-validation-sanitization.md` and run `./.venv/bin/python scripts/test_input_validation.py`.
- If rate-limiting readiness is unclear, review `docs/rate-limiting-abuse-protection.md` and run `./.venv/bin/python scripts/test_rate_limits.py`.
- If audit logging readiness is unclear, review `docs/audit-logging.md` and run `./.venv/bin/python scripts/test_audit_logging.py`.
- If structured logging readiness is unclear, review `docs/structured-logging.md` and run `./.venv/bin/python scripts/test_structured_logging.py`.
- If correlation ID readiness is unclear, review `docs/correlation-ids.md` and run `./.venv/bin/python scripts/test_correlation_ids.py`.
- If dependency-aware health readiness is unclear, review `docs/dependency-aware-health-checks.md` and run `./.venv/bin/python scripts/test_health_checks.py`.
- If operator guidance is unclear, review `docs/operator-runbooks.md` and follow the matching failure scenario.
- If metrics readiness is unclear, review `docs/metrics.md` and run `./.venv/bin/python scripts/test_metrics.py`.
- If alerting readiness is unclear, review `docs/alerts.md` and run `./.venv/bin/python scripts/test_alerts.py`.
- If tracing visibility is unclear, review `docs/tracing-visibility.md` and run `./.venv/bin/python scripts/test_tracing_visibility.py`.
- If rollback readiness is unclear, run `scripts/rollback-checklist.sh` and review `docs/rollback-process.md`.
