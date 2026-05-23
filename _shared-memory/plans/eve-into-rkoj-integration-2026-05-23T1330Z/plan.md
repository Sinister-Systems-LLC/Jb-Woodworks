<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# Fold EVE.exe picker INTO RKOJ.exe — "sick sick EVE.exe system"

> **Status:** `scaffolded` (per `no-bullshit-tested-before-claimed-doctrine-2026-05-23`). The Plan agent that authored this content was read-only and could not write it; this materialization is the parent agent (Sanctum / EVE) persisting the plan honestly.
> **Verb upgrade path:** `scaffolded` → `acceptance-tested` after P1 ships + smoke tests PASS; `shipped` after all 12 final-done criteria (Section 10) verified.

**Created:** 2026-05-23T13:30Z
**Source agent:** Plan (Sonnet) — 108,447 tokens, 29 tool uses, 494 sec runtime, read-only mode
**Operator verbatim 2026-05-23:** *"make a sick sick eve.exe sysstem that can be added to rkoj"*

---

## 5-Bullet TL;DR

- EVE.exe stays the bat-launched standalone picker (`automations/eve-launcher/eve.py`). RKOJ.exe gets an **in-Qt picker pane** that replicates EVE's verbs (1-14 / G / A / N / R / K / S / F / multi / swarm) and routes selections into the existing `AgentsView.spawn_agent` path — NOT a re-spawn of mintty/bash.
- A new shared library `D:\Sinister Sanctum\tools\eve-picker\` is the source-of-truth for `read_projects / read_prefs / visible_projects / render_picker (text) / parse_multi / resolve_pick`. Both EVE.exe (standalone) and RKOJ (PyQt6) import it. Zero external deps so EVE.exe's PyInstaller `--onefile` size budget (<20 MB) and <300 ms cold-start budget stay intact.
- 10 sick-sick uplifts (all measurable acceptance tests): Ctrl+P picker overlay, per-card "Clone-as-EVE-pick" button, swarm/loop toggle on each card, project-color swatches in picker, picker keyboard-only navigation, picker-respects-agent-prefs accents, multi-spawn batch with stagger, resume-saves-blended-with-fresh in the picker, in-app `--profile` for the picker (boot ms label), and `EVE` slash-command parity (`/eve`, `/spawn <key>`, `/swarm <key1,key2>`).
- Phasing P1-P6 totals ~28 hr single-thread; ~16 hr with 2 parallel lanes (one EVE-Sanctum, one RKOJ). P1 (shared lib) and P2 (EVE.exe lift-shift) are prerequisites for P3+ (RKOJ pane). Each phase has explicit acceptance criteria + smoke command + measurable PASS row. No fairy-tale "shipped" verbs.
- Anti-features explicitly forbidden: don't replace `start-sinister-session.ps1`, don't reimplement Launch-Session in RKOJ (QProcess spawn already works per `rkoj-phase1-memory-bootstrap-2026-05-21`), don't add Qt to EVE.exe, don't bypass the canonical-protections doctrine when spawning, don't ship anything tagged "sick" without P-by-P acceptance evidence.

---

## Section 0 — Integration shape (3 sentences)

RKOJ gains an in-panel "EVE Picker" surface (Ctrl+P overlay + a sidebar `EVE` chip) that renders the exact same 14-project / G / A / N / R / K / S / F verb grid that EVE.exe shows in the terminal — but when the operator selects a project, RKOJ dispatches through the **existing** `_spawn_inline → AgentsView.spawn_agent → QProcess(claude --session-id ...)` path (no mintty, no PowerShell). EVE.exe and RKOJ share the picker UI logic by both importing `tools/eve-picker/eve_picker_lib.py` — EVE.exe owns the `mintty + bash + claude` spawn layer, RKOJ owns the `QProcess + claude + agent-card streaming` spawn layer, and the picker logic stays identical between them. Swarm/loop opt-in becomes a per-card chip in RKOJ (visible state of the env-var pair that EVE.exe sets at spawn) so the operator sees at-a-glance which cards are running solo vs in a swarm loop.

---

## Section 1 — Precise split

| Dimension | EVE.exe (standalone) | RKOJ-integrated EVE |
|---|---|---|
| Trigger | `Sinister Start.bat` → `EVE.exe` | `RKOJ.exe` running → Ctrl+P / sidebar EVE chip |
| Runtime | Compiled CPython via PyInstaller --onefile | PyQt6 process (already running) |
| Picker rendering | ANSI escapes to console | `QPickerOverlay` (QWidget) using `eve_picker_lib` plain-text rows |
| Spawn path | `subprocess.call(['powershell.exe', ..., 'start-sinister-session.ps1', '-Project', key])` | `AgentsView.spawn_agent(project_key=key, agent_name=..., mode=...)` |
| Window surface | mintty (new shell window) | In-panel agent card (niri-scroll grid) |
| Identity env vars | exported by `start-sinister-session.ps1` | exported by `agents_tab._make_child_env` |
| Trust pre-acceptance | PS1 `Confirm-AgentPrefs` | `agents_tab._pretrust_project` (existing) |
| Status pills | PS1 status pills in shell prompt | RKOJ header pills (existing) |
| Multi-select | sequential PS1 calls with 400ms gap | sequential `spawn_agent` calls with QTimer.singleShot(400, ...) chain |
| Swarm / loop | `SINISTER_EVE_SWARM=1` / `SINISTER_EVE_LOOP=1` env vars | New `_ClickPill` chips per card mirroring those env vars |
| Resume | EVE.exe falls through to PS1 picker for `A` | RKOJ uses existing `SavedSessionsPicker` (`dialogs.py` L330+) |

### 1.2 Verb-by-verb mapping (22 verbs)

Reference: `_shared-memory/plans/eve-exe-completion-2026-05-23T1230Z/eve-exe-finish-plan.md` Section 1.

| # | Verb | RKOJ behavior | Call |
|---|---|---|---|
| 1 | Numeric 1-14 | Spawn agent card inline | `AgentsView.spawn_agent(project_key=rows[i-1].key)` |
| 2 | G | Spawn "general" project | `spawn_agent(project_key='general')` |
| 3 | A | Open existing `SavedSessionsPicker` | `self._open_sessions_picker()` |
| 4 | N | Open existing `NewAgentDialog` | `self._on_create_agent()` |
| 5 | R | New `RenameProjectDialog` modal → writes `agent-prefs.json` | new |
| 6 | K | Existing `/clear` on focused card; else toast | reuse `AgentCard._on_clear` |
| 7 | S | New `AutonomyToggleDialog` (writes EVE autonomy env preset for future spawns) | new |
| 8 | F | Picker stays open; no special action | no-op |
| 9 | Q | Close overlay | `overlay.hide()` |
| 10 | Multi-select `1,3,5` / `1-3` | Sequential `spawn_agent` chain w/ 400ms stagger | new helper `_dispatch_multi_inline` |
| 11 | Enter (default) | Spawn default_key (sanctum) | `spawn_agent('sanctum')` |
| 12 | Looping picker | Overlay stays visible after each spawn | default behavior |
| 13 | Banner | Top of overlay: same banner + boot-ms via QElapsedTimer | new `_overlay_banner()` |
| 14 | MCP count | `eve_picker_lib.count_mcp()` | imported |
| 15 | Bot count | `eve_picker_lib.count_bots()` | imported |
| 16 | Boot-time self-report | Overlay open time via QElapsedTimer | inline |
| 17 | Status pills | Render PILL_G/B/R inside overlay using `theme.py` colors | new |
| 18 | Per-project agent + accent | `[agent_name / accent_color]` suffix | reuse lib `get_agent_name/get_accent` |
| 19 | utf-8-sig JSON read | already used by `state.load_projects()` + `eve.py` | shared in lib |
| 20 | VT enablement | N/A — Qt does its own rendering | skip in RKOJ branch |
| 21 | Refresh prefs between iterations | Re-call `read_prefs()` whenever overlay re-shown | new |
| 22 | Unknown selection → warn | Toast at bottom of overlay (1s ttl) | new |

### 1.3 What stays OUT of RKOJ (binding)

- mintty (RKOJ embeds conversation in `QPlainTextEdit`, not a shell window)
- bash + PS1 launcher invocation (RKOJ talks to `claude` directly via QProcess)
- The Launch-Session PS1 surface (RKOJ relies on `_pretrust_project` + `_make_child_env` + `_bootstrap_agent_memory` for parity)

---

## Section 2 — Architecture (two paths, one source-of-truth)

```
                          ┌────────────────────────────┐
                          │   eve_picker_lib  (NEW)    │
                          │  D:\Sinister Sanctum\tools │
                          │      \eve-picker\          │
                          │  stdlib-only; no Qt        │
                          ├────────────────────────────┤
                          │ read_projects()            │
                          │ read_prefs()               │
                          │ visible_projects()         │
                          │ get_agent_name / accent    │
                          │ count_mcp / count_bots     │
                          │ resolve_pick(raw_input)    │
                          │ parse_multi()              │
                          │ build_picker_state()  *new*│
                          │ banner_text(state)         │
                          │ picker_text_rows(state)    │
                          │ project_color(key)    *new*│
                          └────────────┬───────────────┘
                                       │ import
              ┌────────────────────────┼─────────────────────────────┐
              │                                                      │
   ┌──────────▼───────────┐                              ┌───────────▼──────────┐
   │ EVE.exe (standalone) │                              │ RKOJ.exe (PyQt6)     │
   │  eve.py (~150 LOC    │                              │  agents_tab +        │
   │  after lift-shift)   │                              │  picker_overlay.py   │
   │  ANSI render          │                              │  QPickerOverlay      │
   │  subprocess.call PS1  │                              │  AgentsView.spawn    │
   │   ↓                   │                              │  _agent()            │
   │  mintty + bash + claude│                             │   ↓                  │
   │  status pills in shell│                              │  QProcess + claude   │
   │                       │                              │  agent-card streaming│
   └──────────────────────┘                              └──────────────────────┘
