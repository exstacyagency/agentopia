# Runbook

## Local bootstrap

```bash
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
```

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

## Troubleshooting

- If validation fails, check for missing files or directories.
- If runtime-check fails, it will print exactly which runtime targets are missing for each service and a JSON report.
- If smoke fails, check the compose file for the expected service names and profiles.
- If a config file is blank, rerun `scripts/agentopia setup`.
- If runtime startup fails, confirm the real Paperclip and Hermes images or commands are correct.
