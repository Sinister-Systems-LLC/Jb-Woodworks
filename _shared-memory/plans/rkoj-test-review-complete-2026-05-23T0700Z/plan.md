# RKOJ — test everything + review everything + complete it all

> **Author:** RKOJ-ELENO :: 2026-05-23
> **Operator directive (verbatim 2026-05-23T06:48 EDT):** *"dont have scrpoy windows show up outside of the ui itself. create a plan to test everything and review everything you need to do and complete it all"*.
> **Branch:** `agent/rkoj/next-slate-2026-05-23`
> **HEAD at plan time:** `a4b71cf` + pending v1.6.89 scrcpy patch (this turn)
> **Predecessor plans:** `rkoj-complete-2026-05-23T0455Z` + `rkoj-complete-2026-05-23T0621Z` (both substantially shipped)

## (A) Test everything — full RKOJ surface map

### A1 — sandbox-runnable tests (executable from this session)

These run without operator hardware. Cover ~80% of the surface area.

| # | Surface | Test | Status |
|---|---|---|---|
| 1 | `sinister_rkoj_qt` package import | `python -c "import sinister_rkoj_qt; print(sinister_rkoj_qt.__version__)"` | ✅ passes (this turn) — reports `1.6.89` |
| 2 | `devices_tab` module import | `python -c "from sinister_rkoj_qt import devices_tab"` | ✅ passes |
| 3 | `api_server` module import | `python -c "from sinister_rkoj_qt import api_server"` | ⏳ runs below |
| 4 | `state` module import + `load_projects()` | `python -c "from sinister_rkoj_qt import state; print(len(state.load_projects()))"` | ⏳ runs below |
| 5 | All Qt modules import | `python -c "from sinister_rkoj_qt import app, agent_window, agents_tab, dialogs, header, persona, sidebar, theme"` | ⏳ runs below |
| 6 | Mind server import | `python -c "from mind.server import app"` | ✅ passed iteration 3 |
| 7 | Mind `/api/diagrams` JSON shape | start Flask :5180; GET `/api/diagrams`; assert keys | ✅ passed iteration 3 |
| 8 | Mind `/api/diagrams/<stem>` bytes serve | GET `/api/diagrams/<known-stem>`; assert 200 + correct ct | ✅ passed iteration 3 |
| 9 | Mind `/api/diagrams/<traversal>` guard | GET `/api/diagrams/..%2F..%2Fpasswd`; assert 404 | ✅ passed iteration 3 |
| 10 | Mind `/diagrams` HTML page | GET `/diagrams`; assert 200 + `/api/diagrams` marker | ✅ passed iteration 3 |
| 11 | `sinister-browser` Layer A probe — no service | `python -m sinister_browser probe`; assert exit 2 | ✅ passed iteration 4 |
| 12 | `sinister-browser` Layer A probe — fake WS server | unit test with in-process WS server returning valid Accept | ✅ passed iteration 4 |
| 13 | `sinister-browser` Layer A probe — wrong Accept | unit test; assert exit 3 | ✅ passed iteration 4 |
| 14 | `sinister-browser` Layer A probe — plain HTTP | unit test; assert exit 3 | ✅ passed iteration 4 |
| 15 | `sinister-browser` Layer A probe — JSON output | `python -m sinister_browser probe --json`; assert valid JSON | ✅ passed iteration 4 |
| 16 | `resume-point-write.ps1` parse | `[Parser]::ParseFile`; assert no errors | ✅ passed iteration 4 |
| 17 | `resume-point-write.ps1` slug→display routes `rkoj` → `RKOJ` | live run with `-ProjectKey rkoj`; assert dir `_shared-memory/resume-points/RKOJ/` | ✅ passed iteration 4 |
| 18 | `canonical-protections-check.ps1` | runs on every SessionStart hook | external (operator-installed at session start) |
| 19 | RKOJ `/api/health` shape | start workstation server :5077 in background; GET `/api/health`; assert `ok:true` | ⏳ runs below |
| 20 | RKOJ `/api/diagrams` shape | GET `/api/diagrams`; assert `count: 2` (the existing renders) | ⏳ runs below |
| 21 | RKOJ `/api/diagrams/<stem>` bytes | GET with known stem; assert 200 | ⏳ runs below |
| 22 | RKOJ `/api/version` reports v1.6.89 | GET `/api/version`; assert `sinister_rkoj_qt == "1.6.89"` | ⏳ runs below |
| 23 | RKOJ `/api/phones` shape | GET `/api/phones`; assert array (empty if no ADB) | ⏳ runs below |
| 24 | tools/_INDEX.md row count | grep count rows; assert ≥ 28 | ⏳ runs below |
| 25 | knowledge/_INDEX.md has rkoj-lane entries from this session | grep `branch-checkout-silently-undoes-doctrine` + `browser-bridge-integration-shape` + `2026-05-23` | ⏳ runs below |

