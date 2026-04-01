#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

echo "Setting up agentopia..."

if [ -f .env ] && [ ! -f .env.backup ]; then
  cp .env .env.backup
fi

mkdir -p config/paperclip config/hermes memory skills

for f in \
  config/paperclip/paperclip.yml \
  config/hermes/hermes.yml
  do
  if [ ! -f "$f" ]; then
    printf '\n' > "$f"
  fi
done

if [ ! -f docker-compose.yml ]; then
  cat > docker-compose.yml <<'YAML'
services:
  paperclip:
    image: paperclipai/paperclip:latest
    container_name: agentopia-paperclip
    ports:
      - "3100:3100"
    env_file:
      - .env
    volumes:
      - ./config/paperclip:/app/config/paperclip
      - ./config/hermes:/app/config/hermes
    restart: unless-stopped

  hermes:
    image: ghcr.io/hermes-agent/hermes:latest
    container_name: agentopia-hermes
    env_file:
      - .env
    volumes:
      - ./config/hermes:/app/config/hermes
      - ./config/paperclip:/app/config/paperclip
    depends_on:
      - paperclip
    restart: unless-stopped
YAML
fi

echo "Done. Add real config before starting services."
