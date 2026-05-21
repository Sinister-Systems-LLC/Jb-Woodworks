# Sinister Term :: master plan 2026-05-21

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane:** `sinister-term`
> **Operator directives this session:**
> - 2026-05-21T11:00Z — *"i want everything to be our own shit. like what he did here so we can have our own terminal"*
> - 2026-05-21T11:55Z — *"i want all jcode features here … we are going to add all jcode features. like swarm so prepare for all that and adding into rkoj workstation etc"*
> - 2026-05-21T12:00Z — *"our command will be sinister then the command"*
> - 2026-05-21T12:05Z — *"i want to do our term just like the jehuang did it in the repo … make sure we are working towards this"*

## Scope clarification (layer-honest)

There are TWO jehuang reference projects, and they live at different layers. We mine BOTH, but they target different surfaces in our stack.

| Reference | Layer | Our parity surface |
|---|---|---|
| **handterm** | VT100/VT220 terminal emulator (PTY owner, GPU glyph renderer, IPC socket protocol) | Windows Terminal / ConHost already provides VT parsing, glyph rendering, scrollback, mouse, clipboard. We DON'T re-implement those. We DO mine the **IPC socket protocol** (`handterm @ open-window / send-text / get-text / send-key / set-title / close / ls`) — that becomes our `sterm-ipc` JSON-over-TCP-localhost server. |
| **jcode** | AI CLI tool (provider routing, swarm, memory, browser, sessions, skills) | This is our actual peer. Every jcode capability maps to a Sinister project lane. Sinister Term owns the CLI namespace + shell + IPC + swarm composition. |

## CLI namespace (operator directive: "sinister then the command")

The shipping CLI binary is `sinister` (plus `sterm` legacy alias). Subcommand layout:

| Subcommand | jcode parity | Owner agent | Status |
|---|---|---|---|
| `sinister start` (default) | `jcode` | sinister-term | this session |
| `sinister run <line>` | `jcode run <command>` | sinister-term | this session |
| `sinister resume [name]` | `jcode --resume <name>` | sinister-term | this session |
| `sinister ctl <cmd>` | (handterm @) | sinister-term | this session (IPC client) |
| `sinister swarm <spawn\|list\|dm\|broadcast\|watch>` | jcode swarm tool | sinister-term composes; sanctum owns inbox/cross-agent | this session |
| `sinister login --provider <name>` | `jcode login --provider <name>` | OPERATOR-ONLY stub this session; full flows = future session (touches _vault/) |
| `sinister auth-test` | `jcode auth-test` | OPERATOR-ONLY stub | future |
| `sinister provider <list\|add>` | `jcode provider add` | OPERATOR-ONLY stub | future |
| `sinister serve` | `jcode serve` | sinister-term | next session (IPC already gives us most of this) |
| `sinister connect` | `jcode connect` | sinister-term | next session |
| `sinister dictate` | `jcode dictate` | DELEGATED → operator's STT command + Sanctum tool? | future |
| `sinister browser <action>` | `jcode browser <action>` | DELEGATED → `_shared-memory/knowledge/agent-browser-bridge-pattern.md` Sanctum | future |
| `sinister memory <recall\|write\|list>` | jcode memory tools | DELEGATED → forge-memory-bridge (already shipped) | shipped via shell builtin `/memory-recall` |
| `sinister help`, `sinister version` | `jcode help` | sinister-term | this session |

## Interactive slash-commands (already shipped + jcode parity additions)

