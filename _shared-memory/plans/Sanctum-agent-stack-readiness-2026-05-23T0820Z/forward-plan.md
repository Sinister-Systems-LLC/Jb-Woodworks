<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Sanctum :: Agent-Stack Readiness Review — Forward Plan

**Created:** 2026-05-23T08:20Z by EVE on Sanctum
**Operator directive (verbatim 2026-05-23):** *"create a plan to review all memory use etc of how we use agents and make sure we have all our features and all jcode features and we are using our custom terminals we made in the bat start file. all things like this so everything is complete efficent. all jcode token saving methods local agents. use docker if you need to and have everything auto start or idle, sleep until a agent needs it then the agent can call and use anything it needs to"*

## Decomposition — what the operator is asking for

8 concurrent readiness goals:

1. **Memory use audit** — all the ways agents read/write memory (forge-memory-bridge, brain entries, inbox/cross-agent, Ruflo, resume-points)
2. **All our features** — Sinister-stack tools at parity with vision
3. **All jcode features** — the 30-row capability matrix (`jcode-feature-matrix.md`)
4. **Custom terminals** — `Sinister Start.bat` → launcher v6 → mintty + git-bash + claude; also Sinister Term + RKOJ Qt embedded
5. **Token-saving methods** — compact mode + session-contracts.md reference instead of inline + resume-point pre_warm_reads + context-pruner
6. **Local agents** — the 13 bot agents + Ruflo + local Ollama (when configured)
7. **Docker** — Docker Desktop available but not running; sanctum-git + Ollama use it when on
8. **Auto-start / idle / wake-on-demand** — current: 11 Sinister scheduled tasks; goal: more services in always-ready-but-idle state

## Current-state snapshot (2026-05-23 08:20Z)

### Memory use surfaces (✅ all healthy)

| Surface | Tool | Status |
|---|---|---|
| Brain (knowledge graph) | `_shared-memory/knowledge/*.md` + `_INDEX.md` | ✅ 50+ entries, indexed |
| Working memory (writable) | `forge_memory_bridge.api.write/recall/delete` | ✅ round-trip tested 2026-05-23 |
| Resume-points | `_shared-memory/resume-points/<project>/<UTC>.json` | ✅ 19 in Sanctum/ + 3 in Sinister Sanctum/ |
| Cross-agent inbox | `_shared-memory/inbox/<slug>/*.json|*.md` | ✅ active, archives rotate >7d |
| Cross-agent broadcasts | `_shared-memory/cross-agent/*.md` | ✅ active |
| PROGRESS append-only | `_shared-memory/PROGRESS/<agent>.md` | ✅ all lanes maintain |
| Semantic memory (delegated) | Ruflo MCP (`mcp__ruflo__agentdb_*`) | ⚠️ Ruflo currently disconnected; reconnects on next Claude restart |
| Forge-memory (BM25 + TF-IDF) | `tools/forge-memory-bridge/` | ✅ installed + functions |
| Memory-graph visualization | `tools/memory-graph-render/` → mermaid | ✅ installed |
| Operator-directives hub | `D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md` (junction) | ✅ resolves via 2026-05-23 junction |

### Agent spawn surfaces (✅ all use --dangerously-skip-permissions per 2026-05-23 doctrine)

| Surface | Spawn pattern | Status |
|---|---|---|
| `Sinister Start.bat` → launcher v6 | mintty.exe → bash → claude | ✅ validated 03:54:55Z (commit `c763ce2`) |
| RKOJ Qt QProcess (per-card) | streaming `claude -p` via QProcess | ✅ shipped (v1.6.84+) |
| RKOJ Qt agent_window | popout window with own claude | ✅ shipped |
| Forge `spawn/claude.py` | subprocess `claude -p` | ✅ shipped |
| Window-manager `/ws/agent` | asyncio subprocess + websocket stream | ✅ shipped |

### jcode parity (`jcode-feature-matrix.md` 30 rows)

| Status count | Rows |
|---|---|
| ✅ shipped | 14 |
| 🚧 in-flight | 4 |
| 📋 planned | 11 |
| 🔄 delegated to Ruflo | 1 |

