#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Setting up agentopia..."

if [ -f .env ] && [ ! -f .env.backup ]; then
  cp .env .env.backup
fi

mkdir -p config/paperclip config/hermes memory skills artifacts

for f in config/paperclip/paperclip.yml config/hermes/hermes.yml; do
  if [ ! -f "$f" ]; then
    printf '\n' > "$f"
  fi
done

if [ ! -f docker-compose.yml ]; then
  cat > docker-compose.yml <<'YAML'
services:
  paperclip:
    image: ${PAPERCLIP_IMAGE}
    container_name: agentopia-paperclip
    ports:
      - "3100:3100"
    env_file:
      - .env
    volumes:
      - ./config/paperclip:/app/config/paperclip
      - ./config/hermes:/app/config/hermes
    healthcheck:
      test: ["CMD-SHELL", "test -n \"$PAPERCLIP_URL\" && test -n \"$PAPERCLIP_API_KEY\" || true"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    profiles:
      - runtime

  hermes:
    image: ${HERMES_IMAGE}
    container_name: agentopia-hermes
    env_file:
      - .env
    volumes:
      - ./config/hermes:/app/config/hermes
      - ./config/paperclip:/app/config/paperclip
    depends_on:
      paperclip:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "test -n \"$HERMES_MODEL_PROVIDER\" && test -n \"$HERMES_MODEL\" && test -n \"$HERMES_API_KEY\" || true"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped
    profiles:
      - runtime
YAML
fi

echo "Done. Add real config before starting services."
