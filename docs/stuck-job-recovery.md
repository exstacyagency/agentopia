# Stuck Job Recovery

This document defines the current minimal stuck-job recovery baseline for the Paperclip queue.

## Goals

- detect queue items stranded by expired worker leases
- provide an operator-safe reset path back to queued state
- keep recovery actions persisted and audited

## Current model

Paperclip now treats a running queue item as recoverable when:

- it has a `worker_id`
- it has a `lease_expires_at`
- the lease expiry is in the past

## Current behavior

Recovery flow:

1. detect recoverable stuck jobs
2. reset queue ownership fields
3. return the queue item to `queued`
4. update the task state back to `queued`
5. record a recovery audit event

## Current verification

Run:

```bash
./.venv/bin/python scripts/test_stuck_job_recovery.py
```

## Notes

This slice does not yet include:

- automatic background recovery loops
- operator approval workflows for recovery
- dead-lettering after repeated recoveries