```

### 2.1 Shared library vs duplication

**Decision: shared library** at `tools/eve-picker/eve_picker_lib.py`.

| Approach | Pro | Con | Verdict |
|---|---|---|---|
| Shared lib | one source of truth; no drift; small size impact | EVE.exe needs `--paths` to PyInstaller; RKOJ needs sys.path setup | **CHOSEN** |
| Duplicate code | each project self-contained | drift guaranteed within ~3 versions | rejected |
| EVE imports from RKOJ | one-direction dep | couples EVE size to RKOJ surface | rejected |
| RKOJ imports from EVE scaffold | one-direction dep | tooling vs project shape mismatch | rejected |

### 2.2 PyInstaller impact on EVE.exe

Add `--paths "D:\Sinister Sanctum\tools\eve-picker"` to PyInstaller invocation. Size delta ~10-30 KB. Boot-time impact negligible (single pure-Python module).

### 2.3 RKOJ import path

Lightweight `sys.path` insertion in `sinister_rkoj_qt/__main__.py`:

```python
import sys
from pathlib import Path
_EVE_LIB = Path(r"D:\Sinister Sanctum\tools\eve-picker")
if _EVE_LIB.exists() and str(_EVE_LIB) not in sys.path:
    sys.path.insert(0, str(_EVE_LIB))
