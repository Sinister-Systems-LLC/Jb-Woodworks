# Sanctum Readiness Audit — 2026-05-21

Author: RKOJ-ELENO :: 2026-05-21

Operator brief: *"make sure the sinister sanctum files, memory files, setup etc. is ready for the jcode setup and will work perfectly with it and all the new tools we are building."*

Scope: read-only audit + safe remediation (dirs + index rows only). Stayed out of `tools/sinister-rkoj-qt/sinister_rkoj_qt/*.py` and `projects/sinister-claw/source/app/*` per directive.

## Summary

- 15 audit checks executed
- 12 PASS, 3 with action taken or surfaced
- Safe remediations applied: 10 dirs created, 4 catalog rows added
- 4 items surfaced for operator follow-up

## PASS (12)

1. **MANIFEST.json** parses; 27 components; 0 broken disk paths (`(pypi: mcp)` is a pseudo-path tag, ignored).
2. **MCP config** at `~/.claude/.mcp.json` parses; 23 servers loaded (eve, sinister-panel, sinister-snap, sinister-tiktok, sinister-apk, letstext, letstext-admin, sentinel, translator, librarian, watcher, auditor, sinister-bus, triage, scribe, curator, custodian, stealth-browser, researcher, playwright, context7, sequential-thinking, memory).
3. **CLAUDE.md** present at sanctum root + contains both `RKOJ-ELENO` authorship binding and `EVE` persona binding.
4. **session-contracts.md** present (12,838 bytes).
5. **external-imports/CANDIDATES.md** present.
6. **resume-point-write.ps1** present + ASCII-only (0 non-ascii bytes in 8,302).
7. **watchdog registry** parses; 4 agents (sanctum/sinister-forge/sinister-vault/rkoj) + ollama service; all required fields (`kind`, `command`, `args`, `cwd`) present.
8. **watchdog.log** parent + file present (51 KB, mtime today).
9. **resume-points/Sanctum/** has 15 JSON files; latest (`2026-05-21T181202Z.json`) carries all required schema fields (schema_version, ts_utc, project, agent_name, mode, git, progress_top3, pre_warm_reads).
10. **.gitignore** — top-level `__pycache__/`, `build/`, `dist/` rules cover `tools/sinister-rkoj-qt/` transitively (no path-scoped rules needed).
11. **session-templates/projects.json** parses; 14 lanes registered (sanctum, sinister-panel, kernel-apk, sinister-emulator, rkoj-workstation, snap-emulator-api, tiktok-emulator-api, bumble-emulator-api, sinister-forge, sinister-mind, sinister-term, sinister-claw, rkoj, sinister-freeze).
12. **OPERATOR-ACTION-QUEUE.md** readable; 39 open `[ ]` items currently tracked.

## FIX-applied (2)

### A. Missing `_shared-memory/` subdirs — 9 dirs created with `.gitkeep`

Created and gitkept (RKOJ-ELENO authorship in placeholder):

- `_shared-memory/inbox/sinister-snap-emu/`
- `_shared-memory/inbox/sinister-tiktok-emu/`
- `_shared-memory/inbox/sinister-bumble-emu/`
- `_shared-memory/inbox/sinister-mind/`
- `_shared-memory/inbox/sinister-jokr/`
- `_shared-memory/inbox/sinister-letstext/`
- `_shared-memory/inbox/sinister-rka/`
- `_shared-memory/inbox/sinister-tg/`
- `_shared-memory/replays/` (referenced by new `/replay` slash command)

All 15 required `_shared-memory/` dirs now exist.

### B. `tools/_INDEX.md` — 4 missing rows added

Added rows for tool dirs that existed on disk but had no catalog entry:

- `sinister-jcode-shim` (shipped 2026-05-21, jcode shim CLI)
- `sinister-model` (shipped, model registry)
- `sinister-recovery-watchdog` (shipped, watchdog.ps1)
- `sinister-usage` (shipped, usage-metrics)

`tools/_INDEX.md` now has 100% coverage of `tools/sinister-*/`, `tools/sanctum-*/`, `tools/forge-*/`, `tools/memory-*/`.

## FIX-recommended-operator-action (4)

### 1. `knowledge/_INDEX.md` significantly under-indexed — 94 .md files on disk, only 4 distinct `.md` refs in index

The index uses prose summaries rather than per-file rows. Either:

(a) Convert `_INDEX.md` to a row-per-file catalog table (1 line per .md), or
(b) Leave as curated brain and accept the disk/index gap.

Operator decision required — per audit doctrine, do NOT auto-add rows. List the 40 most likely brain-worthy candidates (truncated): agent-identity-eve, agent-browser-bridge-pattern, apk-classifier-aup-doctrine, claude-sandbox-autonomy-grant, jcode-feature-matrix, jcode-feature-parity-targets, jcode-memory-graph-visualization-pattern, modular-fleet-cross-lane-integration-2026-05-21, magic-number-audit-taxonomy-2026-05-21, etc. (full list: 94 files in `_shared-memory/knowledge/`).

### 2. `session-templates/projects.json` missing 11 active lanes

Disk lanes not listed in `projects.json` (so launcher can't spawn dedicated windows):

`sinister-bumble-emu`, `sinister-cell-network`, `sinister-dashboard-skeleton`, `sinister-emulator-bundle`, `sinister-eve`, `sinister-jokr`, `sinister-letstext`, `sinister-rka`, `sinister-snap-emu`, `sinister-tg`, `sinister-tiktok-emu`.

NOTE: some are slug-aliased (e.g. `sinister-emulator` vs `sinister-emulator-bundle`, `tiktok-emulator-api` vs `sinister-tiktok-emu`). Operator to decide which lanes deserve their own launch entry vs which are sub-projects of an existing one. This is >5 edits + intent-driven so surfaced rather than auto-added.

### 3. 14 stale heartbeats (>24h)

Stalest first: `sanctum-console-build.beat` (60h), `phones/phone-2.json` (60h), `tiktok-emu.json` (41h), `phones/phone-1.json` (35h), `panel.beat` (35h), `sinister-bumble.json` (34h), `test.json` (33h), `rkoj.json` (32h), `sinister-emulator.json` (32h), `inventions.json` (32h), `tt-api.json` (31h), `snap-emu.json` (30h), `panel.json` (30h), `rkoj-build.beat` (30h).

13 heartbeats are fresh (<24h) including all currently-active lanes (apk, sanctum, tiktok-emulator-api, sinister-term, rkoj-runtime, rkoj-scheduler, kernel-apk, sinister-vault, sinister-forge, sinister-claw, sinister-term-coaudit, rkoj-workstation, letstext).

Recommendation: operator-side prune of slug-renamed/dead heartbeats (`test.json`, `rkoj-build.beat` likely subsumed by `rkoj-runtime.beat` + `rkoj-workstation.json`).

### 4. Resume-point JSON files have UTF-8 BOM

`resume-points/Sanctum/*.json` files were written with UTF-8 BOM (verified on latest file). Default `json.load(open(..., 'r', encoding='utf-8'))` raises `Unexpected UTF-8 BOM`. Either:

(a) Update `automations/resume-point-write.ps1` to emit BOM-less UTF-8 (`-Encoding utf8NoBOM` in PowerShell 7, or `[System.IO.File]::WriteAllText` with `UTF8Encoding($false)`).
(b) Update all readers to use `utf-8-sig`.

Recommendation: fix the writer (1 file, ~5 min) — readers shouldn't have to know.

## Top 5 open OPERATOR-ACTION-QUEUE items (snapshot)

1. Install Rust toolchain (rustup-init.exe) — unblocks jcode source-level fork into `projects/sinister-rkoj/`. ~1.5 GB rustup + ~5-7 GB MSVC.
2. Set `ANTHROPIC_API_KEY` env var (system) — RKOJ.exe v0.6.0 will switch to Anthropic SDK direct tool-use loop.
3. Desktop bat byte-parity drift — sibling sanctum audit found 3 Desktop bats out of sync with canonical tree.
4. Wayward Forge commit on sanctum branch — `66a5b3e feat(forge): PH18 niri columns + PH16 swarm pump...`.
5. Mixed-case resume-point dir — `_shared-memory/resume-points/Sinister Sanctum/` vs `Sanctum/`.

## Files modified by this audit

- `_shared-memory/inbox/sinister-{snap-emu,tiktok-emu,bumble-emu,mind,jokr,letstext,rka,tg}/.gitkeep` (created, 8 files)
- `_shared-memory/replays/.gitkeep` (created, 1 file)
- `tools/_INDEX.md` (4 rows appended for jcode-shim, model, recovery-watchdog, usage)
- `_shared-memory/plans/sanctum-readiness-2026-05-21/audit.md` (this file)

No source files touched. No deletes. No moves. Out-of-scope dirs (`tools/sinister-rkoj-qt/sinister_rkoj_qt/`, `projects/sinister-claw/source/app/`) untouched.

## Verdict

Sanctum is **READY** for jcode setup + the in-flight tool wave. Critical infrastructure (MCP, MANIFEST, watchdog registry, resume-points, CLAUDE.md persona bindings, launcher) all PASS. The 4 surfaced items are non-blocking but deserve operator attention before launch-day:

- BOM in resume-points (will trip naive readers)
- 11 missing launcher lanes (limits one-click spawn)
- 14 stale heartbeats (clutter; some likely dead)
- Knowledge index curation (curation choice, not bug)
