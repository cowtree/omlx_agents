# oMLX setup on this machine

How oMLX is installed and configured on the MacBook Pro used to test the agents in
this repo. Written from the machine's actual state (checked 2026-09-24).

## Machine

| | |
|---|---|
| Chip | Apple M5 Max |
| RAM | 128 GB unified memory |
| oMLX version | 0.6.4 |

## Install

oMLX is installed as a macOS app at `/Applications/oMLX.app`. The app runs the
server (`omlx-server`) in the background and starts it automatically on launch
(`auto_start_on_launch: true`).

The command-line tool `omlx` is also available in the terminal:

- `~/.omlx/bin/omlx` is a small wrapper around the CLI inside the app
  (`/Applications/oMLX.app/Contents/MacOS/omlx-cli`).
- `/opt/homebrew/bin/omlx` is a symlink to that wrapper, which is why `omlx` works
  from any terminal.

Useful commands:

```bash
omlx --version    # print the version
omlx start        # start the background server
omlx stop         # stop it
omlx restart      # restart it (e.g. after changing settings)
omlx diagnose     # check for installation or runtime problems
omlx serve <model> --port 8000   # run a server in the foreground instead
```

## Server

| | |
|---|---|
| Address | `http://localhost:8000` (bound to `127.0.0.1`, so only this Mac can reach it) |
| OpenAI-compatible API | `http://localhost:8000/v1` |
| Admin dashboard | http://localhost:8000/admin |
| API docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

The API requires a key (`/v1/models` returns 401 without one). The key is
`auth.api_key` in `~/.omlx/settings.json`. Copy it into this project's `.env` as
`OMLX_API_KEY`, and never commit it.

Quick check that the server is up and which models it serves:

```bash
curl -H "Authorization: Bearer $OMLX_API_KEY" http://localhost:8000/v1/models
```

## Models

Models live in `~/.omlx/models/` (the `model_dir` setting). Installed:

| Model ID | Size on disk | Context | Notes |
|---|---|---|---|
| `Qwen3.6-35B-A3B-MLX-8bit` | 35 GB | 262,144 tokens | Mixture-of-experts: 35B parameters total, about 3B active per token, so it is fast |
| `MarkItDown` | none | none | Built-in helper that converts documents to Markdown, not a chat model |

The Qwen model came from `lmstudio-community` on Hugging Face and is stored at
`~/.omlx/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-8bit`.

LM Studio is also installed and has a separate model, `Qwen3.6-27B-MLX-8bit`,
in `~/.lmstudio/models/`. oMLX does not use it, because that folder is not in
oMLX's `model_dirs`.

### Thinking mode

Qwen3.6 "thinks" (writes hidden reasoning) before answering by default. On a simple
coding prompt, thinking on took about 14 s and thinking off about 1.5 s. It is turned
off per request with:

```python
extra_body={"chat_template_kwargs": {"enable_thinking": False}}
```

The scripts in this repo read `OMLX_THINKING` from `.env` to decide.

## Files and folders

| Path | What it is |
|---|---|
| `~/.omlx/settings.json` | All server settings, including the API key |
| `~/.omlx/models/` | Downloaded models |
| `~/.omlx/cache/` | On-disk prompt cache (up to 185 GB) |
| `~/.omlx/logs/` | Server logs (kept 7 days) |
| `~/.omlx/stats.json` | Usage statistics |
| `~/Library/Application Support/oMLX/` | App state and control socket |

## Notable settings

From `~/.omlx/settings.json`:

- **Default sampling:** temperature 1.0, top_p 0.95, max context window and max
  output tokens 32,768. The scripts here override temperature per request.
  Requests are limited to 32k tokens unless this setting is raised, even though
  Qwen supports 262k.
- **Concurrency:** up to 8 requests at once.
- **Memory guard:** "balanced", with soft and hard limits at 85% and 95% of memory.
- **Integrations:** MarkItDown is on, and web search uses DuckDuckGo (`ddgs`).
