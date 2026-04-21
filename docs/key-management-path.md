# Key Management Path

This document defines the current supported path for issuing, rotating, and revoking customer API keys.

## Current supported path

Agentopia currently supports file-based client key management through:

- `config/paperclip/client_api_keys.json`
- `scripts/manage_client_api_keys.py`

This path is intended for operator-managed customer key issuance today.

## Issue a new key

```bash
./.venv/bin/python scripts/manage_client_api_keys.py issue \
  --registry config/paperclip/client_api_keys.json \
  --key-id tenant-a-primary \
  --tenant-id tenant-a \
  --org-id org-a \
  --client-id client-a
```

This writes a new active key entry and prints the raw key once.

## Revoke a key

```bash
./.venv/bin/python scripts/manage_client_api_keys.py revoke \
  --registry config/paperclip/client_api_keys.json \
  --key-id tenant-a-primary
```

## Rotate a key

```bash
./.venv/bin/python scripts/manage_client_api_keys.py rotate \
  --registry config/paperclip/client_api_keys.json \
  --key-id tenant-a-primary \
  --new-key-id tenant-a-rotated
```

This revokes the old key and adds a new active replacement key.

## Operational notes

- issue keys per tenant/client identity
- deliver raw keys through a secure channel
- treat printed raw keys as sensitive material
- prefer rotation over long-lived static reuse

## Verification

Run:

```bash
./.venv/bin/python scripts/test_manage_client_api_keys.py
```
