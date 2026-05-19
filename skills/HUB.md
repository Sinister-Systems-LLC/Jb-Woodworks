> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19 (v1 hand-written; future regens via `automations/sync-fleet.ps1 -Apply`)
> **Source of truth:** [`skills/_REGISTRY.yaml`](./_REGISTRY.yaml)
> **Regenerate:** `D:\Sinister Sanctum\automations\sync-fleet.ps1 -Apply`

# Sanctum Skills Hub

**The one place every Sanctum agent reads on cold-start** (per `SESSION-START/00-RULES.md`) to discover every available bot, tool, skill, external import, and invention. Status, install state, security posture, and one-line "when to use it" for each.

## How to use this file

- **As an agent:** read this on cold-start AFTER `DIRECTIVES.md` + `WORK-TOWARD.md`. Skim categories; if you spot a tool that fits your task, follow its `path` for usage.
- **As the operator:** scan `install_state` columns — `pending` and `operator-click` rows are what need your action.
- **To add a new artifact:** append an entry under the right category in `skills/_REGISTRY.yaml`, then run `automations/sync-fleet.ps1 -Apply` to regenerate this file. **Never hand-edit `HUB.md` once sync-fleet is in production** — the next regen overwrites manual changes.
- **To remove an artifact:** flip its `status` to `archived` in the registry and run `sync-fleet -Apply`. Source files can then `git mv` into `_archive/`.

## Counts (as of 2026-05-19 13:30Z)

- **Bots:**       13 (MCP-server agents — the Sinister Bots fleet)
- **Tools:**      11 (operator-facing entry points)
- **Skills:**     11 (reusable modules consumed by tools/automations/bots)
- **Externals:**  10 (imported from public sources via the inflow loop)
- **Inventions:** 9 (idea cards; some shipped, some building)
- **Total:**      54

Plus 38+ Claude Code skills loaded via `claude-flow` (Ruflo) — see the **EXTERNALS** section for Ruflo's entry.

## Pending operator clicks (highest leverage first)

| Artifact | Kind | What unlocks |
|---|---|---|
| **Vault** (bot) | `bot` | `vault.*` MCP tools across every Claude session. See `tools/sinister-vault/INSTALL-MCP.md`. |
| **Ruflo** (external) | `external` | `ruflo.*` MCP tools. `claude mcp add ruflo -- npx ruflo@latest mcp start` + restart. (Note: 38+ claude-flow skills are already live in this session.) |
| **Playwright MCP** | `external` | Structured browser automation. Run `automations/install-mcp-servers.ps1`. |
| **Context7 MCP** | `external` | Live library docs (kills hallucinations). Same install script. |
| **Sequential Thinking MCP** | `external` | Reasoning-chain scaffold. Same install script. |
| **KG-Memory MCP** | `external` | Persistent knowledge graph. Same install script. Writes to `D:\Sinister\Sinister Skills\01_MEMORY\_kg-memory\graph.json`. |
| **Sanctum Console (RKOJ.exe)** (tool) | `tool` | Auto-start daemon. Run `automations/window-manager/install-console-task.ps1 -BatPath <...>`. |
| **Sinister Vault** (tool) | `tool` | Auto-start daemon. Run `tools/sinister-vault/wire-everything.ps1`. |
| **Sanctum-git** (tool) | `tool` | Local Gitea at :3000. See `tools/sanctum-git/FIRST-RUN.md`. |
| **Sinister Crawler / Chatbot** (tools) | `tool` | Both `building`. See `tools/<slug>/SMOKE.md` / `RUN.md`. |

## BOTS — 13 MCP-server agents (the Sinister Bots fleet)