**11 planned rows** still need RKOJ-lane attention (already covered in 0710Z [ASK] to RKOJ).

### Custom terminals

| Terminal | What it is | Status |
|---|---|---|
| mintty + git-bash via launcher | the per-agent purple-tinted window | ✅ working |
| Sinister Term (`projects/sinister-term/`) | `python -m term` shell, also bundled in RKOJ.exe v1.4.0 | ✅ importable, embedded in RKOJ |
| RKOJ Qt embedded scrcpy mirrors | Devices tab phone-screen viewers (v1.6.73-76) | ✅ shipped |
| Windows Terminal `wt.exe` | optional outer-shell when present (preferred over plain cmd) | ✅ honored by .bat |
| Forge TUI (`projects/sinister-forge/source/forge/`) | multi-pane Textual TUI with Agents/Phones tabs | ✅ scaffold; PH planning in `PLAN.md` |

### Token-saving methods

| Method | Where | Status |
|---|---|---|
| Compact-mode cold-start phrase | launcher v6 `Build-Phrase()` — references `session-contracts.md` instead of inlining 6 contracts (saves ~3000 tokens/spawn) | ✅ shipped |
| 3-shape phrase library | scaffold/general/resume — not 9 inline templates | ✅ shipped in v6 |
| Pre-warm reads on resume | `pre_warm_reads[]` in resume-point JSON; child reads only those, not whole brain | ✅ shipped |
| Context-pruner background-rotate | `automations/context-pruner.ps1` hidden on session-start | ✅ exists |
| `/compact` proactive use | session-contracts.md CONTRACT 7 — agents `/compact` after >3 images or >20 file-reads/turn | ✅ doctrine |
| Multi-pane card collapse | RKOJ Qt v1.6.27 — collapsed cards drop from active context | ✅ shipped |
| Stream-json telemetry over `claude -p` | RKOJ Qt v1.6.11-18 — token-by-token + thinking-delta without `ANTHROPIC_API_KEY` | ✅ shipped |
| Token-budget warning + /budget gauge | RKOJ Qt v1.6.70 (jcode parity row 8b) | ✅ shipped |

### Local agents (13 bot MCP servers)

| Bot | Tier | Role | Status |
|---|---|---|---|
| sinister-bus | T1 | dispatcher + handoff replay | ✅ source on disk, compiles, mcp dep installed |
| sentinel | T1 | alarm + watchdog | ✅ has .venv |
| translator | T1 | language translation | ✅ has .venv |
| librarian | T2 | BM25 + FAISS recall | ✅ has faiss-cpu installed |
| watcher | T1 | file/process watchers | ✅ |
| auditor | T1 | audit runs | ✅ |
| triage | T1 | request triage | ✅ requests dep |
| scribe | T2 | Anthropic-API daily digest | ✅ needs ANTHROPIC_API_KEY |
| curator | T2 | code-scout via Anthropic | ✅ needs ANTHROPIC_API_KEY |
| custodian | T1 | 24/7 cleanup daemon | ✅ install-task.ps1 exists |
| stealth-browser | T2 | nodriver browser automation | ✅ |
| researcher | T1 | external info gathering | ✅ |
| vault | T1 | encrypted KV store | ✅ |

All 13 reachable via the new `D:\Sinister\Sinister Skills` junction (commit `a8b8a63`). Loads on next Claude Code restart.

### Docker state

```
Docker version 29.1.3 (CLI installed)
Docker Desktop daemon: NOT RUNNING  ❌
```

