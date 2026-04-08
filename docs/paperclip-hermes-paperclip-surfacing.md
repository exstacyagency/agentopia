# Paperclip ↔ Hermes Paperclip Surfacing Plan

This document describes the Paperclip-visible surfacing path for Hermes execution summaries.

## Implemented step

Agentopia now has:
- a comment-body builder in `paperclip_adapter/comments.py`
- a service helper in `paperclip_adapter/service.py` for posting execution summaries back to Paperclip issues
- a client helper in `paperclip_adapter/http_client.py` for issue comments
- an automatic comment-posting hook in `hermes/app.py` that posts execution summaries when `paperclip_issue_id` is present

## Comment content

Structured issue comments can summarize:
- action label
- action category
- action reason
- operator summary
- policy mode / reason
- run status
- approval id / status when present
- error code / message for blocked actions

The comment heading now varies by review state:
- `## Hermes Execution Summary`
- `## Hermes Preview Summary`
- `## Hermes Blocked Action Summary`
- fallback `## Hermes Review Summary`

## Why comments first

Comments are the lightest first surfacing path that makes the semantic labels visible in the Paperclip UI without requiring immediate Paperclip schema or UI changes.

## Next validation step

Trigger real labeled runs with `paperclip_issue_id` present and confirm these comments appear automatically in the Paperclip issue timeline:
- allowed write summary
- preview summary
- blocked action summary
