# Paperclip Step 2: Adapter Skeleton

This step introduces the first real adapter layer between Agentopia's task envelope and Paperclip's native orchestration object model.

## Scope

This is intentionally a skeleton.

It does **not** perform live HTTP requests yet.

It does:
- parse the Agentopia v1 task envelope
- map that envelope into a Paperclip-native plan
- define the three key orchestration outputs:
  - issue creation payload
  - optional approval creation payload
  - execution trigger payload

## Mapping decisions

### Agentopia task
Maps to a normalized internal `AgentopiaTaskEnvelope`.

### Paperclip issue
Represents the canonical work item.

### Paperclip approval
Created only when the task policy says approval is required.

### Execution trigger
Represents the eventual agent wakeup / issue execution trigger that should cause Hermes-backed execution.

## Files

- `paperclip_adapter/models.py`
- `paperclip_adapter/mapping.py`
- `paperclip_adapter/client.py`
- `scripts/test_paperclip_adapter.py`

## Why this matters

Step 1 identified the real Paperclip objects.
Step 2 turns that into code so the next step can add real HTTP calls and persistence against Paperclip.

## Next step

Step 3 should replace the placeholder plan-building behavior with a live Paperclip client that:
- creates or locates issues
- creates approvals when required
- triggers execution via the appropriate Paperclip agent/heartbeat path
- records linkage IDs for downstream Hermes result handling