```

Alternative: `pip install -e D:\Sinister Sanctum\tools\eve-picker` if we add a `pyproject.toml`.

### 2.4 Why spawn layer must NOT be shared

`start-sinister-session.ps1` (1396 lines) handles mintty + bash + Confirm-AgentPrefs.
`AgentsView.spawn_agent` handles QProcess + agent-card.

Different surfaces by design. Picker logic shares; spawn does NOT.

---

## Section 3 — RKOJ panes to add / extend

### 3.1 NEW: `QPickerOverlay` widget

**File:** `D:\Sinister Sanctum\projects\rkoj\source\sinister_rkoj_qt\picker_overlay.py`

**Triggers:**
- Keyboard: `Ctrl+P` (QShortcut in `app.SinisterWindow._wire()`)
- Sidebar: new `EVE` nav row under `WORKSPACE` (above `Agents`)
- Header: new chip `EVE picker` under `header.CHIP_SETS["agents"]`

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  E V E    // jcode-speed launcher    boot: 142 ms           │
│  ────────────────────────────────────────────────────────── │
│  [mcp:5]  [bots:11]  [--skip-perms]                          │
│  ────────────────────────────────────────────────────────── │
│  Pick a project                                              │
│  * 1) Sanctum             orchestration hub        ●         │
│    2) Sinister Panel      Control Center @ snap... ●         │
│    ...                                                       │
│   14) jkor                jkor lane                ●         │
│                                                              │
│  G) General   A) Resume   N) New Project   R) Rename + Color│
│  K) Clear     S) Autonomy F) Full picker   Q) Quit          │
│   multi: 1,3,5 or 1-3                                        │
│                                                              │
│  ▶ selection [ _________________ ]    [ Spawn ] [ Cancel ]   │
└─────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Lives as `QWidget` overlay on top of `SinisterWindow` (`Qt.WindowType.Tool`)
- Fade-in 120ms via `QPropertyAnimation`
- Esc closes; Enter dispatches default; numeric input triggers immediate dispatch on Enter
- Per-row click also dispatches
- Each row shows `project_color` swatch (8x8 dot) reusing `_PROJECT_COLORS` from `agents_tab.py`
- Banner shows `boot N ms` (QElapsedTimer from open-to-paint)

**NOT in scope (deferred):**
- Fuzzy-search (use existing Ctrl+K)
- Drag-and-drop project reorder
- Edit projects.json from picker

### 3.2 Resume picker integration (Verb A)

Existing `SavedSessionsPicker` (`dialogs.py` L330-499). Verb `A` opens this dialog; zero change to existing dialog.

### 3.3 Per-card swarm/loop chips

**Files:** `agents_tab.py` L800-900 (`_ClickPill` + AgentCard header pill row)

- `SWARM` chip (purple): visible when `SINISTER_EVE_SWARM=1` was set at spawn
- `LOOP` chip (cyan): visible when `SINISTER_EVE_LOOP=1` was set at spawn

Chips MIRROR env vars (read-only state indicator); they don't drive them.

### 3.4 Sidebar EVE nav row

```
WORKSPACE
  ▸ EVE        ← NEW
  ▸ Agents
