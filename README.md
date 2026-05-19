# Sinister Sanctum

> ðŸ“› **Local path:** `D:\Sinister Sanctum\` (junction) **or** `D:\Sinister Sanctum\` (canonical underlying). Both resolve to the same content. Use whichever feels natural; existing scripts use `D:\Sinister Sanctum\` and won't break.
> See **`SANCTUM.md`** for the 5-repo universe (Sanctum + Snap-API-EMU + TikTok-EMU + Panel + Kernel-APK).
> **GitHub org:** `Sinister-Systems-LLC`

Sanctum is the "new library of alexandria" for Sinister â€” the orchestration repo
that every other Sinister company project consumes for bots, automations, docs,
session-start protocols, backup tooling, and the GitHub-push workflow.

> **2026-05-19 pivot:** The flagship workstation binary is now **`RKOJ.exe`** (built from `automations/window-manager/`, replaces `Sanctum-Console.exe`) and the canonical collaborative storage layer is the **Sinister Vault** at `D:\sinister-vault\` (Gitea + Syncthing + MCP + multi-account; daemon on `localhost:5078`). Quick links:
> - RKOJ operator one-pager: [`docs/WORKBENCH.md`](docs/WORKBENCH.md)
> - RKOJ architecture brain entry: [`_shared-memory/knowledge/rkoj-workbench-architecture.md`](_shared-memory/knowledge/rkoj-workbench-architecture.md)
> - Vault tool card: [`tools/sinister-vault/README.md`](tools/sinister-vault/README.md)
> - Vault architecture brain entry: [`_shared-memory/knowledge/sinister-vault-architecture.md`](_shared-memory/knowledge/sinister-vault-architecture.md)
> - Multi-account: [`tools/sinister-vault/ACCOUNTS.md`](tools/sinister-vault/ACCOUNTS.md) | Gitea integration: [`tools/sanctum-git/vault-integration.md`](tools/sanctum-git/vault-integration.md)

**Scope:** ALL Sinister company projects. **Excluded:** LetsText, JOKR-global,
library-of-jokr-mirror, personal stuff, operator-private references (Yurikey
roster, secrets policy). Those stay in the operator's hub at
`D:\Sinister\Sinister Skills\` only and never reach this repo.

## What other agents are doing right now

The operator runs parallel Claude sessions, one per Sinister project. Each
session populates its own subdir under `D:\Sinister\01_Projects\Sinister\<project>\source\`
(per the operator's MASTER-PLAN Phase 1 layout). All of those subdirs are now
in the Custodian backup watch-list, so changes from any agent are snapshotted
every 120s.

Per-project ownership zones are documented in `PARALLEL-AGENT-COORDINATION.md`.
Master (this session) handles cross-project orchestration + Sanctum docs only;
project sources are owned by each project's session.

## Layout

```
D:\Sinister Sanctum\
â”œâ”€â”€ README.md                       you are here
â”œâ”€â”€ LICENSE                         (operator picks: MIT / Apache-2.0 / private)
â”œâ”€â”€ .gitignore                      excludes venvs, node_modules, .env, credentials, snapshots, logs
â”œâ”€â”€ .github/
â”‚   â””â”€â”€ workflows/                  CI for the bots (lint, smoke-test health() calls)
â”œâ”€â”€ bots/                           the 12 Sinister Bots (mirror of 12_LLM_ORCHESTRATION/agents/)
â”‚   â”œâ”€â”€ README.md                   fleet overview + how to install
â”‚   â”œâ”€â”€ _shared/                    bot_memory + runlog Python helpers
â”‚   â”œâ”€â”€ sentinel/   translator/   librarian/   watcher/   auditor/
â”‚   â”œâ”€â”€ sinister-bus/   triage/   scribe/   curator/   custodian/
â”‚   â”œâ”€â”€ stealth-browser/   researcher/
â”‚   â””â”€â”€ install-fleet.ps1
â”œâ”€â”€ projects/                       Sinister-branded source projects (initially junctions; later git submodules or true copies)
â”‚   â”œâ”€â”€ snap-signer/
â”‚   â”œâ”€â”€ sinister-tiktok-emu/
â”‚   â”œâ”€â”€ sinister-snap-emu/
â”‚   â”œâ”€â”€ sinister-bumble-emu/
â”‚   â”œâ”€â”€ sinister-panel/
â”‚   â”œâ”€â”€ sinister-rka-good/
â”‚   â”œâ”€â”€ sinister-snap-apk/
â”‚   â”œâ”€â”€ kernel-su-setup/
â”‚   â””â”€â”€ library-of-alexandria/      (mirror project; verify with operator before publishing)
â”œâ”€â”€ automations/                    cross-project glue (the bat/ps1 the operator runs)
â”‚   â”œâ”€â”€ activate-everything.ps1
â”‚   â”œâ”€â”€ aggregate-gotchas.ps1
â”‚   â”œâ”€â”€ _runlog.ps1
â”‚   â””â”€â”€ refresh-scripts-index.ps1
â”œâ”€â”€ docs/                           Sinister-LLC-public docs only
â”‚   â”œâ”€â”€ BOT-MEMORY-PROTOCOL.md      operator-curated learning protocol
â”‚   â”œâ”€â”€ MCP-NETWORK.md              bot <-> base MCP integration map
â”‚   â”œâ”€â”€ ARCHITECTURE.md             overall system shape
â”‚   â””â”€â”€ ONBOARDING.md               for Leo + future collaborators
â””â”€â”€ _vault/                         master Obsidian vault for Sinister LLC scope
    â”œâ”€â”€ _index.md                   wiki-links into per-group and per-project vaults
    â”œâ”€â”€ attestation/                cross-project attestation notes (RKA, keybox, Yurikey-shape but NOT roster)
    â”œâ”€â”€ automation/                 cross-project automation notes (Luke, KPM, Detector strategies)
    â””â”€â”€ api-surfaces/               per-platform API maps (Snap, TikTok, Bumble) without secrets
