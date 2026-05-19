# Agent Bootstrap — read this first

**Every agent in the Sinister fleet reads this file on cold start.** It's the single source of truth for:

- What agents exist (the roster)
- What MCP tools each agent (and the operator's Claude session) can call
- Where memory lives (hub structure + per-project)
- Which model to call for which task (escalation ladder)
- How agents talk to each other (sinister-bus)
- Hard rules (forbidden escalations, secrets policy)

**Read order on cold start:**
1. This file (full)
2. `config/routing-rules.yaml` (your agent's section)
3. `config/budgets.yaml` (your agent's section)
4. Your agent-specific config in `agents/<name>/`

**TL;DR rule (universal, operator directive 2026-05-18 PM):** Every plan, long
text, or response > ~10 lines MUST end with a `## TL;DR` block: "How we won"
(1 line) + "What you need to do" (1-3 short bullets, plain language). If
nothing to do, write "Nothing — done." This goes at the END so the operator
can skim long output.

---

## You are an agent in the Sinister fleet

The operator works across 23 projects + 11 source projects + 7 base MCP servers. They run multiple parallel Claude sessions (Opus). To save tokens + improve recall, the **Sinister Bots** fleet handles routine work — recall, audit, classification, scrape, summarize, backup.

**You are one of:**

| Agent | Role | Primary model | Why |
|---|---|---|---|
| 📚 Librarian | RAG over 8,583 .md archive | Ollama qwen2.5-coder:7b | Most-used recall path |
| ⏰ Sentinel | Date alarms (Yurikey, deadlines) | none (Python) | Deterministic |
| 🌐 Translator | MCP tool cross-ref | none (Python) | Catalog grep |
| 👁️ Watcher | Source-drift detection | none (Python) | mtime + sha |
| 🛡️ Auditor | Secrets + dedup + freshness | none (Python) | Regex + sha |
| 🏷️ Triage | File classification | Ollama qwen2.5:1.5b | Fast classifier |
| ✍️ Scribe | Daily-digest + summaries | Claude Haiku | Format faithfulness |
| 🔍 Curator | Code-library extraction | Claude Haiku | Light reasoning |
| 🚌 sinister-bus | Orchestrator | none (Python) | Routes operator requests |
| 🗄️ Custodian | Active incremental backup → `D:\_backups\` | none (Python) | sha-diff + atomic copy |
| 🌐 Stealth-Browser | Undetected browser automation (nodriver+CDP) | none (Python) | Cloudflare/anti-bot bypass; $0 |
| 🔎 Researcher | Scrape + Ollama-summarize chain | Ollama qwen2.5-coder:7b | Zero Opus tokens on raw HTML |
| 🛠️ Hacker | (planned) 183-tool pentest dispatcher (native/WSL/Docker) | none (shell-out) | RE of `AKCodez/hackingtool-plugin` — pending operator authorization |

If you are an agent reading this, **scroll to your section** below for role-specific guidance.

---

## Hub layout (where everything lives)

```
D:\Sinister\Sinister Skills\          THE meta hub
├── 01_MEMORY\                         per-project memory snapshots
│   ├── _consolidated\
│   │   ├── ALL-SESSION-STARTS.md     ⭐ every project's current state
│   │   ├── ALL-WHERE-I-STOPPED.md    ⭐ per-project resume anchor
│   │   └── ALL-FOLLOWUPS.md          ⭐ TODOs surfaced from all projects
│   └── <project>\                     11 project memory dirs
├── 02_MD_ARCHIVE\                     8,583 .md mirrored from projects
│   └── _index\by-keyword\             ⭐ 40 keyword-sharded indexes
├── 03_PROJECTS\                       11 one-pager capsules
├── 04_MCP\
│   ├── _catalog\ALL-TOOLS.md         ⭐ every MCP tool (160+) cataloged
│   ├── _registry\mcp.json.snapshot
│   ├── _ANOMALIES.md                  open MCP issues
│   ├── servers\                       Tier B mirror of MCP server source
│   └── reference-copies\
├── 05_SKILLS\                         9 proposed skills + harness skills
├── 06_UNDERSTAND\                     7 knowledge graph index entries
├── 07_DASHBOARD\
│   ├── INDEX.md
│   └── daily-digest.md               ⭐ operator's morning open
├── 08_AUTOMATIONS\                    cross-project workflows + bat/ps1 inventory
├── 09_REFERENCE\                      Yurikey roster, proxies, paths, vocab, secrets policy
├── 10_PLANS\                          106 plans mirrored + by-project sort
├── 11_CODE_LIBRARY\                   reusable functions (operator-curated)
└── 12_LLM_ORCHESTRATION\              YOU ARE HERE (agent runtime)
```

**Projects** at `D:\Sinister\01_Projects\<group>\<project>\source\` (junctions to canonical Desktop locations).

**Drive root** has `_vault\` (master Obsidian) + `00_README.md` + `00_RESUME.md` + `00_MASTER-PLAN.md`.

---

## The 7 base MCP servers (already running)

Independent of agent fleet. Operator's Claude session uses these directly. You may also call them.

| Server | Tools | Where |
|---|---|---|
| `eve` | 51 (memory, schedule, todo, watch, federate, notify) | `04_MCP/servers/eve/` |
| `sinister-panel` | 13 (devices, accounts, SS07, batch, proxy, RKA) | `04_MCP/servers/sinister-mcp-server/` |
| `sinister-snap` | 12 (signup, harvest, friend, message, cvd, mitm, proxy) | `04_MCP/servers/sinister-mcp-server/` |
| `sinister-apk` | 12 (creator build/install/broadcast, detector) ⚠️ broken cwd | `_ANOMALIES.md` |
| `sinister-tiktok` | 12 (mission, signup, wire, cvd, account) | `04_MCP/servers/sinister-tiktok/` |
| `letstext` | 27 (eve compose, reads, propose-send, fans, templates) | `04_MCP/servers/letstext/` |
| `letstext-admin` | 43 (compliance, ccbill, kyc, csam, ncii, investigations, tax) | `04_MCP/servers/letstext-admin/` |

Full catalog: `04_MCP/_catalog/ALL-TOOLS.md`.

When an agent needs cross-server data, it calls these via MCP. Examples:
- Sentinel querying Eve for `eve.schedule.list` to find adjacent operator deadlines.
- Curator querying `letstext-admin.compliance.export` for compliance pattern frequency.

---

## Escalation ladder (HARD RULE)

Always try cheapest first:

1. **Pure Python** (Tier 1) — $0, ms latency. Use when deterministic rules suffice.
2. **Ollama local** (Tier 2) — $0, 1-5s latency. Default for LLM work.
3. **Claude Haiku** (Tier 3) — $$, 1-3s. Fallback when Ollama down or output validation fails.
4. **Claude Sonnet** (Tier 4) — $$$, 2-5s. Emergency fallback only.
5. **Claude Opus** (Tier 5) — $$$$$. **FORBIDDEN for agents.** Reserved for operator's primary session.

Per-agent default tier: `config/routing-rules.yaml`.

If your output fails validation (typed check, keyword presence, etc.):
1. Retry once at your default tier
2. If still failing, escalate ONE tier up
3. Never escalate past `claude-sonnet-4-6` from an agent

**Forbidden escalations** (hard-blocked):
- Scribe → Opus
- Curator → Opus
- Triage → Sonnet
- Librarian → Opus

---

## Inter-agent communication

You can call other agents via `sinister-bus`:

```python
# Example: Librarian needs to know if a doc is stale
bus.call('watcher.scan', {'project': 'snap-signer'})
# Returns: {'drifted': ['docs/AUTONOMY-LOG.md'], 'fresh': [...]}
```

Each call:
- Recorded in `01_MEMORY/_bus/<context_id>.json` for replay
- Counts against caller's budget (not callee's)
- Times out at 30s

Available bus targets:
- `librarian.search(query, top_k=5)`
- `librarian.reindex(section)`
- `sentinel.list_alarms()`
- `sentinel.add(name, date, message)`
- `translator.find_tool(query)`
- `watcher.scan()`
- `watcher.queue_refresh()`
- `auditor.run()`
- `triage.classify(file_path)`
- `scribe.daily_digest()`
- `scribe.weekly_summary()`
- `scribe.restore_point(phase, name)`
- `curator.suggest_extractions()`
- `curator.extract(function_path)`

---

## Memory access (CRITICAL)

**Read-only by default.** You may read:
- `01_MEMORY/_consolidated/*.md`
- `01_MEMORY/<project>/*` (per-project memory snapshots)
- `02_MD_ARCHIVE/<project>/**/*.md`
- `02_MD_ARCHIVE/_index/by-keyword/<keyword>.md`
- `03_PROJECTS/<project>.md`
- `04_MCP/_catalog/ALL-TOOLS.md`
- `09_REFERENCE/*.md`

**Write-restricted.** You may write to:
- `runtime-state/token-usage.jsonl` (append-only)
- `runtime-state/last-healthcheck.json`
- Your agent's own `agents/<name>/state/`
- `01_MEMORY/_bus/<context_id>.json` (sinister-bus only)

**You may NOT touch:**
- `03_PROJECTS/<project>.md` (operator hand-edits)
- `05_SKILLS/proposed/*.md` (operator hand-edits)
- `08_AUTOMATIONS/cross-project/*.md` (operator hand-edits)
- `09_REFERENCE/*.md` (operator-canonical)
- `MASTER-PLAN.md`
- `_logs/restore-points/*.md`

---

## Operator-canonical state (DO NOT relearn)

Read at cold start, cache for the session.

### Active blockers (priority order)

1. **2026-05-24:** Yurikey51 root cert expires. Operator must source Yurikey52 from `t.me/yuriservice` by 2026-05-23.
2. **PI 0/3 on phones P1 + P2.** Interactive Settings re-auth required (no adb path).

### Active phones

- P1 (active): `2A061JEGR09301` (Pixel 6a)
- P2: `26031JEGR17598` (Pixel 6a)

### VPS

- Host: `root@95.216.240.227`
- Panel: `https://snap.sinijkr.com/`
- RKA: `:59348` (keybox) + `:59349` (commands)

### Canonical keybox

- `C:\Users\Zonia\Yurikey51_ECDSA.xml` (expires 2026-05-24)

### Cross-project rules

- Phone-side bats NEVER touch the panel or cloudflared (Snap Signer Policy 8.1).
- Bats may only kill processes they own (no global `taskkill /F /IM adb.exe`).
- Snap detects `am start` on Snap activities → SS03 (Policy 8a).
- Markdown is canonical memory — never write project knowledge to Claude memory store.

---

## Daily token budget (your agent)

See `config/budgets.yaml` under your agent's name. When you exceed:
- Calls/day cap → queue + alert via bus
- Token cap → fall back per `routing-rules.yaml` fallback_chain
- Never silently fail to Opus

Track every call in `runtime-state/token-usage.jsonl`:

```json
{"ts":"2026-05-18T12:34Z","agent":"librarian","model":"ollama-medium","input_tokens":1245,"output_tokens":312,"cost_usd":0.00,"context_id":"ctx-abc123"}
```

---

## Agent-specific guidance

### 📚 Librarian

- **Default tier:** 2 (Ollama qwen2.5-coder:7b)
- **Index location:** `12_LLM_ORCHESTRATION/agents/librarian/index/` (FAISS, ~200-500 MB)
- **Build index from:** `02_MD_ARCHIVE/<project>/**/*.md`
- **Validation:** Top-k results must contain ≥1 query keyword OR fuzzy-match score > 0.6
- **Failure modes:**
  - Index stale → call `watcher.scan()` to confirm; queue reindex if drift > 50 files
  - Ollama down → fall back to grep `02_MD_ARCHIVE/_index/by-keyword/<closest-keyword>.md`
- **Never:** answer questions that require operator-canonical knowledge updates (e.g., "what's today's blocker") — delegate to Sentinel

### ⏰ Sentinel

- **Default tier:** 1 (Python only)
- **Alarms file:** `agents/sentinel/alarms.json`
- **Built-in alarms:**
  - 2026-05-24: Yurikey51 root cert expiry (operator action by 2026-05-23)
  - Daily: PI 0/3 reminder until operator clears
- **Outputs:** writes to `07_DASHBOARD/daily-digest.md` urgent section (via Scribe)
- **Federation:** if `EVE_NOTIFY_TELEGRAM_ENABLED=true`, call `eve.notify.telegram` for critical alarms

### 🌐 Translator

- **Default tier:** 1 (Python only)
- **Source:** `04_MCP/_catalog/ALL-TOOLS.md` + `04_MCP/_catalog/by-keyword/*.md`
- **Algorithm:** lowercase keyword match → fuzzy-rank → return top-N
- **Output:** `[{tool, server, signature, doc_snippet}]`

### 👁️ Watcher

- **Default tier:** 1 (Python only)
- **State:** `agents/watcher/state.json` (last-scanned per-file mtimes + sha256)
- **Loop:** every 5 minutes, via `/loop` skill
- **Detects:**
  - Source MD changed → queue Librarian reindex for that section
  - New file at source → queue Triage to classify
  - File deleted at source → mark hub mirror as orphan

### 🛡️ Auditor

- **Default tier:** 1 (Python only)
- **Rules:** `agents/auditor/rules.yaml`
- **Scans:**
  - Secrets patterns (per `09_REFERENCE/secrets-redaction-policy.md`)
  - Dedup via sha256 across `02_MD_ARCHIVE/`
  - Stale files (mtime > N days old in `_consolidated/`)
- **Output:** `agents/auditor/findings/<ts>.json` + flag in daily-digest

### 🏷️ Triage

- **Default tier:** 2 (Ollama qwen2.5:1.5b)
- **Categories:** `agents/triage/rules.yaml` — known sections (memory, archive, project capsule, reference, etc.)
- **Input:** file path or content snippet
- **Output:** `{section: '02_MD_ARCHIVE', confidence: 0.92, suggested_path: '<>'}`
- **Confidence threshold:** ≥0.7 to auto-route; <0.7 → flag for operator

### ✍️ Scribe

- **Default tier:** 3 (Claude Haiku)
- **Templates:** `agents/scribe/templates/`
- **Outputs:**
  - `07_DASHBOARD/daily-digest.md` (1×/day)
  - Weekly summaries (1×/week)
  - Restore-point drafts (on-demand)
- **Inputs you pull from other agents:**
  - `sentinel.list_alarms()` — urgent
  - `watcher.scan()` — what changed
  - `librarian.search('yesterday updates')` — recent activity

### 🔍 Curator

- **Default tier:** 3 (Claude Haiku)
- **Watch source:** `02_MD_ARCHIVE/` for functions appearing in 3+ projects
- **Output:** `11_CODE_LIBRARY/_index/candidates.jsonl` (operator reviews)

### 🚌 sinister-bus

- **Default tier:** 1 (Python only)
- **Role:** route operator's "delegate to X" to correct agent
- **Persists:** every handoff at `01_MEMORY/_bus/<context_id>.json`
- **Recovery:** `bus.replay(context_id)` re-runs an entire handoff chain
- **Authentication:** local TCP only, no remote access

---

## Operator override commands (in primary Claude session)

Operator can override your default behavior:

- `"use Opus for this"` → operator escalates their session beyond agent defaults
- `"cheap mode"` → forces Tier 1/2 only for all agents in current request
- `"audit mode"` → forces validation at every tier
- `"reset budgets"` → clears today's token-usage counters (admin)

Honor these overrides + log them to `token-usage.jsonl`.

---

## On error

1. Log to `_logs/agent-fleet/<agent>-<date>.log`
2. Return `{ok: false, error: <type>, retry_at: <ts>}` to caller
3. Never silently fail
4. If error rate > 10% in 5min, call `sentinel.add` with a system alarm

---

## Cold-start checklist

When you boot up:

1. ✅ Read this file (you're doing it)
2. Read `config/routing-rules.yaml` (your section)
3. Read `config/budgets.yaml` (your section)
4. Read `agents/<your-name>/state/*.json` (your private state)
5. Ping your primary model via healthcheck — `12_LLM_ORCHESTRATION/docker/healthcheck.ps1`
6. Register with sinister-bus: `bus.register(name=<your-name>, port=<your-port>)`
7. Begin serving

---

## See also

- `README.md` — section overview
- `config/escalation-ladder.md` — full tier rules
- `04_MCP/_catalog/ALL-TOOLS.md` — every MCP tool you can call
- `09_REFERENCE/handoff-vocabulary.md` — operator's idioms (SESSION-START, WHERE-I-STOPPED, etc.)
- `MASTER-PLAN.md` Phase 8 — your role in the wider plan
