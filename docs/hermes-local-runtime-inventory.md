# Hermes Local Runtime Inventory

This document tracks the local/custom Hermes runtime surface used by Agentopia.

## Purpose

Keep the Hermes compatibility surface explicit so upstream Hermes updates do not silently absorb Agentopia-owned behavior.

## Agentopia-owned Hermes files
Core execution behavior currently lives in Agentopia under:
- `hermes/app.py`
- `hermes/executor.py`
- `hermes/policy.py`
- `hermes/file_ops.py`
- `hermes/repo_ops.py`
- `hermes/persistence.py`
- `hermes/callback_store.py`
- `hermes/paperclip_mapping.py`
- `hermes/paperclip_bridge.py`
- `hermes/action_labels.py`

## What this means
These files are not treated as disposable upstream Hermes patches. They are the Agentopia-owned execution layer.

## Upstream Hermes update surface
When upstream Hermes changes, the main update-sensitive areas are:
- runtime startup/config assumptions
- API compatibility and health/model endpoints
- provider/model behavior assumptions
- transport/config values used by the Agentopia bridge

## Rule
Do not move Agentopia-owned behavior from the files above into upstream Hermes just because an upstream update seems close in spirit.
