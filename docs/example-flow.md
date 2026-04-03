# Example Flow

## Purpose

This document shows the intended control flow between Paperclip and Hermes.

## Example task

**Task:** "Summarize the latest repo changes and prepare a short update."

### 1. Inbound request

A request enters Paperclip with:

- task description
- requested urgency
- requester identity
- any required budget or approval context

### 2. Policy check

Paperclip checks:

- whether the request is allowed
- whether a budget is available
- whether the task needs human approval
- whether the work belongs in the current scope

### 3. Dispatch

If the task is approved, Paperclip forwards it to Hermes with:

- task context
- any constraints
- the target runtime or tool permissions
- the required output shape

### 4. Execution

Hermes:

- loads the task
- uses its configured skills/tools
- consults memory if needed
- performs the work
- returns the result

### 5. Audit

Paperclip records:

- what ran
- what was approved
- what was produced
- any follow-up needed

## Request schema

The request contract is now validated in `scripts/contract_runner.py`.

```yaml
task:
  id: task-123
  title: Summarize repo changes
  priority: medium
  requester:
    id: human
    displayName: human
  budget:
    maxCostUsd: 5
    maxRuntimeMinutes: 15
  approval:
    required: false
  constraints:
    outputFormat: markdown
    outputLength: short
    allowNetwork: false
  routing:
    inbound: paperclip
    outbound: hermes
```

## Response schema

The result contract is also validated in `scripts/contract_runner.py`, and the structured output lives in `scripts/output_models.py` with a fixture at `scripts/output_fixture.json`.

```yaml
result:
  taskId: task-123
  status: success
  summary: "Completed task: Summarize repo changes"
  artifacts:
    - README.md
    - docs/example-flow.md
    - artifacts/result.json
    - artifacts/output.json
  audit:
    approvedBy: paperclip
    executedBy: hermes
    runtimeSeconds: 12
```

## Structured output contract

The task runner now builds output from `scripts/output_models.py` and writes it to `artifacts/output.json`.

```yaml
task:
  id: task-123
  title: Summarize repo changes
  priority: medium
handoff:
  from: paperclip
  to: hermes
  policy:
    budgetUsd: 5
    runtimeMinutes: 15
    approvalRequired: false
execution:
  status: success
  summary: "Completed task: Summarize repo changes"
  notes:
    - Validated request contract
    - Validated budget/approval policy
    - Wrote structured output
```

## Why this matters

This repo stays clearer when the boundary between orchestration and execution is explicit.
