> **Author:** RKOJ-ELENO :: 2026-05-21

# RKOJ Changelog

All notable changes to the unified RKOJ project. Format roughly Keep-a-Changelog; versions are RKOJ.exe build versions, not component versions (each lane has its own).

## v1.6.13 — 2026-05-22

**Quick-wins polish.** While operator was testing v1.6.12:

- **AUTO-FOCUS INPUT ON SPAWN**: AgentsView.spawn_agent schedules a
  `QTimer.singleShot(0, card.input.setFocus)` so operator can type
  immediately after a card lands without clicking. (0ms delay so focus
  arrives after Qt finishes laying out the new card.)
- **TERMINAL MIN-HEIGHT 170 → 240**: agents were getting a tiny 170px
  scrolling window for long replies. 240px breathing room (card auto-
  grows beyond this when the operator drags the window taller).
- **MANIFEST.json** version 1.6.12 → 1.6.13.
- **VERSION**: `__init__.py __version__ = "1.6.13"`.

## v1.6.12 — 2026-05-22

**Cumulative cost telemetry + Ctrl+L = clear.** Stacks on top of v1.6.11
jcode-parity stream-json wiring. Operator: *"relaunch and test it and keep
working"* — v1.6.11 verified working end-to-end (stream-json parser test
PASS: 19 events parsed, 6/176 tokens, $0.07 / 4.4s footer captured).

- **CUMULATIVE COST PILL**: new mono pill in the card header strip
  (`$0.0042` style) that accumulates across all turns in the card.
  Updated in `_handle_stream_event` when the `result` event lands.
  Tooltip shows the full breakdown (in tok / out tok / total cost).
  Pill color is `PURPLE_PRIMARY` so it reads as Sanctum brand.
- **AgentCard `_total_cost_usd` / `_total_in_tokens` / `_total_out_tokens`**:
  3 new instance attrs; auto-accumulate from the per-turn `result` event.
- **/cost SLASH COMMAND**: prints the full breakdown into the terminal
  with avg/turn so operator can decide whether to keep going or /close
  the card to limit spend.
- **Ctrl+L = clear** keyboard shortcut. jcode-style keybind parity —
  operator can clear scrollback without typing /clear. Bound at the
  AgentCard level so it works when any input/terminal child has focus.
- **MANIFEST.json** version 1.6.11 → 1.6.12.
- **VERSION**: `__init__.py __version__ = "1.6.12"`.

## v1.6.11 — 2026-05-22

