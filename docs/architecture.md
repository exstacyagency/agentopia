# Architecture

## Overview

This repo is the scaffold for a two-layer agent system:

- **Paperclip** — orchestration, governance, budgets, approvals, and audit trails
- **Hermes** — worker/runtime, skills, memory, and tool execution

The repo should remain business-agnostic until a real use case requires domain logic.

## Ownership boundaries

### Paperclip owns

- org structure
- budgets and approvals
- policy and audit behavior
- deployment orchestration

### Hermes owns

- task execution
- skills and memory
- tool access
- subagent execution

### This repo owns

- config stubs
- bootstrap scripts
- validation helpers
- documentation
- local compose wiring

## Expected flow

1. A task enters the system through Paperclip.
2. Paperclip validates policy, budget, and approval state.
3. Hermes executes the approved work.
4. Results and audit information are recorded back through the stack.

## Current state

The repo currently contains:

- config stubs for Paperclip and Hermes
- setup, validation, doctor, and smoke scripts
- compose wiring placeholders
- contribution and roadmap docs

## What is still missing

- real service integration
- real runtime images or startup commands
- real secret management
- real task routing between Paperclip and Hermes
- deployment and upgrade procedures
