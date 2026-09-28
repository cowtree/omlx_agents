# omlx_agents

A playground for implementing different types of AI agents in Python, from simple
chat calls to structured output and beyond.

## Test setup

All agents are tested against free, open-weight models served locally by
oMLX on an Apple **M5 Max with 128 GB RAM**.
oMLX exposes an OpenAI-compatible API, so the scripts use the official `openai`
Python client pointed at `http://localhost:8000/v1`.

Current model: `Qwen3.6-35B-A3B-MLX-8bit`

See [docs/omlx-setup.md](docs/omlx-setup.md) for how oMLX is installed and
configured on this machine.

## Agents

| Agent | What it shows | Docs |
|---|---|---|
| `main.py` | Basic chat completion against the local model | |
| `structured_output_agent/` | Turns text into validated Pydantic objects, for any output model | [docs/structured-output-agent.md](docs/structured-output-agent.md) |
| `rag-citation-agent/` | Finds the documents that answer a question, with their sources (work in progress) | |

## Roadmap

Twelve agent patterns, built one at a time. The rule for all of them: **open
models only**, running locally. No paid model APIs.

| # | Agent | Status | Open-source approach |
|---|---|---|---|
| 1 | Structured output | ✅ Done | Qwen3.6-35B-A3B on oMLX; Pydantic validation with retries |
| 2 | RAG with citations | 🚧 Retrieval done | Open embedding model (e.g. `bge-small`, `nomic-embed`) via `sentence-transformers`; web fallback via DuckDuckGo or self-hosted SearXNG |
| 3 | ReAct planning | Planned | Local model; iteration limits, loop detection, graceful failure |
| 4 | Multi-tool orchestrator | Planned | Tool registry with OpenAI-style tool calling (Qwen3 supports it); email and calendar tools are fakes |
| 5 | Memory-enabled conversation | Planned | Same embedding model as RAG; SQLite for long-term memory |
| 6 | Human-in-the-loop approval | Planned | Local model; confidence threshold, pause/resume, audit log |
| 7 | Cost-aware router | Planned | A small model (e.g. Qwen3-4B) and a large one (the 35B); local models have no API price, so "cost" is latency, tokens/s and memory |
| 8 | Event-triggered automation | Planned | FastAPI webhook, queue with retries, dead-letter handling and idempotency |
| 9 | Multi-agent debate | Planned | Several agents (different prompts or different open models) plus a critic |
| 10 | Self-reflective with auto-evaluation | Planned | Generate, judge, rewrite; the local model acts as its own judge |
| 11 | Production observability | Planned | Self-hosted Langfuse or Arize Phoenix for tracing, token and latency dashboards |
| 12 | Open-source framework contribution | Planned | A pull request to LangGraph, CrewAI or AutoGen; linked here, not code in this repo |

Each agent gets its own folder, with the same layout as
`structured_output_agent/`. Shared setup (oMLX client, `.env` loading, logging)
will move into a `common/` folder once more agents need it.

### Learnings: structured output agent

The agent covers six parts of a reliable-LLM-output challenge:

| Challenge | How it's done |
|---|---|
| Reliable outputs | A Pydantic model is the contract; its JSON schema goes into the prompt |
| Schema validation | `model_validate_json()` checks JSON, fields, `Literal` values and limits |
| Error handling | API failures and validation failures are handled separately |
| Retry logic | API retry with backoff (1s, 2s) + semantic repair: the validation error is fed back so the model fixes its own answer |
| Logging | Python `logging`; validation attempts and API attempts are logged separately, with response times and token counts |
| Continue safely | `run()` returns an `AgentResult` (`success`, `data`, `error`, `attempts`), so one bad item doesn't stop a batch |

Also worth knowing:

- **Generic over the output model:** `agent.run(prompt, output_model)` works with
  any Pydantic model. New task = new model, no agent changes.
- **Config injection:** `main.py` reads `.env` and passes the client, model and
  thinking setting in; the agent has no config of its own.

See [docs/structured-output-agent.md](docs/structured-output-agent.md) for how
it works, example logs and known limitations.

### Learnings: RAG citation agent (work in progress)

So far this covers the retrieval half of RAG: finding the text that answers a
question and remembering where it came from. There is no model call yet.

| Step | How it's done |
|---|---|
| Knowledge base | A small set of policy `Document`s, each with an `id`, `title`, `content` and `source` file |
| Chunking | `chunk_documents()` splits each document into overlapping word windows (`chunk_size`, `chunk_overlap`); each `Chunk` keeps its `document_id` and `source` for citations |
| Retrieval | `Retriever.search()` scores each chunk by the share of question words it contains and returns the `top_k` best as `RetrievalResult`s |
| Relevance cut-off | `min_score` drops weak matches, so a question the knowledge base can't answer returns nothing instead of a wrong document |

Known limitations:

- **Keyword matching only:** "holiday" won't find the vacation policy. Embeddings would fix this.
- **Every word counts:** words like "the" and "is", and the "s" left over from "company's", count towards the score. That lowers it for longer questions.
- **No answer yet:** the next step is to send the retrieved chunks to the model and have it answer with citations.

## Getting started

Requires [uv](https://docs.astral.sh/uv/) and a running oMLX server.

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Create a `.env` file in the project root:

   ```bash
   OMLX_API_KEY=your-omlx-api-key
   OMLX_MODEL=Qwen3.6-35B-A3B-MLX-8bit
   OMLX_THINKING=false
   ```

3. Run an agent from inside its folder (the `from app...` imports only work there):

   ```bash
   cd structured_output_agent
   uv run main.py
   ```

   The RAG citation agent runs the same way from `rag-citation-agent/`. It
   doesn't need the oMLX server yet. The basic chat script runs from the
   project root with `uv run main.py`.

### Running tests

```bash
uv run pytest
```

Tests live in `structured_output_agent/tests/`, one test class per challenge
(reliable outputs, schema validation, error handling, retry logic, logging,
continue safely). They use a fake client with scripted replies, so they run in
milliseconds and don't need the oMLX server.

### Thinking mode

Qwen models can "think" before answering. This improves results on hard problems
but is much slower (about 14s vs 1.5s on a simple coding prompt). Toggle it with
`OMLX_THINKING` in `.env` (it is off if missing), or for a single run:

```bash
OMLX_THINKING=true uv run main.py
```
