# Agentopia Local Stack

This document makes Agentopia the operational source of truth for booting the local Paperclip + Hermes stack.

## Components

### Paperclip
- upstream repo: `paperclipai/paperclip`
- local checkout (default): `~/.openclaw/workspace/upstream-paperclip`
- currently requires a local fix branch for the Hermes adapter/UI work until that is merged upstream

### Hermes
- isolated Agentopia home: `~/.hermes-agentopia`
- API server port: `8742`
- Open WebUI port: `3001`

## Helper scripts

- `scripts/bootstrap-paperclip-dev.sh`
- `scripts/start-agentopia-stack.sh`
- `scripts/hermes-agentopia-start.sh`
- `scripts/hermes-agentopia-openwebui-up.sh`

## Bootstrap Paperclip

```bash
cd ~/.openclaw/workspace/repo-agentopia
./scripts/bootstrap-paperclip-dev.sh
```

## Start the stack

```bash
cd ~/.openclaw/workspace/repo-agentopia
./scripts/start-agentopia-stack.sh
```

Then follow the printed per-terminal instructions.

## Current dependency note

Until the Paperclip fix branch merges upstream, Agentopia local development depends on that patched Paperclip checkout.
