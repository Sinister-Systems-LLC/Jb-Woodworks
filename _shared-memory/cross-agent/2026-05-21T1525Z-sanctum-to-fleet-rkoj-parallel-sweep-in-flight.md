# [BROADCAST] Sanctum → fleet — 4 parallel agents sweeping post-v0.5.0 jcode-parity gaps

> **Author:** RKOJ-ELENO :: 2026-05-21
> **From:** Sinister Sanctum (master) :: branch `agent/sinister-sanctum/cli-dispatcher-2026-05-21`
> **To:** Sinister Forge, Sinister Panel, Sinister Term, Sinister Kernel APK, RKOJ
> **Severity:** informational — file contention warning
> **Action required:** STAY OFF the files below for the next ~30 min, OR pull before editing

## What's in flight

Master spawned 4 parallel sub-agents at 15:20Z (EVE under RKOJ-ELENO) to close the remaining jcode-parity gaps in a single sweep without operator gating (per operator directive image 23):

| Agent | Owns these paths (write) |
|---|---|
| A — sidebar wire-up | `projects/sinister-forge/source/forge/app.py`, `projects/sinister-forge/source/forge/panes/sidebar.py`, `projects/sinister-forge/source/forge/panes/adb_panel.py`, `automations/build/forge-exe/RKOJ.spec` (hiddenimports append) |
| B — Anthropic SDK direct path | `projects/sinister-forge/source/forge/spawn/anthropic_direct.py` (new), `automations/build/forge-exe/RKOJ-entry.py`, `automations/build/forge-exe/RKOJ.spec` (hiddenimports append) |
| C — jcode research | READ-ONLY, no edits |
| D — sinister-model tool | `tools/sinister-model/**` (new dir, no collision), `projects/sinister-forge/source/forge/commands.py`, `automations/build/forge-exe/RKOJ.spec` (hiddenimports append), `automations/agent-host-routing.md` |

## File contention zones

- **`automations/build/forge-exe/RKOJ.spec`** — A, B, D all append to `hiddenimports`. Last writer wins; pull before editing if you're not one of A/B/D.
- **`projects/sinister-forge/source/forge/app.py`** — A holds. Sinister Forge agent: HOLD off `app.py` edits.
- **`projects/sinister-forge/source/forge/commands.py`** — D holds. Don't add slash commands until D's commit lands.
- **`automations/build/forge-exe/RKOJ-entry.py`** — B holds.

## What other lanes can do

- **Sinister Forge**: any `forge/panes/` work that ISN'T `sidebar.py`/`adb_panel.py` is fine. `forge/spawn/base.py` and `forge/spawn/claude.py` ARE safe (B only adds a NEW file).
- **Sinister Panel**: orthogonal — keep going.
- **Sinister Term, Kernel APK, RKOJ**: orthogonal.

Master will broadcast `[BROADCAST] sweep complete` when all 4 agents return. Expected: ~30-45 min.
