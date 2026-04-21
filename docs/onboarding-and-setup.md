# Onboarding and Setup Instructions

This guide walks a customer or operator through getting the current Agentopia stack running and making the first successful API call.

## Prerequisites

You should have:

- Python 3.9+
- Docker and Docker Compose
- a local checkout of the repo
- an issued client API key for Paperclip

## 1. Clone and enter the repo

```bash
git clone <your-agentopia-repo-url>
cd agentopia
```

## 2. Create a local Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
python -m pip install -e . --no-deps
```

## 3. Create your runtime env file

Start from the tracked template:

```bash
cp env.agentopia.template .env
```

Then set the key runtime values you need for your local stack.

Important variables include:

- `PAPERCLIP_IMAGE`
- `HERMES_IMAGE`
- `PAPERCLIP_URL`
- `PAPERCLIP_CLIENT_API_KEY` or file-based client key config
- `AGENTOPIA_INTERNAL_AUTH_TOKEN`
- `HERMES_MODEL_PROVIDER`
- `HERMES_MODEL`
- `HERMES_API_KEY`

## 4. Run local setup

```bash
./scripts/setup.sh
```

This prepares the local repo environment and supporting runtime pieces.

## 5. Start the stack

```bash
./scripts/start-agentopia-stack.sh
```

Or use the broader entrypoint:

```bash
scripts/agentopia boot
```

## 6. Verify the stack is healthy

Check the Paperclip health endpoint:

```bash
curl http://localhost:3100/health
```

You should receive a response showing whether dependencies are ready.

## 7. Submit your first task

```bash
curl -X POST http://localhost:3100/tasks \
  -H 'Authorization: Bearer tenant-a-key' \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: first-task-001' \
  --data @fixtures/task_request_valid.json
```

Expected result:

- `201 Created`
- JSON task record with an `id`

## 8. Poll task status

```bash
curl http://localhost:3100/tasks/task_123 \
  -H 'Authorization: Bearer tenant-a-key'
```

## 9. Inspect task audit history

```bash
curl http://localhost:3100/tasks/task_123/audit \
  -H 'Authorization: Bearer tenant-a-key'
```

## 10. Cancel a task if needed

```bash
curl -X POST http://localhost:3100/tasks/task_123/cancel \
  -H 'Authorization: Bearer tenant-a-key' \
  -H 'Content-Type: application/json' \
  --data '{"reason":"user requested"}'
```

## Common setup problems

### Health endpoint returns `503`

Usually means one or more dependencies are not configured or not running yet.
Check:

- your `.env`
- local Docker stack status
- internal auth token configuration
- client key file presence if you are using file-based keys

### `401 Unauthorized`

Usually means:

- the client API key is missing
- the key is invalid
- the key is revoked

### `404 task not found`

Usually means:

- the task ID is wrong
- the task was never created
- you are querying the wrong environment

### `403 Forbidden`

Usually means:

- the authenticated tenant does not own that task

## Recommended next reads

After onboarding, use:

- `docs/customer-api-docs.md`
- `docs/public-api-contract.md`
- `docs/runbook.md`
