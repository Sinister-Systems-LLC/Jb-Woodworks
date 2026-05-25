# Sinister LLC architecture

How the pieces fit. For Leo + future collaborators onboarding day 1.

## Three layers

```
┌───────────────────────────────────────────────────────────┐
│  Layer 3: Sinister Bots fleet (13 MCP agents)             │
│  - Recall (librarian, translator, researcher)             │
│  - Audit + maintain (auditor, watcher, custodian)         │
│  - Surface + summarize (scribe, curator, sentinel)        │
│  - Bridge (sinister-bus, stealth-browser, triage, vault)  │
│  Cost: $0-$0.10/day at routine use                        │
└───────────────────────────────────────────────────────────┘
                      ▲ (calls; never calls Opus)
┌───────────────────────────────────────────────────────────┐
│  Layer 2: Sinister projects (8)                           │
│  - snap-signer (pure-API + phone-stack Snap registration) │
│  - sinister-snap-emu (cvd-based Snap signing oracle)      │
│  - sinister-tiktok-emu (TT a11y + signing track)          │
│  - sinister-bumble-emu (BMA signing pipeline)             │
│  - sinister-panel (live dashboard at snap.sinijkr.com)    │
│  - sinister-rka-good (RKA daemon + keybox distribution)   │
│  - kernel-su-setup (Sinister-Detector + KSU mods)         │
│  - library-of-alexandria (cross-project archive)          │
└───────────────────────────────────────────────────────────┘
                      ▲ (depend on)
┌───────────────────────────────────────────────────────────┐
│  Layer 1: Shared infra                                    │
│  - Yurikey (root cert; rotating)                          │
│  - RKA protocol (Hetzner VPS daemon + phone clients)      │
│  - KernelSU + LukeShield (kernel modules)                 │
│  - Sinister Panel (web ops dashboard)                     │
└───────────────────────────────────────────────────────────┘
```

## Data flows

### Operator workflow

1. Operator says "what's expiring" -> Claude session routes to `sentinel.check_urgent` -> $0
2. Operator says "what's the SS03 state" -> `librarian.search "SS03"` -> Ollama -> $0
3. Operator says "scrape this competitor page" -> `researcher.summarize_url` -> stealth-browser + Ollama -> $0
4. Operator says "render today's digest" -> `scribe.generate_digest` -> Haiku ~$0.02
5. Operator says "plan the next phase" -> stays on Opus (multi-step reasoning)

### Memory growth

1. Operator absorbs facts: `<bot>.absorb(fact, source, tags=[])`
2. Bot writes to `agents/<bot>/learned.md` (atomic + audit-logged)
3. If Ollama up, bot eager-embeds the fact -> `learned-embeddings.jsonl`
4. Next call: bot loads top-K relevant facts (vector retrieval) into prompt-cached system message
5. Repeat. Bot grows. Token cost stays flat (~$0.02/call) regardless of fact count.

### Backup

1. Custodian daemon (Windows scheduled task) wakes every 120s
2. Walks `D:\_backups\_config\watch-list.json` sources
3. sha-diffs each file; copies only changed bytes to `D:\_backups\snapshots\<source>\<rel>\<base>.<utc>.<sha8>.<ext>`
4. Appends to `D:\_backups\_manifest.jsonl`
5. Hourly: applies retention (keep last 5, last 7 days, max 30/file)

### Runlog

1. Operator runs `Sinister-Bots-Activation.bat` (or any operator-script)
2. Script emits manifest to `runtime-state/script-runs/<script>-<utc>.json`
3. Bat auto-closes on success
4. Bot in next session calls `sinister-bus.runlog_latest <script>` to learn the outcome
5. Operator-pending next-actions accumulate in `runtime-state/PENDING-NEXT-ACTIONS.md`

## Where each piece lives

| Piece | Path |
|---|---|
| Bot code | `bots/<bot>/server.py` (junction to hub) |
| Shared helpers | `bots/_shared/{bot_memory,runlog}.py` |
| Project code | `projects/<project>/` (junction to operator desktop source) |
| Cross-project docs | `docs/*.md` |
| Operator scripts | `automations/*.ps1` |
| Master Obsidian vault | `_vault/_index.md` |
| Knowledge graph (scope-level) | `06_UNDERSTAND/_scope/sinister-llc/` (in the canonical hub) |
| LICENSE + CONTRIBUTING | repo root |

## TL;DR

- **How we won:** Three clean layers — bots / projects / infra — each independently developable + restore-pointed.
- **What you need to do:** Read `bots/README.md` first if you're working on agent code; read `projects/<project>/README.md` if you're working on a project.
