> **Author:** RKOJ-ELENO :: 2026-05-21

# RKOJ Changelog

All notable changes to the unified RKOJ project. Format roughly Keep-a-Changelog; versions are RKOJ.exe build versions, not component versions (each lane has its own).

## v1.5.1 — 2026-05-21

**Strip pivot — 2 tabs + Panel-exact + niri-scroll.** Operator (verbatim 2026-05-21): *"remove ALL THIS FUCKING SHIT AND LISTEN TO ME very carefully. i want two fucking tabs. agents and devices ... exact sinister panel look ... niri infinite scroll ... glow when they need our input ... X button works"*. The v1.5.0 PyQt6 ship landed but the surface was bloated — Excel ribbon, KPI tiles, project sub-tab strip, workstation tab — none of which the operator wanted. v1.5.1 strips the chrome back to operator-canonical: 2 chip tabs, Panel-exact sidebar, Sheets-style header menu strip, niri-scroll agent grid, folder-tab row, working X.

- **REMOVED**:
  - Excel ribbon (5 groups VIEW/SPAWN/AGENT/AUTOMATE/MAINTAIN — all deleted)
  - 4 KPI tiles (deleted)
  - Workstation tab + sub-pane (operator dropped — Console launches elsewhere)
  - Project sub-tab strip (replaced by folder-tab row in the Agents tab)
  - STATUS panel bottom-left of sidebar
- **KEPT + REWORKED**:
  - Sidebar — now Panel-exact: 3 sections (DAILY / INSIGHTS / MANAGE), mascot block, no STATUS panel
  - Header — now 2 rows: Sheets-style menu strip (File / Edit / View / Insert / ...) on row 1; chip tabs + actions + CreateAgent on row 2
  - Agents tab — now NiriScrollGrid (infinite horizontal/vertical scroll of agent cells, per-project grouping)
  - `persona.py` — EVE binding unchanged
- **NEW**:
  - Folder-tab row in the Agents tab (All chip + per-project chips for filtering the niri-scroll grid)
  - Glow-on-pending animation (cell pulses when the EVE inside needs operator input)
  - Sheets-style menu strip with placeholder QMenus (File / Edit / View / Insert / Format / Data / Tools / Extensions / Help)
  - Working X button + `closeEvent` that terminates all QProcess children before exit (no orphaned `claude` processes)
- Reference: `_shared-memory/knowledge/rkoj-ui-exact-spec-2026-05-21.md` (operator-canonical UI spec doctrine).

## v1.5.0 — 2026-05-21

**Pivot to native PyQt6 desktop app.** Operator (verbatim): *"i dont want a fucking web ui ... popup the ui on the fucking desktop"* + *"function like jcode but be ours and we can foreever expand"*. The pywebview path (v1.4.x) was rejected — HTML/CSS surface read as "web ui". RKOJ.exe v1.5.0 is now a frameless rounded PyQt6 window with Sinister Panel layout + Excel-style ribbon + jcode-form terminals in the Agents tab (QPlainTextEdit + QProcess wrapping `claude --dangerously-skip-permissions -p`).

- Source: new `tools/sinister-rkoj-qt/` (sub-agent shipped this turn) — `sinister_rkoj_qt/{app, sidebar, header, ribbon, kpis, agents_tab, phones_tab, workstation_tab, theme, state, persona}.py`.
- Layout matches `snap.sinijkr.com` exactly: 240px sidebar (mascot + 4 sections + status) + 96px header (chip tabs + actions + clock) + Excel ribbon (5 groups: VIEW/SPAWN/AGENT/AUTOMATE/MAINTAIN) + 4 KPI tiles + project sub-tab strip + main pane.
- Agents tab: niri-style vertical scroll of jcode-form terminals. EVE persona injected verbatim in each opening prompt (RKOJ-ELENO authorship, full Sinister tool list, branch convention).
- Phones tab: 4-stat strip + filter chips + 2-col body (device rail + identity/heartbeat/RKA/kill-switch/ADB shell/scrcpy launch) + live logcat tail.
- Workstation tab: action card grid (vault / brain / watchdog / backups / mcp / explorer).
- Slash-command intercept routes `/help /clear /save /resume /create /skill /mcp /watchdog` to existing forge.commands API; everything else to claude subprocess.
- Extensibility doctrine landed at `_shared-memory/knowledge/sinister-rkoj-extensibility-doctrine.md` — manifest-driven plugin system so we add features forever without touching chrome/panes.
- 5 new jcode-gap slash commands (/pair /ambient /permissions /replay /browser) added to forge.commands.py.
- Build: `pyinstaller --clean --noconfirm tools/sinister-rkoj-qt/RKOJ.spec`. Output replaces `Desktop/RKOJ-Workstation/` so the existing `RKOJ.lnk` shortcut picks it up.

