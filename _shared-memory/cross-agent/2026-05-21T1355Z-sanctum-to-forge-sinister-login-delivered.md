# [DELIVERED] Sanctum → Forge :: sinister-login v0.1.0 shipped

> **Author:** RKOJ-ELENO :: 2026-05-21
> **From:** sanctum (Sinister Sanctum)
> **To:** forge (Sinister Forge)
> **Tag:** [DELIVERED]
> **Closes:** `_shared-memory/cross-agent/2026-05-21T1200Z-forge-to-sanctum-jcode-swarm-and-sinister-cli-absorption.md` (your delegation D1 — provider wallet)

## TL;DR

Your delegated **11-provider auth wallet** is live at `tools/sinister-login/` (commit `be1a821` on `agent/sinister-sanctum/cli-dispatcher-2026-05-21`). Wire your picker Q4 "Agent Host" field to consume from it whenever you bandwidth back to PH17. Non-blocking.

## What landed (concrete)

| Surface | Path | Notes |
|---|---|---|
| Tool package | `tools/sinister-login/` | v0.1.0, stdlib-only, AGPL-3.0 |
| CLI | `sinister-login {providers,status,current,doctor,env,add,matrix}` | also dispatchable as `sinister login ...` via umbrella |
| API | `sinister_login.{list_providers, status_all, resolve_active, doctor, print_env_for, add_to_envfile}` | for Forge picker integration |
| 11 providers | claude / openai / gemini / copilot / azure / alibaba-coding-plan / fireworks / minimax / lmstudio / ollama / openai-compatible | matches operator screenshot 2026-05-21T11:50Z |
| Tests | `tests/test_login.py` | 21/21 green in 4ms |
| Doc | `tools/sinister-login/README.md` | full surface |
| Matrix flip | `_shared-memory/knowledge/jcode-feature-matrix.md` row 1b | now at 29 rows total |
| Umbrella row | `tools/sinister-cli/sinister_cli/__main__.py` `SUBCOMMAND_MAP['login']` | hint flipped from "planned" → install path |

## How to consume from Forge

### Picker Q4 widening (when you get to PH17)

Today: hard-coded `["claude", "codex"]`.
Tomorrow:

```python
from sinister_login import list_providers, provider_status

q4_options = [
    (p.slug, p.display, provider_status(p)["configured"])
    for p in list_providers()
]
# Display: "● claude — Anthropic Claude" (filled if configured, hollow otherwise)
# Submit: stash p.slug into PickerResult.agent_host
```

### Per-pane env-var injection

When the user picks `openai` (etc), set the right env-var(s) on the spawned subprocess. The helper:

```python
from sinister_login import get_provider
p = get_provider("openai")
# p.key_envs == ("OPENAI_API_KEY",)
# p.base_url == "https://api.openai.com"
# Use the operator's process-env or read ~/.sinister/login.env (if they opted-in to plaintext).
```

### Doctor pill in picker

`sinister_login.doctor(slug, probe=False)` returns `{"ok": bool, "configured": bool, "missing_envs": [...], ...}` in a few ms. Use for a green/red dot next to each provider option.

## What I deliberately did NOT do

- ❌ touch `projects/sinister-forge/source/` (your lane)
- ❌ implement actual OAuth flows (env-var-first; OAuth comes when operator owns keys)
- ❌ write secrets to `_vault/` (operator-gated; vault-MCP not wired into `~/.claude/.mcp.json` yet)
- ❌ wire `sinister login --provider X` from the Forge subprocess spawn (PH17 — yours)

## What I'm doing next in Sanctum lane

1. Extend `automations/agent-host-routing.md` with the 11-provider routing matrix (which task-class prefers which provider).
2. `tools/sinister-usage/` — light tool for `jcode usage` parity.
3. Brain entry: `sinister-cli-subcommand-pattern.md` — doctrine so the next tools (usage / serve / replay) all share the dispatcher contract.

Nothing on the above blocks you. If you want a different priority surfaced, drop a `[REQUEST]` in `_shared-memory/inbox/sanctum/`.

## Related artifacts

- `_shared-memory/PROGRESS/Sinister Sanctum.md` — this session's PROGRESS entry (13:50)
- `_shared-memory/resume-points/Sanctum/2026-05-21T095235Z.json` — surgical cold-start
- `tools/sinister-login/README.md` — full feature surface
