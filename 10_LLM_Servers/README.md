<p align = "center" draggable="false" ><img src="https://github.com/AI-Maker-Space/LLM-Dev-101/assets/37101144/d1343317-fa2f-41e1-8af1-1dbb18399719"
     width="200px"
     height="auto"/>
</p>

## <h1 align="center" id="heading">Session 10: LLM Servers</h1>

| 📰 Session Sheet                                                                                                                            | ⏺️ Recording                                                                                                                                                | 🖼️ Slides                                               | 👨‍💻 Repo       | 📝 Homework                                                 | 📁 Feedback                                         |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | ------------- | ----------------------------------------------------------- | --------------------------------------------------- |
| [Session 10: LLM Servers](https://github.com/AI-Maker-Space/The-AI-Engineering-Certification-v1.0/tree/main/00_Docs/Modules/10_LLM_Servers) | [Recording!](https://us02web.zoom.us/rec/share/zXd6__uO2RwCmJUmNyGKY01sbwYjjrkpDDNPbfK_Es0MANaqRpFOqqYX4sEVYY1d.gJwTZk1729siXnjj) <br> passcode: `^1$@$R@.` | [Session 10 Slides](https://canva.link/953giejzt5igxvw) | You are here! | [Session 10 Assignment](https://forms.gle/hc1B1bkTuXzNVrZU) | [Feedback 7/2](https://forms.gle/uj2QvYjHfHKFFQ8a6) |

**⚠️!!! PLEASE BE SURE TO SHUTDOWN YOUR DEDICATED ENDPOINT ON FIREWORKS AI WHEN YOU'RE FINISHED YOUR ASSIGNMENT !!!⚠️**

# Build 🏗️

In today's assignment, we'll be creating Fireworks AI endpoints, and then building a RAG application.

- 🤝 Breakout Room #1
  - Set-up Open Source Endpoint (Instructions [here](./ENDPOINT_SETUP.md)) ((This process may take 15-20min.))
  - Test Endpoint and Embeddings with the `endpoint_slammer.ipynb` notebook.

- 🤝 Breakout Room #2
  - Use the Open Source Endpoints to build a RAG LangGraph application

# Ship 🚢

The completed notebook and your RAG app/notebook!

### Deliverables

- A short Loom of either:
  - the notebook and the RAG application you built for the Main Homework Assignment; or
  - the notebook you created for the Advanced Build

# Share 🚀

Make a social media post about your final application!

### Deliverables

- Make a post on any social media platform about what you built!

Here's a template to get you started:

```
🚀 Exciting News! 🚀

I am thrilled to announce that I have just built and shipped a RAG application powered by open-source endpoints! 🎉🤖

🔍 Three Key Takeaways:
1️⃣
2️⃣
3️⃣

Let's continue pushing the boundaries of what's possible in the world of AI and question-answering. Here's to many more innovations! 🚀
Shout out to @AIMakerspace !

#LangChain #QuestionAnswering #RetrievalAugmented #Innovation #AI #TechMilestone

Feel free to reach out if you're curious or would like to collaborate on similar projects! 🤝🔥
```

# Submitting You Homework

## Main Homework Assignment

Follow these steps to prepare and submit your homework assignment:

1. Follow the instructions in `ENDPOINT_SETUP.md`
2. Replace both `model` values in `endpoint_slammer.ipynb` with the `gpt-oss` endpoint you created in Step 1
3. Run the code cells in `endpoint_slammer.ipynb`
4. Respond to the questions in the section below
5. Build a sample RAG
6. Record a Loom video reviewing what you have learned from this session

**⚠️!!! PLEASE BE SURE TO SHUTDOWN YOUR DEDICATED ENDPOINT ON FIREWORKS AI WHEN YOU HAVE FINISHED YOUR ASSIGNMENT !!!⚠️**

## Questions

### ❓ Question #1:

What is the difference between serverless and dedicated endpoints?

#### ✅ Answer:

Serverless endpoints are shared and you pay per token. You only pay for what you actually send. Nothing has to be set up you just pay as u go. The tradeoff is that you share capacity with everyone else on that model, so latency can vary and you can run into rate limits when things get busy.

Dedicated endpoints give you your own GPUs reserved just for your workload. You pay by the hour for that hardware whether or not you send any requests, so it costs more, but you get consistent latency, guaranteed capacity, and higher throughput.

Serverless is a good fit for experimentation and low or bursty traffic, while dedicated makes sense for steady production load where predictable performance is worth paying for even when idle.

### ❓ Question #2:

Why is it important to consider token throughput and latency when choosing an LLM for user-facing applications?

#### ✅ Answer:

In a user-facing app the latency of inference (how long they wait before the answer starts coming back from the model) is something that users feels directly. Throughput is how fast the tokens stream once it starts. If either one is slow the app feels sluggish even when the answer itself is good.

Throughput also sets a ceiling on how many users you can serve at the same time, so a slow model limits how well the app scales and pushes up the cost per request.

The takeaway is to pick a model that actually fits the task instead of always reaching for the biggest one. You can also route requests, so easy questions go to a small fast model and only the harder ones go to a bigger model. Caching queries helps too, because if you have already seen a question you can return the cached answer instead of paying the latency and cost of running the model again.

## Activity 1: RAGAS Evaluation with Cost Analysis

Use RAGAS to evaluate your open-source Fireworks AI powered RAG app against an OpenAI `gpt-4.1-mini` powered equivalent. Compare retrieval quality, answer faithfulness, and end-to-end accuracy across both providers.

Additionally, instrument both pipelines with **LangSmith** to capture token usage and cost per query. Use LangSmith's tracing and cost dashboards to compare the total cost of running each provider at scale. Include your evaluation results, cost breakdown, and analysis in your Loom video.

## Advanced Activity: Local Models

Swap out the Fireworks AI endpoints for **locally-running open-source models** using [Ollama](https://ollama.com/) or another local inference server of your choice. Run both your embedding model and your chat model locally, and rebuild the RAG pipeline on top of them.

- Compare quality and latency between the local setup and your Fireworks AI hosted endpoint.
- Reflect: what are the trade-offs of local models vs. managed endpoints in a production setting?

Include your findings and a demo in your Loom video.

NOTES from advanced build:

# Advanced Build: Local Models (runbook)

Swap the hosted Fireworks endpoints for locally-running open-source models and
rebuild the RAG on top of them. There is no separate code path. The main app
picks the backend from the `LLM_BACKEND` flag, so you start the same app with a
flag instead of maintaining a second RAG.

- `LLM_BACKEND=fireworks` (default) — hosted Fireworks AI
- `LLM_BACKEND=ollama` — fully local: chat and embeddings both served by Ollama

The switch lives in [`app/models.py`](../app/models.py) (`get_chat_model` and
`get_embeddings`), which [`app/rag.py`](../app/rag.py) and the graphs already use.

## 1. Install Ollama

```bash
brew install ollama      # or download the app from https://ollama.com
ollama serve             # starts the local server on :11434 (the app does this too)
```

## 2. Pull the local models

```bash
ollama pull qwen2.5:3b          # chat / generation (supports tool calling)
ollama pull nomic-embed-text    # embeddings
```

- setting `OLLAMA_CHAT_MODEL`.

## 3. Run the app with the local flag

Point the app at Ollama by setting the flag on startup:

```bash
cd 10_LLM_Servers

LLM_BACKEND=ollama uv run python main.py
```

Without the flag the same commands run against Fireworks, so you can A/B the two
backends by only changing `LLM_BACKEND`.

## 4. Compare (Results)

Run the same question on each backend and note the difference. Run the app once
per backend and compare the two runs (and their LangSmith traces):

```bash
uv run python main.py
LLM_BACKEND=ollama uv run python main.py
```

- Quality: is the local answer as grounded and complete as the Fireworks one?
- Latency: time the full response on each.

Fireworks output data:
![alt text](image-1.png)

Total latency: 33.5s
Total tokens: 7,969 (6,475 input + 1,494 output)
Total cost: $0.0009

Local Ollama output data:
![alt text](image-2.png)
but on 2nd run because it was warm already it was faster:
![alt text](image-3.png)
Total latency: 15.5s cold start | 10 sec warm
Cost: 0$

### Insights (local vs managed)

- Local is effectively free per query once the hardware is paid for, while Fireworks bills per token. That flips the economics at scale: a few dev queries are pennies on Fireworks, but steady production traffic is where a local or self-hosted option starts to pay off.
- Cold start is real. The very first local request pays to load the model into memory (we saw a run jump from ~10s warm to ~15s cold). Hosted endpoints keep the model warm for you, so you never see that penalty. If you run local, keep the model resident or accept a slow first request.
- With local, the document text and the questions never leave the machine, which matters for sensitive data. Nothing depends on a vendor account either, no rate limits, and no surprise suspension (we hit exactly that when the Fireworks credits ran out).
- Model size is the real quality lever.
