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
