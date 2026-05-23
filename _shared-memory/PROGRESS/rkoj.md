# Agent: rkoj (RKOJ umbrella — EVE on RKOJ)

> **Author:** RKOJ-ELENO :: 2026-05-23

Append-only progress log for the `rkoj` umbrella lane (Forge + Term + Workstation + Mind + Claw per `projects.json` v6). Most recent at top.

---

## 2026-05-23 07:30 EDT — /loop iteration 5 — RKOJ v1.6.89 scrcpy-no-stray + BOM bug caught + full test pass

Operator (verbatim 2026-05-23T06:48 EDT): *"dont have scrpoy windows show up outside of the ui itself. create a plan to test everything and review everything you need to do and complete it all"*. Two real bugs caught + fixed; comprehensive test plan written; 29 of ~41 tests executed in-sandbox.

### Ships this iteration

| Surface | Effect |
|---|---|
| `projects/rkoj/source/sinister_rkoj_qt/devices_tab.py::_spawn_scrcpy` | scrcpy now spawned at offscreen `(30000, 30000)` with `--window-width`/`--window-height` pinned to `MIRROR_SIZE` from the first frame. The headline operator complaint addressed at the spawn surface. |
| `devices_tab.py::_try_embed` | Defense-in-depth `ShowWindow(SW_HIDE)` immediately after `FindWindow` returns the HWND, BEFORE `SetParent` + style changes; then `ShowWindow(SW_SHOWNOACTIVATE)` once the window is positioned inside `_body_host`. |
| `projects/rkoj/source/sinister_rkoj_qt/__init__.py` | `__version__ = "1.6.89"` |
| `projects/rkoj/CHANGELOG.md` | v1.6.89 entry at top — root cause + two-part fix + verification path |
| `projects/rkoj/source/sinister_rkoj_qt/state.py::load_projects` | **Real bug caught by running the test plan.** `projects.json` carries a UTF-8 BOM (PowerShell `Out-File` default); `load_projects` opened with `encoding="utf-8"` so `json.load` raised `JSONDecodeError("Unexpected UTF-8 BOM")`; the outer `except` swallowed it; `load_projects` returned `[]`. Resume picker was silently empty whenever the launcher rewrote `projects.json`. Fix: `encoding="utf-8-sig"`. Verified — returns 20 project records now. |
| `_shared-memory/plans/rkoj-test-review-complete-2026-05-23T0700Z/plan.md` (new, ~270 lines) | Full RKOJ surface map split into 5 test categories (A1 sandbox-runnable / A2 offscreen-Qt / A3 ADB-phone / A4 firefox-bridge / A5 PyInstaller-build) + matrix review + bug catches + recommended ordering. |
| `_shared-memory/OPERATOR-ACTION-QUEUE.md` | New top row for v1.6.89 rebuild + on-hardware verify + BOM-fix sanity check |

### Test pass results

| Category | Run | Pass | Fail | Notes |
|---|---|---|---|---|
| A1 sandbox | 25 | 25 | 0 | 12 module imports + `load_projects` (20 records after fix) + 7 RKOJ `/api/*` + 4 Mind `/diagrams` + 4 sinister-browser probe unit tests + 1 resume-point script + 2 indices |
| A2 offscreen-Qt | 4 | 4 | 0 | MainWindow + DevicesView + AgentsView + `_MirrorCard(mock_device)` |
| A3 ADB phone | 7 | 0 | 0 | needs operator hardware (`adb` already sees phone `26031JEGR17598`) |
| A4 firefox-bridge | 1 | 0 | 0 | needs operator XPI + native-host install |
| A5 PyInstaller | 3 | 0 | 0 | operator double-clicks the build script |

### Commits + branch state

