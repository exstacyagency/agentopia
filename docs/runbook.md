# Runbook

## Local bootstrap

```bash
cp .env.example .env
./scripts/setup.sh
```

## Validation

```bash
./scripts/validate.sh
./scripts/doctor.sh
./scripts/smoke.sh
```

## Branching

- Create a new branch for each PR.
- Keep each PR focused on one pass.
- Prefer `scaffold-*` or `feature-*` branch names.

## Current limitations

- Compose services are placeholders until the real runtime targets are confirmed.
- Health checks are only stubs until real service probes are available.
- Secrets should live in `.env` or a secret store, never in the repo.
- Business logic is intentionally deferred.

## Troubleshooting

- If validation fails, check for missing files or directories.
- If smoke fails, check the compose file for the expected service names and profiles.
- If a config file is blank, rerun `./scripts/setup.sh`.
- If runtime startup fails, confirm the real Paperclip and Hermes images or commands are correct.
