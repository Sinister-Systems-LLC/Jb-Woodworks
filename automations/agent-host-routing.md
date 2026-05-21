> **Author:** RKOJ-ELENO :: 2026-05-21

# Sinister Forge :: agent-host-routing

CONTRACT 7 dependency. Declarative task → provider routing layer consulted by Forge sessions at task-dispatch time. v1 is doc-only (no code wire-up) — the doc IS the routing layer; v2+ ingests this into Ruflo `agentdb_semantic-route`.

## How it's used

When a Forge agent needs to pick which LLM provider to dispatch a task to, it reads this table, matches the task's class against the rows, and picks the **Primary**. If primary is rate-limited or refuses (per AUP-RESPECT), fall through the **Fallback chain** in order. Operator-own infrastructure is always allowed (AUP-RESPECT carve-out).

## Routing table

| Task class | Primary | Fallback chain | Rationale |
|---|---|---|---|
| Multi-file refactor / whole-codebase pass / heavy reasoning | `claude-opus-4-7` (1M context) | `claude-sonnet-4-6` → `claude-opus-4-7` (200k) | 1M context for the full sweep; Sonnet handles 200k chunks; Opus 200k as final |
| Single-file edit / narrow patch / quick fix | `claude-haiku-4-5` | `claude-sonnet-4-6` → `claude-opus-4-7` | Cost + latency for narrow scope; escalate only on confusion |
| Peer-review / cross-check / second-opinion | `gpt-4o-mini` (codex-companion) | `gpt-4o` → `claude-opus-4-7` | OpenAI as fresh eyes; already wired via `tools/codex-companion/codex.py` |
| Deep reasoning / hard logic / novel-pattern design | `claude-opus-4-7` | `o1-mini` (codex) → `gpt-4o` | Opus 4.7 strongest at multi-step reasoning; o1-mini as reasoning-second-opinion |
| Local / offline / privacy-sensitive | `Ollama (llama3.3:70b)` | `Ollama (qwen2.5:14b)` → `claude-haiku-4-5` | Zero network egress for sensitive work; falls back to Haiku only if Ollama is down |
| Bulk classification (file triage / quick categorize) | `Ollama (small)` | `claude-haiku-4-5` | Cheap throughput; Sanctum's `triage` bot already uses this path |
| Mermaid / DOT / structural visualization generation | `claude-sonnet-4-6` | `claude-opus-4-7` → `gpt-4o` | Strong at structural output; Sonnet beats Haiku for diagram completeness |
| Search / outline / trace over source | `agentgrep` (Rust binary, pending R9 verdict) | built-in Grep → `claude-haiku-4-5` semantic search | Structured packets > raw lines for agent consumption |
| Web research / external doctrine lookup | `WebSearch` (Claude) → `WebFetch` | `gpt-4o` (codex) → `claude-opus-4-7` | Claude's web tools first; OpenAI for cross-check |
| Code generation from spec | `claude-sonnet-4-6` | `claude-opus-4-7` → `gpt-4o` | Sonnet sweet-spot for codegen; Opus escalation on multi-file specs |
| Tool-using agentic tasks (long horizons) | `claude-opus-4-7` (1M) | `claude-sonnet-4-6` | Tool-use stability + context depth favor Opus 1M |
| Embedding generation / vector ops | `Ollama (nomic-embed-text)` or `Ruflo agentdb_embeddings` | `claude-haiku-4-5` (rare) | Embeddings are deterministic; cheapest local path wins |

## Sinister-project lane preferences

Per-project hints — used when the task class is ambiguous and the project lane is known.

| Project | Preferred primary | Why |
|---|---|---|
| Sinister Panel (TypeScript + Prisma + Next) | `claude-opus-4-7` (1M) for restructure; `claude-sonnet-4-6` for single-route | Recent Wave 1-7 work showed Opus 1M handles the cross-file restructures cleanly |
| Sinister Kernel APK (Kotlin + KSU modules) | `claude-opus-4-7` | Kotlin + native-build reasoning benefits from depth |
| Sinister Snap EMU (Python + protobuf) | `claude-sonnet-4-6` | Sonnet sweet-spot for protobuf + Python orchestration |
| Sinister TikTok API (Python + Frida) | `claude-sonnet-4-6` | Same |
| RKOJ Workstation (FastAPI + vanilla JS) | `claude-sonnet-4-6` for backend; `claude-haiku-4-5` for CSS/HTML polish | Backend logic vs UI tuning split |
| Sinister Vault (Python daemon + Gitea + Syncthing) | `claude-sonnet-4-6` | Backend Python plus deployment scripting |
| Sinister Forge (THIS project) | `claude-opus-4-7` | Architecture-design work; jcode pattern mining benefits from depth |
| Sinister-OS (future hardware) | `claude-opus-4-7` | Hardware design + low-level reasoning |
| Personal Project (operator-defined) | follows task class table | No lane hint |

## AUP-RESPECT integration

Every routing decision honors the AUP-RESPECT contract (CONTRACT 3). If a candidate provider would refuse a task that the operator authorized on their own infrastructure (e.g., `Sinister-Panel` on operator's Hetzner, snap-EMU on operator's keyboxes), the routing layer documents the refusal in `_shared-memory/TIER-3-UNLOCK-PATHS.md` and falls through. **Never** route a refusal-prone provider to operator-third-party-targeting work — that would itself be AUP-violating.

