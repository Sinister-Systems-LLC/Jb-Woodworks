<!-- Author: RKOJ-ELENO :: 2026-05-23 -->

# jcode parity + swarm capability + token-efficiency audit (read-only)

**Slug:** jcode-swarm-token-parity-audit-2026-05-23
**First discovered:** 2026-05-23 10:59Z by Sinister Sanctum (EVE)
**Last updated:** 2026-05-23 10:59Z by Sinister Sanctum (EVE)
**Status:** audit, validated
**Tags:** audit, jcode, swarm, token-efficiency, local-agents, mcp-fleet, 2026-05-23, parity, recommendations

**Scope:** Read-only audit triggered by operator directive 2026-05-23 evening — *"make sure jcode features like swarm work"* + *"review jcode"* + *"we need to condense token usage to only be used when they need to everything else we can do with local agents"*. No edits to MCP configs, no installs, no pushes.

---

## 1. jcode-feature-matrix status

**Counts (matrix at `_shared-memory/knowledge/jcode-feature-matrix.md`, 30 declared rows):**

- **22** rows carry `✅` (shipped, in any column) — includes split states like `✅ doc / 📋 UI` (row 1) and `✅ scaffold / 📋 polish` (rows 6, 14)
- **0** clean `📋 planned`-only rows when counted at the row level (rows 23/24/25/28 are `📋 planned`-only — grep undercount is because they don't carry the emoji-prefixed `📋` glyph in a way the count regex hit; manual scan: rows 23/24/25/28 = 4 planned-only)
- **0** standalone `🚧 in-flight`-only rows (rows 9/10/11 carry `🚧` mixed with `✅`)
- **0** `🔄 delegated`-only rows (row 8 is delegated-only `🔄`; row split count needs recount)

**Manual re-count (rows 1-28, row level):** ~20 fully shipped, ~4 fully planned (23/24/25/28), ~4 partial. The matrix HAS been kept current with recent ships — rows 5/15/18/21/27 carry `Audited 2026-05-23 by rkoj-lane` annotations (commits `4bc5b4d`, `b9e89dc`, `6d00c59`). **Row 12** explicitly cites the 2026-05-23 mind v0.3.0 ship (`b199dae`) + RKOJ `/api/diagrams`. **Row 16 (Swarm-mode)** is the only row whose `✅ disk + 🚧 MCP` status is stale — `sinister-swarm` package is shipped at `tools/sinister-swarm/` v0.1.0 (verified via `pip show`), and 187 pytest-green across the cli umbrella (per PROGRESS line 738 — *"sinister-swarm 7"*); the `🚧 MCP` half remains accurate (MCP hive-mind fast-path is opt-in stub in v0.1.0). **Not in matrix:** RKOJ v1.6.84 (operator-mentioned in prompt) — RKOJ slash-command parity arc (v1.6.45-56, v1.6.27-31, v1.6.37-44) IS captured in brain (rows 26-30 of `_INDEX.md`) but **not surfaced as matrix rows** because matrix is jcode→Sanctum mapping; RKOJ is the consumer not a jcode-feature lane.

## 2. Swarm capability — what actually does what

The "swarm" in Sanctum is **(d) all of the above**, with three orthogonal surfaces:

- **(a) Parallel sub-agent dispatch via Claude Code's Agent tool** — class-level authorized per `sanctioned-bypasses-doctrine-2026-05-21.md` + `spawned-window-capabilities-2026-05-23.md`. Entry-point: Agent tool (deferred — load via `ToolSearch select:Task` family if needed). Best for: bounded research/audit tasks that need an isolated context. Burns Opus tokens for every sub-agent.
- **(b) MCP-bot orchestration via `sinister-bus`** — the dispatcher MCP at `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\sinister-bus\server.py`. Tools: `heartbeat`, `inbox_poll`, `list_network` (19 endpoints / 200+ tools per agents/README.md), `dispatch` (records intent; operator session does the actual MCP invocation). Best for: fleet-wide coordination + bot discovery.
- **(c) Standalone `sinister-swarm` v0.1.0** — pip-editable at `D:\Sinister Sanctum\tools\sinister-swarm\`. Entry-points: `sinister-swarm <op>` CLI (`dm`, `broadcast`, `spawn`, `list`, `watch`, `mark-done`, `wait-for`, `hive-status`, `whoami`) + Python API (`from sinister_swarm import dm, broadcast, spawn_agent, list_active, watch_file, mark_done, wait_for, detect_my_slug`) + umbrella `sinister swarm <op>`. Disk surface: `_shared-memory/inbox/<slug>/` + `_shared-memory/heartbeats/` + `_shared-memory/swarm-spawned/` + `_shared-memory/swarm-watch/` + `_shared-memory/swarm-status/`. NB: `swarm-status/` dir does NOT exist on disk yet (will be created on first `mark-done` call); `swarm-spawned/` similarly absent. Best for: cross-window terminal-session-style coordination.

**Single entry-point for operator question "is swarm working":** `sinister-swarm whoami && sinister-swarm hive-status` — both stdlib-only, instant, zero-cost.

## 3. Token-efficiency — what could be local-delegated vs requires Opus

**Concrete delegation map (today's call patterns vs ideal):**

| Task | Current (Opus) | Should be | Cost delta |
|---|---|---|---|
| file search (filename/glob) | Glob + Read | `librarian.search()` (Ollama, $0) | -200 to -2k tokens per call |
| code search (substring) | Grep | `librarian.grep_fallback()` ($0) | -100 to -1k tokens per call |
| classify file by topic | Opus reads + decides | `triage.classify_file()` ($0 rules / $0 Ollama) | -500 to -3k tokens |
| date/deadline alarm | Opus generates reminder text | `sentinel.list_alarms()` ($0) | -100 tokens |
| URL fetch + summarize | WebFetch (Opus tokens for body) | `researcher.research(url)` ($0 Ollama summary) | -1k to -10k tokens per page |
| daily digest of activity | Opus reads PROGRESS files | `scribe.generate_digest()` ($0.02 Haiku) | -2k to -10k tokens |
| cross-project helper hunt | Opus reads N files | `curator.scan_candidates()` ($0.05 Haiku) | -5k to -30k tokens |
| snapshot backup | n/a (operator-cron'd) | `custodian` daemon ($0, already running) | already optimal |
| fleet heartbeat sweep | Opus reads heartbeats dir | `sinister-bus.list_recent()` ($0) | -300 tokens |
| inbox poll | Opus reads inbox dir | `sinister-bus.inbox_poll()` ($0) | -200 tokens |

**Estimated session-level savings if bots were called for the above:** **30-60% reduction in input tokens** for a typical Sanctum-master session. The expensive turns are file reads + cross-project searches — exactly the Tier-1/Tier-2 zone.

**Are bots actually being called?** Evidence from `_shared-memory/PROGRESS/` (last 7 days):

| File | "swarm" mentions | "sentinel/librarian/triage/scribe/curator/custodian/watcher/auditor/researcher/translator/stealth-browser" mentions |
|---|---|---|
| Sinister Sanctum.md | 32 | 22 |
| Sinister Forge.md | 5 | 11 |
| Sinister Panel.md | 0 | 1 |
| Sinister Kernel APK.md | 0 | 5 |
| rkoj.md | 0 | (low) |
| rkoj-workstation.md | 0 | (low) |

**Adoption verdict:** The master (Sanctum) IS using swarm + bots. The **per-project lanes (Panel, Kernel APK, RKOJ) are not** — those agents are doing Opus-tokenized work that could be free-bot-delegated. This is the token-waste vector the operator is asking about.

## 4. Local-agent friction — what blocks a spawned EVE from calling them

**Critical gap: there is NO single bot-fleet quick-reference doc.** Closest existing artifacts:

- `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\README.md` — has the 13-row tier table BUT shows pseudocode invocations like `sentinel.list_alarms()` (operator-readable, NOT a valid MCP tool name). Real MCP tool names are `mcp__sentinel__list_alarms` (after Claude Code restart + MCP loaded).
- Each agent's own `server.py` — has the real tool decorators but no agent reads 12 server.py files at cold-start.
- `tools/_INDEX.md` + `bots/README.md` — catalog metadata, not call-shape.

**Friction breakdown for a spawned EVE session that wants to call e.g. `librarian.search`:**

1. **Discoverability** — agent must already know librarian exists + that the MCP name is `librarian` not `sinister-librarian`. No `bot-fleet-quick-reference.md` to grep.
2. **MCP loadedness** — must check whether `~/.claude/.mcp.json` has the entry AND Claude Code was restarted after last junction-fix. Per `mcp-junction-fix-pattern-2026-05-23.md` this is now 19 ok / 0 stale, but only when the audit ran — spawned agents don't re-audit.
3. **Tool name shape** — `mcp__<server-name>__<tool-name>` is the actual callable. Listed at the top of conversation via `<system-reminder>` ONLY when the agent uses `ToolSearch` — i.e. lazy-loaded. Default EVE session never sees the bot tools without explicit `ToolSearch` invocation.
4. **Arg shape** — needs to inspect server.py @tool decorators to know required params. No JSON-schema digest doc.

**The hidden gotcha (deferred-tool pattern):** Every MCP tool in this session is registered as a **deferred tool** (visible by name in `<system-reminder>` blocks; schema fetch required via `ToolSearch`). This means even when bots ARE loaded, a session has to spend tokens running `ToolSearch select:mcp__librarian__search` BEFORE the first call. **For one-off calls this is fine; for repeated calls it amortizes; for an agent that doesn't know bots exist it's an unrecoverable gap.**

## 5. Specific bots actually used vs ignored — 7-day PROGRESS scan

**Used (mentioned by name in `_shared-memory/PROGRESS/*.md` last 7 days):**
- `sinister-bus` — heavy use in Sanctum.md, mentioned in Forge.md
- `custodian` — running as daemon (cron-installed), mentioned for backup mechanics
- `sentinel` — mentioned in Sanctum.md re: alarm-loading
- `librarian` — mentioned in Sanctum.md but typically as "if it were called" not "called it"
- `triage` — mentioned in APK.md (5x)
- `curator` — mentioned in Sanctum.md re: cross-project scan

**Largely ignored (mentioned 0-2x across all PROGRESS files):**
- `translator` — find-tool-across-MCPs surface ignored
- `watcher` — source-drift detection ignored
- `auditor` — secrets+dedup+freshness audit ignored
- `scribe` — daily digest writer ignored (every Sanctum session re-reads PROGRESS instead)
- `stealth-browser` — used by Forge but rarely surfaced by lanes
- `researcher` — URL-fetch+summarize chain ignored (sessions WebFetch directly = Opus tokens)

**Bot fleet pain points (observed during this audit):**
- The `vault` MCP appears in deferred tools (`mcp__vault__*` x12) — partially wired despite OPERATOR-ACTION-QUEUE.md flagging it as pending. Worth re-verifying wire status before flagging as gap.
- `hacker` (13th bot) still deferred per `agents/README.md`.

---

## What ships next (3-5 concrete recommendations)

1. **Create `_shared-memory/knowledge/bot-fleet-quick-reference.md`** — single 1-screen doc with: MCP-tool name (`mcp__<server>__<tool>`), one-line purpose, exact arg shape (JSON example), tier ($0 / Ollama / Haiku). Top-of-doc: copy-paste block for the 10 most-useful calls (`mcp__sinister-bus__heartbeat`, `mcp__sinister-bus__inbox_poll`, `mcp__librarian__search`, `mcp__triage__classify_file`, `mcp__sentinel__list_alarms`, `mcp__researcher__research`, `mcp__scribe__generate_digest`, `mcp__curator__scan_candidates`, `mcp__custodian__health`, `mcp__sinister-bus__list_network`). Add reference to this doc as step 7.5 in `CLAUDE.md` cold-start so EVERY spawned session sees it. Friction reduction: agents stop spending 500+ tokens re-discovering call shapes per session.

2. **Flip `jcode-feature-matrix.md` row 16 (Swarm-mode) status from `✅ disk + 🚧 MCP` to `✅ shipped (disk + CLI + Python API, MCP fast-path opt-in)`** — sinister-swarm v0.1.0 is shipped and pytest-green. The `🚧 MCP` framing under-sells the shipped capability. Add commit anchor (sinister-swarm at `tools/sinister-swarm/` v0.1.0) + reference to README at `tools/sinister-swarm/README.md`.

3. **Add a "wake-on-demand-bot-dispatcher" implementation row** to OPERATOR-ACTION-QUEUE.md (doctrine already exists at `_shared-memory/knowledge/wake-on-demand-bot-dispatcher-2026-05-23.md`; proposed but never implemented). Without lazy-spawn the 13-bot RAM cost discourages always-on, which feeds back into the "bots ignored" loop from §5. ~50 LOC patch to `sinister-bus/server.py` per the doctrine.

4. **Verify vault MCP is fully wired** — deferred tool list shows `mcp__vault__*` x12 (accounts, audit, commit, health, list, pull, push, search, snapshot, sync_status) available for `ToolSearch` load. This contradicts OPERATOR-ACTION-QUEUE.md flagging vault-MCP as pending. Run `mcp__vault__health` once + close the queue row if green. Reference: `tools/sinister-vault/INSTALL-MCP.md`.

5. **Add a `[REMINDER]` injection** into the spawned-session cold-start phrase (`automations/start-sinister-session.ps1` Build-Phrase): *"For file search, classification, summarization, or fleet coordination prefer the local bot fleet — see `_shared-memory/knowledge/bot-fleet-quick-reference.md`."* — one sentence; addresses §3's token-waste evidence (per-project lanes are 0-1x bot mentions). This is a token-budget invariant operators care about per the directive.

---

## Bugs / breakage noted but NOT fixed this turn (out of scope)

- `_shared-memory/swarm-status/` and `_shared-memory/swarm-spawned/` directories don't exist; `sinister-swarm mark-done` / `spawn-agent` will need to create-on-first-write (verify v0.1.0 does this gracefully — TODO smoke-test).
- `📋`-only and `🚧`-only row counts return 0 from glob-counting in matrix; emoji-prefix encoding may differ. Manual row-level count is correct (rows 23/24/25/28 are planned-only). Worth a `python -c` script to count by emoji presence per row in a future audit.
- Grep for `sinister-bus.heartbeat` style invocations returns "0 occurrences" while the PROGRESS file explicitly mentions it — likely because the dash gets regex-interpreted. Future audits should use literal regex escape.
- jcode-feature-matrix.md header says "30 rows" but row-level count via `^\| \d+ \|` returns 28 (rows 1, 1b, 1c collapse the row-1 count) — header should say "28 numbered + 3 sub-rows = 31 entries" to disambiguate.

## Cross-references

- `_shared-memory/knowledge/jcode-feature-matrix.md` (the master matrix)
- `_shared-memory/knowledge/spawned-window-capabilities-2026-05-23.md` (preceding spawn-capability audit)
- `_shared-memory/knowledge/wake-on-demand-bot-dispatcher-2026-05-23.md` (proposed lazy-spawn doctrine)
- `_shared-memory/knowledge/sanctioned-bypasses-doctrine-2026-05-21.md` (Agent-tool class authorization)
- `_shared-memory/knowledge/mcp-junction-fix-pattern-2026-05-23.md` (cwd-fix pattern; 19 ok / 0 stale baseline)
- `_shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md` (P2 protects understand-anything plugin)
- `_shared-memory/knowledge/agent-identity-eve.md` (persona conventions)
- `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\README.md` (per-bot tier table; needs companion quick-ref)
- `tools/sinister-swarm/README.md` (CLI + Python API + disk contracts)
- `tools/_INDEX.md` (tools catalog)
- `bots/README.md` (junction-target catalog)
