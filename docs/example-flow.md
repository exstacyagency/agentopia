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

## Message contract sketch

```yaml
task:
  id: task-123
  title: Summarize repo changes
  priority: medium
  requester: human
  constraints:
    maxRuntimeMinutes: 15
    approvalRequired: false
  output:
    format: markdown
    length: short
```

## Why this matters

This repo stays clearer when the boundary between orchestration and execution is explicit.
