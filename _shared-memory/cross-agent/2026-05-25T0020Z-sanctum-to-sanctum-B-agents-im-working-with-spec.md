# Cross-agent: Sanctum-A -> Sanctum-B :: "Agents I'm Working With" sub-page spec

> **Author:** RKOJ-ELENO :: 2026-05-25T00:20Z
> **From:** Sinister Sanctum (lane A, eve-launcher branch)
> **To:** Sinister Sanctum (lane B, sister)
> **Status:** SPEC -- stub shipped; sister-B owns full implementation
> **File touched (this turn):** `tools/eve-picker/main_menu.py`
> **Smoke-tested:** `python main_menu.py --smoke` -> 8 items render in new
> order, footer hint updated, no parse errors.

## Operator directive (verbatim 2026-05-25T00:15Z)

Operator rebranded the K) Kill Fleet menu item to "Agents I'm Working With"
(key = W). Top-level menu now reads:

```
R) Resume Project        - pick a project + spawn
A) Auto Resume           - last project + last agent
G) General Agent         - no project scope
T) Tools                 - automations / health / mesh
N) New Project           - scaffold a new lane
M) Account Manager       - add / login / logout / usage
W) Agents I'm Working With  - active sessions + sister-coord
X) Exit
```

## What lane A shipped this turn (stub, but useful)

`_agents_working_with_action()` in `main_menu.py` (lines ~836-873) currently:

1. Prints `[W] agents-im-working-with: NOT YET IMPLEMENTED -- sister B owns;`
2. Runs `kill-fleet.ps1 -Mode Soft -WhatIf` to LIST live agents (no kills)
3. Waits for Enter, returns to menu

This is operator-actionable as a preview while sister-B builds the full page.

## What lane B owns (full sub-page)

Replace `_agents_working_with_action()` with an interactive sub-page that:

### 1. Discover live agents

Source data combines:

- **`_shared-memory/heartbeats/*.json`** -- per-agent heartbeats (mtime
  within last 5 min = live). Each heartbeat already has
  `agent` / `agent_display` / `slug` / `project` / `account` / `pid` fields.
- **`automations/spawned-windows.jsonl`** (append-only) -- each row records
  spawn events: `{ ts, pid, project, agent, account, mintty_pid }`.
  Cross-reference live heartbeats against most-recent spawn rows per slug.
- **Live-PID filter** -- on Windows, `Get-Process -Id $pid` to confirm the
  mintty + claude PIDs are still running (handles crashes the heartbeat
  hasn't expired yet).

### 2. Row format

```
<idx>  <agent_display> @ <project>   pid=<pid>   age=<min>m   account=<label>
```

Sorted by age ascending (newest at top). Show up to ~20; paginate beyond.

### 3. Per-row actions (single-letter, like the main menu)

- **K** = kill that specific agent (call into `kill-fleet.ps1 -Mode Hard
  -OnlyPid <pid>` -- sister-B may need to add `-OnlyPid` flag to the script;
  fallback `taskkill /F /PID <pid> /T`).
- **R** = raise that window to foreground (Windows `user32.dll
  SetForegroundWindow` via ctypes against the mintty PID's window handle).
- **M** = send a cross-agent inbox message to that agent. Open a text prompt;
  write to `_shared-memory/inbox/<slug>/<ts>-from-sanctum-<topic>.json` with
  `{ from_slug: "sanctum", to_slug: "<slug>", subject, body, ts }`.

### 4. Bottom actions (after the list)

- **A** = Kill All (calls existing `_kill_fleet_action()` -- already exported
  in main_menu.py, kept available for this purpose).
- **B** = Back to main menu.

### 5. Refresh

- **F5** or **r** = re-scan heartbeats + spawned-windows.
- Auto-refresh every ~5 sec while sub-page is open (use the
  `_read_choice_animated_live` pattern in main_menu.py as a reference --
  poll msvcrt.kbhit() at 3 FPS + re-scan timestamp).

## Callback wiring contract

`show_main_menu()` already routes `w` through `cb.get("agents_working_with")`
falling back to `_agents_working_with_action`. Sister-B can:

- Either replace `_agents_working_with_action` in-place (preferred -- keeps
  the stub fallback co-located with the main menu module).
- Or inject via `callbacks={"agents_working_with": <new_fn>}` from eve.py
  if the implementation grows large enough to deserve its own module.

The `kill_fleet` callback key is also still accepted (back-compat) and the
`_kill_fleet_action` symbol is still exported -- sister-B's sub-page can
import and call it directly for the "Kill All" bottom action.

## Files lane B should look at

- `tools/eve-picker/main_menu.py` -- the menu module (this file)
- `automations/eve-launcher/eve.py` -- the entry point that injects callbacks
- `automations/kill-fleet.ps1` -- existing kill script (sister-B may add
  `-OnlyPid` flag for per-row K action)
- `automations/spawned-windows.jsonl` -- spawn-event log
- `_shared-memory/heartbeats/*.json` -- live-agent indicator

## DO NOT

- DO NOT rebuild EVE.exe -- a parallel subagent is doing the final rebuild
  after all main_menu.py edits land.
- DO NOT change the main menu order or letter assignments without
  coordinating back through cross-agent inbox.
- DO NOT remove the stub fallback (`_agents_working_with_action`) until the
  real sub-page is shipped + smoke-tested.

## Compose with

- `_shared-memory/knowledge/eve-ui-uniformity-doctrine-2026-05-24.md`
  (HEADER + BODY + FOOTER canonical layout; use the same color tokens)
- `_shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md`
  (the dashboard-skeleton expand-not-fork rule -- but for terminal UI the
  eve-ui-uniformity doctrine is the closer match)

## Sign-off

Lane A's turn-close: `parse OK` + `smoke OK · _TICK=1 · cols=80`.
8 menu items render in spec order, W routes to stub preview, kill_fleet
back-compat preserved. Ready for sister-B to take ownership.
