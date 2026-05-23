# Cross-project: Local Agent Fleet architecture

**Operator directive (2026-05-18 PM):** "I want you to in parallel review the open space sub agents Claude skill. find it and make our own. it essentially allows us to use local agents to do tasks to save with Claude usage etc. see all places we can use this and even make it that backbone of the entire memory system if we can. anywhere to save tokens but still be efficient in tasks like scraping or recalling from archives. we need agents per this like a librarian a Claude agent could use the MCP system to talk to to make it more efficient to recall archived items."

## North star

**Token-efficient operator workflow.** Most operator queries (recall, scrape, classify, audit) are routine — they don't need Claude Opus. They need fast retrieval + structured output. A local agent fleet wrapped as MCP servers handles routine work; Opus is reserved for creative + complex work only.

## Why MCP as the integration layer

- Operator's Claude session already speaks MCP fluently (7 servers, 160+ tools).
- Adding a new MCP server is zero friction — `.mcp.json` registration + restart Claude.
- Each agent becomes a tool: `librarian.search(query)` is identical in shape to `sinister-panel.devices.list()`.
- Sub-agents can also call other MCP tools (Eve, sinister-panel, etc.) — they become first-class citizens.

## Agent roster (8 agents + 1 orchestrator)

See `05_SKILLS/proposed/10-local-agent-fleet.md` for the full roster. Summary:

| Agent | Role | Backend | Tokens saved |
|---|---|---|---|
| 📚 Librarian | RAG over 8,583 .md archive | Ollama (qwen2.5-coder:7b) + FAISS | 5-10k Opus → 0 |
| 👁️ Watcher | Source-drift detector | Python (mtimes vs manifest) | 2-5k Opus → 0 |
| 🏷️ Triage | File classifier | Ollama (qwen2.5:1.5b) | 1-3k Opus → 0 |
| 🛡️ Auditor | Secrets + dedup + freshness | Python (regex + sha) | 2-5k Opus → 0 |
| ✍️ Scribe | Daily-digest + summaries | Claude Haiku | 20-50k Opus → 5k Haiku |
| 🔍 Curator | Code-library extraction | Claude Haiku | 5-10k Opus → 2k Haiku |
| ⏰ Sentinel | Date alarms + expiry | Python (cron-ish) | 1-2k Opus → 0 |
| 🌐 Translator | MCP tool cross-ref | Python (catalog grep) | 1-3k Opus → 0 |
| 🚌 sinister-bus | Orchestrator | Python (routing) | n/a |

**Expected daily savings:** 60-80% of operator's routine token spend.

## Backbone of memory system

The Librarian agent specifically:

1. **Embedding-indexes** the 8,583 .md archive at hub build time (Phase 8b).
2. Exposes `librarian.search(query, top_k=5)` — returns ranked passages with source paths.
3. **Becomes the primary recall mechanism.** When operator asks "what did we say about Yurikey expiry," Claude session calls `librarian.search` instead of grepping or reading files.
4. **Cross-references with hub structure:** results include hub navigation (e.g., "this is in `01_MEMORY/library-of-alexandria/SESSION-START.md` line 320 + mirror at `02_MD_ARCHIVE/library-of-alexandria/SESSION-START.md`").

The other agents specialize:
- Sentinel watches calendar dates (Yurikey expiry = 2026-05-24)
- Watcher detects when sources change so Librarian's index can refresh
- Triage classifies new files automatically
- Auditor catches secrets / duplicates before they leak
- Scribe drafts the daily-digest from Librarian queries
- Curator suggests code extractions based on cross-project pattern frequency

## How operator interacts