**Real jcode parity — stream-json token-by-token + thinking + tool_use + cost.**
Operator (verbatim, screenshot mid-iteration): *"i want it to work like
jcode and have everything i asked for"*. v1.6.10 fixed the visible `[stderr]
no stdin data received` warning but the chat was still all-text-at-once.
v1.6.11 wires the actual jcode-parity surfaces:

- **STREAM-JSON OUTPUT**: every turn now goes through
  `claude -p --output-format=stream-json --include-partial-messages
  --verbose --session-id|--resume <uuid>`. claude emits NDJSON events
  (one per line) — `_on_stdout` line-buffers them + parses each via
  `_handle_stream_event`.
- **TOKEN-BY-TOKEN STREAMING**: `content_block_delta + text_delta`
  events stream individual tokens into the terminal as they arrive.
  No more all-at-end dump.
- **THINKING DISPLAY**: `thinking_delta` events update the spinner text
  live with a 60-char preview of the current thought (`⠹ 💭 The
  operator wants me to…`). When claude opens a thinking block, the
  spinner prefix swaps from `EVE is thinking…` to `💭 thinking…`.
- **TOOL USE DISPLAY**: `content_block_start + tool_use` renders a jcode
  marker line `● <ToolName>(<input-preview-80-chars>)` then the tool's
  result appears as `✓ <result-preview-120-chars>` from the subsequent
  `user/tool_result` block.
- **PER-TURN FOOTER**: `result` event emits a footer line
  `▸ N in + M out tokens (cache_read=K) · $0.0042 · 3.1s · tools: Bash,Read`
  so operator sees token spend + cost + duration + tools used per turn.
- **SYSTEM EVENT SUPPRESSION**: hook_started / hook_response / init /
  status events are silently dropped from the terminal (too noisy).
- **MANIFEST.json** version 1.6.10 → 1.6.11.
- **VERSION**: `__init__.py __version__ = "1.6.11"`.

## v1.6.10 — 2026-05-22

**Agent-chat polish batch** — `/loop keep going make it better` cadence.
Stacks on top of v1.6.9's picker overhaul. Same EVE on Sanctum branch.

- **MULTI-LINE INPUT**: agent card input is now `_MultiLineInput`
  (QPlainTextEdit subclass) — Enter sends, Shift+Enter inserts a newline.
  Auto-resizes vertically up to a 5-line cap so a long prompt grows the
  input cleanly without blowing up the card; `/retry` switched to
  `setPlainText`. Operator can finally paste / compose multi-paragraph
  prompts without the prior single-line forced-truncation pain.
- **ANSI STRIP**: `_strip_ansi()` regex over every stdout chunk in
  `_on_stdout`. `claude -p` sometimes emits ANSI escape codes when its
  output piper thinks stdout is a TTY; previously those rendered as
  `\x1b[32m...\x1b[0m` garbage in the terminal. Now stripped to plain.
- **TURN COUNTER PILL**: new pill in the card header strip ("0 turns" /
  "1 turn" / "N turns") that bumps in `_on_finished` after each
  completed turn. Operator sees conversation length at a glance without
  having to `/history`.
- **EMPTY-STATE HERO**: `AgentsView` empty state was a single flat label
  "No agents yet — click Create Agent to spawn EVE." Replaced with a
  centered Panel-style hero: 28px purple title + 2-line subtitle (CTA
  → + Create Agent + Sessions sidebar) + a 3-tip row underneath
  (Per-agent session memory · Folder tabs · /help inside any card).
  Makes a fresh-launch RKOJ feel like a destination, not a blank canvas.
- **MANIFEST.json**: `version 1.6.9 → 1.6.10`.
- **VERSION**: `__init__.py __version__ = "1.6.10"`.
- **BUILD**: 44s, 71.68 MB onefile, M1 PASS. Smoke confirmed Qt window
  detected within 8s. EXE on Desktop.

## v1.6.9 — 2026-05-22

**Saved Sessions picker UX overhaul.** EVE on Sanctum, branch `agent/sinister-sanctum/cli-dispatcher-2026-05-21`. Operator brief was "get to work" continuing the rapid v1.6.x iteration after v1.6.8 shipped the inline-resume revert. The picker was lying — button labeled "Open in new window" but v1.6.8 routed everything inline. Plus the operator now has v1.6.7 autoclose saves piling up under `_shared-memory/resume-points/` with no in-UI cleanup. This ship fixes both.

- **TRUTHFUL WORDING**: "Open in new window" → "Resume inline". Subtitle rewritten ("double-click or pick + Resume inline. Del key (or button) removes a save."). Tooltips added on both action buttons clarifying behavior.
- **DELETE FROM PICKER**: "Delete selected" button (left of Cancel) + `Del` key shortcut. Reversible: file is renamed `<name>.json.deleted` on disk, not unlinked — operator can `ren` it back if it was a mistake. Picker self-rebuilds after each delete; Resume button disables when zero rows remain.
- **SAVE_REASON CHIP**: rows now show `[autoclose]` vs `[manual]` so operator can tell at a glance which saves came from the v1.6.7 window-close path vs explicit `/save`.
- **RELATIVE-TIME LABELS**: `_humanize_age()` helper turns ISO8601 `saved_at` into compact "12 min ago" / "3 hr ago" / "2 days ago" / `YYYY-MM-DD` for >30d. Way faster to scan than raw timestamps.
- **TIGHTER ROW LAYOUT**: row 1 = `<project> · <N> turn(s) · <ago> [reason]`; row 2 = `mode <claude> · uuid <abc12345…>` (8-char uuid prefix instead of 36 — full uuid moves to tooltip-territory if needed later).
- **EMPTY-STATE COPY**: tells operator about the v1.6.7 autoclose path so they know saves accumulate even without explicit `/save`.
- **DIALOG SIZE**: +20w/+20h (640×500) to give the richer rows room.
- **NO PUBLIC API CHANGE**: `result_data` schema additive (`save_reason` field added; existing keys unchanged). Callers in `app.py` (`_open_sessions_picker`) + `dialogs.py` (`NewAgentDialog._on_resume_clicked`) continue to work unmodified.
- **MANIFEST.json**: `version 1.6.0 → 1.6.9`, `updated 2026-05-21 → 2026-05-22`.
- **VERSION**: `__init__.py __version__ = "1.6.9"`.

## v1.6.0 — 2026-05-21

**Project-shape promotion + Panel 1:1 patches + Phase-1 memory bootstrap.** Operator (verbatim 2026-05-21, session start): *"i need you to make a porject in projects for rkoj and add everything there that we use for rkoj. ... I want the 1:1 exact ui as sinister panel. 1:1 nothing else everything the same and exact. ... When i click new agent it will be like we click the jcode exe and openeed a window."*

- **MOVED**: `tools/sinister-rkoj-qt/` → `projects/rkoj/source/` via single `git mv` (69 files, history preserved). RKOJ outgrew the `tools/` shape — multi-tab UI, plugin substrate, version-stamped EXE ships, operator-facing primary surface. See `_shared-memory/knowledge/rkoj-project-shape-promotion-2026-05-21.md` for the 7-step promotion pattern + 5 anti-patterns.
- **PATCHED (Panel 1:1)**: `SIDEBAR_WIDTH 220 → 240` (Panel canonical aside) · `QLabel#PageTitle font-size 24 → 26` (Panel `text-[26px]`) · `QPushButton#ChipTab min-height 26 → 30` + padding `4×14 → 6×16` (Panel `h-8 px-4`). Reference: `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/panel-1to1-spec.md`.
- **ADDED (Phase-1 memory⇄jcode integration)**: every spawned agent now writes a heartbeat to disk + seeds PROGRESS + creates inbox/resume dirs at spawn time. Per-card 30s `QTimer` keeps presence live. `QProcessEnvironment` propagates `SINISTER_AGENT_DISPLAY` / `_SLUG` / `_PANE_ID` / `_PROJECT_KEY` / `_HEARTBEAT_PATH` / `_PROGRESS_PATH` / `_RESUME_DIR` / `_INBOX_DIR` / `_AGENT_IDENTITY=EVE` / `_AUTHORSHIP=RKOJ-ELENO` so the spawned `claude -p` child knows its identity from env. AgentSession dataclass +6 fields. Brain entry: `_shared-memory/knowledge/rkoj-phase1-memory-bootstrap-2026-05-21.md`.
- **PATH REFS**: `automations/ship-rkoj-qt-to-desktop.ps1` + `automations/smoke-rkoj-qt.ps1` defaults repointed at `projects/rkoj/source/sinister_rkoj_qt/dist/`. PS-5.1 `Join-Path` paren fix. RKOJ.spec `_TOOL_ROOT` → `_PROJECT_ROOT` for clarity. `projects/rkoj/MANIFEST.json` `rkoj-qt` + `rkoj-qt-extensions` component paths updated. `tools/_INDEX.md` `sinister-rkoj-qt` row removed (it's a project now). `_shared-memory/knowledge/sinister-rkoj-extensibility-doctrine.md` plugin-path refs updated.
- **PLAN DOCS LANDED**: 5 files at `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/`: cleanup-proposal · forward-plan · panel-1to1-spec · memory-jcode-integration-audit · personal-folder-sinister-purge.
- **CROSS-AGENT BROADCAST**: `_shared-memory/cross-agent/2026-05-21T2330Z-sanctum-to-fleet-rkoj-relocation.md` (no-ACK).
- **SMOKE**: M1 PASS (`Sinister Sanctum — RKOJ.exe` Qt window detected <8s). M2 process-survival PASS (25s × 5 samples, RSS stable). M3-M10 require operator click-through.
- **EXE**: 75,160,157 byte onefile (71.68 MB, +4 KB vs v1.5.1 for memory bootstrap helpers) shipped to `C:\Users\Zonia\Desktop\RKOJ.exe` + `RKOJ.lnk` updated.
- **VERSION**: `__init__.py __version__ = "1.6.0"` · `MANIFEST.json version = "1.6.0"`.
- **COMMITS**: `caa66d4` (ship) + `40c478e` (brain).

### Roadmap captured (NOTED but NOT BUILT — operator addendum 2026-05-21)

Future workstation features documented in `_shared-memory/plans/Sanctum-deepclean-2026-05-21T2300Z/forward-plan.md` § C. Build sequence TBD by operator:

- **Devices ADB wiring** — connect all phones, scrcpy embed, per-device logcat
- **Self-hosted AnyDesk replacement** — RustDesk / Guacamole / MeshCentral candidate stack, Tailscale plane, Vault-backed auth
- **Kameleo-style anti-detect browser** — Playwright + Chromium + fingerprint randomization, profile manager in Vault
- **Own Android emulator system** — wrap Sinister Emulator Bundle as RKOJ emulator manager
- **Open extension registry** — every new tool plugs into `projects/rkoj/source/extensions/<slug>/manifest.json`

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
