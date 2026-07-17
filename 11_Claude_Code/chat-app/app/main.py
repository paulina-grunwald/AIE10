import json
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.concierge import generate_reply, stream_reply

STATIC_DIR = Path(__file__).parent.parent / "static"

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

app = FastAPI(title="Codebase Concierge")


class ChatRequest(BaseModel):
    message: str
    conversation_id: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    reply = await generate_reply(request.message, request.conversation_id)
    return ChatResponse(reply=reply)


@app.get("/api/chat/stream")
async def chat_stream(
    request: Request, message: str, conversation_id: str
) -> EventSourceResponse:
    """Same turn as POST /api/chat, but narrated.

    EventSource is GET-only, hence the query params rather than a body.
    """

    async def events():
        async for event in stream_reply(message, conversation_id):
            if await request.is_disconnected():
                # Browser closed the tab; stop burning tokens on an answer nobody
                # will read.
                break
            yield {"event": event["type"], "data": json.dumps({"text": event["text"]})}

    return EventSourceResponse(events())
