"""Model utilities for constructing chat and embedding clients.

Centralizes model wiring so graphs and the RAG pipeline import a single helper
instead of repeating provider-specific configuration.

Backend is selected by the ``LLM_BACKEND`` env var:
  fireworks (default) -> hosted Fireworks AI
  ollama              -> fully local: chat and embeddings both served by Ollama
See advanced_build/README.md for how to start the local server.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"

# Local backend configuration (used when LLM_BACKEND=ollama). Ollama serves both
# the chat model and the embedding model locally.
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "qwen2.5:3b")
OLLAMA_EMBEDDING_MODEL = os.environ.get("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


def _backend() -> str:
    return os.environ.get("LLM_BACKEND", "fireworks").lower()


def get_chat_model(model_name: str | None = None, *, temperature: float = 0) -> Any:
    """Return a chat client for the selected backend (Fireworks or local Ollama)."""
    if _backend() == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model_name or OLLAMA_CHAT_MODEL,
            temperature=temperature,
            base_url=OLLAMA_BASE_URL,
        )
    name = (
        model_name
        or os.environ.get("FIREWORKS_CHAT_MODEL")
        or "accounts/fireworks/models/gpt-oss-20b"
    )
    return ChatOpenAI(
        model=name,
        temperature=temperature,
        openai_api_key=os.environ["FIREWORKS_API_KEY"],
        openai_api_base=FIREWORKS_BASE_URL,
    )


def get_embeddings() -> Any:
    """Return an embedding client for the selected backend.

    fireworks -> Fireworks qwen3-embedding (4096 dims)
    ollama    -> local Ollama embeddings (no torch download, no dimensions param)
    """
    if _backend() == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

    from langchain_openai.embeddings import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=os.environ.get("FIREWORKS_EMBEDDING_MODEL")
        or "accounts/fireworks/models/qwen3-embedding-8b",
        openai_api_key=os.environ["FIREWORKS_API_KEY"],
        openai_api_base=FIREWORKS_BASE_URL,
        check_embedding_ctx_length=False,
        dimensions=4096,
    )


def fix_tool_calls(response: AIMessage) -> AIMessage:
    """Fix invalid tool calls caused by models appending extra tokens like <|call|>."""
    if not response.invalid_tool_calls:
        return response

    fixed = list(response.tool_calls)
    remaining_invalid = []

    for tc in response.invalid_tool_calls:
        cleaned = re.sub(r"\s*<\|call\|>\s*$", "", tc["args"])
        try:
            parsed = json.loads(cleaned)
            fixed.append(
                {
                    "name": tc["name"],
                    "args": parsed,
                    "id": tc["id"],
                    "type": "tool_call",
                }
            )
        except (json.JSONDecodeError, TypeError):
            remaining_invalid.append(tc)

    response.tool_calls = fixed
    response.invalid_tool_calls = remaining_invalid
    return response
