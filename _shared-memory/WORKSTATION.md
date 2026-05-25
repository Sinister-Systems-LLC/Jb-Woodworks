> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Sinister Sanctum :: the workstation

This is the master orientation doc for every Claude session. Read on cold-start (the launcher includes a link in the preamble).

Sanctum is NOT just an orchestration repo. It is the operator's **entire workstation**. Every tool the operator uses to work, build, expand, push, and ship lives inside this folder OR is registered in the catalogs below. The Console (EXE) is the unified surface — one window, all the tools.

## The 13 Sinister Bots fleet

All 13 live at `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\` (junctioned at `D:\Sinister Sanctum\bots\agents\`). Each is an MCP server registered in `~/.claude/.mcp.json`. From any Claude session, you can call:

| Bot | Tier | Cost | Default use |
|---|---|---|---|
| `sentinel` | 1 | $0 | date alarms (Yurikey, deadlines) |
| `translator` | 1 | $0 | MCP-tool catalog search |
| `librarian` | 2 | $0 | RAG over 8,500+ md archive |
| `watcher` | 1 | $0 | source-drift detection |
| `auditor` | 1 | $0 | secrets + dedup + freshness |
| `sinister-bus` | 1 | $0 | orchestrator + runlog + codec + vault + garden + inbox messaging |
| `triage` | 2 | $0 | file classifier (Ollama) |
| `scribe` | 3 | ~$0.02 | daily-digest writer (Claude Haiku) |
| `curator` | 3 | ~$0.05 | code-library scout (Claude Haiku) |
| `custodian` | 1 | $0 | active backup to D:\\_backups\\ |
| `stealth-browser` | 1 | $0 | undetected Chromium (nodriver) |
| `researcher` | 2 | $0 | scrape → Ollama summarize |
| `vault` | 1 | $0 | Sinister Vault MCP (health / list / audit / search / commit / push / pull / snapshot / sync_status / accounts — 10 `mcp__vault__*` tools per `bots/agents/vault/server.py`) |

The Console's "Bots" view (in development) makes these browsable + invokable from the UI. Full call-sheet at `_shared-memory/knowledge/bot-fleet-quick-reference.md` (109 verified `@mcp.tool()` signatures across the 13).

## Sanctum Inventions (operator-vision projects)

Append-only series of operator inventions. Each lives at `D:\Sinister Sanctum\inventions\` + has a tool implementation at `D:\Sinister Sanctum\tools\<slug>\`.

| # | Invention | Status | Implementation |
|---|---|---|---|
| 1 | **Sinister Crawler** | building | `tools/sinister-crawler/` — Telegram bot (videos, ideas, /ask, URL download + transcribe) |
| 2 | **Sinister Chatbot (Eve Powered)** | building | `tools/sinister-chatbot/` — Kameleo-driven Snapchat conversational AI absorbed from Panel |
| 3 | **Sinister Phone Viewer** | shipped | `tools/sinister-phone-viewer/` — scrcpy `--display-id 0` (no virtual display); replaces Panda |
| 4 | **Sanctum Git** (self-hosted Gitea) | building | `tools/sanctum-git/` — local Gitea at :3000; get off github.com |
| 5 | **Codex Companion** | building | `tools/codex-companion/` — OpenAI peer-review skill; cross-checks Claude |
| 6 | **Sinister Vault** | shipped | `tools/sinister-vault/` — 1TB collaborative storage; Gitea for repos, Syncthing for real-time sync, MCP for agent access, multi-account for operator + Leo |

## Tools (catalog at `tools/_INDEX.md`)

Operator-facing entry points. Each tool has its own folder with a README "tool card":

- `session-launcher` — `Start-Sinister-Session.bat` + the PS1 (v6 cinematic boot with ASCII skull, pre-flight checklist, 4-question wizard, multi-agent spawn, multi-account rotation, auto-resume A/G picker)
- `sanctum-console` — `Open-Sanctum-Console.bat` (browser) / `Sanctum-Desktop.bat` (native window via pywebview) / `Sanctum-LAN.bat` (phone access + QR)
- `capture-invention` — `Capture-Invention.bat` (drop ideas into `inventions/`)
- `md-trash-bin` — `Sweep-MD-Trash.bat` (auto-categorize random .md files into `library/`)
- `sinister-crawler` — `Sanctum-Crawler-Start.bat` (Telegram bot)
- `sinister-chatbot` — `Sanctum-Chatbot-Start.bat` (Snap chatbot, Eve-powered)
- `sinister-phone-viewer` — invoked via Console's Devices tab (or `viewer.py` CLI)
- `sanctum-git` — `Sanctum-Git-Start.bat` (boots local Gitea)
- `codex-companion` — `Codex-Review-Test.bat` + `POST /api/codex/review`
- `kameleo-browser` — Leo's pointer (lives in panel source; tool card at `tools/kameleo-browser/`)

Plus operator-side memory tools:
- `Update-Sanctum-Memory.bat` — append a directive (every future agent sees it)
- `Log-Progress.bat` — log an agent's milestone (cross-fleet feed)
- `Log-Knowledge.bat` — append a discovery / fix / workaround to the Sanctum brain
- `Browse-Knowledge.bat` — TUI browse + search the brain
- `Fix-Claude-Memory.bat` — refresh / reset Claude's local cache
- `Mirror-To-Sanctum-Git.bat` — sync a project's branch to local Gitea (and optionally GH)

## Skills (catalog at `skills/_INDEX.md`)

Reusable patterns / libraries / SDKs that tools consume:

- `_shared/bot_memory.py` (under hub) — per-bot facts/embeddings + absorb/recall
- `_shared/inbox.py` — file-based inter-agent messaging + heartbeat
- `_shared/runlog.py` — sinister-runlog/v1 manifest readers
- `_shared/codec.py` — memory codec encode/decode
- `_shared/crypto.py` — vault Fernet wrapper
- `dashboard-skeleton` (Desktop ref) — canonical UI source (iOS blue + Liquid Glass + 16 primitives)
- `eveObservations` — server-side derivation of "Eve thinks…" fan observations
- `kameleo` — Kameleo antidetect browser API client
- `viewer` — scrcpy + ADB containerized helper (per-phone, no virtual display)
- `codex-review` — OpenAI peer-review skill
- `git-mirror` — push current branch to local Gitea + (optionally) GH

## Per-agent branch discipline (forever-rule)

EVERY Claude session works on its own branch named:
```
agent/<your-SINISTER_AGENT_NAME-slugified>/<short-topic>
```

Examples:
- `agent/sinister-snap-api/pure-api-ss03`
- `agent/sinister-sanctum/master-tooling-v6`
- `agent/sinister-tiktok-api/audit-pure-api`

This is how 5+ concurrent Claude sessions don't step on each other. Branches push to BOTH `origin` (github.com) and `sanctum` (localhost Gitea) via `git-mirror push <project-key>`. Merge cross-agent only with operator OK.

## Cross-agent memory (`_shared-memory/`)

The fleet's collective brain. Sub-folders:

| Folder | Purpose |
|---|---|
| `DIRECTIVES.md` | Standing operator rules (read on every cold-start) |
| `WORK-TOWARD.md` | Rolling shared goals across all Sinister projects |
| `PROGRESS/<agent>.md` | Per-agent milestone log (append-only; aggregated by Console) |
| `knowledge/<slug>.md` | The Sanctum brain — per-topic fixes/gotchas/workarounds. Every agent reads + writes. |
| `notes/` | Ad-hoc cross-agent notes (e.g. ADB-containerization quick-card) |
| `notes/phones/<SERIAL>.md` | Per-phone state (capabilities, last attestation, installed modules) |
| `codex-reviews/` | Audit log of every Codex peer-review (verdicts + findings) |

## The Console (EXE) — workstation surface

`RKOJ.exe` (the flagship binary; built via PyInstaller from `desktop_app.py`; previously named `Sanctum-Console.exe`) is the single operator-facing window for ALL of this. Vault drawer in the dev-tools rail surfaces quota meter + recent audit + sync status.

Sidebar (left): tool categories. Currently `Claude agents` (Dashboard / Progress / Memory / Inbox / Settings / Skills / Tools / Inventions / Codex), `Phone viewer` (Devices). Forever-growing — new tools just push to `WINDOW_TOOLS_REGISTRY` in `server.py`.

Top toolbar: `+ NEW WINDOW`, `SPLIT VIEW`, `CLOSE SPLIT`.

Auth: HWID-locked per key. 2 keys: operator + leo (delivered separately via secure channel). First-use binds to the machine's HWID. Same key on a different machine = denied.

LAN mode (`Sanctum-LAN.bat`): exposes :5077 on the LAN with bearer-token auth + QR code → phone scans → operator's console pocketed.

## Cold-start contract (every agent, every turn)

Per the cold-start phrase the launcher injects, every Claude session on cold-start MUST:
1. Read SESSION-START/ in order
2. Read OPERATOR-DIRECTIVES.md (master memory)
3. Read PARALLEL-AGENT-COORDINATION.md (ownership zones)
4. Read `_shared-memory/DIRECTIVES.md` + `WORK-TOWARD.md` + `WORKSTATION.md` (this file)
5. **Read `skills/HUB.md`** (the Skills Hub — single discovery surface for every bot/tool/skill/external/invention; source of truth at `skills/_REGISTRY.yaml`; regen via `automations/sync-fleet.ps1 -Apply`). Added 2026-05-19 per Rule 10.
6. Log progress to `_shared-memory/PROGRESS/<your-name>.md` for every milestone
7. Add agent-authorship to every .bat/.md/.ps1 created
8. Use the Sanctum brain (`_shared-memory/knowledge/`) — write discoveries, read before risky actions
9. Use per-agent branches when pushing

## Aspirational stack (next 90 days)

Per `docs/HARDWARE-ROADMAP.md`:
- Used 3090 24GB → local Llama 3 70B / Mixtral / Qwen 2.5 / DeepSeek-Coder
- 2× 8TB externals → cross-drive backup (off the same disk as originals)
- N100 mini-PC → 24/7 Restic / Syncthing / Tailscale / Gitea / Uptime Kuma
- Used DS220+ NAS → RAID-1 + Nextcloud + Plex
- UPS + managed switch + Pi 5 (Tier 3)

Total ~$2,060 itemized on Desktop at `Hardware-Roadmap.md` with clickable purchase links.

## TL;DR

- **How we won:** Sanctum is now a workstation, not just a repo. Console = one window for every tool + bot + project + phone + brain. Self-hosted Gitea coming for real-time multi-agent work without GH stepping on each other.
- **What each agent does:** read this file, read DIRECTIVES, log progress, write knowledge, use your branch, don't step on lanes. The fleet gets smarter the longer it runs.