What uses Docker when running:
- `tools/sanctum-git/` — Gitea self-host (docker-compose.yml)
- `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\docker\` — Ollama models for Tier-2 bots
- Could host: containerized bots, sandboxed nano-banana, isolated browser-automation

**Operator decision needed**: enable Docker auto-start? Currently manual.

### Auto-start scheduled tasks (11 registered, all Ready)

```
RKOJ                            Ready    — RKOJ.exe at logon
SinisterAPKAutoPush             Ready    — kernel-apk git push at logon
SinisterAPKWatchdog             Ready    — every 5 min
SinisterCustodian               Ready    — 24/7 daemon
SinisterCustodian-DailyRestart  Ready    — daily restart
SinisterSanctumAutoPush         Ready    — every 30 min
SinisterSanctumDailyBackup      Ready    — daily
SinisterVault                   Ready    — vault daemon at logon
Sinister-daily-digest           Ready    — daily scribe runs
Sinister-fleet-monitor          Ready    — fleet heartbeat sweeper
Sinister-sheets-sync            Ready    — sheets sync
```

All "Ready" but per OPERATOR-ACTION-QUEUE the RKOJ + Vault tasks may have crashed on first run (LastTaskResult 0xC0000142 STATUS_DLL_INIT_FAILED). They still trigger on schedule — operator confirms or re-arms.

## Gap matrix — what's NOT ready

| # | Gap | Where | Impact | Owner |
|---|---|---|---|---|
| G1 | Docker Desktop not running | OS service | Tier-2 bots fall back to degraded path (no Ollama models) | operator |
| G2 | Ruflo MCP disconnected mid-session | `~/.claude/.mcp.json` consumer | Lost semantic-memory tools mid-flight | operator (restart Claude) |
| G3 | 11 jcode parity rows still 📋 planned | `jcode-feature-matrix.md` | Full jcode parity not yet hit | RKOJ agent |
| G4 | sinister_apk_mcp source folder empty | `_sinister-skills/02_MD_ARCHIVE/.../sinister_apk_mcp/` | MCP fails silently at boot | operator |
| G5 | No Docker auto-start | OS service | Manual Docker start every reboot | operator |
| G6 | No "wake-on-demand" service mesh | architecture | Bots run continuously OR not at all; no idle→awake transition | architecture |
| G7 | Sleep/idle pattern not implemented | each bot daemon | All bots either always-on (custodian) or always-off (most others) | architecture |
| G8 | Local model fallback path | librarian + Ollama | Currently no graceful "Ollama down → degraded TF-IDF only" handoff signal | librarian agent |

## Forward execution plan — R-rows

**Reversibility scale**: R0 read-only / R1 reversible / R2 commit-required / R3 destructive / R4 operator-gated.

### Phase A — Cleanup + close known gaps (this session, master-actionable)

| Row | Subject | Reversibility | Estimated effort |
|---|---|---|---|
| R1 | Drop cross-agent [ASK] to operator gating sinister_apk_mcp decision | R1 | 1 turn — done in previous turn via OPERATOR-ACTION-QUEUE update |
| R2 | Verify Docker Desktop scheduled-task option (operator click) | R0 | 1 turn — surface, document |
| R3 | Write the wake-on-demand architecture doctrine entry | R1 | 1 turn |
| R4 | Cross-reference all 11 jcode 📋 planned rows into a single status row in PROGRESS for RKOJ agent | R1 | 1 turn (already covered by 0710Z [ASK]) |
| R5 | Audit + harden token-saving paths (compact-mode regression check) | R1 | 1 turn |
| R6 | This forward-plan committed + linked from PROGRESS + OPERATOR-ACTION-QUEUE | R1 | this turn |

### Phase B — Operator-gated unblock (operator-touch this week)

| Row | Subject | Reversibility | Notes |
|---|---|---|---|
| O1 | Restart Claude Code (loads 12 MCPs + 14 plugins; reconnects Ruflo) | R0 | one-click; high-impact |
| O2 | Start Docker Desktop (or set auto-start) | R0 | unlocks Tier-2 LLM bots + sanctum-git |
| O3 | Decide on sinister_apk_mcp source (restore or remove) | R1 or R4 | operator picks |
| O4 | `pip install -e` for any tools still uninstalled (status: 15/15 now installed; check nothing regressed) | R1 | done; verify |
| O5 | Pull Ollama models for Tier-2 bots | R1 | per OPERATOR-ACTION-QUEUE 🟡 |
| O6 | Set `ANTHROPIC_API_KEY` env var | R0 | unlocks scribe + curator + chatbot |

### Phase C — Architecture extensions (multi-session, RKOJ + Forge + Sanctum lanes)

| Row | Subject | Owner | Status |
|---|---|---|---|
| C1 | Wake-on-demand bot dispatcher — sinister-bus extension to start a bot subprocess lazily when first called, idle-kill after N min | sinister-bus / Sanctum | planning |
| C2 | Bot subprocess container option — Docker-based isolation for stealth-browser + nodriver runs | architecture | planning |
| C3 | RKOJ Qt "Bot Status" tab — live status of 13 bots + start/stop controls | RKOJ | planning |
| C4 | Forge PH8 plugin/skill hot-reload | Forge | planned |
| C5 | RKOJ PH7 mermaid diagram panels in-TUI | RKOJ | planned |
| C6 | RKOJ PH13 claude-hooks integration | RKOJ | planned |
| C7 | Forge PH12 skill-discovery from external repos | Forge | planned |
| C8 | agentgrep (operator-gated cargo install) | Forge | planned |
| C9 | Sinister-branded mermaid renderer Rust fork | Sanctum (fork) → RKOJ (consumer) | planned |
| C10 | niri scrollable-tiling multi-pane | Forge | planned |
| C11 | Animated boot art | Forge (PH5) | planned |

## Architecture recommendation: wake-on-demand pattern

Operator's directive includes: *"have everything auto start or idle, sleep until a agent needs it then the agent can call and use anything it needs to"*.

Current state: bots are either always-running scheduled tasks OR always-off until manually invoked. No middle ground.

**Proposed pattern (R3 if implemented for real):**

```
[Agent] —calls—> sinister-bus.dispatch(target='librarian', payload={...})
[sinister-bus] —checks—> is librarian subprocess alive?
                          NO  → spawn it (subprocess.Popen, captures stdout/stderr)
                                 wait for "ready" line in stderr
                                 mark alive_until = now + 5min
                          YES → forward call, reset alive_until = now + 5min
