<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 1
  half_life_days: 180
-->
# Overseer agent doctrine

**Status:** hard-canonical 2026-05-24 (sanctum lane). Implementation shipped same turn: `automations/overseer-agent.ps1`.

**Operator verbatim (2026-05-24, ~20:20Z):** *"if agents get to a bad place or need to be reset have a overseer agent see this and fix stalled agents like they never closed in the first place."*

## What this is

A fleet-wide polling oversight script that classifies every spawned EVE session by heartbeat freshness + PID liveness, then either reaps the dead slot (refcount-correct decrement so account rotation reality matches the counter) or resurrects the lane from its latest resume-point so the agent comes back **like it never closed**.

This is the missing companion to `Reconcile-AccountSessions` — Reconcile drains leaked claude.exe leases on the *spawn* side, the overseer detects + recovers stalled agents on the *runtime* side. Both compose with the refcount-cleanup doctrine.

## State machine

State derived from MAX(heartbeat-age, PID-liveness):

| State | Heartbeat age | PID-liveness | Color | Action |
|---|---|---|---|---|
| **HEALTHY** | < 2 min | alive OR unknown | green | none |
| **SLOW** | 2-10 min | alive OR unknown | cyan | watch |
| **STALLED** | 10-30 min | alive OR unknown | yellow | candidate for Resurrect |
| **DEAD** | > 30 min | OR PID known + `Get-Process` returns nothing | red | Reap mandatory, Resurrect on operator/Watch trigger |

`PID-liveness=unknown` means there is no `spawned-windows.jsonl` row for the slug (e.g. legacy heartbeat or non-launcher spawn). Treated as "do not penalize for missing PID"; age alone decides the state.

## Actions

| Action | Reversibility | What it does |
|---|---|---|
| `-Action Scan` | read-only | Reads every `_shared-memory/heartbeats/*.json`, classifies, renders sorted-by-severity table + totals. Default action. |
| `-Action Reap` | non-destructive (additive field) | For every spawned-windows.jsonl row whose PID is gone AND `closed_at_utc` is missing, append `closed_at_utc` + `closed_by=overseer-agent`. Then call `claude-accounts.ps1 -Action Reconcile` so `current_sessions` matches live process count. |
| `-Action Resurrect -Slug <slug>` | non-destructive (re-spawn only) | Look up the slug's latest resume-point under `_shared-memory/resume-points/<display>/*.json`, resolve `project_key` (from resume-point.project field first, then projects.json fuzzy-match), respawn via `start-sinister-session.ps1 -Project <key>` so cold-start auto-loads the resume-point ("like they never closed"). |
| `-Action Watch -IntervalSec 60` | composes Scan+Reap on a timer | Loop with hard cap `-MaxIterations 10000`. Surfaces DEAD/STALLED candidates but does NOT auto-Resurrect (operator-gated to prevent thrash). Safe-exit on Ctrl+C. |
| `-Action Distribute -DistributeHours 24` (added 2026-05-25 iter 20) | non-destructive (additive inbox messages) | **ACTIVE fan-out of memory updates**: reads `_shared-memory/fleet-updates.jsonl` from last N hours + writes per-lane inbox messages `_shared-memory/inbox/<slug>/<UTC>-overseer-distribute-<id>.json` so EVERY agent gets active push (vs only passive poll on cold-start). Targeting: explicit `target_slugs` from fleet-update row OR keyword-match against 40 known lane slugs OR sanctum default. Dedup via `_shared-memory/overseer-distribute-log.jsonl` (no re-push of same source-id to same target). Scheduled task `SinisterOverseerDistribute` runs this every 30 min. Operator hard-canonical 2026-05-25T00:30Z verbatim: *"have the overseer running for sanctum and have him place the information to the correct polaces it needs to go so that all this will be used"*. |

## Reversibility

- **Scan** — pure read. No mutation.
- **Reap** — adds a `closed_at_utc` timestamp + `closed_by` to existing JSONL rows (atomic .tmp + Move-Item). The row itself is preserved. `Reconcile-AccountSessions` is already-reversible (clamps `current_sessions` to live count + cap). Both are append-style, no destructive ops.
- **Resurrect** — fires `start-sinister-session.ps1 -Project <key>` as a fresh process. Cannot delete files, cannot kill processes, cannot mutate the dead agent's branch. The new agent's cold-start picks up the latest resume-point as it normally would on any spawn.
- **Watch** — composition of Scan+Reap only. Does NOT auto-Resurrect — operator decides per-slug whether the dead agent should come back.

## Composes with

- `safe-quality-loops-doctrine-2026-05-24` (guardrail #8 heartbeat liveness — the loop watches heartbeats; this doctrine acts on them; guardrail #10 operator-interrupt — Watch surfaces DEAD/STALLED but lets operator drive Resurrect).
- `resource-refcount-cleanup-sleep-wake-doctrine-2026-05-24` — Reap is the third refcount-correctness primitive (after `Reconcile-AccountSessions` for `current_sessions` and `bot-lifecycle.ps1` for MCP bots). Closes the open item *spawned-windows.jsonl reaper* listed in that doctrine.
- `claude-accounts.ps1 :: Reconcile-AccountSessions` — Reap calls it directly so the `current_sessions` counter is brought into sync with live processes after each reaping pass.
- `start-sinister-session.ps1` — Resurrect respawns through the same launcher every spawn uses; resume-point auto-load happens for free.
- `detect-similar-agents.ps1` — shares the heartbeat-read pattern (parses `ts_utc` + filters by age); the overseer is the *write* / *act* counterpart to its read-only sister-detection.

## Anti-patterns (NEVER)

- Auto-Resurrect from Watch — a stuck slug + auto-resurrect = respawn loop. Operator decides.
- Killing the dead PID — the PID is already gone; mutating Windows process state on confirmation of absence is meaningless and risky.
- Mutating heartbeat files — the overseer is downstream of heartbeats; never reach back upstream.
- Reaping on a SLOW or STALLED row — Reap is only for PID-gone rows. Stalled-but-alive agents may just be busy on a long tool call.
- Treating `closed_at_utc` as authoritative without periodic re-Reap — file may grow back leaks if an agent crashes between Reap passes.

## Measurable pass criterion

- After `-Action Reap`, `sum(claude-accounts.json[].current_sessions)` matches `Get-Process claude | Measure-Object | %Count` within ±1 (transient lease).
- `Scan` produces a complete table (every `*.json` in `_shared-memory/heartbeats/` represented or skipped with reason) and exits 0 — smoke-test PASS 2026-05-24 (27 rows, 1 HEALTHY / 26 DEAD; correctly identified the live `sanctum-mesh-foundation` lane).
- `Resurrect -Slug sanctum` resolves `project_key=sanctum` and fires the launcher without error (validated via `Get-LatestResumePoint` + `Get-ProjectKeyForSlug` against projects.json v7).
- `Watch` honors `Ctrl+C` (try/catch wrap) and the hard `MaxIterations` cap.

## Smoke commands

```powershell
# Scan (read-only, expected: table, exit 0)
powershell -NoProfile -File automations\overseer-agent.ps1 -Action Scan

# Reap (writes closed_at_utc + calls Reconcile)
powershell -NoProfile -File automations\overseer-agent.ps1 -Action Reap

# Resurrect a specific slug
powershell -NoProfile -File automations\overseer-agent.ps1 -Action Resurrect -Slug sanctum

# Watch (60s interval, max 10000 iters, Ctrl+C to stop)
powershell -NoProfile -File automations\overseer-agent.ps1 -Action Watch -IntervalSec 60
```

Updated: 2026-05-24
