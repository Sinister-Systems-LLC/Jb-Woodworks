# Sinister Command Center + Loop/Swarm Default-On — Plan (iter-23 sub-4)

**Author:** RKOJ-ELENO :: 2026-05-25 (sanctum lane; sub-agent a3a1fbc5d34eddce7, persisted by sanctum master)
**Operator utterance:** 2026-05-25T06:33:48Z — *"think of how i can control, open, manage multiple claude agents at once in the most efficent manner you can come up with based on everything we have been building and our customs. make sure loop and swarm mode come on by deafult for each agent"*

Two atomic asks: (a) **command-center surface** to control N agents from one screen; (b) **loop=on + swarm=on default-true** at the spawn-flow layer.

## Current-state survey

- **40 live heartbeat slugs** in `_shared-memory/heartbeats/*.json`.
- **Spawn flow:** `Start-Sinister-Session.bat` → `automations/start-sinister-session.ps1` (2692 LOC).
- **Mode prompts** at `start-sinister-session.ps1:1385-1468 Prompt-AgentModes`. Defaults today: `swarm=$false` (l.1394), `loop=$true` (l.1395).
- **Per-project overrides:** `projects.json projects[].default_modes` — already populated `swarm=true` for 24/27 projects, `loop=true` for ALL 27.
- **Heartbeat schema** lacks `swarm`/`loop` fields — those live in `_shared-memory/agent-modes/<slug>.json` (only ~4 files).
- **W-key placeholder:** `main_menu.py:1112 _agents_working_with_action` currently runs `kill-fleet.ps1 -Mode Soft -WhatIf` and prints "NOT YET IMPLEMENTED". **The command center IS this missing W-key sub-page.**

## Operator overhead today (to find one stalled agent)

1. Task Manager → mintty PIDs.
2. `cat _shared-memory/spawned-windows.jsonl` → map PID→slug.
3. `cat _shared-memory/heartbeats/<slug>.json` → iter / focus / ts_utc.
4. `automations/fleet-health.ps1` for staleness.
5. To kill one: ALT-TAB OR `kill-fleet.ps1 -Mode Hard` (kills ALL).
6. To message one: hand-write JSON into `_shared-memory/inbox/<slug>/`.

## Proposed Command Center TUI (under EVE.exe W-key)

**Entry:** existing W-key (fills placeholder `main_menu.py:1112`).
**Module:** new `tools/eve-picker/command_center.py` imported by `eve-launcher/eve.py main()` callbacks.
**Uniformity:** header `--- Sinister Command Center ---`, footer `B) Back  X) Exit`, canonical color tokens only (PURPLE/DARKP/BRIGHTP/WHITE/SOFT/DIM/OK/WARN/FAIL).

### Dashboard layout (10 columns + bulk footer)

```
--- Sinister Command Center --- (tick 4s)

#  slug              display              acc  iter  last_event (60c trunc...)   hb_age  branch          L  S  st
1  sanctum           Sinister Sanctum     prp   23   iter-23 research swarm...    37s    agent/sin...     R  on  *
2  kernel-apk        Kernel APK           ylw    7   iter-7 detector clean...     82s    agent/ker...     R  on  *
...
bulk: (PA) poke all  (PL) poke loop=on  (KA) kill all  (KS) kill stale  (RA) restart all  (FA) follow all
per-row: digit -> select; then P/R/K/V/M/F/S/L
B) Back   X) Exit
```

### Per-row hotkeys (8)

| Key | Action | Dispatched via |
|---|---|---|
| P | poke | `agent-poke.ps1 -Action Poke -Slug <s> -Priority high` |
| R | restart (graceful close + re-spawn) | NEW `automations/agent-restart.py` |
| K | kill (Soft; Hard on 2nd press in <2s) | `kill-fleet.ps1 -Mode Soft -LauncherPid <pid>` |
| V | view progress (paged tail) | pure Python file read |
| M | message inbox (paged) | reuses `inbox-manifest-build.ps1` |
| F | follow tail (merged stream) | NEW `automations/agent-follow.py` |
| S | toggle swarm | NEW `automations/agent-modes-toggle.py --field swarm` |
| L | toggle loop | same script `--field loop` |

### Status icon

- `*` `hb_age <= 120s` AND iter changed last 5min — OK_GREEN
- `!` `hb_age <= 600s` AND same focus 3+ ticks — WARN
- `X` `hb_age > 600s` — FAIL
- `?` no heartbeat but PID alive — WARN

## Loop+swarm default-on plumbing

### JSON edits

1. **`automations/session-templates/agent-prefs.json`** — add top-level `"default_modes": {"swarm": true, "loop": true, "loop_relentless": true}`.
2. **`automations/session-templates/projects.json`** — add top-level `"fleet_default_modes": {"swarm": true, "loop": true, "loop_relentless": true}` fallback for future projects without `default_modes`.

### PS1 edit

3. **`automations/start-sinister-session.ps1:1394`** — flip hard-fallback `defSwarm` from `$false` to `$true`. Update precedence ladder comment to: (1) `projects[].default_modes` → (2) env `SINISTER_DEFAULT_SWARM`/`LOOP` → (3) `agent-prefs.json users[<email>].default_modes` → (4) `agent-prefs.json default_modes` → (5) hard-fallback `{swarm:true, loop:true}`.
4. **Prompt copy l.1424** — `[y/N]` → `[Y/n]` when `defSwarm=true`.

### Per-spawn override preserved

