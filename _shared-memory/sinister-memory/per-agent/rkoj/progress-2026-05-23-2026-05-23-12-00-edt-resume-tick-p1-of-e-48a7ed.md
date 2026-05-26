---
format_version: 2
author: RKOJ-ELENO
slug: rkoj
heading_id: 2026-05-23-2026-05-23-12-00-edt-resume-tick-p1-of-e-48a7ed
saved_at: 2026-05-26T21:11:30Z
length: 3937
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# rkoj :: 2026-05-23 12:00 EDT — RESUME tick — P1 of eve-into-rkoj-integration shipped (smoke-tested) — `tools/eve-picker/` shared library + 34/34 tests PASS

Resume picked from `resume-points/RKOJ/2026-05-23T103728Z.json`. Plan `eve-into-rkoj-integration-2026-05-23T1330Z` Section 7 P1 (4hr R1) executed in one turn. P1 unblocks P2 (EVE.exe lift-shift) + P3 (RKOJ overlay).

### Ships this turn (smoke-tested per no-bullshit doctrine verbs)

| Surface | Effect |
|---|---|
| `tools/eve-picker/eve_picker_lib.py` (new, ~250 LOC) | Single-module library. Stdlib-only (acceptance L5 PASS via AST scan). API: `read_projects` / `read_prefs` / `visible_projects` / `get_agent_name` / `get_accent` / `project_color` (curated palette + HSV-from-hash fallback) / `count_mcp` / `count_bots` / `build_picker_state(boot_ms, projects_json, prefs)` / `parse_multi` / `resolve_pick` / `banner_text` / `picker_text_rows` / `prompt_agent_modes_from_env`. Dataclasses: `PickerRow` / `PickerState` / `PickResult` / `AgentModes`. Render-agnostic — returns plain text rows; callers wrap with ANSI or QLabel. |
| `tools/eve-picker/tests/test_parse_multi.py` (12 tests) | L2 canonical + edge cases (clamp, dedupe, malformed, whitespace, reversed-range). |
| `tools/eve-picker/tests/test_resolve_pick.py` (19 tests) | L1 visible-only + L3 numeric=sanctum + L4 quit + every verb (G/A/N/R/K/S/F/Q + multi + numeric + unknown + default + out-of-range). |
| `tools/eve-picker/tests/test_acceptance.py` (3 tests) | L5 AST-scanned imports (zero non-stdlib) + L6 import-time measured (subprocess.python -c) + live `build_picker_state()` round-trip against repo `projects.json`. |
| `tools/eve-picker/tests/fixtures/{projects.json,agent-prefs.json}` | Hermetic fixtures for L1/L3/L4 — visible-keys filter + per-project accent override. |
| `tools/eve-picker/README.md` + `.gitignore` | Tool-card. Status `smoke-tested`. |

### Test pass (evidence)

```
python -m unittest discover -s tests -v
... 34 ok, 0 fail
Ran 34 tests in 0.117s
OK
[live-build-state] 15 rows assembled in 1.04 ms
[import-time]      eve_picker_lib loaded in 17.90 ms
```

| Acceptance | Target | Measured | Verdict |
|---|---|---|---|
| L1 visible-keys filter | matches `projects.json` v7 | 3-row fixture round-trip + 15 rows live | PASS |
| L2 `parse_multi('1,3-5,7', 14)` | `[1,3,4,5,7]` | `[1,3,4,5,7]` | PASS |
| L3 `resolve_pick('1')` | `numeric` / `['sanctum']` | `numeric` / `['sanctum']` | PASS |
| L4 `resolve_pick('Q')` | `quit` | `quit` | PASS |
| L5 zero non-stdlib imports | AST scan | 0 offenders | PASS |
| L6 import time < 20 ms | warm 20 ms / ceiling 50 ms | 17.90 ms cold-subprocess | PASS |
| L7 EVE.exe < 300 ms after lift-shift | — | DEFERRED to P2 | — |
| L8 RKOJ overlay < 60 ms | — | DEFERRED to P3 | — |

### What did NOT change this turn (precise verbs)

- `automations/eve-launcher/eve.py` — **untouched**. Lift-shift refactor is P2, not P1. P1 is just the lib + tests.
- RKOJ source — **untouched**. Picker overlay is P3.
- `jcode-feature-matrix.md` — **untouched**. Row add is P6 gate.
- Brain `_INDEX.md` — **untouched**. Doctrine entry is P6 gate.

### Why P1 first (architectural justification)

P2 (eve.py lift-shift) and P3 (RKOJ overlay) BOTH depend on the lib existing. Shipping P1 standalone with comprehensive smoke tests means future agents can refactor eve.py against a verified contract — the 34 tests are the regression net for P2.

### Open in-lane (carried)

- P2: refactor `eve.py` to import lib; rebuild EVE.exe; verify `--profile` < 300 ms (acceptance L7) — 2 hr, R2
- P3: add `picker_overlay.py` to RKOJ; Ctrl+P shortcut; verbs 1, 2, 8, 9, 11 — 8 hr, R2
- P4/P5/P6 per plan Section 7
- Sinister-browser Layer C: Forge `/browser` slash + Term `/jcode-browser` alias — ~30 min when operator wants live firefox-bridge
- Mind.server `load_projects` BOM defense audit — ~5 min

### 5-check gate

✅ inbox is just the 15:45Z autonomy broadcast (no reply required); TaskList #1/#2 completed, #3 closing; PROGRESS appended; smoke-tested only — no fairy-tale `shipped` verb until P6 gate; resume-point write next.

---
