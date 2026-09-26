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