- Y/n prompt still fires unless `SINISTER_SKIP_MODES_PROMPT=1`.
- `--no-swarm` / `--no-loop` flags (`eve.py:29-30`).
- Command Center per-row S/L flips `agent-modes/<slug>.json` + drops `kind=mode-flip` inbox row.

### Heartbeat schema extension

Per-launch heartbeat writer (generated `launch.sh`) adds three fields: `swarm: bool`, `loop: bool`, `loop_relentless: bool`. Eliminates command center cross-reading `agent-modes/<slug>.json` per tick.

## New automations (5 Python files, no .bat/.ps1)

1. `tools/eve-picker/command_center.py` — TUI page; exports `show_command_center(callbacks=None)`.
2. `automations/agent-restart.py` — graceful close PID → re-invoke launcher with `SINISTER_RESUME_SLUG=<slug>` + `SKIP_MODES_PROMPT=1`.
3. `automations/agent-follow.py` — merged `tail -f` of heartbeat + PROGRESS + inbox; `--slug X` or `--all`.
4. `automations/agent-modes-toggle.py` — atomic-rename writer for `agent-modes/<slug>.json` + inbox `mode-flip` row; mesh-coord locks via subprocess.
5. `automations/command-center-live.py` — optional daemon (schtask) maintaining `_shared-memory/command-center-snapshot.json` every 2s.

## Existing-tool reuse (DO NOT re-invent)

`agent-poke.ps1` (P/PA/PL), `kill-fleet.ps1` (K/KA/KS), `fleet-health.ps1` (staleness seed), `loop-relentless-watchdog.ps1 -Action Status`, `mesh-coordinator.ps1 -Action Check`, `inbox-manifest-build.ps1` (M-key listing), `fleet-update.ps1 -Action List` (broadcast view), `_shared-memory/spawned-windows.jsonl` (PID↔slug), `_shared-memory/agent-modes/<slug>.json` (state fallback), `main_menu.py:_GLOW_BG_PALETTE` + `_EDGE_GLYPH_*` + `_highlight_row()` (visual consistency), `eve_ui.py` color tokens.

## Pass criterion (6 binary checks)

1. **W-key → command center, not stub.** `python tools/eve-picker/command_center.py --smoke` exits 0 + renders ≥3 mock rows.
2. **Every `heartbeats/*.json` slug shows up** within 5s of opening page (verify vs `ls _shared-memory/heartbeats/*.json | wc -l`).
3. **`swarm` AND `loop` default-true for brand-new project** with no `default_modes`. Test: `SKIP_MODES_PROMPT=1` + synthetic key → launch.sh exports `SINISTER_SWARM_MODE=1` AND `SINISTER_LOOP_MODE=1`.
4. **`agent-prefs.json default_modes` field exists** with `{swarm:true, loop:true, loop_relentless:true}` and is read by `Prompt-AgentModes` (grep test).
5. **Per-row S/L toggle produces TWO artifacts atomically:** updated `agent-modes/<slug>.json` + `inbox/<slug>/<utc>-mode-flip-<rand>.json`.
6. **Bulk `KA` requires 2-press confirm within 3s** — no accidental fleet wipe.

## Anti-patterns (DO NOT)

1. **Do NOT fork a separate TUI app.** EVE.exe is the single entry surface; command center is a W-key sub-page module.
2. **Do NOT block on `subprocess.run`.** Use `subprocess.Popen` so dashboard doesn't freeze on slow scripts.
3. **Do NOT bypass `mesh-coordinator.ps1 -Action Check`** before writing `agent-modes/<slug>.json`.
4. **Do NOT use destructive bulk actions without 2-press confirm** (KA/KS/RA).
5. **Do NOT introduce new color tokens.** Uniformity-doctrine PURPLE/DARKP/BRIGHTP/WHITE/SOFT/DIM/OK/WARN/FAIL only.
6. **Do NOT re-implement `agent-poke.ps1` / `kill-fleet.ps1` in Python.** Reuse via subprocess (ban is on NEW `.ps1`/`.bat`, calling existing OK).
7. **Do NOT auto-toggle swarm/loop based on heuristics.** Operator-initiated only.
8. **Do NOT silently swallow a failed kill.** Surface `FAIL: …` in dashboard row; don't remove row.

## Rollout phases

- **P0:** plumbing only (3 JSON edits + 1 PS1 hard-fallback flip + heartbeat-writer extension). Verify: new spawn shows `swarm=on loop=relentless` in window title. **Pass:** checks #3 + #4.
- **P1:** Command Center MVP (read-only dashboard, no actions). Wire W-key. **Pass:** checks #1 + #2.
- **P2:** per-row actions (P/R/K/V/M/F/S/L) + row-selection nav + 2-press destructive-confirm. **Pass:** checks #5 + #6.
- **P3:** bulk actions + filters (`/` text, T tier, O loop-on, E stale) + optional `command-center-live.py` daemon. Update `_shared-memory/knowledge/_INDEX.md` with `command-center-doctrine-2026-05-25.md`. **Pass:** all 6 + verified 5-agent end-to-end demo.

## Critical files for implementation

- `tools/eve-picker/command_center.py` (NEW)
- `tools/eve-picker/main_menu.py:1082-1190` (wire W-key callback)
- `automations/eve-launcher/eve.py` (~l.3637 — inject callback)
- `automations/start-sinister-session.ps1:1385-1468` (Prompt-AgentModes ladder)
- `automations/session-templates/agent-prefs.json` (top-level `default_modes`)
- `automations/session-templates/projects.json` (top-level `fleet_default_modes`)

(Full extended plan available in sub-agent transcript a3a1fbc5d34eddce7; this file is the actionable summary for execution iter.)
