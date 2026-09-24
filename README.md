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

| Agent | What it shows |
|---|---|
| `main.py` | Basic chat completion against the local model |
| `structured_output_agent/` | Structured output: the model analyzes an article and returns JSON that is validated with a Pydantic model, retrying up to 3 times if the output is invalid |

### Structure of an agent folder

```
structured_output_agent/
├── main.py          # entry point: reads .env, creates the client and agent, runs it
└── app/
    ├── agent.py     # StructuredOutputAgent: prompt, LLM call, validation and retries
    └── models.py    # Pydantic model the output must match (ArticalAnalysis)
```

`main.py` is the only place that reads `.env`. It passes the model name and the
thinking setting into the agent, so the agent code has no config of its own.

### Learnings: structured output agent

- **Structured output:** the prompt asks the LLM for JSON with fixed fields
  (`title`, `summary`, `sentiment`) instead of free text, so the result can be
  used directly by code.
- **Validation with Pydantic:** the raw LLM output is never trusted.
  `ArticalAnalysis.model_validate_json()` checks that it is valid JSON, that all
  fields are present, and that `sentiment` is one of `positive`, `negative` or
  `neutral` (enforced with `Literal`). Anything else raises a `ValidationError`.
- **Agentic loop with retry:** LLM output is not deterministic, so a failed
  validation is not the end. The agent calls the model again, up to
  `max_retries` times, and returns the first response that passes validation.
- **Fail loudly:** if every attempt fails, the agent raises a `RuntimeError`
  instead of returning `None`, so the caller can't silently continue with a
  missing result.
- **Config injection:** the agent receives the client, model and thinking
  setting from `main.py` rather than reading `.env` itself. This keeps the agent
  reusable and easy to test with different settings.

Possible next step: feed the validation error back to the model on the retry,
so it can fix its own mistake instead of trying again with the same prompt.

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

   The basic chat script runs from the project root with `uv run main.py`.

### Thinking mode

Qwen models can "think" before answering. This improves results on hard problems
but is much slower (about 14s vs 1.5s on a simple coding prompt). Toggle it with
`OMLX_THINKING` in `.env` (it is off if missing), or for a single run:

```bash
OMLX_THINKING=true uv run main.py
```
