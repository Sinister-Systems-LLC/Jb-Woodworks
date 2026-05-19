# Agent fleet — implementation

Phase 8 agents. Each = standalone Python MCP server.

## Status (2026-05-18 build — Sinister Bots fleet)

| Agent | Phase | Code | Tier | Cost/call | Status |
|---|---|---|---|---|---|
| 🚌 sinister-bus | 8g | `sinister-bus/server.py` | 1 | $0 | ✅ shipped |
| ⏰ sentinel | 8c | `sentinel/server.py` | 1 | $0 | ✅ shipped (3 default alarms loaded) |
| 🌐 translator | 8c | `translator/server.py` | 1 | $0 | ✅ shipped (cached catalog read) |
| 📚 librarian | 8b | `librarian/server.py` | 2 | $0 (Ollama) | ✅ shipped (needs Ollama + FAISS index built) |
| 👁️ watcher | 8d | `watcher/server.py` | 1 | $0 | ✅ shipped |
| 🛡️ auditor | 8d | `auditor/server.py` | 1 | $0 | ✅ shipped |
| 🏷️ triage | 8f | `triage/server.py` | 2 | $0 (Ollama) | ✅ shipped (rules-mode fallback when Ollama down) |
| ✍️ scribe | 8e | `scribe/server.py` | 3 | ~$0.02 | ✅ shipped (Haiku + prompt caching) |
| 🔍 curator | 8f | `curator/server.py` | 3 | ~$0.05 | ✅ shipped (Haiku + prompt caching) |
| 🗄️ custodian | 8f+ | `custodian/server.py` | 1 | $0 | ✅ shipped (active backup to `D:\_backups`) |
| 🌐 stealth-browser | 8i | `stealth-browser/server.py` | 1 | $0 | ✅ shipped (nodriver + CDP; RE of vibheksoni/stealth-browser-mcp) |
| 🔎 researcher | 8i | `researcher/server.py` | 2 | $0 (Ollama) | ✅ shipped (stealth-browser + Ollama summary chain) |
| 🛠️ hacker | 8j | (pending) | 1 | $0 | 🟡 deferred — RE of AKCodez/hackingtool-plugin, awaits operator authorization |

**12/13 Sinister Bots shipped + 12/12 registered in `.mcp.json` (active after Claude Code restart).** Hacker agent is pending — needs operator OK to fetch the upstream tool catalog (sandbox flagged the dual-use scope).

**Network state (verified 2026-05-18):** `sinister-bus.list_network` returns **19 endpoints** (12 bots + 7 base MCPs) totaling ~200+ tools. First Custodian snapshot pass wrote **4,368 files / 53 MB** to `D:\_backups\snapshots\`.

## One-click install + register

```powershell
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION'
.\install-fleet.ps1
# Or dry-run first:
.\install-fleet.ps1 -DryRun
```

This:
1. Creates `.venv/` per agent dir
2. `pip install -r requirements.txt` per agent
3. Registers each agent in `~/.claude/.mcp.json`

Restart Claude Code → 6 new MCP servers available.

## Tier 1 (pure Python, zero cost) agents — work immediately

After install + Claude restart:
- `sentinel.list_alarms()` → Yurikey deadline + PI re-auth alerts
- `translator.find_tool("sign apk")` → matching MCP tools across all servers
- `watcher.scan()` → source-drift detection
- `auditor.run()` → secrets + dedup + freshness audit
- `sinister-bus.list_recent()` → recent handoffs
- `triage.classify_file(path)` → rules-mode classification (Ollama optional)
- `custodian.snapshot_now()` → manual backup pass (daemon runs continuously)
- All `<agent>.health()` → status check

## Tier 3 (Haiku) agents — need ANTHROPIC_API_KEY

```powershell
[Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY','sk-ant-...','User')
# Restart Claude Code so the env var propagates.
```

- `scribe.generate_digest(preview=true)` → render today's digest (no write)
- `scribe.generate_digest()` → write `07_DASHBOARD/daily-digest.md`
- `curator.scan_candidates(top_k=10)` → cross-project helper-function suggestions
- `curator.write_proposal()` → `11_CODE_LIBRARY/_proposals/curator-<utc>.md`

## Backup daemon (Custodian)

After Claude restart, also install the 24/7 background daemon:

```powershell
cd 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian'
.\install-task.ps1
```

Two scheduled tasks (`SinisterCustodian` + `SinisterCustodian-DailyRestart`) run the
backup loop even when Claude Code is closed. Logs at `D:\_backups\_logs\custodian-<date>.log`.

## Tier 2 (Ollama) — librarian

Needs:
1. Docker running
2. `docker compose up -d` in `12_LLM_ORCHESTRATION/docker/`
3. `librarian.reindex()` first time (3-5 min)

After that, `librarian.search("yurikey expiry")` returns vector-ranked passages from the 8,500 MD archive at $0 cost.

When Ollama down: `librarian.search` falls back to `librarian.grep_fallback` automatically (reads `02_MD_ARCHIVE/_index/by-keyword/` shards first).

## Health check

```powershell
# Verify each agent
foreach ($a in 'sentinel','translator','librarian','watcher','auditor','sinister-bus','triage','scribe','curator','custodian') {
    Write-Host "=== $a ==="
    # In Claude session, call: <agent>.health()
}
```

## Inter-agent calls

Currently bus.dispatch RECORDS intent; the operator's Claude session does the actual MCP invocation. Future enhancement: bus drives an HTTP layer for true autonomous agent-to-agent calls.

## Telemetry

Every agent call logs to `12_LLM_ORCHESTRATION/runtime-state/token-usage.jsonl`:

```json
{"ts":"2026-05-18T16:00Z","agent":"sentinel","model":null,"input_tokens":0,"output_tokens":0,"cost_usd":0,"tool":"list_alarms"}
```

Daily-digest (Scribe) summarizes this from the same JSONL. Operator's monthly cost projection:

| Tier | Calls/day | Cost/call | Monthly |
|---|---|---|---|
| 1 (Python agents) | 200+ | $0 | $0 |
| 2 (Ollama) | 50 | $0 | $0 |
| 3 (Haiku — Scribe/Curator) | 5 | ~$0.05 | $7.50 |
| 4 (Sonnet fallback) | 0-1 | ~$0.30 | ~$5 worst case |
| 5 (Opus) | 0 (forbidden for agents) | — | $0 |
| **TOTAL** | | | **~$10/month** vs ~$280/month without fleet |

Savings: ~$270/month.
