"""Compare the RAG app on hosted Fireworks vs local Ollama.

Runs the same question through both backends and prints each answer and how long
it took. Both runs use the app's existing RAG graph; only the LLM_BACKEND value
changes between them, so there is no duplicated retrieval logic here.

Usage:
    uv run python advanced_build/compare_backends.py
    RAG_QUESTION="How often should I deworm my kitten?" uv run python advanced_build/compare_backends.py
"""

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# This file lives in advanced_build/, so add the project root to the import path
# so that "import app.rag" works when running the script directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env", override=False)

# Find the PDF no matter which folder you run the script from.
os.environ.setdefault("RAG_DATA_DIR", str(PROJECT_ROOT / "data"))

import app.rag as rag  # noqa: E402

QUESTION = os.environ.get(
    "RAG_QUESTION", "What are the recommended vaccinations for kittens?"
)
ANSWER_PREVIEW_LENGTH = 600


def warm_up():
    """Pay one-time costs (tokenizer download, reading the PDF from disk) before
    timing, so they don't unfairly land on whichever backend runs first."""
    rag._tiktoken_len("warm up")
    data_dir = Path(os.environ["RAG_DATA_DIR"])
    for pdf in data_dir.rglob("*.pdf"):
        pdf.read_bytes()


def run_backend(backend):
    """Build the RAG for one backend, ask the question, and time both steps."""
    os.environ["LLM_BACKEND"] = backend

    # Clear the cache so the graph is rebuilt with this backend's models.
    rag._get_rag_graph.cache_clear()

    # Step 1: load the PDF, split it, embed the chunks, build the index.
    start = time.perf_counter()
    graph = rag._get_rag_graph()
    index_seconds = time.perf_counter() - start

    # Step 2: answer the question using that index.
    start = time.perf_counter()
    output = graph.invoke({"question": QUESTION})
    query_seconds = time.perf_counter() - start

    return output["response"], index_seconds, query_seconds


def main():
    print(f"Question: {QUESTION}\n")
    warm_up()

    results = []
    for backend in ("fireworks", "ollama"):
        if backend == "fireworks" and not os.environ.get("FIREWORKS_API_KEY"):
            print("Skipping fireworks: FIREWORKS_API_KEY is not set.\n")
            continue

        answer, index_seconds, query_seconds = run_backend(backend)
        total_seconds = index_seconds + query_seconds

        print(f"----- {backend} -----")
        print(answer.strip()[:ANSWER_PREVIEW_LENGTH])
        print(f"index: {round(index_seconds, 1)}s")
        print(f"query: {round(query_seconds, 1)}s")
        print(f"total: {round(total_seconds, 1)}s\n")

        results.append((backend, index_seconds, query_seconds))

    print("===== SUMMARY =====")
    for backend, index_seconds, query_seconds in results:
        total_seconds = index_seconds + query_seconds
        print(
            f"{backend}: "
            f"index {round(index_seconds, 1)}s, "
            f"query {round(query_seconds, 1)}s, "
            f"total {round(total_seconds, 1)}s"
        )


if __name__ == "__main__":
    main()
