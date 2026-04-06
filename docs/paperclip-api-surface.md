# Paperclip API Surface for Hermes Integration

This document captures the actual upstream Paperclip API objects relevant to integrating Hermes.

## Key finding

Paperclip does **not** expose a generic `/tasks` API as its primary orchestration surface.

The upstream server routes indicate that the orchestration model is built around:

- `issues`
- `approvals`
- `agents`
- `heartbeat-runs`
- `goals`
- `projects`

## Most relevant route families

### Issues
Paperclip issues appear to be the closest analogue to executable work items.

Why they matter:
- issues can be assigned
- issues can be linked to active execution runs
- issue pages can surface live runs and active runs

### Approvals
Approvals are first-class objects and are explicitly linked to issues.

Why they matter:
- Paperclip already has a governance object for risky work
- approvals can wake the requesting agent after approval
- approval payloads can carry structured action requests

### Agents
Agents are first-class managed entities.

Why they matter:
- agents can be created, configured, paused, resumed, and woken up
- Paperclip already tracks runtime state, task sessions, and configuration revisions
- agents can expose live heartbeat runs and runtime-state objects

### Heartbeat runs
Heartbeat runs appear to be the actual execution-run abstraction in Paperclip.

Why they matter:
- heartbeat runs have status, events, logs, and workspace operations
- live runs can be queried per company and per issue
- active run linkage is already present in issue state

## Route evidence summary

### Approvals
- `GET /companies/:companyId/approvals`
- `POST /companies/:companyId/approvals`
- `POST /approvals/:id/approve`
- `POST /approvals/:id/reject`
- `GET /approvals/:id/issues`

### Goals
- `GET /companies/:companyId/goals`
- `POST /companies/:companyId/goals`

### Agents
- `GET /companies/:companyId/agents`
- `POST /companies/:companyId/agents`
- `POST /agents/:id/wakeup`
- `GET /companies/:companyId/heartbeat-runs`
- `GET /heartbeat-runs/:runId`
- `GET /heartbeat-runs/:runId/events`
- `GET /heartbeat-runs/:runId/log`
- `GET /issues/:issueId/live-runs`
- `GET /issues/:issueId/active-run`

## Integration implication

Agentopia should not try to force Paperclip into a fake generic `task` abstraction if Paperclip's real model is:

- issue = work item
- approval = governance gate
- heartbeat run = execution run
- agent = execution actor

## Recommended mapping

### Agentopia v1 task request
Map into Paperclip as:
- **Issue** for the work item
- **Approval** if policy requires gating
- **Agent wakeup / heartbeat run** for execution trigger

### Agentopia v1 task result
Map back into Paperclip as:
- heartbeat run status / logs / events
- issue execution linkage
- issue comments, artifacts, or activity log entries

## Immediate next implementation step

Build a Paperclip adapter that targets these real object types:

1. create or identify an issue as the canonical work item
2. create an approval when required
3. wake the appropriate Hermes-connected agent
4. observe heartbeat runs as the execution state
5. persist result/artifact linkage back onto the issue/activity stream
