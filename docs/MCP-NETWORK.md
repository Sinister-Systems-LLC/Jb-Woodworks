# Sinister Bots <-> MCP Network integration

**Total surface after install:** 19 MCP servers, ~200+ tools.

```
7 base MCP servers (operator's pre-existing)         12 Sinister Bots (this hub)
+ eve                  (51 tools)                    + sentinel
+ sinister-panel       (13 tools)                    + translator
+ sinister-snap        (12 tools)                    + librarian
+ sinister-tiktok      (12 tools)                    + watcher
+ sinister-apk         (12 tools)                    + auditor
+ letstext             (27 tools)                    + sinister-bus
+ letstext-admin       (44 tools)                    + triage
                                                     + scribe
                                                     + curator
                                                     + custodian
                                                     + stealth-browser
                                                     + researcher
```

`sinister-bus.list_network()` returns the full inventory at runtime. `sinister-bus.find(query)` substring-matches across names + kinds.

## How they pair (concrete integrations)

These are the high-leverage couplings. Most are operator-driven (operator's session chains the calls); a few are bot-internal (already wired in agent code).

### sentinel <-> eve.notify
**What:** Sentinel detects urgent alarms (`check_urgent()`). Operator (or future bot-internal HTTP layer) dispatches to `eve.notify.telegram` to push the alarm.
**Why:** Operator doesn't have to check the dashboard to know Yurikey is expiring.
**Manual call today:**
```
alarms = sentinel.check_urgent(window_days=2)
for a in alarms:
    eve.notify.telegram(text=f"URGENT: {a['name']} - {a['message']}")
```

### custodian <-> eve.notify
**What:** Custodian daemon detects backup failure / `errors > 0` in a snapshot pass. Bus carries the alarm; operator session forwards to telegram.
**Why:** Silent backup failure is worse than no backup at all.

### scribe <-> eve.schedule.list + sentinel.check_urgent
**What:** Scribe's daily digest already reads `sentinel/alarms.json` directly (file-level coupling). Future enhancement: also read `eve.schedule.list` for non-alarm scheduled items.

### librarian <-> eve.memory.search
**What:** Librarian searches `02_MD_ARCHIVE/` (8,500 .md files). Eve's memory store has a different surface (operator-curated facts). Operator can cross-reference by calling both then merging — or build a "super-search" skill that fans out to both.
**Pattern:**
```
hits_archive = librarian.search("yurikey expiry")
hits_eve = eve.memory.search("yurikey expiry")
# operator's session merges + dedupes by sha
```

### translator <-> librarian (already wired in spirit)
**What:** Translator catalogs MCP TOOLS (`04_MCP/_catalog/`). Librarian catalogs MARKDOWN DOCS. Together they cover "is there a tool/doc for X" without needing the operator to know which surface to ask.
**Pattern:**
```
tools = translator.find_tool("scrape stealth")
docs  = librarian.search("scrape stealth")
```

### researcher <-> eve.memory.write (recommended future)
**What:** When researcher summarizes a URL, write the summary into `eve.memory` so later sessions have a cached answer without re-scraping.
**Pattern:**
```
r = researcher.summarize_url("https://...", focus="X")
eve.memory.write(key=f"research:{hash(url)}", value=r['summary'], tags=['research','cached'])
```

### sinister-bus <-> everything
Bus knows all 19 endpoints (see `bus.list_network()`). Bus records every operator handoff to `01_MEMORY/_bus/<ctx_id>.json` — chain replays survive crashes.

## How bots talk to each other today

**Current state (Phase 8i):**
- Bots are independent MCP servers; they DO NOT call each other over the wire.
- ONE exception: `researcher` imports `stealth-browser`'s `server.py` directly (in-process) to fetch pages. No MCP transport between them yet.
- Cross-bot coordination is operator-driven: operator (Opus) reads bus context, calls each bot in sequence.

**Future (Phase 8k):**
- Add HTTP layer to bus so bots can dispatch to one another without operator in the loop.
- Until then, the file-system handoff (Sentinel writes `alarms.json`; Scribe reads it) is the lightweight integration pattern.

## Cost discipline reinforced by this network

With 19 MCPs, the temptation is for Opus to "just call them all." Don't. Routing rules (in `config/escalation-ladder.md`):

1. **Recall / search / classify / scrape / audit / backup / digest** → delegate to a bot. Tier 1-3 by default. $0-$0.05/call.
2. **Project-specific automation** (panel control, snap signing, tiktok ops, apk packaging) → base MCPs. These are project-essential, not cost-flexible.
3. **Eve federation / memory writes / notifications** → base MCPs, but only when a bot can't already handle the read side.
4. **Anything genuinely creative / multi-step / novel** → Opus stays.

## Adding a new MCP

When operator adds a new MCP server (either as a base or a bot):

1. Register in `~/.claude/.mcp.json` (manually, or via `install-fleet.ps1` for bots).
2. Add to `KNOWN_AGENTS` in `12_LLM_ORCHESTRATION/agents/sinister-bus/server.py` so `bus.list_network()` sees it.
3. If it's a bot, also add to `install-fleet.ps1`'s `-Agents` default + `agents/README.md` status table.
4. Add catalog entry under `04_MCP/_catalog/by-server/<name>.md` (refresh.ps1 -Section 04 auto-generates).
5. If integration with existing bots is useful, add a row to this file's "How they pair" section.

## Verify the network is alive

```
sinister-bus.health        -> total_endpoints=19, known_bots=12, known_base_mcps=7
sinister-bus.list_network  -> full inventory
sinister-bus.find scrape   -> matches stealth-browser + researcher
translator.list_servers    -> base MCP tool counts (cached)
```
