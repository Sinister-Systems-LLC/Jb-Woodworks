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

## Multi-provider login (jcode-login parity — ✅ shipped 2026-05-21)

> **Operator directive 2026-05-21 (verbatim):** *"our commands will be sinister then the command"* + jcode `jcode login --provider <X>` screenshot.

`sinister login --provider <X>` is **shipped** as `tools/sinister-login/` v0.1.0 (commit `be1a821`). v0.1.0 reads keys from process env first; `~/.sinister/login.env` opt-in via `--allow-plaintext`. v0.2.0 will route to Sinister Vault at `vault://providers/<provider>` once vault-MCP is wired into `~/.claude/.mcp.json`. Each row pins the provider's lane integration + AUP-RESPECT posture.

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

### Login UX (v0.1.0 shipped commands)

```bash
sinister login providers              # list all 11 providers + configured/missing status
sinister login current                # which provider would the fleet use right now (preference-resolved)
sinister login doctor claude          # env-only diagnosis (no network)
sinister login doctor openai --probe  # opt-in TCP-handshake reachability (no HTTP body, no auth)
sinister login env claude             # print PowerShell `$env:ANTHROPIC_API_KEY=...` lines
sinister login add claude --key sk-... --allow-plaintext  # REFUSED unless --allow-plaintext (canonical-11)
sinister login matrix                 # print the jcode-feature-matrix row for this tool
```

### v0.2.0 planned additions (post vault-MCP)

```bash
sinister login --provider claude --oauth      # OAuth flow (delegates to Claude Code CLI)
sinister login --provider <X> --vault         # store in vault://providers/<X> instead of env-file
sinister login --logout --provider <X>        # revoke from vault
```

### Operator-action queue dependencies

- `ANTHROPIC_API_KEY` env var still listed in OPERATOR-ACTION-QUEUE.md — `sinister login current` resolves it ambiently when present
- `OPENAI_API_KEY` env var — already set this session; `sinister login current` resolves to openai when ANTHROPIC_API_KEY missing
- Vault MCP loading — `sinister login add --vault` (v0.2.0) gates on this; v0.1.0 falls back to `~/.sinister/login.env` only when `--allow-plaintext` is explicit

### Preference order override

`SINISTER_LOGIN_PREFERENCE=openai,claude,ollama` (env var) overrides the default order `claude > openai > gemini > fireworks > openai-compatible > lmstudio > ollama > copilot > azure > minimax > alibaba-coding-plan`. `resolve_active()` returns the first configured provider in that order.

## Per-provider routing posture (added 2026-05-21T14:10Z post sinister-usage ship)

> Mirror of the task-class table from the provider's perspective. When the dispatcher picks a provider first (e.g. operator said "use Ollama") and then needs to know what task classes it should accept, consult this. When the dispatcher picks a task class first, use the top-of-doc table.

| Provider | Primary for | Fallback for | Quota visibility (via `sinister-usage`) |
|---|---|---|---|
| `claude` (Anthropic) | Multi-file refactor (1M), deep reasoning, tool-using agentic, **Forge / Sanctum / Kernel-APK** primary | All Claude family fallback inside itself (Opus↔Sonnet↔Haiku) | ❌ console-only (`console.anthropic.com/settings/usage`) — `sinister-usage check claude` → endpoint_known=no |
| `openai` (GPT-4o / Codex) | Peer-review (gpt-4o-mini), reasoning second-opinion (o1-mini) | Multi-file refactor, code-gen from spec, mermaid generation | ✅ `/v1/usage` (bearer; date query-string required) — `sinister-usage check openai` returns full row |
| `gemini` (Google) | (none yet — operator-gated) | Mermaid / structural viz alt-renderer | ❌ GCP-billing aggregated; per-key endpoint not exposed |
| `copilot` (GitHub) | IDE-side completions only (NOT autonomous sessions) | — | ✅ `/user/copilot/billing` (bearer; personal-account endpoint) |
| `azure` (Azure OpenAI) | Enterprise-tenant / dealership-IT (post-Freeze PH14) | OpenAI primary fallback if direct API rate-limited | ❌ Azure Cost Management (not the OpenAI-shape API) |
| `alibaba-coding-plan` (Qwen / DashScope) | Region-specific deferred | — | ❌ DashScope console only |
| `fireworks` (open-weight hosted) | Hosted Llama / Mixtral when Ollama down | Local-fallback ladder (when both Ollama + LM Studio degraded) | ✅ `/inference/v1/usage` (bearer; tier-dependent; confirm field on current plan) |
| `minimax` | Region-specific deferred | — | ❌ platform.minimaxi.com console |
| `lmstudio` (local) | Privacy-sensitive, offline | Bulk classification when Ollama down | local — no quota, no cost; `sinister-usage check lmstudio` → auth=local, skipped from reports |
| `ollama` (local) | Embedding generation (`nomic-embed-text`), bulk classification (small models), privacy-sensitive (`llama3.3:70b`) | LM Studio when Ollama down | local — no quota; same as above |
| `openai-compatible` (vLLM / TGI / LiteLLM / Groq / Together / OpenRouter) | Catch-all when none of the named providers fit | Last-resort hosted fallback | varies; set `SINISTER_USAGE_OAI_COMPAT_URL` to override the registry entry |

### Composition with the v0.1.0 tools

The router consults `sinister-usage` at dispatch-time to skip providers with degraded quota visibility — but **quota is advisory, not gating** in v0.1.0 (no actual quota numbers returned). The router consults `sinister-login` to skip providers without a configured key (returning `provider_status()["configured"] = False`). Concretely:

```python
# Pseudocode the dispatcher should follow
from sinister_login import status_all, resolve_active
from sinister_usage import check as usage_check

def pick_provider(task_class):
    primary_chain = ROUTING_TABLE[task_class]  # from agent-host-routing.md
    for slug in primary_chain:
        st = next((s for s in status_all() if s["slug"] == slug), None)
        if st and st["configured"]:
            return slug
    return resolve_active()["slug"] if resolve_active() else None
```

### v0.2.0 promotion path

When `sinister-usage` ships `--remote` (v0.2.0), the dispatcher gains real quota numbers and can:
- Skip a primary that's at >95% of monthly quota
- Pick the fallback that has the largest remaining budget
- Refuse the task entirely if all providers in the chain are quota-exhausted
- Surface a `[QUOTA-LOW]` chip in Forge picker Q4 and Term toolbar

Until v0.2.0 lands, dispatchers should call `sinister-usage check <slug>` as a hint only — `endpoint_known=True` means "operator will be able to see real usage in console / dashboard", not "we currently know how much budget remains".