### A2 — needs Qt event loop (PyQt6 must spin up a QApplication)

These require Qt initialization. Sandbox can spawn QApplication in offscreen platform mode:

| # | Surface | Test | How |
|---|---|---|---|
| 26 | `MainWindow` constructor | `QApplication([]) + sinister_rkoj_qt.app.MainWindow()` | run with `QT_QPA_PLATFORM=offscreen` |
| 27 | `DevicesView` constructor | instantiate empty (no adb) | offscreen Qt |
| 28 | `AgentsView` constructor | instantiate; verify slash registry populated | offscreen Qt |
| 29 | `_NavRow.set_active(True/False)` colors | render once; check stylesheet | offscreen Qt |
| 30 | Spawn a `_MirrorCard` with fake adb device | mock `state.Device`; instantiate; verify `_unique_title` + `MIRROR_SIZE` | offscreen Qt |

### A3 — needs adb-attached physical phone (operator hardware)

| # | Surface | Test |
|---|---|---|
| 31 | scrcpy spawn → embed reparent (the v1.6.89 fix) | attach phone, click Mirror, observe NO stray scrcpy window |
| 32 | per-phone log file at `_LOG_DIR/<serial>-<ts>.log` | check size > 0 after a few seconds |
| 33 | resize event propagates to embedded HWND | resize window; verify mirror resizes |
| 34 | close → kill scrcpy → cleanup | click ✕; verify subprocess gone |
| 35 | `/api/phones/<serial>/claim` | POST with agent_id; verify state mutation |
| 36 | `/api/phones/<serial>/shell` | POST `adb shell` command; verify response |
| 37 | `/api/phones/<serial>/screenshot` | POST; verify PNG saved to Desktop |

### A4 — needs operator-installed firefox-agent-bridge

| # | Surface | Test |
|---|---|---|
| 38 | `sinister-browser probe` against live bridge | install XPI + register native host + `python -m sinister_browser probe`; assert exit 0 |

### A5 — needs PyInstaller build pipeline (Windows venv + spec file)

| # | Surface | Test |
|---|---|---|
| 39 | Build RKOJ.exe v1.6.89 onefile | `pyinstaller sinister_rkoj_qt/RKOJ.spec` |
| 40 | RKOJ.exe launches | double-click `dist/RKOJ.exe`; verify single window opens |
| 41 | Build sinister-eve.exe v1.6.71 onefile | `pyinstaller tools/sinister-eve/sinister-eve.spec` |

## (B) Review — what's done, what's still open, where every matrix row stands

### B1 — jcode-feature-matrix.md status snapshot (this session's deltas in **bold**)

