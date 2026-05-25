<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# 05 — Roadmap

Six phases, P0 → P5. Each phase has measurable exit criteria.

## P0 — Scaffold + first entity (THIS ITER)

Status: **shipped (this iter)**

Deliverables:
- Project scaffold (folder layout, pyproject, .gitignore, .env.example).
- 7 docs: 00-overview / 01-entity-design / 02-color-palettes / 03-render-engine / 04-artistic-doctrine / 05-roadmap (this) / 06-sinister-os-integration.
- Engine skeleton (`engine.py`) — renders a frame string given (entity, palette, frame_counter, energy).
- Palette table (`palettes.py`) — 5 palettes for the 5 P0 entities (idle + high-energy each = 10 rows).
- Entity registry (`entities/__init__.py`) — sanctum loaded; others as TODO.
- One working entity file: `entities/sanctum.py`.
- CLI: `python -m sinister_term_themes demo sanctum --frames N` runs cleanly.
- 3 smoke tests: registry-loads / palette-loads / demo-doesn't-crash.

Exit criterion: `python -m sinister_term_themes demo sanctum --frames 5` exits 0 with visible ASCII output.

## P1 — Full entity catalog + multi-project demo

Deliverables:
- 4 more entity files: `entities/sinister_panel.py`, `entities/sinister_os.py`, `entities/snap_api_quantum.py`, `entities/sinister_sleight.py`.
- `python -m sinister_term_themes demo <key> --frames N` works for each.
- Palette blending implemented (HSV space lerp between idle and high-energy at given energy).
- A `--energy <0.0-1.0>` flag on the demo command for visual testing.

Exit criterion: each of the 5 entities renders 30 frames @ each of energy = 0.0 / 0.5 / 1.0 with visibly different palettes.

## P2 — Sidecar terminal + real energy

Deliverables:
- EnergyTap reads from a real source: stdin pipe or a tail of a Claude log file.
- Sidecar render mode: open a second terminal window (Windows Terminal pane / new conhost) and render there while the Claude session runs in the primary terminal.
- `--source stdin` / `--source pipe <path>` / `--source file <path>` CLI flags.
- Documentation of the operator's invocation: pipe Claude's output to Ancestral Remotion.

Exit criterion: with a real Claude session piped in, the entity's energy bar tracks Claude's actual byte-rate over a 1-minute window.

## P3 — Auto-detect project + auto-attach

Deliverables:
- Project auto-detect via env var (`SINISTER_ACTIVE_PROJECT_KEY`) set by `start-sinister-session.ps1`.
- EVE.exe menu entry to launch Ancestral Remotion in sidecar mode for the current project.
- Graceful palette/entity miss handling (unknown project → Sanctum fallback).

Exit criterion: spawning a Claude session via EVE picker for any project shows that project's entity automatically.

## P4 — Sinister OS embed surface

Deliverables:
- A documented IPC protocol so Sinister OS surfaces (dashboard tiles / status bar / wallpaper) can embed a render frame.
- A "frame producer" mode that emits ANSI frames to a unix socket / named pipe at 30fps, consumable by any OS surface.
- An example consumer in the Sinister OS prototype (per the lane's UI scaffold).

Exit criterion: a Sinister OS prototype dashboard tile shows a live Ancestral Remotion render of the currently-active project.

## P5 — Command-center hive-mind layout

Deliverables:
- Multi-entity grid: every active project's entity rendered as a tile in a single command-center surface.
- Aggregate energy: each tile's energy independently; a grand-total energy bar.
- "Look-at" affordance: clicking / focusing a tile expands it to fullscreen.
- Tony-Stark grade vibe: the operator sits in front of one surface and sees the entire fleet's living state at a glance.

Exit criterion: the operator can open one surface and see the entire fleet — every active agent's entity, every project's mood — in real time.

## Out of scope (for now)

- Sound synthesis.
- VR/AR overlays.
- Per-character cell-level animation (line-level is sufficient for the artistic doctrine).
- User-customizable palettes (the catalog is canonical through P3+).
