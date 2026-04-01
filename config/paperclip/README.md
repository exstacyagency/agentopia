# Paperclip config

Governance, org structure, budgets, approvals, and audit configuration belong here.

## Expected files

- `paperclip.yml` — org, budgets, approvals, and audit defaults

## Notes

- Keep business logic out of this directory.
- Keep secrets in `.env` or a secret store, not in config files.
- Prefer additive changes over rewrites.
