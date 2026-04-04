# Hermes + Open WebUI Integration

This repo does not attempt to invent a fake native Hermes dashboard anymore.

Instead, it documents and wires the supported browser UI path for Hermes Agent:

- **Hermes Agent** provides an OpenAI-compatible API server
- **Open WebUI** provides the browser UI

## Architecture

- Hermes API server: `http://127.0.0.1:8642/v1`
- Hermes health: `http://127.0.0.1:8642/health`
- Open WebUI: `http://localhost:3000`

## 1. Configure Hermes

Add to `~/.hermes/.env`:

```env
API_SERVER_ENABLED=true
API_SERVER_KEY=your-secret-key
```

## 2. Start Hermes

Run Hermes in its native mode:

```bash
hermes gateway
```

You should see output indicating the API server is listening on `http://127.0.0.1:8642`.

## 3. Start Open WebUI

From this repo root:

```bash
export OPENAI_API_KEY=your-secret-key
./scripts/hermes-openwebui-up.sh
```

Then open:

- `http://localhost:3000`

## 4. Verify connectivity

```bash
curl http://127.0.0.1:8642/health
curl http://127.0.0.1:8642/v1/models
```

Expected:
- `/health` returns a healthy status
- `/v1/models` includes `hermes-agent`

## 5. Open WebUI configuration

If the environment variable path does not auto-populate the backend:

- Log into Open WebUI
- Admin Settings → Connections
- Add OpenAI-compatible connection:
  - URL: `http://host.docker.internal:8642/v1`
  - API key: same value as `API_SERVER_KEY`

## Notes

- This is the supported browser UI path for Hermes.
- The upstream Hermes repo does not appear to ship a Paperclip-style native board/dashboard app.
- Open WebUI is therefore the correct browser surface for Hermes in this stack.
