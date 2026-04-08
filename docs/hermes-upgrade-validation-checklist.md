# Hermes Upgrade Validation Checklist

Run this checklist whenever upstream Hermes or the local Hermes runtime assumptions change.

## Core runtime checks
- Hermes health endpoint responds
- Hermes model listing still works
- Hermes executor `/internal/execute` still accepts valid task envelopes

## Safe-route validation
- `file_analysis` allowed path works
- `file_write` approved path works
- `file_write` blocked path still works
- `file_write` overwrite controls still work
- `repo_write` preview mode still works
- `repo_write` approved apply path still works
- `repo_write` blocked/overwrite-approval path still works

## Durability checks
- result persistence still works
- callback delivery still works
- callback retry and callback inspector still work

## Review and approval checks
- approval linkage survives into result metadata
- write action summary still shows policy/action fields
- approval reconciliation still works

## Acceptance rule
Do not treat a Hermes update as accepted until these checks pass or are explicitly waived with documented reasons.
