# Codebase Concierge

A chat web app whose backend is a Claude Agent SDK agent. Point it at a repository, ask
questions in the browser, and the agent reads the code to answer.

Built for Session 11 of the AI Engineering Certification.

## Setup

```bash
uv sync
export ANTHROPIC_API_KEY="sk-ant-..."      # required once the agent is wired in
export TARGET_REPO="/absolute/path/to/repo" # the repo the concierge answers about
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 and ask something like "what does this repo do?".

## API

`POST /api/chat`

```json
{"message": "what does this repo do?", "conversation_id": "abc-123"}
```

```json
{"reply": "..."}
```

Send the same `conversation_id` across messages to continue a conversation — the server
maps it to a persistent agent session so follow-ups keep context.

## Layout

```text
app/main.py        FastAPI routes — thin adapter over the concierge
app/concierge.py   the chat brain: generate_reply()
static/index.html  the whole frontend
```
