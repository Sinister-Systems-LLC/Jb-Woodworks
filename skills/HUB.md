> **Author:** Sanctum sync-fleet.ps1 (regenerated)  ::  2026-05-19T14:07Z
> **Source of truth:** [`skills/_REGISTRY.yaml`](./_REGISTRY.yaml)
> **Regenerate:** `D:\Sinister Sanctum\automations\sync-fleet.ps1 -Apply`

# Sanctum Skills Hub

**The one place every Sanctum agent reads on cold-start** (per `SESSION-START/00-RULES.md`) to discover every available bot, tool, skill, external import, and invention. Status, install state, security posture, and one-line "when to use it" for each.

## How to use this file

- **As an agent:** read this on cold-start AFTER `DIRECTIVES.md` + `WORK-TOWARD.md`. Skim categories; if you spot a tool that fits your task, follow its `path` for usage.
- **As the operator:** scan `install_state` columns -- `pending` and `operator-click` rows are what need your action.
- **To add a new artifact:** append an entry under the right category in `skills/_REGISTRY.yaml`, then run `automations/sync-fleet.ps1 -Apply` to regenerate this file. Never hand-edit `HUB.md` -- the next regen overwrites manual changes.
- **To remove an artifact:** flip its `status` to `archived` in the registry and run `sync-fleet -Apply`. Source files can then `git mv` into `_archive/`.

## Counts (as of 2026-05-19T14:07Z)

- **Bots:**       13 (MCP-server agents -- the Sinister Bots fleet)
- **Tools:**      11 (operator-facing entry points)
- **Skills:**     16 (reusable modules consumed by tools/automations/bots)
- **Externals:**  10 (imported from public sources via the inflow loop)
- **Inventions:** 9 (idea cards; some shipped, some building)
- **Total:**      59

## Pending operator clicks

| Artifact | Kind | Why it's pending |
|---|---|---|
| **Sinister Vault** | tool | pending |
| **Sanctum Console (RKOJ.exe)** | tool | pending |
| **Sinister Crawler** | tool | pending |
| **Sinister Chatbot** | tool | pending |
| **Sanctum-git (self-hosted Gitea)** | tool | pending |
| **sk-swarm-coord** | skill | pending |
| **sk-vector-memory** | skill | pending |
| **sk-federation** | skill | pending |
| **sk-observability** | skill | pending |
| **sk-aidefence** | skill | pending |
| **kameleo** | skill | pending |
| **git-mirror** | skill | pending |
| **Playwright MCP** | external | operator-click |
| **Context7 MCP** | external | operator-click |
| **Sequential Thinking MCP** | external | operator-click |
| **KG-Memory MCP** | external | operator-click |
| **Sanctum Git (self-hosted Gitea)** | invention | pending |
| **Sinister Vault** | invention | pending |

## BOTS

| Name | Slug | Status | Install state | Description |
|---|---|---|---|---|
| **Sentinel** | `sentinel` | shipped | registered | Date alarms (Yurikey expiry, deadlines). Tier 1, $0/call. |
| **Translator** | `translator` | shipped | registered | MCP-tool catalog search across 268+ tool names. Tier 1, $0/call. |
| **Librarian** | `librarian` | shipped | registered | RAG over 8,500+ md archive (Ollama). Tier 2, $0/call (Ollama). |
| **Watcher** | `watcher` | shipped | registered | Source-drift detection via SHA256 manifest compare. Tier 1, $0/call. |
| **Auditor** | `auditor` | shipped | registered | Secrets scan + dedup + freshness check. Tier 1, $0/call. |
| **Sinister-bus** | `sinister-bus` | shipped | registered | Orchestrator + runlog + codec + vault + memory garden + inbox messaging. Tier... |
| **Triage** | `triage` | shipped | registered | File classifier (16 categories). Tier 2, $0/call (Ollama). |
| **Scribe** | `scribe` | shipped | registered | Daily-digest writer. Tier 3 (Claude Haiku), ~$0.02/call. |
| **Curator** | `curator` | shipped | registered | Code-library scout (helper-function extractor). Tier 3, ~$0.05/call. |
| **Custodian** | `custodian` | shipped | registered | Active backup to D:\_backups\ (SHA256 dedup). Tier 1, $0/call. |
| **Stealth-browser** | `stealth-browser` | shipped | registered | Undetected Chromium via nodriver + CDP. Tier 1, $0/call. |
| **Researcher** | `researcher` | shipped | registered | Scrape -> Ollama summarize chain. Tier 2, $0/call. |
| **Vault** | `vault` | shipped | registered | Unified façade: daemon, Gitea, Syncthing, filesystem. Tier 1, $0/call. |

