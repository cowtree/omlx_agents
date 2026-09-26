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

### Learnings: structured output agent

- **Structured output:** the LLM returns JSON matching a Pydantic model instead
  of free text, so code can use the result directly.
- **Generic over the output model:** `agent.run(prompt, output_model)` works with
  any Pydantic model (article analysis, entity extraction, ...). New task = new
  model, no agent changes.
- **The schema is the prompt:** `model_json_schema()` puts field types,
  descriptions and limits into the prompt, so prompt and validation can't drift
  apart.
- **Validation with Pydantic:** raw LLM output is never trusted;
  `model_validate_json()` checks JSON, fields, `Literal` values and limits.
- **Agentic loop with self-repair:** on invalid output, the agent sends the
  model its previous answer plus the validation error and asks it to fix it, up
  to `max_retries` times.
- **API retries with backoff:** connection errors, timeouts and rate limits are
  retried separately, waiting 1s, then 2s.
- **Fail loudly:** after the last attempt the agent raises instead of returning
  `None`.
- **Logging:** each validation attempt and API attempt is logged, with response
  times and token counts.
- **Config injection:** `main.py` reads `.env` and passes the client, model and
  thinking setting in; the agent has no config of its own.

See [docs/structured-output-agent.md](docs/structured-output-agent.md) for how
it works, example logs and known limitations.

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