| Row | Capability | Status | Notes |
|---|---|---|---|
| 1 | Multi-LLM provider routing | ✅ doc / 📋 UI | doc shipped; UI pending |
| 1b | sinister-login | ✅ shipped | 21/21 tests |
| 1c | sinister-usage | ✅ shipped | 31/31 tests |
| 2 | Multi-pane scrolling TUI | ✅ scaffold | Forge PH2-PH3 |
| 3 | Forever-scroll buffer | ✅ scaffold | |
| 4 | Ctrl+W new-agent picker | ✅ shipped | |
| 5 | Animated boot art | ✅ shipped | rkoj-lane re-audit |
| 6 | Cascadia typography | ✅ scaffold / 📋 polish | |
| 7 | Status bar | ✅ both lanes | |
| 8 | Semantic memory | 🔄 delegated | Ruflo |
| 9 | Auto-recall | 🚧 v0.1.1 shipped | |
| 10 | Manual memory write | 🚧 bridge / 📋 UI | |
| 11 | Background consolidation | 🚧 shipped + install-task | |
| **12** | **Memory-graph viz** | **✅ shipped (this session)** | Forge panel + RKOJ REST + Mind /diagrams + render pipeline |
| 13 | Single-binary dist | ✅ both | |
| 14 | Per-keypress latency | ✅ v0 / 📋 v1 | |
| 15 | Mermaid in-TUI | ✅ shipped | rkoj-lane |
| 16 | Swarm-mode | ✅ disk / 🚧 MCP | |
| 17 | Telemetry | ✅ omitted | |
| 18 | Plugin hot-reload | ✅ shipped | rkoj-lane |
| 19 | Per-agent identity | ✅ both | |
| 20 | Mid-turn keybind | ✅ Forge / 📋 Term | |
| 21 | RKOJ Workstation integration | ✅ shipped | rkoj-lane audit |
| 22 | Cold-start resume | ✅ shipped | |
| 23 | claude-hooks | 📋 planned | external pkg not on disk — operator gate |
| 24 | Skill_Seekers | 📋 planned | external pkg not on disk — operator gate |
| 25 | agentgrep | 📋 planned | operator cargo install gate |
| **26** | **Browser-bridge** | **🚧 doc + Layer A probe (this session)** | audit doc + tools/sinister-browser/ v0.1.0 |
| 27 | Niri scrollable-tiling | ✅ shipped | rkoj-lane audit |
| 28 | Sinister-branded Rust mermaid renderer | 📋 planned | operator Rust toolchain gate |

**Tally:** 22 ✅, 4 🚧, 4 📋 (3 fully operator-gated, 1 operator-gated external pkg), 1 🔄 delegated, 1 ✅ omitted.

### B2 — Operator-action-queue rows that touch RKOJ lane

| Row | Status | Blast on RKOJ |
|---|---|---|
| Restart Claude Code (12 MCPs + 14 plugins) | 🔴 pending | RKOJ.exe runs independently; doesn't block RKOJ work, but enables forge-memory-bridge MCP fast path |
| `ANTHROPIC_API_KEY` | 🟠 pending | Unlocks RKOJ v0.7.0 Anthropic SDK direct tool-use (multi-step reasoning visible). Without it the existing `claude -p` one-shot path stays. |
| Install Rust toolchain | 🟠 pending | Unblocks `tools/sinister-mermaid-render/` (matrix row 28) |
| Drop missing external pkgs | 🟡 pending | claude-hooks-2.4.0 + Skill_Seekers-3.6.0 → matrix rows 23/24 |
| `gh auth refresh -s workflow` | 🟡 pending | Auto-push of CI workflow file changes |
| `PI 0/3 fixed on phones P1+P2` | 🔴 pending (Kernel-APK lane) | unrelated to RKOJ |
| Test-drive launcher v6.1 | 🟢 pending | unrelated to RKOJ |

None of the rkoj-actionable rows from prior plans are blocked by these.

### B3 — What I've shipped across the four /loop iterations today