`59667b7` + `ab16d16` (both same v1.6.89 message — see note below) landed on `agent/sinister-generator/source-package-2026-05-23` due to a sibling-agent `git checkout` mid-session; rkoj branch ref was then fast-forwarded via `git branch -f agent/rkoj/next-slate-2026-05-23 ab16d16` (no history rewrite — it's a clean fast-forward from `a4b71cf`). Pushed to origin after one HTTP 408 retry.

### Multi-agent git-index contention storm

5+ concurrent `git.exe` processes from sibling lanes (jb-woodworks, showmasters, sinister-generator, sinister-seraphim, launcher) held the `.git/index.lock` for ~25 minutes mid-session, causing my staged commits to fail/duplicate. Recovery via fast-forward + `git branch -f` to the right ref. Anti-pattern to capture in the next brain-entry cycle: "multi-agent git-index contention storm — N concurrent lanes need `git worktree add` isolation or serialization through a single writer".

### 5-check gate

✅ inbox empty; TaskList #1-#14 all completed; PROGRESS appended; matrix already at correct ✅/🚧/📋 state; resume-point written to `_shared-memory/resume-points/RKOJ/2026-05-23T073733Z.json`.

---

## 2026-05-23 06:42 — /loop iteration 4 — matrix flips + Layer A probe + script fix

Operator: *"keep working on everyting you need to complete"*. Continued the cycle on the now-pushed `agent/rkoj/next-slate-2026-05-23` branch. Three concrete deliverables shipped:

### Ships this iteration

| Surface | Effect |
|---|---|
| `_shared-memory/knowledge/jcode-feature-matrix.md` row 12 | 🚧 → ✅ **shipped**. All four memory-graph consumers (Forge `Ctrl+D` panel + RKOJ `/api/diagrams` + Mind `/diagrams` web view + render pipeline) now target the single on-disk cache. Notes column rewritten to point at Mind v0.3.0 + commit `b199dae`. |
| `_shared-memory/knowledge/jcode-feature-matrix.md` row 26 | Notes updated. Status flipped from `🚧 doc` to `🚧 doc + Layer A probe` (still 🚧 — full ✅ when Layer B+C+D land). References the new audit doc + `tools/sinister-browser/` package. |
| `tools/sinister-browser/` v0.1.0 (new package, 4 files + tests) | Layer A connectivity probe for the upstream firefox-agent-bridge. stdlib-only. TCP-connect + minimal RFC 6455 §4.2.2 HTTP Upgrade handshake (computes the expected `Sec-WebSocket-Accept` and compares against server response). Exits 0=alive / 2=not-installed / 3=installed-but-unreachable. CLI: `sinister-browser probe [--host --port --timeout --json]` + `sinister-browser version`. 4/4 unittests green (against in-process fake servers: nothing-listening / valid-WS / wrong-accept / plain-HTTP). pyproject.toml AGPL-3.0-or-later + RKOJ-ELENO authors. Registered in `tools/_INDEX.md`. |
| `automations/resume-point-write.ps1` slug-map | `'rkoj'` slug now routes to `'RKOJ'` display dir (the umbrella per projects.json v6) instead of legacy `'RKOJ Workstation'`. PROGRESS lookup updated to `'rkoj.md'`. Legacy `rkoj-workstation` sub-lane unchanged for back-compat. Parse-validated + live-tested: resume-point now writes to `_shared-memory/resume-points/RKOJ/2026-05-23T064149Z.json`. |

### Smoke-test transcripts

```
# Layer A probe — no bridge running (expected exit 2)
$ python -m sinister_browser probe
sinister-browser :: 127.0.0.1:8766 :: NOT-INSTALLED
  bridge not installed or Firefox not running (ConnectionRefusedError)
exit=2

# JSON output
$ python -m sinister_browser probe --json
{ "exit_code": 2, "summary": "bridge not installed or Firefox not running (ConnectionRefusedError)", ... }
exit=2

# Unit tests (in-process fake servers)
test_exit_0_when_valid_ws_handshake ... ok
test_exit_2_when_nothing_listening ... ok
test_exit_3_when_plain_http ... ok
test_exit_3_when_wrong_accept ... ok
Ran 4 tests in 1.178s — OK
```

### Matrix status overall after this iteration

| Row | Before | After |
|---|---|---|
| 12 (memory-graph viz) | 🚧 PNG + Forge + REST API shipped, Mind view pending | ✅ shipped |
| 26 (browser-bridge) | 🚧 doc | 🚧 doc + Layer A probe |

3 rows of the original 11-row Sanctum ASK still in flight: 22 (Mind nodes — different from /diagrams, deferred), 23 (claude-hooks, external pkg not on disk), 24 (Skill_Seekers, external pkg not on disk). 2 rows fully operator-gated: 25 (agentgrep cargo install) + 28 (Rust mermaid renderer toolchain). Layer B+C+D of sinister-browser deferred until operator brings up live firefox-agent-bridge — Layer A is the green-path connectivity probe.

### 5-check gate

✅ inbox empty; TaskList resolved (#8/9/10 all completed, #11 = this turn); PROGRESS appended; matrix flips committed in same turn; resume-point write next (correctly into `RKOJ/` after the script fix).

---

## 2026-05-23 06:30 — /loop dynamic iteration 3 — Mind /diagrams web view + 2 brain entries

EVE on RKOJ, cold-resume in `resume` mode at HEAD `73c628b` (the operator anti-revert doctrine commit). Per the `2026-05-23T1545Z-from-sanctum-no-more-self-imposed-blocks.json` broadcast, per-agent branches push freely. Branch cut fresh as `agent/rkoj/next-slate-2026-05-23` after catching the **pre-doctrine HEAD branch-cut hazard** (see brain entry below).

### Ships this iteration

| Surface | Effect |
|---|---|
| `projects/sinister-mind/source/mind/server.py` (+~70 LOC) | Three new endpoints. `/api/diagrams` returns the same JSON shape as RKOJ Workstation `:5077` (so both surfaces target the same on-disk cache at `_shared-memory/forge-memory/mermaid-renders/`). `/api/diagrams/<stem>` serves bytes with proper Content-Type (path-traversal-guarded — Flask appends charset to text/* automatically so I dropped the explicit `; charset=utf-8` to avoid duplicate-charset headers). `/diagrams` serves the new HTML page. Bumped Mind to `version = "0.3.0"`. |
| `projects/sinister-mind/source/mind/static/diagrams.html` (new, ~410 LOC) | Sinister-themed memory-graph viewer. Liquid-glass aesthetic matches `index.html` (uses existing `mind.css` palette + page-local CSS for the grid + modal). Auto-refresh every 15s. Tile grid newest-first, click to open full-size modal (`<img>` for PNG/SVG, `<iframe>` for HTML, fetch-as-text `<pre>` for `.mmd`). Ext filter + count badge + ESC closes modal. Empty-state messaging handles three cases (renders-dir missing / dir-empty / filter-empty). |
| `projects/sinister-mind/source/mind/static/index.html` (small edit) | New "Views" sidebar section with `◈ Graph` + `◇ Memory-graph diagrams` nav links so the operator can hop between surfaces. |
| `_shared-memory/knowledge/branch-checkout-silently-undoes-doctrine-2026-05-23.md` (new, ~80 lines) | Captures the pre-doctrine HEAD branch-cut regression caught this session: `git checkout agent/rkoj/complete-without-operator-2026-05-23` (HEAD `b9e89dc`) silently rewrote CLAUDE.md to the 6-step cold-start (no DO-NOT-REVERT block, no understand-anything pre-call). System reminder *"CLAUDE.md was modified, either by the user or by a linter"* masked the cause as user/linter when it was git. Standing rule: always cut new per-agent branches off the latest doctrine HEAD; if you must resurrect a pre-doctrine branch, fast-forward-merge the doctrine commit first. Indexed in `_INDEX.md`. |
| `_shared-memory/knowledge/browser-bridge-integration-shape-2026-05-23.md` (new, ~140 lines) | Read-only audit of `firefox-agent-bridge v0.9.9` on disk at `C:/Users/Zonia/Desktop/Github Research/`. Documents the upstream three-layer architecture (Rust `browser` CLI + Rust native-messaging host + signed XPI) + the WebSocket JSON wire protocol on `:8766`. Codifies the **wrap-not-clone** integration shape: Layer A probe (`tools/sinister-browser/probe.py`) + Layer B pythonic API + Layer C Forge `/browser` slash + Layer D `skills/sinister-browser/SKILL.md` mirror. Resolves the MIT-vs-AGPL license gap by wrap-only (no source copy). Indexed in `_INDEX.md`. Matrix row 26 flips ✅ once Layer A+B+C+D land — deferred until operator asks. |
| `_shared-memory/plans/rkoj-complete-2026-05-23T0621Z/forward-plan.md` (new) | This iteration's plan. Documents the 0455Z slate as substantially shipped + the new 5-row slate + the operator-gated rows (Restart Claude Code, ANTHROPIC_API_KEY, Rust toolchain, missing external pkgs, `gh auth refresh -s workflow`) — none blocking. |

### Smoke-test transcript (Mind diagrams surface)

```
/diagrams            : HTTP 200  ct=text/html; charset=utf-8  bytes=14091  has-marker=True
/api/diagrams        : HTTP 200  ct=application/json  count=2
/api/diagrams/<stem> : HTTP 200  ct=text/html; charset=utf-8  bytes=959  stem=2026-05-21T163838Z
/api/diagrams/..%2F..%2Fpasswd          HTTP 404 (path-traversal guard fired)
/api/diagrams/this-stem-does-not-exist  HTTP 404 (missing-stem guard fired)
```

Two diagrams already in the cache (the `2026-05-21T163727Z` + `2026-05-21T163838Z` Forge mermaid renders shipped earlier); the page renders them as tiles with `.html` + `.mmd` sibling pills.

### Matrix delta after this iteration

Row 12 (Memory-graph visualization) — the last 🚧 component (Mind web view) is now shipped. The full row reads:

> `tools/memory-graph-render/` → mermaid → `mermaid-rs-renderer` → PNG + Forge `panes/mermaid_panel.py` + RKOJ `/api/diagrams` + **Mind `/diagrams` page consuming the same cache**

All four endpoints (Forge in-TUI panel + RKOJ REST API + Mind web view + render pipeline) now target the single source of truth at `_shared-memory/forge-memory/mermaid-renders/`. Row 12 ready to flip 🚧 → ✅ in the matrix on the next Sanctum-lane edit; rkoj-lane has noted the flip in this PROGRESS row.

### What's still open in-lane

- **Row 23 (claude-hooks)** + **Row 24 (Skill_Seekers)**: external packages still not on disk under `C:/Users/Zonia/Desktop/Github Research/`. Need operator to drop the upstream source before integration.
- **Row 26 (browser-bridge)**: audit doc shipped this turn; Layer A+B+C+D wrapper deferred until operator asks.
- **Row 25 (agentgrep)** + **Row 28 (Rust mermaid renderer)**: operator-gated (toolchain installs).

### 5-check gate

✅ inbox empty (only the no-reply broadcast); TaskList resolved (#1-#7 all completed); PROGRESS appended; matrix-delta noted (row 12 ready-to-flip); resume-point write next.

---

## 2026-05-23 05:30 — /loop "complete everything" iteration 2 — 3 more matrix rows ✅ + RKOJ /api/diagrams

EVE on RKOJ, continuing the /loop dynamic mode after the forward-plan slate closed in commit `9b76247`. Operator: *"complete everything and dont stop"*. Cycled three more in-lane follow-ups + one new RKOJ Workstation API endpoint, all without operator gates.

### Ships this iteration

| Commit | Surface | Effect |
|---|---|---|
| `4bc5b4d` | `forge/skills.py` + `forge/app.py` (watchdog auto-reload) | jcode-parity row 18 → ✅. `start_watcher()` schedules a `watchdog.observers.Observer` on the skill roots; reacts to `*.md` changes; lazy-imports watchdog (no-op on missing dep); wired in `on_mount`. Smoke-tested. |
| `4bc5b4d` | `forge/panes/mermaid_panel.py` (new, 164 LOC) | jcode-parity row 15 → ✅. Ctrl+D opens a textual panel listing cached mermaid renders (newest-first, 12 rows, human-age formatter, click-to-open in OS viewer). Auto-refreshes every 15s. Wired into `app.py` bindings + command palette. |
| `4bc5b4d` | `jcode-feature-matrix.md` row 5 re-audit | Row 5 corrected 🚧 → ✅ (boot art has always been wired — initial grep missed the `BootScreen` class). |
| (this turn) | `rkoj/source/sinister_rkoj_qt/api_server.py` (+95 LOC) | Row 12 advanced: `GET /api/diagrams` lists cached renders; `GET /api/diagrams/<stem>` serves bytes with proper Content-Type. Path-traversal guarded. Enables future Mind web view + RKOJ desktop_app embed without extra wiring. |

### Matrix delta after both iterations

Originally 11 rows planned/in-flight per Sanctum's ASK; 6 now ✅, 4 still 🚧 (Mind web view, claude-hooks, Skill_Seekers external repos, browser-bridge), 1 operator-gated (agentgrep), 1 operator-gated (Rust mermaid renderer).

### What's still open in-lane

- **Row 23 (claude-hooks)** + **Row 24 (Skill_Seekers)**: external packages NOT on disk under `C:/Users/Zonia/Desktop/Github Research/` (verified). Both need operator to drop the upstream source before integration.
- **Row 26 (browser-bridge)**: `firefox-agent-bridge-0.9.9/` IS on disk and could be wrapped. Deferred — operator hasn't asked.
- **Row 25 (agentgrep)** + **Row 28 (Rust mermaid renderer)**: operator-gated (toolchain installs).

### 5-check gate

✅ inbox empty (no new entries this iteration); TaskList resolved (#7/8/9/10 all completed); PROGRESS appended; matrix flips committed; resume-point write next.

---

## 2026-05-23 04:55 — resume pickup + complete-without-operator forward-plan

EVE on RKOJ, cold-resume in `resume` mode (no prior `rkoj`-slug resume-point on disk; falling back to PROGRESS/rkoj-workstation.md + plans/rkoj-*-2026-05-21/ + inbox + git log -20). RKOJ.exe is at v1.6.88 per `__init__.py __version__` (commit `915a878`).

**Branch cut**: `agent/rkoj/complete-without-operator-2026-05-23` off prior HEAD `b9e89dc`. Sibling-lane dirty tree (22 modified + 16 deleted in `_shared-memory/` from Sanctum master sweep + Showmasters) left UNTOUCHED per canonical-10. My commits go through clean staging only.

**Context-review summary (CONTRACT 1):**
- **Shipped (last 14 commits, v1.0.2 → v1.6.88):** workstation API server :5077, single-Desktop entry, /api slash, install-apk, embed device viewer, per-phone agent claims (v1.6.79 + state.py::claim_phone), advanced view, image paste, resizable window, transparent cards + breathing glow, Panel canonical colors, Resume picker merges all projects.json entries, per-phone scrcpy stderr → log, Sini-stray-window leak fix, sidebar nav labels visible, sinister-eve.exe (8.1 MB onefile), token-budget warning + /budget gauge, jcode skill-frontmatter parity.
- **In-flight:** none on disk; latest commit shipped.
- **Inbox unread (5):** (a) Sanctum jcode-parity ASK 2026-05-23T0710Z — reply_required: yes, asks for matrix flips on 11 rows; (b) Sanctum projects.json v6 schema NOTIFY 2026-05-23T0815Z — informational, optional patch; (c) kernel-apk staging-race NOTIFY 2026-05-21T1930Z — reply_required: false, archivable; (d) Sanctum session-picker-spec ASK 2026-05-21T0300Z — likely superseded by v1.6.88 Resume picker; (e) Sanctum forge-dashboard-spec ASK 2026-05-21T1108Z — needs audit vs Forge source.
- **Operator-gated (cross-project, not RKOJ-specific):** Restart Claude Code (activates 12 MCPs + 14 plugins), Set ANTHROPIC_API_KEY (unlocks RKOJ v0.7.0 multi-step reasoning), Install Rust toolchain (jcode source fork), enable nano-banana billing.

**Forward-plan written:** `_shared-memory/plans/rkoj-complete-2026-05-23T0455Z/forward-plan.md` (this turn).

**TaskList state:** 4 rows. #1 in-progress (this turn), #2-4 pending.

**5-check gate:** ✅ directive logged inline; TaskList in-flight; PROGRESS appended top; queue-flip pending (next slice); resume-point write pending (terminal task).

---