## TOOLS

| Name | Slug | Status | Install state | Description |
|---|---|---|---|---|
| **Sinister Vault** | `sinister-vault` | shipped | pending | 1TB collaborative storage (daemon :5078, Gitea, Syncthing, MCP, multi-account). |
| **Session Launcher** | `session-launcher` | shipped | registered | Themed cold-start session launcher (project picker, accent, mode, --model inj... |
| **Sanctum Console (RKOJ.exe)** | `sanctum-console` | shipped | pending | Flagship workbench: 2-tab + ribbon + cycle-points + scheduler + popout + Vaul... |
| **Capture Invention** | `capture-invention` | shipped | registered | CLI to capture invention cards into inventions/YYYY-MM-DD-<slug>.md. |
| **MD Trash Bin** | `md-trash-bin` | shipped | registered | Auto-categorize random .md files into library/; sweep stale files to _trash/. |
| **Sinister Crawler** | `sinister-crawler` | building | pending | Telegram bot: /idea, /ask, /research, URL download + transcribe, plain text -... |
| **Sinister Chatbot** | `sinister-chatbot` | building | pending | Snapchat conversational AI (Eve-powered, Kameleo-driven 2x2 grid). |
| **Sinister Phone Viewer** | `sinister-phone-viewer` | shipped | registered | Per-phone scrcpy + ADB (physical display only; per-serial; never bare adb). |
| **Codex Companion** | `codex-companion` | shipped | registered | OpenAI peer-review (gpt-4o-mini/4o/o1-mini). Auth/crypto/payment/>100 LOC gate. |
| **Sanctum-git (self-hosted Gitea)** | `sanctum-git` | shipped | pending | Local Gitea at :3000 + git-mirror script. Per-agent branch + double-remote push. |
| **Panel Config** | `panel-config` | shipped | registered | Loopback-first panel routing knob (primary localhost, fallback prod, source t... |

## SKILLS

| Name | Slug | Status | Install state | Description |
|---|---|---|---|---|
| **Dashboard Skeleton** | `dashboard-skeleton` | shipped | registered | Canonical Sinister UI source: tokens, primitives, Liquid Glass, 16 doctrine p... |
| **sk-swarm-coord** | `sk-swarm-coord` | candidate | pending | Multi-agent swarm coordination: 12 MCP tools, 6 topologies, 5 consensus strat... |
| **sk-vector-memory** | `sk-vector-memory` | candidate | pending | Vector substrate (28 MCP tools): AgentDB + ONNX MiniLM + HNSW + RaBitQ (32x m... |
| **sk-federation** | `sk-federation` | candidate | pending | Cross-installation federation: zero-trust mTLS+ed25519, 5-tier trust, PII pip... |
| **sk-observability** | `sk-observability` | candidate | pending | OpenTelemetry-compatible structured logging + distributed tracing + metrics. ... |
| **sk-aidefence** | `sk-aidefence` | candidate | pending | AI safety: PII detection + prompt-injection defense + runtime hardening (LD_P... |
| **bot_memory** | `bot_memory` | shipped | registered | Per-bot facts + embeddings store with absorb()/recall(). Cross-session durabl... |
| **inbox** | `inbox` | shipped | registered | File-based inter-agent messaging + heartbeat protocol. |
| **runlog** | `runlog` | shipped | registered | sinister-runlog/v1 manifest reader/writer (session tool-calls/prompts/outputs). |
| **codec** | `codec` | shipped | registered | Memory codec: encode/decode persisted bot state blobs. |
| **crypto** | `crypto` | shipped | registered | Vault Fernet wrapper: symmetric AES-128-CBC + HMAC-SHA256, PBKDF2 200k iterat... |
| **eveObservations** | `eveObservations` | shipped | registered | Eve derivation: deriveEveObservations(fan) returns top-3 observations (tone-p... |
| **kameleo** | `kameleo` | shipped | pending | Antidetect browser client (Kameleo CLI :5050). Windows+Chrome fingerprints, 2... |
| **codex-review** | `codex-review` | shipped | registered | review(content, *, context, language, depth) -> {verdict, findings, summary}. |
| **viewer** | `viewer` | shipped | registered | Per-phone ADB + scrcpy helper. forbid_global_adb() raises on bare adb. |
| **git-mirror** | `git-mirror` | shipped | pending | Mirror Sanctum projects to localhost Gitea. Subcommands: init/push/push-all/s... |

## EXTERNALS

| Name | Slug | Status | Install state | Description |
|---|---|---|---|---|
| **Ruflo** | `ruflo` | shipped | registered | Multi-agent orchestration platform for Claude Code. Swarm + vector memory + n... |
| **Playwright MCP** | `playwright` | scouted | operator-click | Browser automation. Complements stealth-browser; structured page interactions... |
| **Context7 MCP** | `context7` | scouted | operator-click | Live library docs (kills hallucinations). Up-to-date API references for any p... |
| **Sequential Thinking MCP** | `sequential-thinking` | scouted | operator-click | Reasoning-chain scaffold. Explicit step-by-step decomposition for complex pro... |
| **KG-Memory MCP** | `memory` | scouted | operator-click | Cross-session persistent knowledge graph. Augments markdown brain with semant... |
| **Anthropic Cookbook** | `anthropic-cookbook` | scouted | not-applicable | First-party Anthropic recipes. Pattern source for brain entries (Phase E defe... |
| **MCP Registry** | `mcp-registry` | scouted | not-applicable | Official MCP server registry. Recurring discovery source for new bots (Phase D). |
| **Blender** | `blender` | scouted | not-applicable | 3D modeling / animation suite. MCP integrations exist via blender-mcp; use ca... |
| **Adobe Creative Cloud** | `adobe` | scouted | not-applicable | Photoshop / Premiere / After Effects automation. ExtendScript or Adobe API; u... |
| **Autodesk Fusion 360** | `autodesk-fusion` | scouted | not-applicable | CAD/CAM/CAE 3D modeling. Python API for scripting; use case TBD. |

## INVENTIONS

| Name | Slug | Status | Install state | Description |
|---|---|---|---|---|
| **Sinister Crawler** | `sinister-crawler` | building | not-applicable | Telegram bot for capturing ideas, asking the fleet, downloading + transcribin... |
| **Sinister Chatbot (Eve Powered)** | `sinister-chatbot` | building | not-applicable | Kameleo-driven Snapchat conversational AI; absorbed from Panel; Eve fan-obser... |
| **Sinister Phone Viewer** | `sinister-phone-viewer` | shipped | registered | scrcpy --display-id 0 (physical only) replaces Panda; per-serial; never bare ... |
| **Sanctum Git (self-hosted Gitea)** | `sanctum-git` | shipped | pending | Local Gitea at :3000; per-agent branches; double-remote push to escape GH ste... |
| **Codex Companion** | `codex-companion` | shipped | registered | OpenAI peer-review skill; cross-checks Claude on auth/crypto/payment/>100 LOC. |
| **Sinister Vault** | `sinister-vault` | shipped | pending | 1TB collaborative storage; Gitea repos + Syncthing sync + MCP + multi-account. |
| **Claude Window Manager** | `claude-window-manager` | designing | not-applicable | Multi-window Claude session orchestration with cycle-points + scheduler + pop... |
| **Session Resume + Guided Scaffold** | `session-resume-and-scaffold` | building | registered | Cold-start session scaffold + cycle-points + CLAUDE.md auto-gen per-project. |
| **Skill Review + Case-Study Workflow** | `skill-case-study` | drafting | not-applicable | Operator-triggered structured review of any skill/tool/invention. Thumb -> fl... |

## Security overview

See [`skills/SECURITY.md`](./SECURITY.md) for the full security posture: deny-list, allow-list scope, Vault Fernet encryption, Codex peer-review gate, lane discipline, external-imports workflow, MCP hygiene.

## Quick links

- [`_REGISTRY.yaml`](./_REGISTRY.yaml) -- the source of truth this file is generated from
- [`_INDEX.md`](./_INDEX.md) -- the legacy skills catalog (folder + code-library tables)
- [`../tools/_INDEX.md`](../tools/_INDEX.md) -- the tools catalog
- [`SECURITY.md`](./SECURITY.md) -- security overview
- [`../_shared-memory/external-imports/CANDIDATES.md`](../_shared-memory/external-imports/CANDIDATES.md) -- inflow loop
- [`../_shared-memory/DIRECTIVES.md`](../_shared-memory/DIRECTIVES.md) -- standing operator directives
- [`../_shared-memory/knowledge/_INDEX.md`](../_shared-memory/knowledge/_INDEX.md) -- the Sanctum brain
- [`../SESSION-START/00-RULES.md`](../SESSION-START/00-RULES.md) -- cold-start contract