| Slash | jcode parity | Status |
|---|---|---|
| `/forge` `/mind` `/launch` `/projects` `/heartbeats` `/commits` `/bot` `/skill` `/cd` `/help` `/clear` `/exit` | n/a (our own) | ✅ PH1-PH6 |
| `/inbox` `/cross-agent` `/ca` `/ask` `/progress` | parity for jcode swarm DM/broadcast inside session | ✅ PH9-PH10 |
| `/memory-recall` `/memory-write` `/memory-list` (`/mr` `/mw` `/ml`) | parity for jcode explicit memory tools | ✅ PH13 |
| `/account` | jcode `/account` — switch provider account | 📋 PH-CLI-LOGIN (operator-only flow) |
| `/alignment` | jcode `/alignment` — centered mode | 📋 future (low priority) |
| `/Resume` | jcode `/Resume` — cross-harness resume | 📋 future (sanctum owns cross-harness) |
| `/swarm <spawn\|list\|dm\|broadcast>` | jcode swarm tool inside session | 📋 PH-SWARM this session |
| `/conflict` `/diff-watch` | jcode "code shifting under its feet" file-edit notification | 📋 PH-SWARM-WATCH future session |
| `/dictate` | jcode dictate inside session | 📋 future |
| `/login` | jcode `/login` inside session | 📋 future |
| `/serve` `/connect` | jcode server/client inside session | 📋 PH-SERVE future |

## Keybinding parity

