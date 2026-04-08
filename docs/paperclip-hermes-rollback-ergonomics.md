# Paperclip ↔ Hermes Rollback Ergonomics

This document describes the first operator-facing ergonomics layer added on top of the initial `file_revert` route.

## New scripts

### Revert candidates

```bash
cd /Users/work/.openclaw/workspace/repo-agentopia
python3 scripts/list_revert_candidates.py
```

Shows recent successful `file_write` runs that can be used as rollback candidates, including:
- task id
- run id
- target path
- previous hash
- new hash
- change preview
- previous bytes
- whether the file existed before
- whether content changed

### Review dashboard

```bash
python3 scripts/review_write_actions.py
```

Now also includes:
- `completed_reverts`

## Paperclip surfacing

Rollback comments are now labeled as:
- `## Hermes Revert Summary`

This makes revert actions distinct from ordinary execution summaries in Paperclip issue history.

## Why this matters

Rollback is now not only possible but easier to:
- discover
- audit
- explain
- surface back into Paperclip
