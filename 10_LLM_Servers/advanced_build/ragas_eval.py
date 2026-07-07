"""Activity 1: RAGAS evaluation and cost comparison, Fireworks versus OpenAI.

Runs the same cat-health questions through the retrieval pipeline on both
providers, scores them with RAGAS (using gpt-4.1-mini as the judge), and sums
token usage to estimate cost per question.

Needs OPENAI_API_KEY and FIREWORKS_API_KEY in .env. With LANGSMITH_TRACING=true
(and LANGSMITH_API_KEY / LANGSMITH_ENDPOINT for the EU instance) each stage traces
into its own LangSmith project via tracing_v2_enabled: ragas-eval-fireworks and
ragas-eval-openai for the pipeline runs, ragas-eval-judge-fireworks and
ragas-eval-judge-openai for the RAGAS judge calls.

Run: uv run python advanced_build/ragas_eval.py
"""

import sys
import types

stand_in = types.ModuleType("langchain_community.chat_models.vertexai")
stand_in.ChatVertexAI = type("ChatVertexAI", (), {})
sys.modules.setdefault("langchain_community.chat_models.vertexai", stand_in)

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env", override=True)
os.environ.setdefault("RAG_DATA_DIR", str(PROJECT_ROOT / "data"))

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.tracers.context import tracing_v2_enabled
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

import app.rag as rag

PRICE_PER_MILLION = {
    "fireworks": {"input": 0.07, "output": 0.30},
    "openai": {"input": 0.40, "output": 1.60},
}

QUESTIONS = [
    ("What are the core vaccines recommended for kittens?",
     "The core vaccines for kittens are rabies, feline herpesvirus-1, feline calicivirus, and feline panleukopenia virus. Feline leukemia virus is also core for kittens and young cats."),
    ("At what age should kittens begin their vaccination series?",
     "Kittens start the core vaccine series at six to eight weeks, with boosters every three to four weeks until about sixteen to eighteen weeks."),
    ("Why is revaccination at six months recommended for kittens?",
     "Revaccinating against feline panleukopenia, herpesvirus-1, and calicivirus at six months reduces the window of susceptibility from maternal antibodies interfering with earlier doses."),
    ("What is the difference between core and non-core vaccines?",
     "Core vaccines are recommended for all cats against widespread or severe diseases, while non-core vaccines depend on the cat's lifestyle, exposure, and location."),
    ("For which cats is the feline leukemia virus vaccine considered core?",
     "The feline leukemia virus vaccine is core for kittens and young cats because of age-related susceptibility, with revaccination for cats that stay at high risk."),
]


def answer_all_questions(backend):
    os.environ["LLM_BACKEND"] = backend
    rag._get_rag_graph.cache_clear()
    graph = rag._get_rag_graph()

    usage = UsageMetadataCallbackHandler()
    samples = []
    with tracing_v2_enabled(project_name=f"ragas-eval-{backend}"):
        for question, reference in QUESTIONS:
            result = graph.invoke({"question": question}, config={"callbacks": [usage]})
            samples.append({
                "user_input": question,
                "response": result["response"],
                "retrieved_contexts": [document.page_content for document in result.get("context", [])],
                "reference": reference,
            })

    input_tokens = sum(entry.get("input_tokens", 0) for entry in usage.usage_metadata.values())
    output_tokens = sum(entry.get("output_tokens", 0) for entry in usage.usage_metadata.values())
    return samples, input_tokens, output_tokens


def cost_per_question(backend, input_tokens, output_tokens):
    price = PRICE_PER_MILLION[backend]
    total = input_tokens / 1_000_000 * price["input"] + output_tokens / 1_000_000 * price["output"]
    return total / len(QUESTIONS)


def main():
    judge_model = LangchainLLMWrapper(ChatOpenAI(model="gpt-4.1-mini", temperature=0))
    judge_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    for backend in ("fireworks", "openai"):
        samples, input_tokens, output_tokens = answer_all_questions(backend)
        with tracing_v2_enabled(project_name=f"ragas-eval-judge-{backend}"):
            scores = evaluate(EvaluationDataset.from_list(samples), metrics=metrics, llm=judge_model, embeddings=judge_embeddings)
        print(f"\n{backend}: {scores}")
        print(f"  Cost per question: ${round(cost_per_question(backend, input_tokens, output_tokens), 6)}")


if __name__ == "__main__":
    main()
