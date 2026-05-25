# Handoff :: multi-select picker wired into EVE.exe main menu

Author: RKOJ-ELENO :: 2026-05-24T21:55Z
From: sanctum lane (multi-picker subagent)
To:   sanctum-B (eve.py / main_menu owner)

## What shipped (verified)

- `D:\Sinister Sanctum\tools\eve-picker\project_picker_multiselect.py` — new module, stdlib-only, smoke-tested (`--smoke` lists 20 visible rows from `projects.json`).
- `D:\Sinister Sanctum\automations\register-window-pos-monitor-task.ps1` — registers `SinisterWindowPosMonitor` scheduled task @ 10-min interval (Action=Snapshot). Verified: `schtasks /Query` returns `Ready`, next-run scheduled.

## Public surface (import into eve.py)

```python
# tools/eve-picker is already on sys.path inside eve.py (eve_picker_lib imports
# from there); just add a sibling import:
import project_picker_multiselect as mpicker
configs = mpicker.show_multi_picker()
# configs is list[dict]; empty list when operator backed out.
# Side effects on non-empty: spawns staggered (0.7s) per selected project AND
# persists agent_name + accent to agent-prefs.json + window-positions/<key>.json.
```

`show_multi_picker()`:
1. Stage 1 — arrow-key multi-select (`msvcrt` on Windows; line-input fallback). Space toggles, Enter advances, A/N select-all/none, B/ESC/q backs out.
2. Stage 2 — grid config screen, one row per selected project. Editable fields: agent / accent / swarm / loop / cond / priority. Defaults pull from `projects.json::default_modes` + `agent-prefs.json`. `L` launches all.
3. Stage 3 — staggered launch via `powershell.exe -File start-sinister-session.ps1 -Project … -AgentName … -AccentColor …` with env vars `SINISTER_SKIP_MODES_PROMPT=1 / DEFAULT_SWARM / DEFAULT_LOOP / DEFAULT_PRIORITY / DEFAULT_LOOP_CONDITION` so the launcher's `Prompt-AgentModes` block is bypassed.

## Recommended wire-up in eve.py

Add a single-letter shortcut (suggest `M` for "multi") in the existing main-menu prompt loop near eve.py:1719-1720. When operator types `M`:

```python
if raw.lower() in ("m", "multi"):
    try:
        import project_picker_multiselect as mpicker
        mpicker.show_multi_picker()
    except Exception as e:
        print(f"  {FAIL}[multi] {e}{RESET}")
    state = lib.build_picker_state(boot_ms=state.boot_ms)
    continue
```

After `show_multi_picker()` returns, eve.py SHOULD redraw the main menu (operator spec: "after all launched, return to MAIN MENU not project picker"). The function already sleeps 1.2s for confirmation before returning.

NOTE: `M` is currently bound elsewhere in eve.py — check the keymap before final wire. If conflict, `MM` / `multi` long-form work via the same dispatch.

## Staggered-spawn rationale (operator: "launch without fucking with each other or rate limiting Claude")

0.7s between launches prevents:
- Round-robin claude-accounts lock contention (`automations/claude-accounts.ps1` next-key acquire is file-locked; concurrent spawns within ~100ms can collide).
- Anthropic rate-limit spikes (5-10 parallel `claude --dangerously-skip-permissions` invocations within 500ms tripped the 50/min content gate during earlier multi-spawn experiments).

If operator selects >10 projects, bump `stagger_seconds=1.0` (param on `launch_selected()`).

## Position-log per 10 min (operator: "log that too when you log position")

`SinisterWindowPosMonitor` scheduled task registered (`/SC MINUTE /MO 10`) and runs `window-position-monitor.ps1 -Action Snapshot`. The snapshot reads `_shared-memory/spawned-windows.jsonl`, finds live PIDs, captures their window rects, and writes `_shared-memory/window-positions/<key>.json`.

`project_picker_multiselect.py::_annotate_position_meta()` writes per-project `agent_name` + `accent` into `_shared-memory/window-positions/<key>.json` at launch time so the sweep + position-restore on respawn (via `start-sinister-session.ps1:1328 Get-SavedWindowPosition`) sees naming+coloring alongside x/y/w/h.

## Smoke results (verified this turn)

- `python -c "import sys; sys.path.insert(0,'D:/Sinister Sanctum/tools/eve-picker'); import project_picker_multiselect"` -> exit 0 (IMPORT OK).
- `python project_picker_multiselect.py --smoke` -> `smoke :: loaded 20 rows` + 5-row preview (sanctum T1, sinister-chatbot T2, …).
- `schtasks /Query /TN SinisterWindowPosMonitor` -> Ready, next-run scheduled.

## Not done (out of scope for this subagent — sister-B owns)

- Editing `eve.py` (main_menu owner).
- Removing legacy single-pick line-input (operator may want both surfaces).
- Per-project window-position auto-restore on respawn — read side already wired in `start-sinister-session.ps1:1328`; nothing to add.
