#!/usr/bin/env bash
set -euo pipefail

PAPERCLIP_DIR="${PAPERCLIP_DIR:-$HOME/.openclaw/workspace/upstream-paperclip}"
PAPERCLIP_BRANCH="${PAPERCLIP_BRANCH:-feature/paperclip-hermes-local-adapter-and-ui-fixes}"

if [ ! -d "$PAPERCLIP_DIR/.git" ]; then
  echo "Paperclip repo not found at $PAPERCLIP_DIR" >&2
  echo "Clone it first: gh repo clone paperclipai/paperclip $PAPERCLIP_DIR" >&2
  exit 1
fi

cd "$PAPERCLIP_DIR"
git fetch origin
if git show-ref --verify --quiet "refs/heads/$PAPERCLIP_BRANCH"; then
  git checkout "$PAPERCLIP_BRANCH"
else
  echo "Local branch $PAPERCLIP_BRANCH not found; trying origin/$PAPERCLIP_BRANCH" >&2
  git checkout -b "$PAPERCLIP_BRANCH" "origin/$PAPERCLIP_BRANCH"
fi
pnpm install

echo "Paperclip dev environment prepared on branch: $PAPERCLIP_BRANCH"
echo "Start with: cd $PAPERCLIP_DIR && pnpm dev"
