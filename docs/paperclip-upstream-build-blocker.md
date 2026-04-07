# Upstream Paperclip Build Blocker

## Observed problem

Starting the upstream Paperclip dev server currently fails locally.

Initial command used:

```bash
cd /Users/work/.openclaw/workspace/upstream-paperclip
pnpm dev
```

This surfaced TypeScript build failures, but the root install-time blocker was confirmed with:

```bash
cd /Users/work/.openclaw/workspace/upstream-paperclip
pnpm install
```

## Confirmed blocker

A direct dependency of the server cannot be fetched:

```text
ERR_PNPM_FETCH_404: GET https://registry.npmjs.org/hermes-seiko-adapter: Not Found - 404
```

This leaves the workspace in a broken install state and explains the downstream build failures.

## Secondary observed symptom

TypeScript build failures in plugin SDK code referencing:

```text
Cannot find module '@seikoai/shared' or its corresponding type declarations.
```

Those appear downstream of the broken install / package graph.

## Why this blocks integration

The Agentopia Paperclip adapter can only perform true live integration once the upstream Paperclip server is running.

Until then:
- step 1 is complete
- step 2 is complete
- step 3 is complete
- step 4 is blocked on upstream Paperclip dev startup

## Recommended next action

Fix the upstream Paperclip local build so `/api/health` becomes reachable, then rerun the live integration probe.
