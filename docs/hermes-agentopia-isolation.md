# Isolated Hermes Environment for Agentopia

This setup creates a second Hermes environment on the same machine without interfering with the shared trading-bot Hermes instance.

## Isolated paths

- Hermes home: `~/.hermes-agentopia`
- Env file: `~/.hermes-agentopia/.env`
- API server port: `8742`
- Open WebUI port: `3001`

## Scripts

- `scripts/hermes-agentopia-env.sh`
- `scripts/hermes-agentopia-start.sh`
- `scripts/hermes-agentopia-status.sh`
- `scripts/hermes-agentopia-openwebui-up.sh`
- `scripts/hermes-agentopia-openwebui-down.sh`

## Start isolated Hermes

```bash
cd ~/.openclaw/workspace/repo-agentopia
./scripts/hermes-agentopia-start.sh
```

## Check status

```bash
./scripts/hermes-agentopia-status.sh
```

## Start isolated Open WebUI

```bash
./scripts/hermes-agentopia-openwebui-up.sh
```

Then open `http://localhost:3001`.

## Why this exists

The shared Hermes instance under `~/.hermes` overlaps with trading bot work. This isolated environment avoids stomping on that install by using a separate `HERMES_HOME`, API port, and Open WebUI instance.
