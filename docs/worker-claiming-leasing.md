# Worker Claiming and Leasing

This document defines the current minimal worker claiming and leasing baseline for the Paperclip queue.

## Goals

- ensure only one worker owns a queued task at a time
- allow expired worker claims to be reclaimed
- keep claim ownership persisted in the queue record

## Current model

Queue items now track:

- `worker_id`
- `lease_expires_at`

A worker can claim a queued task when:

- the queue item is unclaimed, or
- the prior lease has expired

## Current behavior

When a worker claims a task:

- Paperclip records the `worker_id`
- Paperclip records `lease_expires_at`
- only that worker may dispatch the task while the lease is active

If the lease expires:

- another worker may reclaim the task

## Current config

- `PAPERCLIP_QUEUE_LEASE_SECONDS`

Default:

- `60` seconds

## Verification

Run:

```bash
./.venv/bin/python scripts/test_worker_leasing.py
```

## Notes

This slice does not yet include:

- lease heartbeats/renewal
- worker liveness checks beyond lease expiry
- multi-item batch claiming
