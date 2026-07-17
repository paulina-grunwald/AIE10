import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.concierge import generate_reply

STATIC_DIR = Path(__file__).parent.parent / "static"

# uvicorn leaves the root logger at WARNING; without this the concierge's tool-call
# lines never reach the console.
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
