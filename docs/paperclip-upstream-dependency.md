# Paperclip Upstream Dependency for Agentopia

Agentopia currently depends on a locally bootable Paperclip development instance.

## Current upstream issue

The public upstream `paperclipai/paperclip` repo does not currently boot cleanly in this environment without a local Hermes adapter workspace package and several frontend fixes.

Those upstream fixes were prepared separately in:

- `paperclipai/paperclip` PR #90

## Why this matters

Agentopia step 4+ integration work requires a live Paperclip instance so the Agentopia adapter can exercise real issue / approval / agent wakeup flows.

## Current operational recommendation

For local Agentopia development:

1. Use the upstream Paperclip repo checkout
2. Apply or checkout the Paperclip fix branch/PR
3. Run Paperclip locally
4. Use Agentopia to integrate against that running instance

## Local dependency summary

Agentopia is the integration/orchestration glue repo.
Paperclip remains the upstream control-plane repo.

Until the relevant Paperclip fixes land upstream, Agentopia local development depends on that patched Paperclip checkout.
