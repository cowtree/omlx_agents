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

| Script | What it shows |
|---|---|
| `main.py` | Basic chat completion against the local model |
| `agent_str_output.py` | Structured output: the model returns JSON that is validated with a Pydantic model |

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

3. Run an agent:

   ```bash
   uv run agent_str_output.py
   ```

### Thinking mode

Qwen models can "think" before answering. This improves results on hard problems
but is much slower (about 14s vs 1.5s on a simple coding prompt). Toggle it with
`OMLX_THINKING` in `.env`, or for a single run:

```bash
OMLX_THINKING=true uv run main.py
```
