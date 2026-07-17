# Codebase Concierge

A chat UI over a Claude Agent SDK agent that answers questions about a target repository.

## Run

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000   # http://localhost:8000
```

Smoke-test the endpoint without the browser:

```bash
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what does this repo do?","conversation_id":"test-1"}'
```

## Architecture

`app/concierge.py::generate_reply` is the seam — the only chat logic in the app, and the
one thing `/api/chat` calls. Keep it that way: the route stays a thin adapter, and swapping
the brain never means touching `app/main.py`.

The agent is read-only by design. There is no human at a permission prompt on a server, so
the toolset is the safety boundary — do not widen `READ_ONLY_TOOLS` to Write/Edit/Bash.

Non-obvious, and worth not relearning the hard way: `allowed_tools` does NOT restrict the
agent. It only auto-approves tools so headless runs don't stall waiting for a prompt. The
restriction is `tools=`. With `allowed_tools` alone the agent still reached for Bash and ran
git itself — verified, not theoretical. Both options are set, and they must stay in sync.

`TARGET_REPO` (env var) is the repo the agent answers questions about; it becomes the
agent's `cwd`.

## Conventions

- Frontend is plain HTML/CSS/JS in `static/index.html`. No framework, no build step.
- `conversation_id` comes from the browser; the server maps it to an SDK `session_id`.
