# Paperclip ↔ Hermes UI-Facing Dashboard

This document describes the first native Paperclip-facing dashboard layer for Agentopia review semantics.

## Approach

Instead of creating a brand new Paperclip page first, Agentopia now publishes an issue-scoped document snapshot back into Paperclip.

That means the dashboard is visible in the existing Paperclip issue detail UI through the issue documents surface.

## Published document

Key:
- `agentopia-review-dashboard`

Title:
- `Agentopia Review Dashboard`

## Snapshot contents

The document includes:
- action label/category
- operator summary
- action reason
- policy mode / reason
- run status
- decision trace summary
- target paths
- approval context
- error details when present

## Why this path

This keeps the architecture clean:
- Agentopia owns semantics and decision logic
- Paperclip provides the native issue-facing surface
- no large Paperclip UI fork is required for the first dashboard pass

## Next validation step

After restarting Hermes to load the new document-publishing hook:
1. trigger a Paperclip-linked action
2. confirm the issue receives the normal summary comment
3. confirm the issue documents section contains `Agentopia Review Dashboard`
4. inspect the document body for policy and decision-trace content