OPERATIONS
  ▸ Devices
```

### 3.5 Header chip set extension

`header.py` `CHIP_SETS["agents"]` becomes:

```python
"agents": [("agents", "Agents"), ("eve", "EVE picker"), ("resume", "Resume")]
```

`_on_chip("eve")` → open picker overlay.

---

## Section 4 — Shared library `tools/eve-picker/`

### 4.1 Layout

```
D:\Sinister Sanctum\tools\eve-picker\
├── eve_picker_lib.py        # single-module library (stdlib-only)
├── README.md                 # tool card
├── pyproject.toml            # optional (if pip install -e route chosen)
├── tests/
│   ├── test_resolve_pick.py
│   ├── test_parse_multi.py
│   └── fixtures/
│       └── projects.json
└── .gitignore                # __pycache__/, *.pyc
```

### 4.2 Library API (proposed signatures)

```python
# eve_picker_lib.py
from __future__ import annotations
import json, os, time, uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SANCTUM_ROOT = Path(os.environ.get('SINISTER_SANCTUM_ROOT', r'D:\Sinister Sanctum'))
PROJECTS_JSON = SANCTUM_ROOT / 'automations' / 'session-templates' / 'projects.json'
PREFS_JSON = SANCTUM_ROOT / 'automations' / 'session-templates' / 'agent-prefs.json'

@dataclass
class PickerRow:
    index: int
    key: str
    display: str
    tag: str
    agent_name: str
    accent: str
    is_default: bool
    customized: bool
    project_color: str

@dataclass
class PickerState:
    rows: list[PickerRow]
    default_key: str
    mcp: int
    bots: int
    boot_ms: int

def read_projects() -> dict: ...
def read_prefs() -> Optional[dict]: ...
def visible_projects(projects_json: dict) -> list[dict]: ...
def get_agent_name(key: str, prefs: Optional[dict]) -> str: ...
def get_accent(key: str, prefs: Optional[dict]) -> str: ...
def count_mcp() -> int: ...
def count_bots() -> int: ...
def project_color(key: str) -> str: ...
def build_picker_state(boot_ms: int) -> PickerState: ...
def parse_multi(pick: str, max_n: int) -> list[int]: ...

@dataclass
class PickResult:
    verb: str   # "numeric"|"general"|"auto-resume"|"new"|"rename"|"clear"|
                # "autonomy"|"full"|"quit"|"multi"|"default"|"unknown"
    keys: list[str] = field(default_factory=list)
    raw: str = ""