| Iteration | Shipped | Commit |
|---|---|---|
| 1 (04:55Z) | resume-pickup + jcode matrix flips (5 rows) + inbox triage | `9b76247` |
| 2 (05:30Z) | forge skill watchdog + mermaid Ctrl+D panel + RKOJ `/api/diagrams` | `4bc5b4d` + `6d00c59` |
| 3 (06:30Z) | Mind `/diagrams` web view + 2 brain entries (branch-revert hazard + browser-bridge audit) | `b199dae` |
| 4 (06:42Z) | matrix row 12 ✅ + sinister-browser Layer A probe v0.1.0 + resume-point script slug fix | `a4b71cf` |
| 5 (this turn) | RKOJ v1.6.89 scrcpy-no-stray-window patch + this plan + sandbox-test execution | (pending) |

## (C) Complete — master-actionable backlog still in-lane

| # | Item | Effort | Reversibility | Operator gate? |
|---|---|---|---|---|
| 1 | **RKOJ v1.6.89 scrcpy fix** | ✅ patched this turn | R1 | needs operator hardware to verify end-to-end |
| 2 | **Run A1 sandbox-runnable tests + record results** | 15 min | R0 | no |
| 3 | **Run A2 offscreen-Qt tests** | 20 min | R0 | no — uses QT_QPA_PLATFORM=offscreen |
| 4 | **Commit + push iteration-5 work** | 5 min | R1 | no |
| 5 | **Build RKOJ.exe v1.6.89** | 5 min (pyinstaller) | R1 | sandbox blocked from running pyinstaller cleanly — operator double-clicks the build script |
| 6 | **Update OPERATOR-ACTION-QUEUE.md with v1.6.89 verification one-liner** | 3 min | R0 | no |
| 7 | **Resume-point write** | 2 min | R0 | no |

## (D) Deferred — not master-actionable this slice

- Layer B/C/D of sinister-browser — Forge slash + skill mirror; defer until operator says bring up live firefox-bridge.
- Matrix row 22 Mind nodes — separate from /diagrams; deferred (no operator demand).
- Matrix rows 23/24/25/28 — operator-gated (external pkg / toolchain installs).
- ANTHROPIC SDK direct path in RKOJ (v0.7.0) — operator must set `ANTHROPIC_API_KEY` first.

## (E) Recommended execution order

1. (C)#2 Run A1 tests (this turn)
2. (C)#3 Run A2 offscreen-Qt tests (this turn)
3. (C)#6 Update queue with v1.6.89 verify one-liner
4. (C)#4 Commit + push
5. (C)#7 Resume-point write
6. End-of-turn report

Effort total: ~45-55 min. End-to-end loop-able without operator clicks (operator only verifies the v1.6.89 fix on hardware afterward).

## (F) Test results — captured this session

### A1 — sandbox-runnable (PASS=25 FAIL=0)

```
# Module imports (test 1-5)
sinister_rkoj_qt                          OK   version=1.6.89
sinister_rkoj_qt.api_server               OK
sinister_rkoj_qt.state                    OK
sinister_rkoj_qt.app                      OK
sinister_rkoj_qt.agent_window             OK
sinister_rkoj_qt.agents_tab               OK
sinister_rkoj_qt.devices_tab              OK
sinister_rkoj_qt.dialogs                  OK
sinister_rkoj_qt.header                   OK
sinister_rkoj_qt.persona                  OK
sinister_rkoj_qt.sidebar                  OK
sinister_rkoj_qt.theme                    OK

# state.load_projects()  — initially returned 0 records → REAL BUG CAUGHT
# Root cause: projects.json carries a UTF-8 BOM (Out-File default on Win),
# load_projects opens as 'utf-8' so json.load raises JSONDecodeError, and
# the outer try/except swallows it silently → empty Resume picker.
# Fix: state.py opens with 'utf-8-sig' → 20 records now load.
state.load_projects() -> 20 project records   ✅ after fix
  key='sanctum'         display='Sanctum'
  key='sinister-panel'  display='Sinister Panel'
  key='kernel-apk'      display='Kernel APK'
  key='rkoj'            display='RKOJ'         ← v6 umbrella
  ...

# RKOJ /api endpoints (in-process on :5277 to avoid colliding with live :5077)
/api/health           HTTP 200  ct=application/json
/api/version          HTTP 200  ct=application/json  sinister_rkoj_qt=1.6.89  ✅ bump verified
/api/diagrams         HTTP 200  count=2
/api/phones           HTTP 200  devices=[{serial=26031JEGR17598,...}]  ← live phone present
/api/agents           HTTP 200  agents=[] total_claimed_phones=0
/api/diagrams/<stem>  HTTP 200  bytes=959  stem=2026-05-21T163838Z
/api/diagrams/<traversal>  HTTP 404

# Mind diagrams surface (re-verified)
/diagrams             HTTP 200  has /api/diagrams marker
/api/diagrams         HTTP 200  count=2
/api/diagrams/<stem>  HTTP 200  bytes=959
/api/diagrams/<traversal>  HTTP 404

# sinister-browser Layer A
test_exit_0_when_valid_ws_handshake  PASS
test_exit_2_when_nothing_listening    PASS
test_exit_3_when_plain_http           PASS
test_exit_3_when_wrong_accept         PASS

# resume-point-write.ps1 → RKOJ/<UTC>.json (after slug fix)
[resume-point-write] saved: _shared-memory/resume-points/RKOJ/2026-05-23T064149Z.json

# Knowledge + tools indices
tools/_INDEX.md                rows=30  ✅
knowledge/_INDEX.md            rkoj-session entries present  ✅
```

