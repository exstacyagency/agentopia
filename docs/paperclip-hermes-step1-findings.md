# Paperclip ↔ Hermes Step 1 Findings

## Objective

Inspect the real upstream Paperclip API surface and identify the actual object model Agentopia should integrate with.

## Conclusion

Paperclip's execution/orchestration model is not centered on a generic `/tasks` route.

Instead, the relevant integration objects are:

- **Issues** — the canonical work item / operational ticket
- **Approvals** — governance and decision gates
- **Agents** — managed execution actors
- **Heartbeat runs** — the execution-run and lifecycle object

## Why this matters

This changes the next implementation step:

Instead of inventing a fake Paperclip `task` API, Agentopia should adapt its task contract to the real Paperclip object model.

## Proposed canonical mapping

- Agentopia task → Paperclip issue
- approval-needed task → Paperclip approval linked to issue
- Hermes execution → Paperclip heartbeat run / active run on issue
- result/artifacts → issue-linked logs/activity/comments/artifact refs

## Verified source files

Inspected upstream route files:

- `server/src/routes/index.ts`
- `server/src/routes/issues.ts`
- `server/src/routes/approvals.ts`
- `server/src/routes/goals.ts`
- `server/src/routes/agents.ts`

## Verified route families

- company issues / issue detail
- approvals and approval→issue linkage
- agents and agent wakeups
- heartbeat runs, events, and logs
- issue live run / active run views

## Next step after this

Implement a Paperclip adapter that:

1. creates or identifies an issue
2. creates an approval if required
3. triggers Hermes execution through the appropriate agent wakeup path
4. monitors heartbeat run state
5. stores result linkage in a Paperclip-native way
