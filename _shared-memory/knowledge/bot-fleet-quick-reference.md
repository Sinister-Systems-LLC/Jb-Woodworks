<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Bot Fleet :: Quick Reference

**Created:** 2026-05-23 (EVE on Sanctum, Phase-2 B.6 of `sanctum-complete-and-expand-2026-05-23T1145Z`)
**Purpose:** One-glance call sheet for the 13 Sinister MCP bots. Skim this BEFORE reaching for Opus on a routine task — most file searches, classifications, scrapes, digests, and cross-project hunts route to a free local bot at ~0 input-token cost.
**Source of truth:** every entry below was extracted from the live `@mcp.tool()` decorators in `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\<bot>\server.py` (Sanctum mirror at `bots/<bot>/` via junction). Tool signatures match the actual function definitions, not inferred.

---

## TL;DR — what to call instead of asking Opus

| You want to… | Don't do this | Do this instead | Why |
|---|---|---|---|
| Find a `.md` in the archive | Grep + 5KB of context | `librarian.search(query, top_k=5)` | FAISS + Ollama if available, grep fallback always |
| Classify a file's purpose | LLM call w/ rules in prompt | `triage.classify_file(path)` | Ollama 1.5B model, rules fallback |
| Scrape a URL + summarize | WebFetch + reasoning turn | `researcher.summarize_url(url, focus=...)` | stealth-browser → Ollama chain, no token spend |
| Heartbeat / inbox poll | Manually write JSON | `sinister-bus.heartbeat(my_agent=...)` + `inbox_poll(my_agent=...)` | Canonical per CLAUDE.md Rule 9 |
| Find any MCP tool by topic | Memorize ~160 tool names | `translator.find_tool(query, top_k=5)` | Semantic search across all 7 servers |
| Daily digest of fleet activity | Opus rollup | `scribe.generate_digest()` | Haiku, ~$0.02/day, cached prompt |
| Cross-project helper hunt | Sweep + Opus assessment | `curator.scan_candidates(top_k=10)` | Pure-Python scan + Haiku assess; ~$0.05/run |
| Backup a file before edit | manual cp / git stash | `custodian.snapshot_now(path=<file>)` | dedup by sha; `restore(path, version)` to roll back |
| Track an expiry / deadline | manual calendar entry | `sentinel.add(name, due_iso, severity=...)` | computed `days_until`, snoozable |
| Scan repo for secrets | `git secrets`/manual grep | `auditor.scan_secrets(path=...)` | persisted findings under `agents/auditor/findings/` |

**Estimated savings per Sanctum-master session:** 30-60% input-token reduction when these substitute for Opus on routine work (anchor: `jcode-swarm-token-parity-audit-2026-05-23`).

---

## Fleet at a glance

