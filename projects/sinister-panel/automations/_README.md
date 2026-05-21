# Sinister-Panel

**Source (canonical):** `D:\Sinister\01_Projects\Sinister\Sinister-Panel\source\` *(physical copy as of 2026-05-18 PM LATE — was a directory junction to `C:\Users\Zonia\Desktop\Sinister-Panel\` before the operator promoted D:\ to be the new main working tree)*
**Legacy fallback (read-only from here on):** `C:\Users\Zonia\Desktop\Sinister-Panel\` — kept as snapshot; do not commit from this tree.
**Hub memory:** See [hub memory](../../../Sinister Skills/01_MEMORY/sinister-panel/) — \SESSION-START.md\ + \RESUME.md\ + \WHERE-I-STOPPED.md\.

## One-line state

Live at snap.sinijkr.com. 4 containers healthy. 24/7 Automation Cockpit shipped 2026-05-15. D:\ promoted to canonical 2026-05-18.

## How to work on this

Open `D:\Sinister\01_Projects\Sinister\Sinister-Panel\source\` in your editor (VSCode / etc.). All of git, npm, deploys, and the agent memory layer live inside this tree.

**Deploy from D:\ (canonical):** double-click `_OneClick_Deploy.bat` next to this README — it `cd`s into `source\` and runs the same 9-step pipeline. Same script as the Desktop's `Sinister_OneClick_Deploy.bat` (which was also updated 2026-05-18 to point at this D:\ tree, so muscle-memory still works).

**Auth-tweaks coordination handoffs** with the APK agent live in `_handoffs/` — request/response MDs paired by date.

## Vault entry

Open `_vault/` in Obsidian to navigate this project's memory + cross-references.

## Cross-references

- Group navigator: `..\_README.md` + `..\_vault\_index.md`
- Hub capsule: `..\..\..\Sinister Skills\03_PROJECTS\sinister-panel.md`
- Drive master vault: `..\..\..\_vault\`

## MCP + Agent fleet access

This project (like every project in this hub) has **full access to:**

### 7 base MCP servers (160+ tools)
- `eve` (51 tools — memory, schedule, todo, watch, federate, notify)
- `sinister-panel` (13 — devices, accounts, SS07, batch, proxy, RKA)
- `sinister-snap` (12 — signup, harvest, friend, message, cvd, mitm, proxy)
- `sinister-apk` (12 — creator + detector APK build/install/broadcast)
- `sinister-tiktok` (12 — mission, signup, wire, cvd, account)
- `letstext` (27 — eve compose, reads, propose-send, fans, templates)
- `letstext-admin` (43 — compliance, ccbill, kyc, csam, investigations, tax)

Full catalog: [`../../../Sinister Skills/04_MCP/_catalog/ALL-TOOLS.md`](../../../Sinister%20Skills/04_MCP/_catalog/ALL-TOOLS.md)

### 8 specialist agents (Phase 8 — fleet)

- 📚 **Librarian** — RAG over 8,583 .md archive (`librarian.search`, `librarian.reindex`)
- ⏰ **Sentinel** — date alarms (`sentinel.list_alarms`, `sentinel.add`)
- 🌐 **Translator** — MCP tool cross-ref (`translator.find_tool`)
- 👁️ **Watcher** — source-drift detection (`watcher.scan`, `watcher.queue_refresh`)
- 🛡️ **Auditor** — secrets + dedup + freshness (`auditor.run`)
- 🏷️ **Triage** — file classification (`triage.classify`)
- ✍️ **Scribe** — daily-digest, summaries (`scribe.daily_digest`)
- 🔍 **Curator** — code-library extraction (`curator.suggest_extractions`)
- 🚌 **sinister-bus** — orchestrator (`bus.call`, `bus.replay`)

Agent bootstrap: [`../../../Sinister Skills/12_LLM_ORCHESTRATION/AGENT-BOOTSTRAP.md`](../../../Sinister%20Skills/12_LLM_ORCHESTRATION/AGENT-BOOTSTRAP.md)

### How to delegate

Operator's Claude session (or any agent in this project's context) calls these tools directly via MCP. Examples:
- `librarian.search('yurikey expiry')` → returns top 5 relevant passages ($0 cost)
- `translator.find_tool('sign apk')` → returns matching MCP tools across all servers
- `scribe.daily_digest()` → regenerates the morning briefing (Haiku-backed, ~$0.08)

Auto-updates: when new tools or agents land, they appear here next refresh tick. No project changes needed.