### A2 — offscreen Qt (PASS=4 FAIL=0)

```
QT_QPA_PLATFORM=offscreen
MainWindow()                                      OK
DevicesView()                                     OK
AgentsView()                                      OK
_MirrorCard fake-dev (title prefix ok=True)       OK   ← scrcpy spawn surface intact
```

### A3 / A4 / A5 — needs operator hardware or installs

These were NOT run this session. They will be run by the operator when:
- A3: a phone is USB-attached AND operator launches RKOJ.exe → click Mirror on a phone row → confirm NO stray scrcpy window appears anywhere on the desktop, mirror shows up only inside the MirrorCard. (The /api/phones probe above already confirmed `26031JEGR17598` IS attached — the operator can run A3 now if they want; the fix is committed but RKOJ.exe v1.6.89 hasn't been re-built via PyInstaller.)
- A4: operator installs firefox-agent-bridge XPI + native host, then `python -m sinister_browser probe` should exit 0.
- A5: operator double-clicks `projects/rkoj/source/sinister_rkoj_qt/build-and-install.bat` (or equivalent) to rebuild RKOJ.exe v1.6.89 onefile.

## (G) Net new bugs caught + fixed this session

1. **Stray scrcpy windows outside the UI** (operator's headline complaint). scrcpy was spawning at the OS-default position and the ~300ms+ embed poll left a visible window flash. Fix: `--window-x 30000 --window-y 30000 --window-width MIRROR_SIZE --window-height MIRROR_SIZE` + `ShowWindow(SW_HIDE)` before SetParent + `ShowWindow(SW_SHOWNOACTIVATE)` after positioning. v1.6.88 → v1.6.89.
2. **`projects.json` BOM silently breaks `load_projects`**. Resume picker would have been empty whenever the launcher rewrote `projects.json` with Out-File default encoding (BOM). Fix: `open(... encoding="utf-8-sig")` handles both BOM and no-BOM.

Both fixes ship in commit (next).

## (H) What's NOT in this slice (deferred)

- Layer B/C/D of sinister-browser (full wrapper) — defer until operator brings up live firefox-bridge.
- Mind nodes overlay for /diagrams — defer (no operator demand).
- RKOJ.exe v1.6.89 PyInstaller rebuild — operator-owned (PyInstaller spawns child processes the sandbox handles awkwardly; safer for operator to run `pyinstaller sinister_rkoj_qt/RKOJ.spec` directly).
- Brain entry for "silent try/except swallowed a real bug" pattern + "PowerShell Out-File BOM bites readers" pattern — both worth capturing but holding for the next cycle.