```

## Vault + knowledge-graph chain (per operator directive 2026-05-18 PM)

Three layers of Obsidian vault, all wiki-linked:

```
D:\Sinister Sanctum\_vault\              MASTER (Sinister LLC scope)
   |  wiki-links into
   v
D:\Sinister Sanctum\projects\<group>\_vault\    GROUP (e.g. Sinister-APIs/, Sinister-Mobile/)
   |  wiki-links into
   v
D:\Sinister Sanctum\projects\<project>\_vault\  PROJECT
```

Three layers of understand-anything knowledge graph:
- **Per project** at `06_UNDERSTAND/<project>/graph.json` (existing pattern)
- **Per group** at `06_UNDERSTAND/_groups/<group>/graph.json` (new â€” combines project graphs)
- **Per scope** at `06_UNDERSTAND/_scope/sinister-llc/graph.json` (new â€” master)

Edges flow up: a node in a project graph references nodes in its group graph;
group nodes reference scope nodes. Operator opens the master vault to navigate
the entire LLC; project vault for deep dive.

## What is NOT in this repo (operator-private)

- LetsText (all 2.0 work, dashboards, admin)
- JOKR-global, library-of-jokr-mirror
- Personal scripts, Quality-of-Life, Games
- `09_REFERENCE/yurikey-roster.md` (the roster itself; the *shape* of Yurikey may be discussed in `docs/`)
- `09_REFERENCE/secrets-redaction-policy.md` (the policy itself; reference it from docs/ONBOARDING.md by name only)
- `01_MEMORY/_consolidated/ALL-*.md` (operator daily working state)
- `_backups/`, `_logs/`, `runtime-state/`, `01_MEMORY/_bus/`

## Migration status

This directory was scaffolded **2026-05-18** during the Sinister Bots Phase 8i+
activation pass. Real project content arrives in a follow-up step after:
1. The operator confirms which projects + at which path (source vs junction vs copy).
2. The per-project secrets scrub completes (auditor.run on each source root).
3. The git remote(s) are decided (one monorepo, or per-project submodules).

See `_logs/MIGRATION-STATUS.md` (created on first migration pass).

## Install (when ready)

```powershell
cd 'D:\Sinister Sanctum'
.\automations\activate-everything.ps1   # registers bots from THIS dir, not the hub
```

The bots reuse the same `bot_memory` + `runlog` modules; they just live under a
different root. `SINISTER_HUB_ROOT` env var lets a single Claude install point
at either `D:\Sinister\Sinister Skills` (operator's private hub) or
`D:\Sinister Sanctum` (the business-shared repo).

## UI design system

**Operator directive (2026-05-19):** use `C:\Users\Zonia\Desktop\dashboard-skeleton\` ONLY for all new UIs.

Every UI surface in Sanctum and downstream product repos consumes the `dashboard-skeleton` token set, Liquid Glass material classes, and 16 doctrine primitives. Panel-side accent is iOS blue (`#0A84FF`); Sanctum-side accent is the purple ramp (`#7A3DD4` / `#A06EFF` / `#4A1F8E`) paired with the master logo at `C:\Users\Zonia\Desktop\INPO\Things\ART\Img.png`.

See **[`docs/UI-DESIGN-SYSTEM.md`](docs/UI-DESIGN-SYSTEM.md)** for token tables, Liquid Glass catalog, primitive list, type scale, when-to-consume-what guide, and forbidden patterns. Upstream authority: `C:\Users\Zonia\Desktop\dashboard-skeleton\THEME-DOCTRINE.md`.
