# Paperclip Step 3: HTTP Client

This step replaces the pure plan-building adapter with the first live HTTP client layer for Paperclip.

## Scope

This step adds:
- a Paperclip HTTP client
- a service layer that uses the step-2 adapter plan and performs live API operations
- HTTP-level tests against a fake local Paperclip server

## Supported operations

- create issue
- create approval
- wake agent

## Why this matters

Step 2 proved the mapping.
Step 3 proves the adapter can actually speak to Paperclip's route surface over HTTP.

## Current limitation

This still uses a fake local Paperclip test server in automated tests.
The next step should connect this service layer to a real Paperclip development instance and handle real response shapes, errors, and lookup flows.
