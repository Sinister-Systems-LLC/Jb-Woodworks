# Addendum — Freeze fix + fleet inventory (tools / bots / MCP)

> Author: RKOJ-ELENO :: 2026-05-25
> Triggered by operator 2026-05-25T~02:18Z: *"check if our local agent network. mcp server or something along those lines are causing the agents to randomly just freeze and same for my cmd window like i cant close then it all comes back we need to fix these things along with everything else take note"* + *"review also all tools we can make. all bots we have and mcp servers that we have that can be combined. made better etc. use overseer and get him working on the sinister sanctum project and trickle down to all projects so we have the infinite expand and improving loop"*
> Composes with: master plan `plan.md` (swimlanes 1-7) — this addendum adds swimlane 8 (freeze fix) and surfaces the inventory needed for swimlanes 5/6.

## TL;DR — what we found

**Freeze + zombie windows = a real fleet-wide stability bug.** Diagnostic snapshot at 2026-05-25T02:36Z:

| Process | Count | Total RAM | Note |
|---|---:|---:|---|
| conhost.exe | **92** | 705 MB | Each cmd/powershell/mintty spawns one. 92 = severe pile-up |
| powershell.exe | **26** | 2.3 GB | Scheduled task spawn-flood (8 in 8 seconds, ~5min cadence) |
| node.exe | 26 | 933 MB | MCP child processes per Claude session |
| claude.exe | **14** | 7.7 GB | 6 spawned in 1 minute at 21:17Z (iter-30 7-agent parallel spawn) |
| cmd.exe | 29 | 121 MB | Console host overflow |
| mintty | 14 | 239 MB | One per Claude session window |

**12 scheduled tasks failing** with non-zero LastResult codes:
- 4 returning `4294770688` (0xFFFD0000 — Windows shutdown / task host crashed mid-run): SinisterAPKAutoPush, SinisterAPKWatchdog, SinisterCustodian, SinisterSanctumDailyBackup
- 4 returning `1` (generic exec failure): RKOJ, SinisterCustodian-DailyRestart, SinisterScrcpyP1, SinisterScrcpyP2, SinisterVault
- 2 returning `2` (file not found): Sinister-fleet-monitor, Sinister-sheets-sync
- 1 returning `2147942667` (0x8007010B — directory not found): Sinister-daily-digest

**6 zombie claude/mintty sessions** older than 4 hours (oldest 7.1 hr).

**Ollama not a Windows service** — running as user-mode process. Scheduled tasks running as SYSTEM cannot reach the 13 Ollama-backed bots.

## Root cause map (highest probability ranked)

1. **The "comes back" pattern = host-crash scheduled tasks auto-restarting.** 4 tasks (APKAutoPush + APKWatchdog + Custodian + SanctumDailyBackup) are failing on EVERY fire with task-host-crash. The next scheduled fire (5-30 min later) starts a fresh instance → operator closes window → 5 min later a new one spawns. **Most likely the primary "comes back" symptom.**
2. **Spawn flood = simultaneous cadence on watchdog tasks.** SinisterMeshCoordSweep + SinisterToolAutotrigger + SinisterOverseer + SinisterAPKWatchdog + SinisterLoopRelentlessWatchdog + Sinister-fleet-monitor all on ~5min cadence → 6 powershell spawns per cycle × 12 cycles/hour = 72 ps spawns/hour. 26 currently active = ~3-4 cycles worth still alive.
3. **MCP child process pile-up.** 14 claude × ~2 node MCP children each = 28 node processes. If any MCP hangs on init (especially install-time hangs for dormant `playwright`/`context7`/`memory`/`sequential-thinking`), the parent claude session blocks. **"Can't close" = parent in a syscall waiting on MCP handle.**
4. **Ollama context mismatch.** 13 local bots (librarian / sentinel / triage / etc) depend on Ollama. Ollama is user-mode, not a Windows service. Scheduled tasks as SYSTEM context fail to reach it → silent failures → no log → operator doesn't see → bots "freeze" from operator perspective.

## Operator-actionable fixes (priority order)

| # | Priority | Action | How |
|---|---|---|---|
| **F1** | 🔴 HIGH | Reap zombies | `powershell -File automations\diagnose-fleet-freeze.ps1 -KillZombies -Confirm` (kills 6 sessions > 4 hr) |
| **F2** | 🔴 HIGH | Investigate 4 host-crash tasks (4294770688) | Read the action logs; very likely missing `-WindowStyle Hidden` + missing redirected stdio causing the host crash on terminal-attached run |
| **F3** | 🟡 MED | Register Ollama as Windows service | `sc.exe create Ollama binPath='C:\\Program Files\\Ollama\\ollama.exe serve' start=auto displayname='Ollama LLM Server'` → restart bots |
| **F4** | 🟡 MED | Stagger scheduled task cadences | SinisterMeshCoordSweep + ToolAutotrigger + Overseer + APKWatchdog + LoopRelentlessWatchdog + fleet-monitor should NOT all fire on the 5-min grid. Spread to 5/6/7/8/9/10 min offsets |
| **F5** | 🟢 LOW | Disable dormant MCP servers in `~/.claude.json` | playwright / context7 / memory / sequential-thinking are wired but install scripts not run → potential hang on init |

