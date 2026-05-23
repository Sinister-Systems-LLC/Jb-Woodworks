<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
# tools/eve-picker — shared picker logic for EVE.exe + RKOJ.exe

> **Status:** `smoke-tested` (P1 of `eve-into-rkoj-integration-2026-05-23T1330Z`).

Single-module library. Stdlib-only. Render-agnostic.

## What it does

Source-of-truth for picker behavior that EVE.exe (ANSI console) and RKOJ.exe
(PyQt6 in-panel overlay) both need:

| Concern | API |
|---|---|
| Filesystem readers | `read_projects()` / `read_prefs()` |
| Project enumeration | `visible_projects(projects_json)` |
| Per-project identity | `get_agent_name(key, prefs)` / `get_accent(key, prefs)` |
| Per-project color | `project_color(key)` (curated palette + HSV-from-hash fallback) |
| Environment counts | `count_mcp()` / `count_bots()` |
| State assembly | `build_picker_state(boot_ms, ...)` -> `PickerState` |
| Multi-select parse | `parse_multi('1,3,5', 14)` -> `[1, 3, 5]` |
| Verb resolution | `resolve_pick(raw, state)` -> `PickResult(verb=..., keys=[...])` |
| Render helpers (plain text) | `banner_text(state)` / `picker_text_rows(state)` |
| Agent-mode env-var read | `prompt_agent_modes_from_env()` -> `AgentModes(swarm, loop, loop_interval_s)` |

## What it deliberately does NOT do

- No ANSI escapes (EVE.exe wraps `picker_text_rows()` with color codes)
- No Qt imports (RKOJ wraps `picker_text_rows()` with QLabel rows)
- No subprocess / spawn logic (each surface owns its spawn path)
- No third-party dependencies (acceptance criterion L5)

## Callers

- `automations/eve-launcher/eve.py` — adds ANSI render + `subprocess.call(PS1)` dispatch
- `projects/rkoj/source/sinister_rkoj_qt/picker_overlay.py` (P3) — adds QWidget overlay + `AgentsView.spawn_agent()` dispatch

## Wiring

Both callers add this directory to `sys.path` (or PyInstaller `--paths`):

```python
import sys
from pathlib import Path
_EVE_LIB = Path(r"D:\Sinister Sanctum\tools\eve-picker")
if _EVE_LIB.exists() and str(_EVE_LIB) not in sys.path:
    sys.path.insert(0, str(_EVE_LIB))
import eve_picker_lib
```

## Acceptance (from plan Section 4.4)

| # | Criterion | Status |
|---|---|---|
| L1 | `read_projects()` returns same dict from both binaries | smoke-tested via shared fixture |
| L2 | `parse_multi('1,3-5,7', 14) == [1,3,4,5,7]` | unit-tested |
| L3 | `resolve_pick('1', state).verb == 'numeric' and .keys == ['sanctum']` | unit-tested |
| L4 | `resolve_pick('Q', state).verb == 'quit'` | unit-tested |
| L5 | Zero non-stdlib imports | AST-scanned |
| L6 | Import time < 20 ms | measured |
| L7 | EVE.exe still < 300 ms cold-start | deferred to P2 |
| L8 | RKOJ picker overlay opens < 60 ms | deferred to P3 |

## Tests

```bash
cd "D:\Sinister Sanctum\tools\eve-picker"
python -m unittest discover -s tests -v
```