def resolve_pick(raw: str, state: PickerState) -> PickResult: ...
def banner_text(state: PickerState) -> list[str]: ...
def picker_text_rows(state: PickerState) -> list[str]: ...

@dataclass
class AgentModes:
    swarm: bool = False
    loop: bool = False
    loop_interval_s: int = 0

def prompt_agent_modes_from_env() -> AgentModes: ...
```

### 4.3 Lift-shift list from `eve.py`

| eve.py loc | Function | Goes to lib? |
|---|---|---|
| L66-80 | `enable_vt_on_windows` | NO (EVE-only) |
| L83-89 | `read_projects` | YES |
| L92-98 | `read_prefs` | YES |
| L101-104 | `visible_projects` | YES |
| L107-110 | `get_agent_name` | YES |
| L113-116 | `get_accent` | YES |
| L119-130 | `count_mcp` | YES |
| L133-137 | `count_bots` | YES |
| L140-151 | `banner` (renders) | NO (lib gives `banner_text`; EVE wraps ANSI) |
| L154-178 | `render_picker` (renders) | NO (lib gives `picker_text_rows`; EVE wraps ANSI) |
| L181-191 | `dispatch_project` | NO (EVE-only PS1 dispatch) |
| L194-203 | `dispatch_interactive` | NO (EVE-only PS1 dispatch) |
| L206-213 | `dispatch_multi` | NO (EVE-only) |
| L216-243 | `parse_multi` | YES |
| L246-301 | `main` | NO (EVE-only loop) |

After P2, `eve.py` becomes ~150 LOC (down from 306).

### 4.4 Library acceptance criteria

| # | Criterion | Smoke test |
|---|---|---|
| L1 | `read_projects()` returns same dict from both binaries | `assert eve_picker_lib.read_projects() == json.loads(PROJECTS_JSON.read_text('utf-8-sig'))` |
| L2 | `parse_multi('1,3-5,7', 14) == [1,3,4,5,7]` | unit test |
| L3 | `resolve_pick('1', state).verb == 'numeric' and .keys == ['sanctum']` | unit test |
| L4 | `resolve_pick('Q', state).verb == 'quit'` | unit test |
| L5 | Zero non-stdlib imports | AST scan |
| L6 | Import time <20 ms | `python -X importtime` |
| L7 | EVE.exe still <300 ms after lift-shift | `EVE.exe --profile` |
| L8 | RKOJ picker overlay opens within 60 ms | `QElapsedTimer` instrumentation |

---

## Section 5 — RKOJ feature uplift (10 sick-sick features)

Each row: actionable, testable, with acceptance criterion.

| # | Feature | Today | Sick-sick state | Effort | R-class | Acceptance test |
|---|---|---|---|---|---|---|
| 1 | In-panel project picker (Ctrl+P) | None | `QPickerOverlay` <60ms; 14 projects + verbs; Esc closes; numeric+Enter spawns inline | 8 hr | R2 | Ctrl+P → overlay paints <60ms (`QElapsedTimer`); type `1`+Enter → card appears; Esc closes; 5-run avg logged |
| 2 | Per-card swarm/loop chips | No visual indication | SWARM + LOOP chips in card header when env vars present | 3 hr | R2 | Spawn with `SINISTER_EVE_SWARM=1` → chip visible; click → toast; spawn without → no chip |
| 3 | Per-project color swatch in picker | No color cues | 8x8 dots using `_PROJECT_COLORS` (lifted into lib) | 2 hr | R1 | 14 rows render 14 dots matching `agents_tab._PROJECT_COLORS` |
| 4 | Multi-spawn with 400ms stagger | None | Picker accepts `1,3,5` → 3 cards with 400ms gap | 3 hr | R2 | Type `1,2,3`+Enter → 3 cards in ~1.2s; 3 fresh heartbeats |
| 5 | `/eve` slash command | None | Type `/eve` in any card → picker overlay opens | 1 hr | R1 | Registry row added; `/eve` triggers `picker_overlay.show()` |
| 6 | `/spawn <key>` and `/swarm <k1,k2>` slash | None | `/spawn rkoj` spawns rkoj card; `/swarm a,b,c` multi-spawns | 3 hr | R2 | `/spawn sinister-panel` → new card; `/swarm rkoj,sanctum` → 2 cards |
| 7 | Picker boot-ms self-report | None | Banner shows `boot N ms`; logs to baseline file once per session | 2 hr | R2 | First overlay open writes row to `script-runs/rkoj-picker-boot-baseline.json`; 5 invocations <60ms |
| 8 | Resume picker blended into overlay (A) | Separate modal | `A` opens existing `SavedSessionsPicker` directly | 1 hr | R1 | Type `A` → resume modal opens; pick session → card opens with `--resume` |
| 9 | Per-card "Clone-as-EVE-pick" button | `/clone` exists command-only | `↻` icon in card header → opens picker pre-filled to card's project | 2 hr | R1 | Click icon → overlay opens with default = card's project_key |
| 10 | Keyboard-only ergonomics | N/A | Arrow up/down navigates; Tab cycles verbs; Enter dispatches; `?` shows help | 4 hr | R2 | 5 sequential picks in <10s keyboard-only; `?` shows help block |

**Total effort:** ~29 hr single-thread; ~15 hr wall-clock with parallel agents.

**Justification per row:** Rows 1/3/7/10 = direct EVE.exe parity. Rows 2/9 = visibility win. Rows 4/6 = multi-spawn parity. Rows 5/8 = slash command vocab.

---

## Section 6 — Anti-features (what NOT to do)

1. Don't add picker UI redundantly in every RKOJ tab. One canonical surface.
2. Don't make EVE.exe depend on Qt. (~80 MB binary + 500-800 ms cold-start regression.)
3. Don't replace RKOJ's existing agent cards. Picker spawns INTO that surface.
4. Don't ship "sick sick" features that haven't passed acceptance test. Per no-bullshit doctrine Rule 1.
5. Don't add features the operator hasn't explicitly asked for.
6. Don't reimplement Launch-Session inside RKOJ. PS1 owns mintty/bash/trust; RKOJ has agent-level parity already.
7. Don't bypass canonical-protections doctrine. Picker spawns still respect `_pretrust_project` + `--dangerously-skip-permissions`.
8. Don't make the overlay modal-blocking. Operator can multi-spawn then dismiss.
9. Don't pull `claude` invocation into the lib. Spawn is per-surface.
10. Don't bump `eve_picker_lib` schema-version on additive changes.
11. Don't ship overlay without Esc working. Acceptance test row.
12. Don't auto-fall-back to picker on EVE.exe crash. Crash should be visible.

---

## Section 7 — Phasing

| Phase | What | Effort | R-class | Owner | Verb at close |
|---|---|---|---|---|---|
| **P1** | Ship `tools/eve-picker/`; lift functions from `eve.py`; 3 smoke tests | 4 hr | R1 | EVE-Sanctum | smoke-tested |
| **P2** | Refactor `eve.py` to import lib; rebuild EVE.exe; verify `--profile` <300 ms; all 14 projects launch | 2 hr | R2 | EVE-Sanctum | acceptance-tested |
| **P3** | Add `picker_overlay.py` to RKOJ; wire Ctrl+P + sidebar + header chip; verbs 1, 2, 8, 9, 11 | 8 hr | R2 | RKOJ | smoke-tested |
| **P4** | Wire verbs 3, 4, 5, 7 (A/N/R/S) + multi-select | 6 hr | R2 | RKOJ | smoke-tested |
| **P5** | Swarm/loop chips; `/eve`, `/spawn`, `/swarm` slashes; clone-as-EVE button | 5 hr | R2 | RKOJ | smoke-tested |
| **P6** | Acceptance pass for all 10 features; update brain `_INDEX.md` + `jcode-feature-matrix.md`; archive plan | 3 hr | R1 | EVE-Sanctum | **shipped** |

**Total: ~28 hr single-thread; ~16 hr with 2 parallel lanes.**

P1 → P2 sequential. P3-P5 sequential within RKOJ lane. P6 gate.

---

## Section 8 — Operator-gated decisions

| Q | Decision | Recommendation |
|---|---|---|
| 1 | Approve shared library at `tools/eve-picker/`? | YES |
| 2 | Approve adding picker UI inside RKOJ (additive only)? | YES |
| 3 | Approve swarm/loop chips in agent cards? | YES |
| 4 | Approve `Ctrl+P` as picker trigger? | YES (no conflict found) |
| 5 | `tools/` placement vs `projects/eve-picker/`? | TOOLS (no UI, library shim) |
| 6 | `--paths` PyInstaller flag vs copy-at-build? | --paths |
| 7 | Sidebar nav: EVE above or below Agents? | ABOVE |
| 8 | Auto-add slash commands to `SLASH_COMMANDS` registry? | YES |
| 9 | Multi-spawn stagger: keep 400ms or RKOJ-tune? | KEEP 400ms |
| 10 | Acceptance bar for "sick sick": acceptance-tested or smoke-tested? | acceptance-tested |

---

## Section 9 — Composability

Composes with:

1. `eve-exe-launcher-jcode-speed-parity-2026-05-23`
2. `rkoj-introspection-cluster-v1.6.45-56-2026-05-22` (Pattern #1: Card → AgentsView signal fan-out)
3. `rkoj-runtime-ergonomics-cluster-v1.6.37-44-2026-05-22` (Pattern #6: extract-method discipline)
4. `rkoj-session-continuity-pattern-2026-05-21` (UUID per pane; A verb honors)
5. `rkoj-phase1-memory-bootstrap-2026-05-21` (picker doesn't bypass `_bootstrap_agent_memory`)
6. `rkoj-project-shape-promotion-2026-05-21` (lib stays in `tools/`, doesn't promote)
7. `rkoj-stream-json-jcode-parity-2026-05-22` (picker-spawned cards inherit stream-json)
8. `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (verbs throughout)
9. `do-not-revert-operator-canonical-protections-2026-05-23` (P1-P9 still PASS after spawn)
10. `forever-expanding-modular-architecture-doctrine` (disk-first state canonical)
11. `eve-exe-completion-2026-05-23T1230Z/eve-exe-finish-plan.md`