## v1.4.1 — 2026-05-21

**MCP Phase 2A — `/mcp` subcommand wire-up.** Builds on v1.4.0's bundled `mcp` Python SDK. `/mcp` now supports 5 subcommands: `list` (default, shows server name + command + args), `show <name>` (pretty-print JSON config), `status` (SDK + config + server-count health probe), `tools <name>` (placeholder, documents Phase 2B follow-up + import-from-bundled-SDK example), `call <server> <tool> [json]` (placeholder, documents the async-Textual-loop integration needed).

- Source: `projects/sinister-forge/source/forge/commands.py::_cmd_mcp` rewritten.
- Phase 2B (live stdio tool calls) still queued — needs an async-safe wrapper since Textual's event loop is already running.

## v1.4.0 — 2026-05-21

**Integrated bundle ship — Term + MCP SDK + Skills + workstation auto-launch + vault auto-spawn.** Operator escalation: *"we are working on rkoj exe not fucking bat ... combingin all thigns we have been working on rkoj workstation, jcode, all the skills we ahve made, mcp, our new console system"*. The v1.3.0 ship was UI-complete but the EXE bundle was thin (forge + 7 sinister-* tools only). v1.4.0 fattens the bundle.

- **Sinister Term bundled inside the EXE** — `term` package added to `RKOJ.spec` via `collect_submodules("term")` + `collect_data_files("term")`. No more separate `sterm` process; the terminal lives inside RKOJ.
- **MCP Python SDK bundled** — `mcp` package collected (Phase 1). Phase 2 (forge.bridge wires to `~/.claude/.mcp.json` for eve/sinister-panel/sinister-snap/sinister-tiktok/vault/ruflo) is a follow-up turn.
- **Skills/*.md content shipped inside the binary** — `datas.append((skills_root, "skills"))` puts the 6 candidate skills (sk-swarm-coord, sk-vector-memory, sk-federation, sk-observability, sk-aidefence, dashboard-skeleton) inside the EXE as a SkillRegistry fallback when `~/.sinister/skills/` is empty.
- **Workstation console auto-launch from EXE** — `workstation_panel.py` path typo fixed (`D:/Sinister/Sanctum/...` → `D:/Sinister Sanctum/...`); Open-Browser button now `subprocess.Popen` spawns `desktop_app.py` detached when `:5077` is idle (one click instead of two); Launch button prefers in-tree daemon over dist/RKOJ.exe.
- **Vault daemon auto-spawn at EXE startup** — `RKOJ-entry.py` new `_ensure_background_services(sanctum_root)` runs before TUI mount; if `:5078` idle, `tools/sinister-vault/daemon.py` spawns detached.
- **Binary size**: 50.2 MB (+287 KB vs v1.3.0's 50.0 MB) — minimal cost for the integration.
- Reference commit: `e34ac7a feat(rkoj): v1.4.0 EXE integration scope — term + skills + MCP + workstation auto-launch + vault auto-spawn` + ship commit (this commit).

## v1.3.0 — 2026-05-21

**Sinister Panel layout — mascot + 2 tabs + per-project sub-tabs.** Operator parity ship of the Sinister Panel chrome onto the Forge sidebar.

- Sinister Panel-style sidebar — mascot block + two top-level tabs (Agents / Phones) — `projects/sinister-forge/source/forge/panes/sidebar.py`
- `AgentsDashboard` pane with per-project sub-tabs — one sub-tab per active project — `projects/sinister-forge/source/forge/panes/agents_dashboard.py`
- Workstation tab in sidebar — surfaces the Console window manager inside the TUI — `projects/sinister-forge/source/forge/panes/workstation_panel.py`
- Auto-spawn Sanctum agent on first launch — render-safe tab labels (no crash on empty/non-ascii)
- Reference commits: `83393a5` (sidebar + AgentsDashboard) · `c46e941` (auto-spawn + workstation tab) · `9f4529b` (ship marker)

## v1.2.0 — 2026-05-21

**Agents tab = single console.** Niri strip auto-hides when only one workspace is active — cleaner default for the common case.

- `NiriWorkspaceGrid` enters single-workspace mode by default; strip surfaces only at count ≥ 2 — `projects/sinister-forge/source/forge/panes/niri_workspace.py`
- Agents tab compose() simplified — single-console path skips the strip entirely
- Verified all 15 jcode-form features work in single-pane mode (commit `0224d5b`)
- Reference commits: `972bd2d` (NiriWorkspaceGrid single-workspace default) · `0224d5b` (jcode-form 15/15 verified) · `80d6df2` (ship marker)

## v1.1.0 — 2026-05-21

**Sinister Panel chrome, Niri workspace grid, 6 new slash impls, D-drive consolidation.** Operator ship of fleet-wide UI doctrine + ergonomic upgrades + workstation reorg.

- Sinister Panel chrome theme applied globally — 7497-char `THEME_CSS` block in `projects/sinister-forge/source/forge/theme.py`, picked up by every Forge pane on cold-start
- `NiriWorkspaceGrid` in the Agents tab — scrollable workspace columns with `Ctrl+Left/Right` (column nav), `Ctrl+Shift+Left/Right` (column reorder), `Ctrl+1..9` (jump-to-column); lives in `projects/sinister-forge/source/forge/panes/niri_workspace.py`
- `/mermaid` command — wires `memory-graph-render` into the TUI; renders brain-graph or session-graph as an ASCII mermaid block inside the active pane
- 5 more real slash impls: `/todo` `/focus` `/diff` `/search` `/export` (replacing v0.9.0 stubs; no `_cmd_*` lane-discipline violations)
- D-drive reorg Phase 1+2+3 — `D:\Backups\*` consolidated; `D:\sinister-vault` and `D:\Sinister\Sinister Skills` moved into Sanctum with backward-compat junctions; 5 clean projects relocated to `projects/sinister-*`
- Reference commits: `f722550` `d7e38c0` and the Phase 3 commit (GG2 agent, lands separately)

## v1.0.0 — 2026-05-21

**Forge TUI is now the default `RKOJ.exe` entry mode.** Operator directive (image 27 escalation): one project, one EXE, jcode-form base expanded with every skill / bot / tool the fleet has built.

- Forge TUI launches by default on `RKOJ.exe` (no flag needed)
- Sidebar visible on launch — Agents tab + ADB tab populated immediately
- `--shell` flag falls back to the v0.x `>` prompt (parachute mode)
- `RKOJ.exe info` prints manifest from `projects/rkoj/MANIFEST.json`
- Umbrella `projects/rkoj/` created in Sanctum — README + MANIFEST + INTEGRATION + this CHANGELOG
- EVE persona binding across heartbeats, commit trailers, pane headers
- Authorship migrated to RKOJ-ELENO on all new files

## v0.9.0 — 2026-05-21 (pre-umbrella)

Real implementations replacing earlier stubs.

- `/clear` — clears pane scrollback + resets context window
- `/compact` — invokes Anthropic compaction; preserves system prompt + last N turns
- `/context` — prints active context window stats (tokens used / budget / cache hit rate)
- `/save NAME` — persists conversation to `~/.sinister/sessions/NAME.jsonl`
- `/unsave NAME` — deletes a saved session
- `/rename OLD NEW` — renames a saved session
- `/rewind N` — rolls pane back N turns, refreshes prompt from journal
- jcode sidecar shim (`tools/sinister-jcode-shim/`) — translates jcode-style flags to SDK args

## v0.8.0

- `/help` overlay form — discoverable command list inside the TUI
- `/start` picker — choose project (sanctum / forge / freeze / ...) at boot
- 40+ jcode command stubs landed (69 total command surface)

## v0.7.0

- `anthropic_direct.py` — direct SDK path
  - parallel tool use
  - prompt caching (ephemeral + persistent breakpoints)
  - extended-thinking panel (delta-stream)
  - budget guard (token-cost ceilings per pane)
  - JSONL journaling for every request/response

## v0.6.0

- Anthropic SDK direct path added as alternative to `claude` subprocess
- Multi-step tool reasoning loop with retry + backoff

## v0.5.0

- jcode-shell rewrite
- `/resume` reconstructs context from the most recent JSONL journal
- forge-memory-bridge integration (BM25 + TF-IDF)
- `claude -p` invocation pattern for one-shot prompts inside scripts

## Conventions

- Versions before v1.0.0 lived in the sinister-forge lane CHANGELOG; this file consolidates them at the umbrella level going forward.
- Each component (forge, term, workstation, tools/*) keeps its own per-lane CHANGELOG; this file only tracks the integrated `RKOJ.exe` build.
- "EVE persona" + "RKOJ-ELENO authorship" are operator-canonical 2026-05-21 (see `_shared-memory/knowledge/agent-identity-eve.md`).