| Name | Slug | Tier | Cost | When to use |
|---|---|---|---|---|
| Sentinel | `sentinel` | 1 | $0 | Date alarms (Yurikey expiry, deadlines). |
| Translator | `translator` | 1 | $0 | Search the catalog of 268+ MCP tool names. |
| Librarian | `librarian` | 2 | $0 (Ollama) | RAG over 8,500+ md archive. |
| Watcher | `watcher` | 1 | $0 | Source-drift detection (SHA256 manifest compare). |
| Auditor | `auditor` | 1 | $0 | Secrets + dedup + freshness check. |
| Sinister-bus | `sinister-bus` | 1 | $0 | Orchestrator + runlog + vault + memory garden + inbox. |
| Triage | `triage` | 2 | $0 (Ollama) | File classifier (16 categories). |
| Scribe | `scribe` | 3 | ~$0.02 | Daily-digest writer (Claude Haiku). Needs `ANTHROPIC_API_KEY`. |
| Curator | `curator` | 3 | ~$0.05 | Code-library scout. Needs `ANTHROPIC_API_KEY`. |
| Custodian | `custodian` | 1 | $0 | Active backup to `D:\_backups\`. |
| Stealth-browser | `stealth-browser` | 1 | $0 | Undetected Chromium via nodriver + CDP. |
| Researcher | `researcher` | 2 | $0 | Scrape -> Ollama summarize. |
| **Vault** (`pending`) | `vault` | 1 | $0 | Daemon + Gitea + Syncthing + multi-account. See `tools/sinister-vault/INSTALL-MCP.md`. |

## TOOLS — 11 operator-facing entry points

| Name | Slug | Status | When to use |
|---|---|---|---|
| Sinister Vault | `sinister-vault` | shipped (daemon live; auto-start pending) | 1TB collaborative storage, daemon at :5078. |
| Session Launcher | `session-launcher` | shipped | Themed cold-start (project/accent/mode/--model). Desktop bat. |
| Sanctum Console (RKOJ.exe) | `sanctum-console` | shipped (auto-start pending) | Flagship workbench. 2-tab + ribbon + dev-tools rail. |
| Capture Invention | `capture-invention` | shipped | CLI to drop invention cards into `inventions/`. |
| MD Trash Bin | `md-trash-bin` | shipped | Auto-categorize random .md files; sweep stale to `_trash/`. |
| Sinister Crawler | `sinister-crawler` | building | Telegram bot for ideas/asks/research/URLs. |
| Sinister Chatbot | `sinister-chatbot` | building | Snapchat conversational AI (Eve-powered, Kameleo). |
| Sinister Phone Viewer | `sinister-phone-viewer` | shipped | Per-phone scrcpy + ADB (physical display only). |
| Codex Companion | `codex-companion` | shipped | OpenAI peer-review for auth/crypto/payment/>100 LOC. |
| Sanctum-git | `sanctum-git` | shipped (first-run pending) | Local Gitea at :3000 + git-mirror. |
| Panel Config | `panel-config` | shipped | Loopback-first panel routing. |

## SKILLS — 11 reusable modules

| Name | Slug | When to use |
|---|---|---|
| Dashboard Skeleton | `dashboard-skeleton` | All new UIs — Liquid Glass + 16 doctrine primitives. |
| bot_memory | `bot_memory` | Per-bot durable facts + embeddings. `absorb()` / `recall()`. |
| inbox | `inbox` | File-based inter-agent messaging + heartbeat. |
| runlog | `runlog` | sinister-runlog/v1 manifest reader/writer. |
| codec | `codec` | Memory blob encode/decode. |
| crypto | `crypto` | Vault Fernet (AES-128-CBC + HMAC-SHA256, PBKDF2 200k). Needs `SINISTER_VAULT_PASSPHRASE`. |
| eveObservations | `eveObservations` | Top-3 fan-observation derivation (tone-priority). |
| kameleo | `kameleo` | Antidetect browser client (Windows+Chrome, 2x2 tiling). |
| codex-review | `codex-review` | OpenAI peer-review function. Logs to `_shared-memory/codex-reviews/`. |
| viewer | `viewer` | Per-phone ADB + scrcpy. `forbid_global_adb()` raises on bare `adb`. |
| git-mirror | `git-mirror` | Mirror to localhost Gitea. Pending Sanctum-git first-run. |

## EXTERNALS — 10 imported (or scouted) from public sources

| Name | Slug | Status | Source |
|---|---|---|---|
| **Ruflo** (claude-flow) | `ruflo` | scouted (skill catalog LIVE; MCP wire pending) | `github.com/ruvnet/ruflo` MIT, SHA `c292e5f...` |
| Playwright MCP | `playwright` | scouted (install script ready) | `@playwright/mcp@latest` |
| Context7 MCP | `context7` | scouted (install script ready) | `@upstash/context7-mcp@latest` |
| Sequential Thinking MCP | `sequential-thinking` | scouted (install script ready) | `@modelcontextprotocol/server-sequential-thinking` |
| KG-Memory MCP | `memory` | scouted (install script ready) | `@modelcontextprotocol/server-memory` |
| Anthropic Cookbook | `anthropic-cookbook` | scouted (Phase E deferred — pattern extracts only) | `github.com/anthropics/claude-cookbooks` |
| MCP Registry | `mcp-registry` | scouted (Phase D deferred — `tools/mcp-discover/`) | `registry.modelcontextprotocol.io` |
| Blender | `blender` | scouted (Image 1 queue; use case pending) | `blender.org` |
| Adobe Creative Cloud | `adobe` | scouted (Image 1 queue; use case pending) | `adobe.com/creativecloud.html` |
| Autodesk Fusion 360 | `autodesk-fusion` | scouted (Image 1 queue; use case pending) | `autodesk.com/products/fusion-360` |

**Note on Ruflo / claude-flow:** even though the MCP server isn't yet wired via `claude mcp add ruflo`, **38+ claude-flow Claude Code skills are already loaded** in this Claude Code session (visible in the system-reminder skill list — `agentdb-*`, `github-*`, `hive-mind-advanced`, `reasoningbank-*`, `swarm-*`, `v3-*`, etc.). These are invokable via the `Skill` tool right now. The MCP wire is the additional path that exposes Ruflo's `ruflo.*` programmatic tools (vs the skill catalog which is invocation-style).

## INVENTIONS — 9 idea cards (some shipped, some in flight)

| # | Slug | Status |
|---|---|---|
| 1 | `sinister-crawler` | building |
| 2 | `sinister-chatbot` | building |
| 3 | `sinister-phone-viewer` | shipped |
| 4 | `sanctum-git` | shipped |
| 5 | `codex-companion` | shipped |
| 6 | `sinister-vault` | shipped |
| 7 | `claude-window-manager` | designing (paused) |
| 8 | `session-resume-and-scaffold` | building |
| 9 | `skill-case-study` | drafting |

## Security overview

Every Sanctum capability is shaped by these gates (see [`skills/SECURITY.md`](./SECURITY.md) for the full posture):

- **Deny-list:** `rm -rf` against root paths, `git push --force` to main/master, `taskkill /F /IM adb.exe`, sandbox-blocked categories from `SESSION-START/03-GOTCHAS.md`.
- **Allow-list scope:** 210+ Bash patterns pre-authorized in `~/.claude/settings.json`. `bypassPermissions: true` + `skipAutoPermissionPrompt: true` — operator trusts the config; deny-list is the safety floor.
- **Vault:** secrets live under `_vault/`. Fernet AES-128-CBC + HMAC-SHA256, PBKDF2 200k iterations. Passphrase via `SINISTER_VAULT_PASSPHRASE` env var.
- **Codex peer-review gate:** any auth / crypto / payment / secrets / >100 LOC code-touch runs through `tools/codex-companion/codex.py`. `fail` or `warn`+high-severity → BLOCK.
- **Lane discipline:** master never touches `projects/<proj>/source/` or `~/.claude/.mcp.json` directly. Per-project agents own their lane. Operator owns LICENSE.
- **External-imports workflow:** scout → case-study → Codex review → operator 👍/👎 → promote/archive. Append-only audit at `_shared-memory/external-imports/CANDIDATES.md`.
- **MCP hygiene:** `install-mcp-servers.ps1` always backs up `.mcp.json` first. Operator restarts Claude Code in a fresh window.

## Quick links

- [`_REGISTRY.yaml`](./_REGISTRY.yaml) — the source of truth this file is generated from
- [`_INDEX.md`](./_INDEX.md) — the legacy skills catalog (folder + code-library tables)
- [`../tools/_INDEX.md`](../tools/_INDEX.md) — the tools catalog
- [`SECURITY.md`](./SECURITY.md) — security overview
- [`../_shared-memory/external-imports/CANDIDATES.md`](../_shared-memory/external-imports/CANDIDATES.md) — inflow loop
- [`../_shared-memory/external-imports/README.md`](../_shared-memory/external-imports/README.md) — inflow-loop spec
- [`../_shared-memory/DIRECTIVES.md`](../_shared-memory/DIRECTIVES.md) — standing operator directives
- [`../_shared-memory/knowledge/_INDEX.md`](../_shared-memory/knowledge/_INDEX.md) — the Sanctum brain
- [`../SESSION-START/00-RULES.md`](../SESSION-START/00-RULES.md) — cold-start contract
- [`../docs/ENV-VARIABLES.md`](../docs/ENV-VARIABLES.md) — every env var Sanctum reads
- [`../docs/RKOJ-OPERATOR-GUIDE.md`](../docs/RKOJ-OPERATOR-GUIDE.md) — RKOJ workbench guide

## How "one place we grow that all agents can use" works

1. Operator (or master agent) edits `_REGISTRY.yaml` to add/update an artifact.
2. Run `automations/sync-fleet.ps1 -Apply` — regenerates this file, prints drift vs `.mcp.json`.
3. Any pending operator clicks land in the "Pending operator clicks" table above.
4. Every fresh Claude session reads this HUB on cold-start (per `SESSION-START/00-RULES.md` update) and reports back what's available.
5. New tools / skills / externals are added via the case-study workflow (operator-gated thumbs). See `_shared-memory/DIRECTIVES.md` and `_shared-memory/external-imports/README.md`.