---

## Section 10 — Done definition (final)

The integration is **shipped** when:

1. `tools/eve-picker/eve_picker_lib.py` exists, stdlib-only, <20 ms cumulative import.
2. EVE.exe rebuilt + still <300 ms cold-start (operator-measured).
3. RKOJ.exe has picker overlay, opens via Ctrl+P / sidebar / header chip.
4. All 22 EVE.exe verbs work in RKOJ side.
5. Swarm/loop chips visible per card when env vars set at spawn.
6. New slash commands `/eve`, `/spawn <key>`, `/swarm <list>` registered + auto-help listed.
7. Per-card clone-as-EVE button works.
8. All 10 sick-sick features (Section 5) have PASS rows in PROGRESS.
9. `jcode-feature-matrix.md` row added.
10. Brain `_INDEX.md` row added.
11. Plan archived to `_shared-memory/plans/_archive/eve-into-rkoj-integration-2026-05-23T1330Z/`.
12. Operator-verified: no regression in EVE.exe standalone; no regression in RKOJ pre-existing spawn path; new picker overlay opens <60 ms first-paint.

If any of 1-12 has no evidence row in end-of-turn summary, verb is `acceptance-tested` (or lower), NOT `shipped`.

---

## Critical files for implementation

- `D:\Sinister Sanctum\automations\eve-launcher\eve.py` (existing scaffold; lift-shift target P1/P2)
- `D:\Sinister Sanctum\projects\rkoj\source\sinister_rkoj_qt\agents_tab.py` (existing; reused for spawn; extended with chips in P5)
- `D:\Sinister Sanctum\projects\rkoj\source\sinister_rkoj_qt\app.py` (existing; new Ctrl+P shortcut + `_open_picker_overlay()` wiring in P3)
- `D:\Sinister Sanctum\projects\rkoj\source\sinister_rkoj_qt\dialogs.py` (existing NewAgentDialog + SavedSessionsPicker; extended with Rename + Autonomy modals in P4)
- `D:\Sinister Sanctum\tools\eve-picker\eve_picker_lib.py` (NEW in P1)

Files referenced (not modified):
- `state.py` (L96-118 `load_projects`)
- `header.py` (L42-50 CHIP_SETS extension)
- `automations/session-templates/projects.json` (v7)
- `automations/session-templates/agent-prefs.json` (v2)
- `automations/eve-launcher/build-eve-exe.bat` (PyInstaller wrapper; gets `--paths` in P2)

---

*End of plan.*