## How to extend

To add a new task class or provider:

1. Add a row to the appropriate table above.
2. Commit with `Co-Authored-By: RKOJ-ELENO`.
3. No code wire-up needed in v1 (the doc IS the routing layer).
4. Forge sessions re-read this file at cold-start via `pre_warm_reads[]` (see CONTRACT 7 RESUME-POINT-DISCIPLINE).

In v2+, the routing logic moves into Ruflo `agentdb_semantic-route` — at which point this doc becomes the *training corpus* for the route classifier rather than the routing layer itself. Backwards-compatible: the doc stays canonical, the classifier learns from it.

## Open questions (future operator decisions)

- **Gemini integration:** the table mentions `gemini-2.0-flash` as a possible mermaid generator. Sanctum has no Gemini API key wired. Add later if operator wants the option.
- **Ollama model picks:** specific model names (`llama3.3:70b`, `qwen2.5:14b`, `nomic-embed-text`) are placeholders pending operator-confirmed local fleet. Update once `ollama list` is run.
- **Codex depth selection:** codex-companion has 3 depths (gpt-4o-mini / gpt-4o / o1-mini). The table picks per task; a routing-aware depth-selector could be added.
- **Cost budgets per task class:** v1 has no $/task budget; v2+ should add a `max_cost_usd` field to gate runaway sweeps.

## Multi-provider login (jcode-login parity — Forge PH17 dependency)

> **Operator directive 2026-05-21 (verbatim):** *"our commands will be sinister then the command"* + jcode `jcode login --provider <X>` screenshot.

`sinister login --provider <X>` (TODO `tools/sinister-login/` v0.2.0) manages per-provider tokens. Tokens land in **Sinister Vault** at `vault://providers/<provider>` — never plaintext env vars. Each row pins the provider's lane integration + AUP-RESPECT posture.

| Provider | `sinister login --provider` | Auth flow | Vault path | AUP-RESPECT notes |
|---|---|---|---|---|
| Claude (Anthropic) | `claude` | OAuth (Claude Code CLI) OR `ANTHROPIC_API_KEY` | `vault://providers/claude/token` | Primary fleet provider; canonical for Sanctum/Forge/Term/Freeze |
| OpenAI (ChatGPT / GPT-4o / Codex) | `openai` | API key | `vault://providers/openai/key` | Peer-review + reasoning second-opinion via `tools/codex-companion/` |
| Google Gemini | `gemini` | OAuth OR API key | `vault://providers/gemini/key` | Open question above — not yet wired; mermaid alt-renderer candidate |
| GitHub Copilot | `copilot` | GitHub OAuth (existing `gh auth`) | `vault://providers/copilot/token` | IDE-side completions only; not for autonomous sessions |
| Azure OpenAI | `azure` | Azure AD + endpoint | `vault://providers/azure/{endpoint,key}` | Enterprise / dealership-IT path (post-Freeze PH14 multi-tenant) |
| Alibaba Coding Plan | `alibaba-coding-plan` | API key + endpoint | `vault://providers/alibaba/key` | Region-specific; deferred until international scope opens |
| Fireworks | `fireworks` | API key | `vault://providers/fireworks/key` | Open-weight hosted (Llama / Mixtral / etc); fallback for Ollama-down |
| MiniMax | `minimax` | API key | `vault://providers/minimax/key` | Region-specific; deferred |
| LM Studio (local) | `lmstudio` | local-only (no key needed by default) | `vault://providers/lmstudio/endpoint` | Operator's local LM server; `--base-url http://127.0.0.1:1234/v1` |
| Ollama (local) | `ollama` | local-only | `vault://providers/ollama/endpoint` | Already in fleet for embeddings + small classifiers |
| OpenAI-compatible (custom) | `openai-compatible` | base URL + optional key | `vault://providers/openai-compatible/{base_url,key?}` | Catch-all for vLLM / TGI / LiteLLM / any OpenAI-shaped server |

### Provider × task-class compatibility (preferred fallback chain)

When routing falls through the table above, the order within each class is:

1. **Claude** family (primary for most classes)
2. **OpenAI** family (peer-review + reasoning fallback)
3. **Local** (Ollama / LM Studio) for embedding + classification + privacy-sensitive
4. **Hosted-open-weight** (Fireworks / openai-compatible) when local is down
5. **Regional** (Gemini / Azure / Alibaba / MiniMax) only when explicitly picked

### Login UX

```
sinister login --provider claude            # opens OAuth or prompts for key
sinister login --provider ollama            # confirms local endpoint reachable
sinister login --provider openai-compatible # prompts for base URL + optional key
sinister login --list                       # show all configured providers + token age
sinister login --logout --provider <X>      # revoke from vault
```

### Operator-action queue dependencies

- `ANTHROPIC_API_KEY` env var still listed in OPERATOR-ACTION-QUEUE.md — `sinister login --provider claude --use-env` reads from env when present, else prompts
- `OPENAI_API_KEY` env var — same pattern for `--provider openai`
- Vault MCP must be loaded for Vault-backed storage; falls back to `~/.sinister-login/` plaintext (with permission 0600) when Vault MCP unavailable
