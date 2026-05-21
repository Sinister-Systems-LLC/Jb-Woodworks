# sinister-model

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Version:** 0.1.0

Per-provider model registry + active-model state for the Sinister Sanctum fleet. jcode-model parity.

## Install

```bash
pip install -e "D:/Sinister Sanctum/tools/sinister-model"
```

## CLI

```bash
# list models for the currently logged-in provider (via sinister-login)
sinister-model list

# list models for a specific provider
sinister-model list anthropic
sinister-model list openai --json

# show all providers + model counts
sinister-model providers

# show the active model
sinister-model current

# set the active model
sinister-model set claude-opus-4-7[1m]

# show model details
sinister-model info gpt-5

# clear active selection
sinister-model clear
```

Also reachable via the umbrella dispatcher: `sinister model list` etc.

## Providers covered (11)

`anthropic`, `openai`, `google`, `xai`, `mistral`, `groq`, `deepseek`, `openrouter`, `cohere`, `perplexity`, `together`.

The `sinister-login` aliases `claude` -> `anthropic` and `gemini` -> `google` are accepted automatically.

## State file

Active model is persisted to `~/.config/sinister/model.json` (or `$XDG_CONFIG_HOME/sinister/model.json`). Override via `SINISTER_MODEL_STATE_PATH`.

## Composes with

- `tools/sinister-login/` — read currently-logged-in provider
- `tools/sinister-usage/` — per-provider quota visibility
- `automations/agent-host-routing.md` — task-class -> model selection
- `tools/sinister-cli/` — umbrella `sinister model ...` dispatcher