## Swimlane 8 — Freeze + zombie monitor (new, ADDS to master plan)

**Status:** 🟢 shipped this turn — `automations/diagnose-fleet-freeze.ps1` (~200 LOC, 5 finding categories, JSON output, optional -KillZombies -Confirm)
**Cost:** ~3s per diagnosis run
**Risk:** zero by default; -KillZombies -Confirm is opt-in
**Lift:** observability + remediation of fleet-stability issues — composes directly with `quantum-fleet-100x` (a frozen fleet ships 0× of anything)
**Next iter:** wire into `SinisterOverseer` polling so the diagnosis runs every 30 min hidden, emits a `fleet-update kind=fix priority=high` row when zombies > 5 OR conhost > 50 OR scheduled-task failure count > 3

---

## Fleet inventory (tools / bots / MCP — synthesized from 3 parallel sub-agents)

### A. Tools (19 in `tools/_INDEX.md`)

Key clusters:
- **Memory:** forge-memory-bridge, memory-graph-render, sinister-vault, sanctum-backup
- **Coordination:** sinister-swarm, sinister-watchdog, sinister-bus, sinister-cli
- **External I/O:** sinister-browser, sinister-crawler, stealth-browser, nano-banana
- **Identity:** eve-picker, sinister-login, claude-accounts
- **Quality:** sinister-review, codex-companion, auditor, sinister-utils
- **Discovery:** mcp-discover, translator
- **Image:** nano-banana (Gemini wrapper)

**Highest-leverage NEW tool to build (gap analysis):**
1. **`sinister-trace-collector`** — end-to-end latency + memory + CPU tracing across DM → broadcast → spawn chains. Watchdog only does liveness; we have no observability into "why did this run take 3 min vs 30s yesterday".
2. **`sinister-operator-mode`** — wrap `sinister-cli` with utterance → intent → tool-dispatch logging to forge-memory for replay/training (jcode-operator-mode parity). Composes with operator-utterance-tracking-doctrine.
3. **`sinister-schema-compat`** — schema/version contract for every tool's output JSON; sinister-utils `fleet_test` adds compat matrix.

### B. Bots (13 in `bot-fleet-quick-reference.md`)

| Tier | Bots | Cost | Use for |
|---|---|---|---|
| Tier 1 (Python, free) | sentinel · translator · watcher · auditor · sinister-bus · custodian · stealth-browser · vault | $0 | Routine I/O + coordination + secrets scan |
| Tier 2 (Ollama, free) | triage · librarian · researcher | $0 (Ollama-deps) | File classify · RAG over 8.5k .md · scrape→summarize |
| Tier 3 (Anthropic, paid) | scribe · curator | ~$0.02-0.05/call | Daily digest · code-library scout |

**Token-tier routing — codify into doctrine (swimlane 5):**

| Task | Right bot | Avoid |
|---|---|---|
| Deadline / date check | sentinel | Asking Opus to track dates |
| Find a brain entry | librarian | Grep + manual read |
| Secrets/dedup scan | auditor | Regex guessing in prompt |
| File-purpose classify | triage | Haiku LLM call per file |
| Web summarize | researcher | Pasting HTML into Opus |
| Pre-edit safe checkpoint | custodian | Manual git stash |
| Helper-extraction scout | curator | Opus loop over 50 files |
| MCP tool find | translator | Memorizing 19 server names |
| Cross-agent message | sinister-bus | Direct calls bypass audit |
| Source-drift detect | watcher | Manual diffs |

**Underused bots:** watcher, translator, transcriber (potentially decommissioned — needs audit).

### C. MCP servers (~18 wired, several dormant)

**Active:** eve, sinister-panel, sinister-snap, sinister-tiktok, letstext, letstext-admin, sentinel, translator, librarian, watcher, auditor, sinister-bus, triage, scribe, curator, custodian, stealth-browser, researcher (mostly Ollama-bridged).

**Dormant (install pending):** playwright, context7, sequential-thinking, memory (the official MCP memory server). **Note:** these dormant servers may be a freeze-cause if their init handshake hangs.

