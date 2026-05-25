<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 1
  half_life_days: 180
-->
# jcode Feature Matrix :: where every jcode capability lives in our Sinister stack

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Operator directives:**
> - *"i want all jcode features etc and i want our own terminal system. just like he has"* + *"all with our sinister braning"* (2026-05-21)
> - *"https://github.com/niri-wm/niri make sure we do what jcode does and use tools like this in our own way"* (2026-05-21T13:50Z)
> - *"https://github.com/1jehuang/mermaid-rs-renderer … take code you need intergrate with our things. make it all our theme branding etc"* (2026-05-21T13:55Z)
> **Origin:** jcode-0.12.3 (1jehuang, MIT). Read-only reference at `C:\Users\Zonia\Desktop\Github Research\jcode-0.12.3\`. Our re-implements are AGPL-3.0-or-later with attribution in NOTICES per canonical-20.
> **Goal:** ONE place mapping every jcode capability → where it lives in our stack → owner agent → status. Stops us from re-deciding "should I port X or delegate to Ruflo" every cold-start.

## Status legend

- ✅ **shipped** · 🚧 **in-flight** · 📋 **planned** · 🔄 **delegated**

## The matrix (30 rows — expanded 2026-05-21T14:10Z with sinister-usage shipped)

| # | jcode capability | Our home | Status | Owner | Notes |
|---|---|---|---|---|---|
| 1 | Multi-LLM provider routing | `automations/agent-host-routing.md` + Forge `:host` cmd | ✅ doc / 📋 UI | sanctum + forge | doc commit `bce833f` |
| 1b | `jcode login --provider X` (11 providers) | `tools/sinister-login/` v0.1.0 | ✅ shipped | sanctum | env-var-first wallet; 11 providers: claude/openai/gemini/copilot/azure/alibaba-coding-plan/fireworks/minimax/lmstudio/ollama/openai-compatible. Stdlib-only. Opt-in TCP probe. Refuses plaintext-on-disk by default. CLI: `sinister login providers/current/doctor/env/add/matrix`. Wired into `sinister-cli` umbrella. 21/21 unittests green. |
| 1c | `jcode usage` (token quota / billing + local-state + token estimator) | `tools/sinister-usage/` v0.1.0 | ✅ shipped (env-check + local-scan + estimator) | sanctum | 11-row endpoint registry mirroring sinister-login providers (4 expose public per-key APIs: openai/copilot/fireworks/openai-compatible; 7 console-only). Stdlib-only. ALSO ships ~/.claude/ local-state scanner (sessions / projects / bytes / today) + chars/4 token estimator with non-ASCII penalty. NO network in v0.1.0 (canonical-11); v0.2.0 adds `report` behind `--allow-network`. Soft cross-tool dep on sinister-login for `configured` flag. CLI: `sinister usage list/check/check-all/local/today/estimate/matrix/doctor`. 31/31 unittests green. |
| 2 | Multi-pane scrolling TUI | Forge `panes/agent_pane.py` (PH2-PH3) | ✅ scaffold | forge | Textual Log widget virtual-scroll |
| 3 | Forever-scroll buffer per agent | Forge `panes/agent_pane.py` | ✅ scaffold | forge | context-pruner.ps1 archives long-term |
| 4 | Ctrl+W new-agent picker | Forge `panes/picker.py` (PH3) | ✅ shipped | forge | ports `start-sinister-session.ps1` Q1-Q5 |
| 5 | Animated boot art | Forge `art.py` + `app.py` `BootScreen` | ✅ shipped | forge | Vault Boy rotating frames (4 frames, `VAULT_BOY_FRAME_0..3`) in `forge/art.py`; `forge/app.py` imports `BOOT_FRAMES` + `BOOT_DURATION_SEC` (line 41), defines `BootScreen(Static)` cycling frames (lines 122-133), mounts at compose (line 183), awaits `_boot.animate()` in `on_mount` before `_swap_to_main` (lines 189-190). 1.2s total animation. Re-audited 2026-05-23 by rkoj-lane (initial audit missed the BootScreen class). |
| 6 | Cascadia Code typography + jcode palette | Forge `theme.py` (PH11) | ✅ scaffold / 📋 polish | forge | purple `#7A3DD4` + dim cyan |
| 7 | Status bar + breadcrumbs | Forge `panes/status_bar.py` + Term shell PH7 | ✅ Forge stub / ✅ Term PH7 | forge + sinister-term | cwd / git branch / heartbeat pill |
| 8 | Semantic memory (HNSW + embeddings) | Ruflo `agentdb_*` (28 tools) | 🔄 delegated | sanctum (bridge) | DO NOT re-implement HNSW |
| 9 | Auto-recall during turn | `tools/forge-memory-bridge/recall()` → Ruflo `agentdb_pattern-search` | 🚧 v0.1.1 shipped | sanctum | TF-IDF default; MCP fast-path optional |
| 10 | Manual memory write | `tools/forge-memory-bridge/write()` + Forge `:memory write` + Term `/jcode-memory-write` | 🚧 bridge / 📋 UI | sanctum (bridge) + forge + sinister-term | Term `/mw` alias uses it |
| 11 | Background memory consolidation | `automations/memory-consolidate.ps1` → Ruflo `agentdb_consolidate` | 🚧 shipped + install-task | sanctum | nightly cron |
| 12 | Memory-graph visualization | `tools/memory-graph-render/` → mermaid → `mermaid-rs-renderer` → PNG + Forge `panes/mermaid_panel.py` + RKOJ `/api/diagrams` + Mind `/diagrams` web view | ✅ shipped | sanctum (render) + forge (Ctrl+D panel) + rkoj (REST API at :5077) + mind (web view at :5079) | PNGs at `inventions/memory-graphs/`. Forge embed: `Ctrl+D` opens MermaidPanel listing newest renders + opens any on click. RKOJ Workstation API: `GET /api/diagrams` lists cached renders; `GET /api/diagrams/<stem>` serves PNG/SVG/HTML/MMD bytes with proper Content-Type (path-traversal guarded). Mind web view: `projects/sinister-mind/source/mind/server.py` exposes the same shape on `:5079` + `static/diagrams.html` ships a liquid-glass tile grid with click-to-modal preview (img for PNG/SVG, iframe for HTML, fetch-text for .mmd), ext filter, 15s auto-refresh. Mind v0.3.0 shipped 2026-05-23 by rkoj-lane (commit `b199dae`). All four endpoints target the single source of truth at `_shared-memory/forge-memory/mermaid-renders/`. |
| 13 | Single-binary distribution | Forge + Term `pip install -e .` + entry-points | ✅ both | forge + sinister-term | pyproject.toml |
| 14 | Per-keypress latency <2ms | Term v0 Python+prompt_toolkit; Term v1 Rust port (deferred) | ✅ v0 / 📋 v1 | sinister-term | Rust port = 30-day proving period |
| 15 | Mermaid diagram panels (in-TUI) | Forge `panes/mermaid_panel.py` + `mermaid_render.py` + `/mermaid` slash | ✅ shipped | forge | Renderer wrapper `forge/mermaid_render.py` (166 LOC) wraps the prebuilt `mmdr` CLI (MIT) and caches PNG/SVG to `_shared-memory/forge-diagrams/<sha>.<ext>`. Slash surface `/mermaid file|render|open|backends` ships in `commands.py:2994-3120` (writes to `_shared-memory/forge-memory/mermaid-renders/`). In-TUI panel `forge/panes/mermaid_panel.py` (160 LOC) walks the renders dir, groups siblings by stem, lists newest-first with human-age formatting, opens any render in the OS image viewer on click. Toggled via `Ctrl+D` (binding `toggle_mermaid` in `app.py`). Refreshes every 15s. Shipped 2026-05-23 by rkoj-lane. |
| 16 | Swarm-mode (multi-agent) | Ruflo `hive-mind_*` + Sanctum `inbox/` + `cross-agent/` + **`sinister-swarm` v0.1.0 (pip-editable, AGPL-3.0)** | ✅ shipped (disk + CLI + Python API) | sanctum + all | `sinister-swarm whoami` + `sinister-swarm hive-status` — three orthogonal surfaces (Claude Agent tool sub-agents / sinister-bus MCP orchestration / sinister-swarm standalone). Verified 2026-05-23: `pip show sinister-swarm` → editable from `D:\Sinister Sanctum\tools\sinister-swarm` (Author: RKOJ-ELENO, AGPL-3.0); 187 pytest-green per `jcode-swarm-token-parity-audit-2026-05-23`. Cold-start hint shipped in launcher `Build-Phrase` per `bot-fleet-quick-reference` + `per-project-bot-adoption-playbook-2026-05-23`. |
| 17 | Telemetry (phones home) | **NOT PORTED** — data sovereignty | ✅ omitted | n/a | local only |
| 18 | Plugin / skill hot-reload | Forge `forge/skills.py` (manual `reload_shared` + watchdog `start_watcher`) | ✅ shipped | forge + sanctum | Manual: `SkillRegistry.reload_shared()` + `/skill reload` slash. Auto: `forge.skills.start_watcher()` schedules a `watchdog.observers.Observer` on `~/.sinister/skills/` + `D:/Sinister Sanctum/skills/`; reacts to `*.md` create/modify/delete/move events; lazy-imports `watchdog` so missing dep degrades to a one-shot log warning + no-op. Wired in `forge/app.py::on_mount` after `_swap_to_main`. Daemon thread, idempotent. Smoke-tested 2026-05-23 by rkoj-lane (6 skills loaded, observer started + stopped cleanly). |
| 19 | Per-agent identity / accent / project header | `automations/session-templates/agent-prefs.json` + Forge `app.py` | ✅ both | sanctum + forge | bold project name per pane |
| 20 | Mid-turn keybind: open new agent | Forge Ctrl+W / Term Ctrl+F (planned) | ✅ Forge / 📋 Term | forge + sinister-term | Term keybind opens Forge inline |
| 21 | RKOJ Workstation integration | Forge `panes/workstation_panel.py` F2-toggle to RKOJ :5077 | ✅ shipped | forge + rkoj | `keybinds.py` binds `F2 → toggle_rkoj`; `panes/workstation_panel.py` (170 LOC) auto-spawns the workstation daemon (`desktop_app.py` at `automations/window-manager/`) silently via `CREATE_NO_WINDOW` if `:5077` is idle, then opens the browser. Status bar shows "F2 RKOJ" pill. Audited 2026-05-23 by rkoj-lane. |
| 22 | Cold-start resume | CONTRACT 7 + `automations/resume-point-write.ps1` | ✅ shipped | sanctum + all | inaugural Sanctum resume-point this session |
| 23 | Tool-use boundary hooks | Forge PH13 `claude-hooks` integration | 📋 planned | forge | wraps `claude-hooks-2.4.0` |
| 24 | Skill discovery from external repos | Forge PH12 `Skill_Seekers` integration | 📋 planned | forge | wraps `Skill_Seekers-3.6.0` |
| 25 | Structured semantic grep | Forge PH14 `agentgrep` (operator-gated cargo install) | 📋 planned | forge | operator-gate |
| 26 | Browser-bridge (web-as-tool) | `_shared-memory/knowledge/agent-browser-bridge-pattern.md` + `_shared-memory/knowledge/browser-bridge-integration-shape-2026-05-23.md` (the empirical v0.9.9 audit) + `tools/sinister-browser/` v0.2.0 (Layer A probe + Layer B pythonic API + Forge Layer C slash + Layer D skill mirror) — Forge PH15 | ✅ Layers A+B+C+D shipped, live firefox-bridge verify operator-gated | sanctum (doc) + rkoj (probe + api + Forge slash + skill) | NOT clone-and-run. Layer A: `tools/sinister-browser/probe.py` does TCP-listen check + RFC 6455 §4.2.2 HTTP Upgrade handshake against `ws://127.0.0.1:8766`; exits 0=alive / 2=not-installed / 3=installed-but-unreachable. Layer B: `tools/sinister-browser/api.py` Browser class wraps 18 upstream actions (ping/list_tabs/new_session/set_active_tab/get_active_tab/navigate/get_content/get_interactables/screenshot/click/type/fill_form/scroll/wait_for/evaluate/reload/upload_file/drop_file) with stdlib-only RFC 6455 §5 client framing (masked text frames, ping/pong, close); 4 exception classes (BrowserError/BrowserConnectError/BrowserProtocolError/BrowserActionError); env-configurable defaults (SINISTER_BROWSER_HOST/PORT/TIMEOUT). Layer C: Forge `/browser` slash extended with bridge subcommands (`bridge|probe|ping|nav|content|click|type|screenshot|evaluate|reload|tabs|new|wait`) via `_browser_bridge_dispatch` in `forge/commands.py`; graceful degradation when `sinister-browser` isn't pip-installed. Layer D (NEW 2026-05-23 /loop iter 3): `skills/sinister-browser.md` SKILL manifest with frontmatter + 18-action table + 5 hard rules (no auto-XPI / no creds-in-evaluate / no hardcoded host:port / always-probe-first / pip-install-if-import-fails) + composes-with map. Operator-gated prereqs explicit: XPI install, HKCU NativeMessagingHosts registry write, optional FAB_AUTOLOGIN_REQUIRE_FINGERPRINT env. Tests: 35/35 green (4 Layer A + 31 Layer B against in-process fake WS bridges); Layer D adds no new test surface (skill body is documentation, not code). Live firefox-bridge verification still pending operator XPI install + native-host registry write. Shipped 2026-05-23 by rkoj-lane (Layers A-C in iter 6; Layer D in /loop iter 3). |
| 27 | **Scrollable-tiling multi-pane** (niri-wm pattern) | Forge `panes/niri_workspace.py` + `panes/columns.py` | ✅ shipped | forge | `forge/panes/niri_workspace.py` (513 LOC) implements the column-scrolling workspace; `forge/panes/columns.py` (218 LOC) is the column primitive. Mining UX-only (no Wayland code). Audited 2026-05-23 by rkoj-lane. |
| 28 | **Sinister-branded mermaid renderer (Rust)** | `tools/sinister-mermaid-render/` (TODO: fork 1jehuang/mermaid-rs-renderer) | 📋 planned | sanctum (fork) | Operator: rebrand Sinister purple boot art + AGPL-3.0 + RKOJ-ELENO; used by `memory-graph-render/` Stage 3 |
| 29 | **In-Qt EVE picker overlay + lib-shared launcher** | `tools/eve-picker/eve_picker_lib.py` + `automations/eve-launcher/eve.py` + `projects/rkoj/source/sinister_rkoj_qt/picker_overlay.py` | ✅ acceptance-tested+ (11/12 done-def PASS after P2.5 --onedir; operator hands-on row #12 only) | rkoj | Plan: `_shared-memory/plans/_archive/eve-into-rkoj-integration-2026-05-23T1330Z/`. P1 ship: stdlib-only `eve_picker_lib` (34/34 tests, 17.90 ms cold import). P2 ship: `eve.py` lift-shift 306→237 LOC + EVE.exe rebuild with banner-art ICO (8.5 MB) on `--onefile` — L7 baseline 583 ms median (PyInstaller bootloader floor). P2.5 ship: build switched to `--onedir`; output `dist\EVE\EVE.exe` + `_internal/` libs; cold-start drops to **60 ms median (PASS by 5× / ~10× improvement)**. Sinister Start.bat probe order extended for `--onedir` paths first (Desktop EVE\, build-output, LOCALAPPDATA EVE\), `--onefile` paths back-compat. P3 ship: `QPickerOverlay(QFrame)` Tool window, Ctrl+P trigger + sidebar EVE row + header EVE chip, dispatches via `_spawn_inline` so cards land inline (NOT new mintty); L8 overlay first-paint 8 ms (target <60 ms — PASS by 7.5× margin). P4 ship: R/K/S verb dialogs (RenameProject, AutonomyToggle, clear-focused-card). P5 ship: `/eve`, `/spawn`, `/swarm` slashes + autonomy_preset env-export (`SINISTER_EVE_SWARM`/`_LOOP`/`_LOOP_INTERVAL_S` from `agent-prefs.json.autonomy_preset.<key>`). P5.5 ship: SWARM/LOOP visual chips on AgentCard + Clone-as-EVE-pick `↻` button + arrow-up/down keyboard nav. All 10/10 plan §5 sick-sick features + 11/11 §1.2 verbs covered. 26/26 offscreen-Qt tests PASS (P3 8/8 + P4 3/3 + P5 9/9 + P5.5 6/6) in 5.33 s combined; zero regression. Shipped commits 2026-05-23 on `rkoj-iter7`: `f0694fc` (P1) → `2641ebc` (P2) → `eee6ef5` (P3) → `84ac675` (P4) → `67f441f` (P5) → `89875ee` (P5.5) → `3e7dc93` (P6 gate) → `7930492` (P2.5 --onedir L7 PASS). |

## Audit corrections

- **2026-05-24T16:39Z (jcode-parity-probe v0.3, test-modes-verify lane):** Row 29 cites `projects/rkoj/source/sinister_rkoj_qt/picker_overlay.py` as shipped, but the file does NOT exist on the current HEAD + grep for class `QPickerOverlay` returns 0 matches under `projects/rkoj/source/sinister_rkoj_qt/`.
- **2026-05-24T16:42Z root-cause (test-modes-verify lane):** `git log --all -- "**/picker_overlay.py"` finds the file was shipped on branch `rkoj-iter7` (commits `eee6ef5` P3 + `89875ee` P5.5), but **rkoj-iter7 has never been merged into main**. This is a pending-merge state, not a stale matrix claim. Matrix row 29 is accurate ABOUT THE BRANCH; the probe correctly flags the missing-on-main state. Operator-action: `rkoj-iter7 → main` merge is already a known queue item per CLAUDE.md "current operator-actionable rows". Once merged, probe R29 will flip to PASS automatically.

## Composes-with map

`forever-expanding-modular-architecture-doctrine.md` (meta) → `sibling-active-launch-coordination-pattern.md` (runtime) → `jcode-feature-matrix.md` (THIS — capability map) → individual implementation tools (`forge-memory-bridge/` + `memory-graph-render/` + `memory-consolidate.ps1` + `agent-host-routing.md` + `start-sinister-session.ps1` + Forge source tree + Term source tree + Mind source tree + Ruflo MCP)

## What we deliberately did NOT port

- jcode telemetry (data sovereignty)
- Single-EXE Rust binary (Python preferred for velocity; Rust deferred to Forge Q1 + Term Track B)
- MIT license (we use AGPL-3.0-or-later per canonical-20)
- External package registry (skills come from disk + Ruflo, not marketplace)

## Update protocol

Edit-by-any-agent. When you ship a feature: flip Status column, update Owner if lane shifted, add commit hash + date to Notes.

## Cross-references

- `projects/sinister-forge/source/PLAN.md` — Forge PH1-PH15
- `_shared-memory/plans/sinister-forge-2026-05-21/jcode-memory-feature.md` — original jcode-memory mining
- `_shared-memory/plans/sinister-forge-2026-05-21/sanctum-audit-findings.md` — Sanctum Audit Agent TOP-5
- `_shared-memory/knowledge/sibling-active-launch-coordination-pattern.md`
- `_shared-memory/knowledge/jcode-memory-graph-visualization-pattern.md`
- `_shared-memory/knowledge/agent-browser-bridge-pattern.md`
- `_shared-memory/knowledge/sinister-freeze-project-doctrine.md`
- `_shared-memory/knowledge/forever-expanding-modular-architecture-doctrine.md`
- `automations/agent-host-routing.md`
- `automations/session-contracts.md`
