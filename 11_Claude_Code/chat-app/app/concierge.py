"""The chat brain.

`generate_reply` is the seam: the only thing `/api/chat` calls. Everything about how
the agent is configured and constrained lives here.
"""

import asyncio
import logging
import os
from pathlib import Path

from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    create_sdk_mcp_server,
    query,
    tool,
)

logger = logging.getLogger(__name__)

TARGET_REPO = Path(os.environ.get("TARGET_REPO", Path.cwd())).resolve()

SYSTEM_PROMPT = f"""You are a codebase concierge for the repository at {TARGET_REPO}.

Answer questions about this repository concisely — a short paragraph, not an essay.
Ground every claim in the code: read the relevant files before answering, and cite the
file paths (and line numbers where useful) you relied on. If the repository does not
answer the question, say so plainly instead of guessing.
"""

# Read-only. This agent runs headless, so there is no human at a permission prompt —
# the toolset IS the safety boundary. Bash/Write/Edit must never appear here.
#
# Two options, two jobs — `allowed_tools` alone is NOT a sandbox:
#   tools=         which tools exist at all. This is the restriction.
#   allowed_tools= which of those run without prompting. Headless has no one to
#                  prompt, so anything omitted here would stall the request.
READ_ONLY_TOOLS = ["Read", "Glob", "Grep", "mcp__concierge__git_log"]

MAX_TURNS = 25

# conversation_id (from the browser) -> SDK session_id, so follow-ups keep context.
_sessions: dict[str, str] = {}


@tool(
    "git_log",
    "Recent git commit history, newest first. Use this for questions about recent "
    "changes, who changed what, or how the code got to its current state. Optionally "
    "pass a repo-relative path (file or directory) to see only commits touching it.",
    {"limit": int, "path": str},
)
async def git_log(args: dict) -> dict:
    """Read-only git history.

    The agent has no Bash, so this is its only route to history. Args are clamped and
    passed as a list (never a shell string), so the model cannot smuggle in extra git
    flags or shell syntax, and `path` is resolved and confined to the target repo.
    """
    limit = max(1, min(int(args.get("limit", 10)), 50))

    argv = [
        "git",
        "-C",
        str(TARGET_REPO),
        "log",
        f"-{limit}",
        "--date=short",
        "--pretty=format:%h  %ad  %an  %s",
    ]

    path = (args.get("path") or "").strip()
    if path:
        resolved = (TARGET_REPO / path).resolve()
        if not resolved.is_relative_to(TARGET_REPO):
            logger.warning("git_log rejected out-of-repo path: %s", path)
            return {
                "content": [
                    {"type": "text", "text": f"Path '{path}' is outside the repository."}
                ]
            }
        argv += ["--", str(resolved)]

    process = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        text = f"git log failed: {stderr.decode().strip() or 'unknown error'}"
    else:
        text = stdout.decode().strip() or "No commits found."

    logger.info("git_log tool called (limit=%s, path=%s)", limit, path or "<repo root>")
    return {"content": [{"type": "text", "text": text}]}


concierge_tools = create_sdk_mcp_server(
    name="concierge", version="1.0.0", tools=[git_log]
)


def _build_options(conversation_id: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        tools=READ_ONLY_TOOLS,
        allowed_tools=READ_ONLY_TOOLS,
        mcp_servers={"concierge": concierge_tools},
        cwd=str(TARGET_REPO),
        max_turns=MAX_TURNS,
        resume=_sessions.get(conversation_id),
    )


async def generate_reply(message: str, conversation_id: str) -> str:
    """Run one turn of the agent loop and return its final answer.

    Agent failures come back as a chat reply, not a 500 — a broken agent should look
    like an apology in the transcript, not a dead fetch() in the browser.
    """
    try:
        reply = ""
        async for msg in query(prompt=message, options=_build_options(conversation_id)):
            if isinstance(msg, SystemMessage) and msg.subtype == "init":
                session_id = msg.data.get("session_id")
                if session_id:
                    _sessions[conversation_id] = session_id
            elif isinstance(msg, ResultMessage):
                reply = msg.result or ""

        return reply or "I couldn't come up with an answer for that one. Try rephrasing?"

    except Exception:
        logger.exception("agent failed for conversation %s", conversation_id)
        return "Something went wrong while I was reading the repository. Please try again."