[every 60s] sinister-bus scan: kill any subprocess where alive_until < now
```

Benefits:
- 13 bots don't consume RAM continuously
- Cold-start ~500ms (Python module import + MCP handshake)
- 5-min idle window means bursty work stays warm
- Operator can override with always-on for hot bots (custodian, sinister-bus itself)

Cost:
- ~50 LOC in `sinister-bus/server.py` to implement lazy-spawn + idle-kill
- Each bot needs a `start_kit` script (single entry: import + register + serve)
- Need a `bus.health(target)` tool to peek without waking

**Master-actionable**: I can draft this as a brain-entry doctrine + the 50-line patch to `sinister-bus/server.py`. Sibling-lane: sinister-bus is in `D:\Sinister Sanctum\_sinister-skills\12_LLM_ORCHESTRATION\agents\sinister-bus\` which is operator-owned + sibling-active. Drop an [ASK] to bus agent instead.

## Recommended next actions (priority-ordered)

### Master-actionable this session

1. R3 — write `wake-on-demand-bot-dispatcher-2026-05-23.md` brain entry capturing the proposed pattern
2. R5 — token-saving compact-mode regression check (verify launcher v6 phrase still ~3000 tokens lighter than v5 inline)
3. R6 — this forward-plan committed + referenced in PROGRESS + OPERATOR-ACTION-QUEUE

### Operator click-thru (in queue)

- O1 (restart Claude) — biggest single unblock
- O2 (Docker Desktop) — unlocks Tier-2 LLM bots
- O3 (sinister_apk_mcp) — closes the MCP gap

### Cross-agent (drop [DELEGATE] to right lane)

- C1-C11 — surface to RKOJ + Forge + sinister-bus via inbox messages

## Cross-references

- `_shared-memory/knowledge/jcode-feature-matrix.md`
- `_shared-memory/knowledge/sanctioned-bypasses-doctrine-2026-05-21.md` (updated 2026-05-23 block)
- `_shared-memory/knowledge/launcher-v6-concise-rewrite-2026-05-23.md`
- `_shared-memory/knowledge/spawn-validation-end-to-end-2026-05-23.md`
- `_shared-memory/knowledge/mcp-junction-fix-pattern-2026-05-23.md`
- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md`
- `automations/session-contracts.md`
- `projects/sinister-forge/source/PLAN.md` (PH1-PH15)
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` (2026-05-23 sections)
- `projects/rkoj/MANIFEST.json` (v1.6.86 component list)