| Bot | Tier | Cost/call | Role | Tool count |
|---|---|---|---|---|
| `sentinel` | 1 (Py) | $0 | Date alarms (expiries, deadlines) | 7 |
| `translator` | 1 (Py) | $0 | MCP-tool catalog search across all servers | 5 |
| `watcher` | 1 (Py) | $0 | Source-drift detection (sha + mtime) | 5 |
| `auditor` | 1 (Py) | $0 | Secrets + dedup + freshness scan | 5 |
| `sinister-bus` | 1 (Py) | $0 | Orchestrator + heartbeat + inbox + runlog + codec + vault-lock + scripts | 28 |
| `custodian` | 1 (Py) | $0 | Active backup to `D:\_backups\` with restore | 7 |
| `stealth-browser` | 1 (Py + nodriver) | $0 | Undetected Chromium automation | 11 |
| `vault` | 1 (Py) | $0 local | sinister-vault repo + Syncthing + audit + accounts | 10 |
| `triage` | 2 (Ollama) | $0 | File classifier (LLM + rules fallback) | 5 |
| `librarian` | 2 (Ollama + FAISS) | $0 | RAG over 8,500+ `.md` archive | 4 |
| `researcher` | 2 (Ollama) | $0 | scrape → summarize → compare chain (+ absorb) | 7 |
| `scribe` | 3 (Haiku) | ~$0.02 | Daily digest + weekly summary | 7 |
| `curator` | 3 (Haiku) | ~$0.05 | Code-library extraction scout | 8 |

Total: **109 MCP tools across 13 bots**, all free except scribe ($0.02) + curator ($0.05).

---

## How to call (deferred-tool loading)

Bot MCPs are **deferred** in spawned sessions — schemas don't ship in the opening prompt. Two-step load + call:

1. `ToolSearch select:mcp__<server>__<tool>` (loads schema, one-shot per call name)
2. Call `mcp__<server>__<tool>(...)` like any normal tool

Naming convention: server prefix is the bot folder name with `-` → `_` (FastMCP normalization), so:
- `bots/sinister-bus/server.py` → tools surface as `mcp__sinister_bus__<tool>`
- `bots/stealth-browser/server.py` → tools surface as `mcp__stealth_browser__<tool>`
- single-word slugs are unchanged: `mcp__librarian__search`, `mcp__vault__list`

### Loading-state reality check (verified 2026-05-23T19:30Z)

This documents what's **actually loadable** in a typical Sanctum-master session vs what's **registered on disk**:

| Bot | In `~/.claude/.mcp.json`? | In `claude mcp list` (Connected)? | `ToolSearch select` works? | Notes |
|---|---|---|---|---|
| `vault` | ✓ user-scope | ✓ Connected | ✓ (10 tools loaded) | Fully functional now |
| `ruflo` | ✓ user-scope | ✓ Connected | ✓ (many tools loaded) | Fully functional now |
| `sentinel` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `librarian` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `sinister-bus` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `translator` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `watcher` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `auditor` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `custodian` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `triage` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `researcher` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `scribe` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `curator` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |
| `stealth-browser` | ✓ registered | ✗ NOT active | ✗ schemas not in deferred list | Needs Claude restart |

**Action required to unlock the full fleet in a session:** Restart Claude Code (per OPERATOR-ACTION-QUEUE 🔴 row). The 12 bot MCPs are registered in `~/.claude/.mcp.json` but only load on cold-start.

**Filesystem fallback (works in ANY session, no MCP needed):** every bot has a Python module. Direct-import path:

```python
# Example: librarian-equivalent without the MCP wrapper
import sys; sys.path.insert(0, r"D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\librarian")
import server  # the FastMCP server module
result = server.search(query="forge memory", top_k=5)
```

Same for any other bot — the `@mcp.tool()` decorated functions are also normal Python callables.

---

## Per-bot detail

### `sentinel` — date alarms (Tier 1, $0)

| Tool | Signature | When to use |
|---|---|---|
| `list_alarms` | `(include_past=False) → list[alarm]` | "What's due in the next week?" |
| `check_urgent` | `(window_days=7) → list[alarm]` | Gate on session-start; pipe to operator queue |
| `add` | `(name, due_iso, severity="normal", message="", tags=[])` | Record any new deadline (severity: critical/high/warning/normal) |
| `remove` | `(alarm_id)` | Close a closed item |
| `snooze` | `(alarm_id, until_iso)` | Skip noise without losing the alarm |
| `add_from_runlog` | `(manifest_id_or_path, severity="warning")` | Auto-promote a runlog `next_actions` row into an alarm |
| `health` | `()` | smoke-probe |

### `translator` — find any MCP tool (Tier 1, $0)

| Tool | Signature | When to use |
|---|---|---|
| `find_tool` | `(query, top_k=5) → list[match]` | "I forget — which bot does X?" |
| `list_servers` | `() → list[server]` | Audit which MCPs are wired |
| `tools_by_server` | `(server) → list[tool]` | Enumerate one server's surface |
| `refresh_catalog` | `() → ok` | After registering a new MCP |
| `health` | `()` | smoke-probe |

### `watcher` — source-drift detection (Tier 1, $0)

| Tool | Signature | When to use |
|---|---|---|
| `scan` | `(project=None) → list[drifted_file]` | Detect un-synced edits across product repos |
| `queue_refresh` | `(file, project=None)` | Manually enqueue a file for the refresh cycle |
| `list_queue` | `(limit=50)` | See what `refresh.ps1` will consume next |
| `clear_queue` | `()` | After refresh consumes |
| `health` | `()` | smoke-probe |

### `auditor` — secrets + dedup + freshness (Tier 1, $0)

| Tool | Signature | When to use |
|---|---|---|
| `scan_secrets` | `(path=None) → list[finding]` | Pre-commit / pre-push secret scan |
| `scan_duplicates` | `() → list[dup_set]` | Find `.md` with identical sha256 |
| `scan_stale` | `(days=30) → list[file]` | Surface `_consolidated/` rot |
| `run` | `() → full_report` | Full audit, persisted under `findings/<ts>.json` |
| `health` | `()` | smoke-probe |

### `sinister-bus` — orchestrator (Tier 1, $0) ★ **highest-leverage bot**

**Identity + coordination (canonical Rule 9):**

| Tool | Signature | When to use |
|---|---|---|
| `heartbeat` | `(my_agent)` | Every turn (mandatory per CLAUDE.md) |
| `who_is_online` | `()` | See which siblings are active |
| `inbox_send` | `(to_agent, message, from_agent="unknown", …)` | Cross-lane message |
| `inbox_poll` | `(my_agent, mark_consumed=True, limit=50)` | Every turn — surface `[DELEGATE]` / `[ASK]` / `[INFO]` |
| `inbox_reply` | `(msg_id, my_agent, response)` | Close a peer ask |
| `delegate_to` | `(agent_name, prompt, timeout_sec=60, …)` | Hand off a sub-task to a sibling |
| `inbox_stats` | `()` | Audit unread-count per lane |

**Dispatch + replay:**

| Tool | Signature | When to use |
|---|---|---|
| `dispatch` | `(target, args=None, context_id=None)` | Route a request through the bus (instead of direct MCP) |
| `replay` | `(context_id)` | Reconstruct a handoff chain |
| `list_recent` | `(n=20)` | Last 20 bus events |
| `record_response` | `(context_id, agent, tool, result)` | Log a response back |
| `list_network` | `() → 19 endpoints` | Verify fleet wiring |
| `find` | `(query) → list[entry]` | Substring search across agents + kinds |

**Runlog + scripts:**

| Tool | Signature | When to use |
|---|---|---|
| `runlog_list` | `(limit=20)` | Recent operator-run script manifests |
| `runlog_latest` | `(script_name)` | Most recent manifest for a script |
| `runlog_summary` | `(id_or_path)` | Condensed view of one manifest |
| `pending_actions` | `()` | Operator-action items surfaced from runlogs |
| `consume_pending` | `(mark_checked=True, archive=True)` | Close them out |
| `list_scripts` | `()` | What's runnable via `run_script` |
| `run_script` | `(name, timeout_sec=120, extra_args=None)` | Dispatch a known script through the bus |

**Codec + vault-lock + memory:**

| Tool | Signature | When to use |
|---|---|---|
| `encode` / `decode` | `(text)` | Sinister-codec round-trip |
| `codec_status` | `()` | Probe codec wiring |
| `vault_lock` / `vault_unlock` / `vault_status` | `(path, …)` | Operator-vault file gating |
| `memory_garden` | `()` | Cross-bot absorbed-facts roll-up |
| `health` | `()` | smoke-probe |

### `custodian` — active backup (Tier 1, $0)

| Tool | Signature | When to use |
|---|---|---|
| `snapshot_now` | `(source=None, path=None)` | Before any R3+ edit (manual safety net) |
| `list_versions` | `(path, source=None)` | "When did this file change?" |
| `restore` | `(path, version=None, dest=None, source=None)` | Roll a file back |
| `cleanup` | `(dry_run=False)` | Apply retention policy |
| `diff` | `(path, source=None)` | Current vs last snapshot |
| `config` | `()` | View active watch-list |
| `health` | `()` | smoke-probe |

### `stealth-browser` — undetected Chromium (Tier 1, $0)

| Tool | Signature | When to use |
|---|---|---|
| `open` | `(url, wait_for_selector=None)` | Navigate (auto-launches Chrome on first call) |
| `screenshot` | `(path=None, full_page=False)` | PNG capture |
| `html` | `()` | Full DOM |
| `scrape_text` | `(max_chars=20000)` | `document.body.innerText` |
| `scrape_links` | `() → up to 200 anchors` | All `<a href>` |
| `click` | `(selector)` | CSS click |
| `type` | `(selector, text, delay_ms=30)` | Form fill |
| `wait_for` | `(selector, timeout_sec=10)` | Sync gate |
| `evaluate` | `(js)` | Arbitrary JS in page |
| `close` | `()` | Free resources |
| `health` | `()` | smoke-probe |

### `vault` — sinister-vault (Tier 1, $0 local)

Already loaded in this session as `mcp__vault__*` (10 tools).

| Tool | Signature | When to use |
|---|---|---|
| `list` | `(path="", depth=1)` | Browse `D:\sinister-vault\<path>` |
| `search` | `(query, limit=20)` | Substring grep across all vault repos + sync folder |
| `audit` | `(limit=50, kind=None)` | Tail vault daemon audit log |
| `commit` | `(repo, file_path, message, account="operator")` | Stage+commit+push one file to a Gitea repo |
| `push` / `pull` | `(repo, branch)` | git push/pull a vault repo branch |
| `sync_status` | `()` | Syncthing folder state |
| `accounts` | `()` | Enumerate `D:\sinister-vault\accounts\<name>` |
| `snapshot` | `(subtree="repos")` | On-demand snapshot via vault daemon |
| `health` | `()` | smoke-probe |

### `triage` — file classifier (Tier 2 Ollama, $0)

| Tool | Signature | When to use |
|---|---|---|
| `classify_file` | `(path, use_llm=True)` | "Where does this file belong?" |
| `classify_text` | `(text, hint=None, use_llm=True)` | Same, but raw text snippet |
| `classify_batch` | `(paths, use_llm=True)` | Bulk classification |
| `list_categories` | `()` | Show the canonical category catalog |
| `health` | `()` | Reports Ollama status + active classifier mode |

### `librarian` — RAG over `.md` archive (Tier 2 Ollama + FAISS, $0)

| Tool | Signature | When to use |
|---|---|---|
| `search` | `(query, top_k=5)` | Semantic search; falls back to grep if FAISS down |
| `grep_fallback` | `(query, top_k=5)` | Force pure-grep (always available) |
| `reindex` | `(section=None)` | Rebuild FAISS from `02_MD_ARCHIVE/` |
| `health` | `()` | smoke-probe |

### `researcher` — scrape + summarize chain (Tier 2 Ollama, $0)

| Tool | Signature | When to use |
|---|---|---|
| `lookup` | `(query, url=None, top_k=3)` | Topic lookup with optional URL |
| `summarize_url` | `(url, focus=None)` | Open via stealth-browser → Ollama summary |
| `compare` | `(urls, focus)` | Multi-URL comparison along a focus axis |
| `absorb` | `(fact, source, tags=None)` | Persist a fact to researcher memory |
| `list_facts` | `(limit=50)` | View absorbed facts |
| `forget` | `(fact_substring)` | Audit-logged removal |
| `health` | `()` | smoke-probe |

### `scribe` — Haiku daily digest (Tier 3, ~$0.02)

| Tool | Signature | When to use |
|---|---|---|
| `generate_digest` | `(preview=False, model=None)` | Writes `07_DASHBOARD/daily-digest.md` |
| `weekly_summary` | `(preview=False, model=None)` | 7-day rollup to `07_DASHBOARD/weekly/<iso-week>.md` |
| `list_inputs` | `()` | Debug-view of what scribe would feed Haiku (no spend) |
| `absorb` / `list_facts` / `forget` | (same shape as researcher) | Bot-memory protocol |
| `health` | `()` | Anthropic SDK + key + peers + memory |

### `curator` — code-library scout (Tier 3, ~$0.05)

| Tool | Signature | When to use |
|---|---|---|
| `scan_candidates` | `(roots=None, top_k=10, recent_days=30)` | Cross-project helper-function hunt |
| `assess_file` | `(path)` | Pure-Python single-file assessment, no LLM |
| `write_proposal` | `(out_path=None)` | Generates proposal to `11_CODE_LIBRARY/_proposals/<utc>.md` |
| `list_origins` | `()` | Source roots curator scans |
| `absorb` / `list_facts` / `forget` | (same shape) | Bot-memory protocol |
| `health` | `()` | smoke-probe |

---

## Composition recipes

**Cold-start canonical (every turn):**
```
sinister-bus.heartbeat(my_agent="EVE on Sanctum")
sinister-bus.inbox_poll(my_agent="EVE on Sanctum")
```

**"What do I work on?" (operator-action surface):**
```
sentinel.check_urgent(window_days=7)
sinister-bus.pending_actions()
```

**"Find that doc" (instead of grep+read+context):**
```
librarian.search(query="forge memory bridge usage", top_k=5)
# or, if FAISS unhappy:
librarian.grep_fallback(query="forge memory bridge usage", top_k=5)
```

**"Summarize this URL without burning Opus tokens":**
```
researcher.summarize_url(url="...", focus="security model")
```

**"Backup before risky edit":**
```
custodian.snapshot_now(path="D:/Sinister Sanctum/CLAUDE.md")
# edit...
# if regret:
custodian.restore(path="D:/Sinister Sanctum/CLAUDE.md", version="<sha8>")
```

**"Daily fleet rollup":**
```
scribe.generate_digest(preview=True)   # see inputs, no Haiku spend
scribe.generate_digest()                # commit to dashboard
```

---

## Anti-patterns

1. **Don't re-load tool schemas every call.** `ToolSearch select:mcp__<server>__<tool>` is a one-shot per call name; once loaded, the schema persists for the session.
2. **Don't call `librarian.reindex()` casually.** It rebuilds the FAISS index over 8,500+ docs — slow + I/O heavy. Only when archive content has changed materially.
3. **Don't call Tier-3 bots in a loop.** scribe and curator are paid (Haiku). Batch + cache. Use `list_inputs()` / `assess_file()` to preview before the LLM call.
4. **Don't bypass `sinister-bus.heartbeat`.** Filesystem fallback (`_shared-memory/heartbeats/<slug>.json`) exists for when the MCP isn't loaded, but bus heartbeat is canonical when available.
5. **Don't `dispatch` what you can call directly.** `sinister-bus.dispatch(target=..., args=...)` is for cross-agent indirection / audit-trail needs. Direct MCP call is faster + cheaper for in-session work.
6. **Don't paste secrets into `auditor.scan_secrets(path=)`.** It scans on disk; pass a path, not a content blob.
7. **Don't assume a bot is loaded.** Check the deferred-tool list at session-start (top of prompt). If absent, `claude` was started cold and the MCP couldn't bind — note the gap and either work around or surface to operator queue.

---

## Composes with

- `jcode-swarm-token-parity-audit-2026-05-23` (this quick-ref is recommendation #1 from that audit)
- `wake-on-demand-bot-dispatcher-2026-05-23` (idle-kill pattern that reduces bot RAM footprint while preserving this calling surface)
- `mcp-junction-fix-pattern-2026-05-23` (how the bot cwds resolve via NTFS junctions)
- `spawned-window-capabilities-2026-05-23` (confirms every spawned EVE has access to this fleet)
- `pip-editable-hides-mcp-cwd-emptiness-2026-05-23` (audit pattern for "why is this MCP not loading?")
- `forge-memory-usage-2026-05-23` (orthogonal: forge-memory-bridge is per-agent working memory; bots are fleet services)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (every signature in this file was extracted from live `@mcp.tool()` decorators — no inferred APIs)

---

## Maintenance

- **When a bot ships a new `@mcp.tool()`:** add a row in the bot's per-bot table here. Bump `Updated` in `_INDEX.md` row.
- **When a bot changes a signature:** re-extract from `server.py` and update the row. Old signature → `_archive/` per forever-upgrade doctrine.
- **When fleet count changes (new bot lands or one is retired):** update the "Fleet at a glance" + "Tool count" totals + `bots/README.md` table.
- **Verification command** (run any time to re-validate this file's accuracy):
  ```powershell
  Get-ChildItem "D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\*\server.py" |
    Select-String -Pattern '@mcp\.tool\(\)' -Context 0,2
  ```