**Ruflo MCP (~200 sub-tools across 20+ namespaces):** observed via deferred-tool list at session init. Highest 100×-relevant sub-tools:
1. `hive-mind_spawn` / `hive-mind_consensus` — BFT cross-agent voting → swimlane 6 parallel fan-out
2. `agentdb_pattern-search` + `agentdb_hierarchical-recall` — semantic vector recall → swimlane 7 (compounds with forge-memory swimlane 1)
3. `memory_search_unified` — cross-session semantic search → swimlane 7
4. `hooks_intelligence_pattern-store` — persistent learning store → swimlane 4 QKMS lessons feedback
5. `workflow_execute` — dependency-aware multi-step orchestration → replaces sequential bash chains
6. `embeddings_rabitq_search` — 32× compressed quantized vectors (50 MB for 1.66 GB brain per `quantum-fleet-discipline-doctrine`)
7. `neural_train` — SONA self-improvement → adaptive agent tuning
8. `coordination_consensus` — BFT decision voting → cross-machine trustless coord
9. `daa_workflow_execute` — decentralized autonomous workflow
10. `agent_spawn` — cost-tracked dispatch with swarm registration

**MCP gaps:**
1. Ruflo swarm coordinator wiring to Sanctum 19-bot fleet (currently parallel ecosystems, not composed)
2. ADB / Android device-control MCP (per Snap/TikTok lanes)
3. Real-time cost-governance MCP (token budgeting + spend alerts per agent)

---

## Overseer activation (operator: "use overseer and get him working on the sinister sanctum project and trickle down to all projects")

Overseer is real and partially wired:
- `automations/overseer-agent.ps1`
- 6 brain entries: charter / doctrine / token-efficiency / unified-improvement-engine / lessons-from-first-audit / audit-sinister-term
- 2 scheduled tasks LIVE: `SinisterOverseer` (5min cadence) + `SinisterOverseerDistribute` (30min cadence)
- Per-project recipes: `projects/sinister-overseer/config/improvement-recipe.json` with 3 attached (eve-compliance / sinister-chatbot / sinister-sleight)

**Gap to close (swimlane 9 — Overseer fleet activation):**
1. **Add sinister-sanctum to improvement-recipe.json** — currently the umbrella has no recipe; overseer can't trickle Sanctum-class improvements.
2. **Add every per-project lane to improvement-recipe.json** — kernel-apk, snap-emu, panel, chatbot, letstext, jb-woodworks, showmasters, freeze, generator, term, os, os-mobile, imessage-bridge, sleight, snap-api-quantum, emulator-bundle. Each gets a 5-line recipe stub.
3. **Wire diagnose-fleet-freeze.ps1 into Overseer's Sensor layer** — when freeze symptoms detected, Overseer emits high-priority fleet-update rows + creates inbox pokes per the new LOOP-RELENTLESS doctrine.
4. **CrossProjectAggregator already exists** — once recipes are attached, the "infinite expand + improve loop" runs by itself.

**Status:** 🟡 designed but not shipped this turn (the freeze-fix took priority). Iter-115 swimlane 9 candidate.

---

## Composability map (what 100× actually means)

```
Operator utterance
   ↓
operator-utterance-tracking (already shipped)
   ↓
overseer Sensors poll → WatchBus dedup → Detector classify (Haiku)
   ↓                                       ↑
Triage diagnose (Sonnet) → Contradiction Engine (Haiku) → Proposer (Opus, rare)
   ↓
ApplyGate → low-risk auto-fix | high-risk → operator inbox
   ↓
LessonsStore → CrossProjectAggregator → fan-out to similar lanes
   ↓
fleet-update channel high-priority broadcast
   ↓
each lane reads update on next /loop tick (RELENTLESS rule 8) → SHIP THIS TURN
   ↓
forge-memory write outcome → indexed for recall (210 brain entries already there post-swimlane-1)
   ↓
forever-improve audit → improvement-log row
   ↓
(loop continues — operator's "infinite expand + improve" pattern)
```

Each arrow is a tool/bot/MCP. The compound multiplier is the LOOP, not any single arrow.

## Pass criterion for this addendum

1. ✅ `automations/diagnose-fleet-freeze.ps1` exists + runs clean (smoke-tested 2026-05-25T02:36Z)
2. ✅ Diagnostic JSON written to `_shared-memory/diagnostics/fleet-freeze-2026-05-25T023619Z.json`
3. ✅ 6 zombies surfaced + 12 failing tasks surfaced + Ollama-not-a-service surfaced
4. ✅ Inventory of 19 tools + 13 bots + 18 MCP + Ruflo sub-tools synthesized
5. ✅ Overseer activation plan named (swimlane 9, queued for next /loop iter)
6. ✅ 5 operator-actionable fixes F1-F5 ranked

## Composes with

- `quantum-fleet-100x-master-plan-2026-05-25T0128Z/plan.md` (swimlanes 1-7 + this 8 + queued 9)
- `_shared-memory/knowledge/no-visible-powershell-windows-doctrine-2026-05-25.md` (the visible-window scheduled-task audit)
- `_shared-memory/knowledge/loop-relentless-pursuit-doctrine-2026-05-25.md` (rules 8-11 driving SHIP-THIS-TURN cadence)
- `_shared-memory/knowledge/overseer-unified-improvement-engine-2026-05-24.md` (the 6-slice engine this addendum activates)
- `_shared-memory/knowledge/bot-fleet-quick-reference.md` (the bot routing table this addendum codifies)