```
# Morning open
Operator: "What's the daily digest?"
  → Claude calls scribe.daily_digest()
  → Scribe (Haiku) calls librarian.search + sentinel.list_alarms + watcher.scan
  → Returns formatted digest
  → Cost: ~5k Haiku tokens (was: ~50k Opus)

# Recall query
Operator: "Find everything we wrote about Yurikey expiry"
  → Claude calls librarian.search("yurikey expiry")
  → Librarian (Ollama) returns top 5 passages with paths
  → Cost: 0 Opus tokens (was: 5-10k)

# Cross-project audit
Operator: "Is anything sensitive committed?"
  → Claude calls auditor.run()
  → Auditor (Python) scans + returns findings
  → Cost: 0 Opus tokens (was: 2-5k)
```

## Implementation order (Phase 8 sub-phases)

See `05_SKILLS/proposed/10-local-agent-fleet.md` for sub-phase 8a-8h timeline.

**Most impact first:** Librarian (8b) — replaces the biggest token sink.
**Then easy wins:** Sentinel + Translator (8c) — pure Python, no LLM, zero cost.
**Then quality-of-life:** Scribe (8e) — Haiku-backed daily digest.

## Token budget per agent (monthly estimate)

Assuming heavy operator use (50 queries/day):

| Agent | Calls/day | Cost/call | Daily | Monthly |
|---|---|---|---|---|
| Librarian | 20 | $0 (Ollama) | $0 | $0 |
| Watcher | 96 (5min loop) | $0 (Python) | $0 | $0 |
| Triage | 5 | $0 (Ollama) | $0 | $0 |
| Auditor | 1 | $0 (Python) | $0 | $0 |
| Scribe (Haiku) | 2 | ~$0.02 | $0.04 | $1.20 |
| Curator (Haiku) | 1 | ~$0.05 | $0.05 | $1.50 |
| Sentinel | 24 (hourly) | $0 (Python) | $0 | $0 |
| Translator | 10 | $0 (Python) | $0 | $0 |
| **TOTAL** | | | **<$0.10** | **<$3** |

Compare: 50 Opus queries/day at avg 5k tokens = ~$3-5/day = $90-150/month.

**Savings: ~$90/month minimum, likely $300+/month at full utilization.**

## Risks

- **Ollama setup overhead** — operator needs to install Ollama + pull models (~10 GB disk).
- **FAISS index size** — embeddings for 8,583 .md ≈ 200-500 MB. Lives at `04_MCP/agent-fleet/librarian/index/`. Excluded from git.
- **Local LLM accuracy** — qwen2.5-coder:7b is competent but not Opus-level. For nuanced queries, agent should escalate to Haiku then Opus.
- **MCP server stability** — Python + FastMCP needs to handle Claude session reconnects gracefully.
- **Ollama runtime resource** — keep `ollama serve` running. Use Windows Task Scheduler for auto-start.

## Failure modes + fallbacks

1. **Ollama down** → Librarian falls back to grep over `02_MD_ARCHIVE/_index/by-keyword/` (deterministic, slower, no LLM).
2. **FAISS index stale** → Watcher detects + queues `librarian.reindex`. Index rebuilds nightly.
3. **Haiku rate-limited** → Scribe falls back to template-only daily-digest (no LLM polish).
4. **Sentinel alarm missed** → Daily-digest cross-checks all alarms regardless of Sentinel state.

## Discoverable existing skills (operator mentioned)

Operator referenced an "open space sub agents Claude skill." To find:
- Check `~/.claude/plugins/marketplaces/` for entries matching `agent`, `subagent`, `multi-agent`, `orchestrate`
- WebSearch for "Claude Code sub-agent skill" or "claude-flow"
- Check Anthropic Cookbook (cookbook.anthropic.com) for agent patterns

Even if we adopt an existing framework, our **agent roster** (Librarian, Sentinel, Triage, etc.) is Sinister-specific and needs to be built regardless.

## See also

- `05_SKILLS/proposed/10-local-agent-fleet.md` — full skill proposal
- `MASTER-PLAN.md` — Phase 8 timeline
- `04_MCP/_registry/mcp.json.snapshot` — existing MCP registration pattern
