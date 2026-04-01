# Hermes config

Agent runtime config, skills, memory, and tool wiring belong here.

## Expected files

- `hermes.yml` — runtime, memory, skills, and tool settings

## Notes

- Keep agent behavior and runtime concerns separate from governance.
- Keep secrets in `.env` or a secret store, not in config files.
- Prefer additive changes over rewrites.
