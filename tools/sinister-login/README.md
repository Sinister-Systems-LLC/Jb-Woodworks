# sinister-login

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0-or-later
> **Status:** v0.1.0 (initial scaffold)

Sinister Sanctum's jcode-login parity tool. Implements the `sinister login --provider X` wallet listed in the operator's 2026-05-21T11:50Z directive.

## What it is

A small stdlib-only Python package that surfaces an 11-provider auth wallet matching jcode v0.12.3's `jcode login --provider` matrix:

| slug | provider | auth | key env |
|---|---|---|---|
| claude | Anthropic Claude | apikey | `ANTHROPIC_API_KEY` |
| openai | OpenAI | apikey | `OPENAI_API_KEY` |
| gemini | Google Gemini | apikey | `GEMINI_API_KEY` / `GOOGLE_API_KEY` |
| copilot | GitHub Copilot | oauth | `GITHUB_TOKEN` / `GH_TOKEN` |
| azure | Azure OpenAI | apikey | `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` |
| alibaba-coding-plan | Alibaba Qwen (DashScope) | apikey | `DASHSCOPE_API_KEY` |
| fireworks | Fireworks AI | apikey | `FIREWORKS_API_KEY` |
| minimax | MiniMax | apikey | `MINIMAX_API_KEY` + `MINIMAX_GROUP_ID` |
| lmstudio | LM Studio (local) | local | none (default `:1234`) |
| ollama | Ollama (local) | local | none (default `:11434`) |
| openai-compatible | OpenAI-compatible (generic) | apikey | base-url + key (Groq, Together, OpenRouter, …) |

## Install

```bash
pip install -e "D:/Sinister Sanctum/tools/sinister-login"
```

## CLI

After install, `sinister login` (via the umbrella) or `sinister-login` (direct) both work.

```bash
sinister login providers          # 11-row table; configured/missing
sinister login status             # alias of providers
sinister login current            # which provider would the fleet use right now
sinister login doctor claude      # env check only
sinister login doctor claude --probe   # opt-in TCP-handshake check (no HTTP body, no auth)
sinister login env claude         # print export commands for the provider
sinister login add claude --key sk-... --allow-plaintext  # REFUSED by default; opt-in only
sinister login matrix             # print the jcode-feature-matrix row for this tool
```

## Programmatic API

```python
from sinister_login import (
    list_providers, get_provider, provider_status,
    status_all, resolve_active, doctor, print_env_for, add_to_envfile,
)

resolve_active()                  # -> dict or None
doctor("claude", probe=False)     # env-only diagnosis
doctor("openai", probe=True)      # opt-in reachability
```

## Design constraints

- **Stdlib only** — no requests, no httpx, no openai-sdk. We diagnose; we don't proxy.
- **Env-var first** — keys live in process env (or `~/.sinister/login.env` opt-in). No plaintext is written to disk without `--allow-plaintext`.
- **No silent reachability probes** — `doctor` is env-only by default; `--probe` runs a TCP handshake only (read-only, no HTTP body, no auth).
- **Composes with `_vault/`** — once `vault-MCP` is wired into `~/.claude/.mcp.json`, the `add` subcommand will route to vault instead of an env-file. Tracked as a future enhancement.
- **Composes with `agent-host-routing.md`** — that file decides which provider serves which task class; this tool only manages keys + reachability.

## Lane

`tools/sinister-login/` is Sanctum's lane. Forge consumes via `sinister login` subcommand (already wired through `tools/sinister-cli/`). Term picks the picker output for its agent-host field.

## Why this tool exists

1. Operator screenshot 2026-05-21T11:50Z: jcode login flows + *"our commands will be sinister then the command"*.
2. Forge cross-agent `2026-05-21T1200Z-forge-to-sanctum-jcode-swarm-and-sinister-cli-absorption.md` DELEGATED the provider wallet to Sanctum's lane.
3. `sinister-cli` umbrella already listed `login` as one of the 2 unbuilt subcommands; this closes that gap.