| jcode keybinding | Action | Our binding | Status |
|---|---|---|---|
| Alt+C | centered text mode | not yet mapped | 📋 future low-pri |
| Shift+Enter | queue input (wait for current turn) | n/a (we don't have a "turn" — we exec directly) | n/a |
| Enter | immediate send | implicit | ✅ |
| (jcode doesn't ship a /forge etc) | n/a | Ctrl+L=clear / Ctrl+F=/forge / Ctrl+N=/mind / Ctrl+H=/heartbeats / Ctrl+I=/inbox / Ctrl+P=/projects | ✅ PH11 |

## IPC API surface (handterm @ parity, our extensions)

The IPC server runs on `127.0.0.1:5081` (next free port after Forge :5078 / Mind :5079 / RKOJ :5077). Bearer token written to `_shared-memory/sterm-ipc-token.txt` (gitignored, machine-local). JSON-over-TCP request/response.

### handterm parity endpoints

| Endpoint | handterm equivalent | What it does |
|---|---|---|
| `health` | `handterm @ ls` | { ok, version, pid, ts_utc, cwd } |
| `state` | (no direct equivalent) | { cwd, project, branch, inbox_count, freshest_heartbeat, history_lines } |
| `send-text <text>` | `handterm @ send-text` | Insert text into the current prompt buffer (does not submit) |
| `send-key <key>` | `handterm @ send-key` | Synthetic keystroke (e.g. `enter`, `c-l`) |
| `get-prompt` | `handterm @ get-text` | Current FormattedText prompt segments as JSON |
| `get-toolbar` | (no direct equivalent) | Current FormattedText toolbar segments |
| `get-history [limit]` | (no direct equivalent) | Tail of history.jsonl |
| `set-title <title>` | `handterm @ set-title` | Change console title |
| `close` | `handterm @ close` | Exit sterm gracefully |
| `ls` | `handterm @ ls` | List all running sterm IPC sessions on this host |
| `dispatch <line>` | (our extension) | Run a slash command synchronously; return CommandResult |

### Sinister extensions

| Endpoint | What it does |
|---|---|
| `subscribe <event>` | SSE-style streaming for `heartbeat`, `inbox-arrival`, `dispatch`, `prompt-change` |
| `swarm-spawn <project>` | Delegate to start-sinister-session.ps1 (sanctum lane) |
| `swarm-broadcast <message>` | Write to cross-agent/ (composes existing pattern) |

## Swarm composition (jcode swarm parity → our existing infrastructure)

jcode swarm has 4 capabilities. We map each to existing Sanctum-owned infrastructure:

| jcode swarm feature | Our implementation | Status |
|---|---|---|
| Spawn agent in same repo | `start-sinister-session.ps1` (sanctum) + per-project worktree | ✅ shipped (sanctum) |
| Server-managed coordination | Disk-first (`_shared-memory/inbox/` + `_shared-memory/cross-agent/`) + optional Ruflo MCP hive-mind fast-path | ✅ shipped (sanctum + ruflo MCP) |
| DM one agent | `/ask <agent> <message>` writes `inbox/<agent>/<ts>-ask-from-sinister-term.json` | ✅ PH9 |
| Broadcast to all | `_shared-memory/cross-agent/<ts>-broadcast.md` convention | ✅ existing |
| File-edit notifications | Brain entry `multi-agent-branch-contention-isolation-pattern.md` documents the failure mode + git update-ref recovery | 📋 PH-SWARM-WATCH for the proactive notification |
| Conflict resolution | `git diff` + brain entry `verify-head-before-commit-multi-agent.md` | ✅ doctrine shipped |
| Autonomous swarm spawn | Sanctum's `Start-Sinister-Session.bat` + agent-prefs.json + canonical-10 lane discipline | ✅ already a-canonical pattern |
| Headed vs headless | `start-sinister-session.ps1 -Headless` mode | ✅ existing |

So `sinister swarm` is mostly a thin CLI surface composing existing pieces.

## Memory composition (jcode memory parity → forge-memory-bridge)

| jcode memory feature | Our implementation | Status |
|---|---|---|
| Semantic embedding per turn | Ruflo `embeddings_generate` MCP tool | 🔄 delegated to ruflo |
| Cosine similarity memory recall | `forge_memory_bridge.recall()` (TF-IDF default) + Ruflo `agentdb_pattern-search` (MCP fast-path) | ✅ v0.1.0 shipped, has known bug in write() (sanctum bug report 11:50Z) |
| Sideagent memory extraction | Cron via `automations/memory-consolidate.ps1` (Sanctum) | ✅ shipped |
| Explicit memory tools | `/memory-recall` `/memory-write` `/memory-list` in Sinister Term | ✅ PH13 (with monkey-patch workaround for write bug) |
| Session-RAG | `_shared-memory/sinister-term-history/history.jsonl` + future `sinister search-history <query>` | 📋 future |
| Ambient consolidation | `automations/memory-consolidate.ps1` (Sanctum) | ✅ shipped |
| Graph consolidation (staleness + conflicts) | `forge_memory_bridge.consolidate()` | ✅ shipped (untested) |

## Provider login (jcode parity, all OPERATOR-ONLY)

Per canonical-3 AUP-RESPECT + canonical-10 lane discipline, _vault/ + auth tokens + API keys are operator-owned. Our stub:

```
sinister login --provider <name>
  -> prints: per-provider instructions + the operator-facing CLI/URL they need
  -> never auto-executes auth (no headless OAuth, no token mint)
  -> writes a TODO to OPERATOR-ACTION-QUEUE.md
```

Supported providers (parity surface only, exec deferred to operator):

claude / openai / copilot / gemini / azure / alibaba-coding-plan / openrouter / openai-compatible / opencode / opencode-go / zai / kimi / 302ai / baseten / cortecs / deepseek / firmware / huggingface / moonshotai / nebius / scaleway / stackit / groq / mistral / perplexity / togetherai / deepinfra / fireworks / minimax / xai / lmstudio / ollama / chutes / cerebras / cursor / antigravity / google

Headless flags ported: `--no-browser` / `--print-auth-url` / `--json` / `--callback-url <url>` / `--auth-code <code>` / `--complete`. These produce the right scaffolding output even though we don't execute the auth.

## Sibling integration hooks

| Sibling | What they need from us | What we need from them | Status |
|---|---|---|---|
| **Sanctum** | Term IPC endpoint `state` for status dashboards. Term `swarm-spawn` delegates to their `start-sinister-session.ps1`. | Fix `forge_memory_bridge.api.write()` shadowed-list bug (bug report filed 11:50Z). Confirm OPERATOR-ACTION-QUEUE entries for `sinister login` flows. | 1 ASK filed, 1 BUG filed |
| **Forge** | Term IPC `state` + `dispatch` so Forge can show + drive a sterm pane. Term `/forge` already inline-boots Forge. | Forge can call our IPC to render a "Sinister Term" tab in Claw / RKOJ workstation. Forge spawns its own swarm agents via our `swarm-spawn` (which routes to Sanctum's launcher). | 1 ASK filed (wayward commit 11:45Z) |
| **RKOJ** | Term IPC `state` + `subscribe` (SSE stream of state changes). RKOJ embeds a live Term pane next to Agents tab. | RKOJ should add a "Sinister Term" surface to their workstation per `rkoj-workstation-ui-layout.md` doctrine. | ASK to be filed this session |
| **Panel** | Term IPC `health` for fleet-health dashboard. | Panel surfaces sterm-IPC liveness on the Command Center. | Optional this session |
| **APK** | n/a (lane is Android keybox, no Term integration) | n/a | none |

## Phase roadmap

Shipped this session:
- PH7-PH14 (committed in `0e8490d`, `b321b6b`, `500c3ae`, `36df2c5` on `agent/sinister-term/ph7-resume-2026-05-21`)

Next slice (this session continues):
- **PH-CLI** `sinister` CLI namespace (subcommand dispatcher) — entry point rename
- **PH15** `Sinister.bat` one-click launcher on Desktop
- **PH16** `sterm-ipc` server (handterm @ parity, JSON-over-TCP-localhost, bearer auth)
- **PH17** `sinister ctl <cmd>` CLI client
- **PH-SWARM** `sinister swarm <spawn|list|dm|broadcast>` thin composition
- **PH-LOGIN** `sinister login --provider <name>` stub (operator-only)
- **PH-RUN** `sinister run <line>` non-interactive one-shot dispatch
- **PH-RESUME** `sinister resume [name]` reads latest resume-point
- **PH-PROVIDER-STUB** `sinister provider list|add` stub
- **PH-BROWSER-STUB** `sinister browser status|setup|<action>` stub → delegates to Sanctum agent-browser-bridge work
- **PH18** IPC tests (auth + every endpoint + concurrency)
- **PH19** Brain entry: `sterm-ipc-pattern.md` + flip jcode-feature-matrix.md rows
- **PH20** Cross-agent updates to Sanctum + Forge + RKOJ

Future sessions:
- PH-SERVE `sinister serve` (persistent background server) + PH-CONNECT `sinister connect`
- PH-DICTATE — needs operator's STT command
- PH-BROWSER full — Firefox Agent Bridge integration (Sanctum delegation)
- PH-LOGIN full — actual OAuth flows (operator-gated, _vault/ writes)
- PH-ACCOUNT `/account` switching inside shell
- PH-CACHE-WARN — Claude cache-cold UI warning
- PH-AGENTGREP — Sanctum delegation (matrix row 25)
- PH-SKILL-LAZYLOAD — Forge delegation
- PH-RKOJ-EMBED — RKOJ delegation
- PH-RUST — Track B (30 days after v0 proves out)

## Attribution

Per canonical-20: AGPL-3.0-or-later, NOTICES file credits jcode (Justin Huang, https://github.com/1jehuang/jcode) for inspiration. Our re-implementations carry `Author: RKOJ-ELENO :: <date>` headers; their code stays in `C:\Users\Zonia\Desktop\Github Research\jcode-0.12.3\` as read-only reference per canonical-22 (AGPL-quarantine for MIT-source code mining).

## Related

- `_shared-memory/knowledge/jcode-feature-matrix.md` (the 28-row capability map)
- `_shared-memory/knowledge/sibling-active-launch-coordination-pattern.md`
- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md`
- `_shared-memory/knowledge/verify-head-before-commit-multi-agent.md` (this session)
- `_shared-memory/knowledge/agent-browser-bridge-pattern.md` (Forge PH15 doc, future)
- `_shared-memory/knowledge/forge-bridge-rest-sse-pattern.md` (Forge :5078 bridge — our IPC pattern peer)
- `automations/agent-host-routing.md` (multi-provider doctrine, sanctum)
- `automations/start-sinister-session.ps1` (swarm-spawn target, sanctum)
- `projects/sinister-term/README.md` (lane README — phase table)
