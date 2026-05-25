<!-- Author: RKOJ-ELENO :: 2026-05-24 -->

<!-- decay:
  category: fact
  confidence: 0.9
  reinforcements: 0
  half_life_days: 180
-->

# Stale-State Reconciliation Pattern (analyzer gap-fill #3)

**Created:** 2026-05-24T23:00Z
**Authority:** Brain semantic-graph analyzer 2026-05-24T22:07Z (recommended this gap-fill); pattern observed in 4+ shipped automations across the fleet.

Generalizes the **"reconcile-vs-reality"** discipline used by 4+ Sanctum automations so future lanes have one canonical reference instead of re-inventing per-component.

---

## The pattern in one sentence

> **Local state (counters / leases / queue entries / lock files) is an OPTIMISTIC mirror of reality; on EVERY read or periodic tick, reconcile against the ground truth (process table / file mtime / disk presence) and stream-repair drift.**

## Why it exists

Multi-agent fleets accumulate stale state when processes crash, mintty windows close uncleanly, schedulers reboot, or operator force-quits a session. Without reconciliation, counters drift indefinitely (e.g. `current_sessions: 26` when only 3 claude.exe are alive) and stale locks block legitimate work forever.

## Four shipped implementations (extracted)

### 1. `automations/claude-accounts.ps1 :: Reconcile-AccountSessions`

- **Local state:** `current_sessions` integer per account in `_shared-memory/claude-accounts.json`
- **Ground truth:** `Get-Process claude.exe | Measure-Object | .Count`
- **Reconcile:** if `sum(current_sessions) != count(claude.exe) +/- 1`, snap each account to its actual share OR zero out leak
- **Trigger:** every `Get-NextAvailableAccount` call (self-healing on lease request)
- **Root-cause find:** `_shared-memory/claude-accounts.json` had grown to 1664 MB from runaway `_comment` concat; reconcile caught it + stream-repaired to 3.5 KB (1.66 GB reclaimed)

### 2. `automations/mesh-coordinator.ps1 :: -Action Sweep`

- **Local state:** lock files under `_shared-memory/mesh-locks/<focus>.json` with `expires_utc` TTL
- **Ground truth:** wall-clock time vs `expires_utc`
- **Reconcile:** remove any lock where `now > expires_utc`
- **Trigger:** `SinisterMeshCoordSweep` scheduled task every 10 min + manual `-Action Sweep` calls

### 3. `automations/heartbeat-sweep.ps1`

- **Local state:** per-slug heartbeat files in `_shared-memory/heartbeats/<slug>.json` with `last_update_utc`
- **Ground truth:** wall-clock time vs `last_update_utc` (fallback: file mtime)
- **Reconcile:** move heartbeats older than `-MaxAgeHours` (default 24) to `_archive/<yyyymmdd>/`
- **Trigger:** `SinisterToolAutotrigger` cron daily + on-demand `-Apply`
- **First production run reclaimed:** 25 stale heartbeats archived

### 4. `automations/link-ingest.ps1 :: Acquire-Lock` (sentinel-file pattern)

- **Local state:** `.queue.lock` sentinel file
- **Ground truth:** file mtime of sentinel
- **Reconcile:** if sentinel older than 10s, treat as stale + reclaim
- **Trigger:** every Add/Process call

## The canonical reconciliation skeleton

```powershell
function Reconcile-<State> {
    $localCount = (Get-LocalState).Count           # OPTIMISTIC
    $actualCount = (Get-GroundTruth).Count          # REALITY
    if ($localCount -eq $actualCount) { return $localCount }
    if (($actualCount - $localCount) -ge $TOLERANCE) {
        Write-AccountsLog "drift detected: local=$localCount actual=$actualCount" 'WARN'
        Snap-LocalState -To $actualCount             # STREAM-REPAIR
        return $actualCount
    }
}
```

**Three required components:**

1. **Read local + read truth** -- BOTH; never trust one.
2. **Tolerance** -- accept N+/-1 jitter (claude.exe spawn race / sentinel race).
3. **Stream-repair** -- write the corrected value INLINE; never queue for later.

## When to apply

| Trigger | Pattern |
|---|---|
| Local counter accumulating | Reconcile on every read of the counter |
| Lease / lock with TTL | Sweep on cron OR on next acquire |
| Per-file marker (sentinel / heartbeat) | Mtime check + auto-archive past threshold |
| Queue entries pending external processing | Reconcile against external state (process table / network / filesystem) |

## Anti-patterns

1. **Polling reconcile in a tight loop** -- bursty CPU; do it on read OR scheduled tick, never spin.
2. **Reconciling without tolerance** -- spawn-race jitter triggers thrash; +/-1 is the floor.
3. **Treating reconcile as authoritative without periodic re-check** -- ground truth changes between reads; refresh.
4. **Adding a NEW counter without a reconcile path** -- the bug that ate 1.66 GB before someone added Reconcile-AccountSessions.
5. **Hiding reconcile diff in logs only** -- when drift is large (3+ stddev), surface to operator queue OR fleet-update so operator can audit the underlying cause.

## Operator-actionable surfaces

```powershell
# Force-reconcile claude-accounts (heals counter drift)
powershell -File automations/claude-accounts.ps1 -Action Reconcile

# Force-sweep mesh-locks (purges expired)
powershell -File automations/mesh-coordinator.ps1 -Action Sweep

# Force-sweep stale heartbeats (with apply)
powershell -File automations/heartbeat-sweep.ps1 -MaxAgeHours 24 -Apply

# Status of all reconciliations (via tool-autotrigger)
powershell -File automations/tool-autotrigger.ps1 -Action Status
```

## Composes with

- `resource-refcount-cleanup-sleep-wake-doctrine-2026-05-24` (sibling's; THIS doctrine generalizes its reconcile-against-claude.exe pattern to ALL stale-state classes)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (mesh-coord Sweep is implementation #2 of this pattern)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 4 self-audit: reconcile IS the self-audit primitive)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R3 gradual: reconciliation prevents drift from accumulating)
- `brain-decay-implementation-schema-2026-05-25` (decay scoring + supersede is a SOFT reconcile pattern for knowledge state)

## Verification

```powershell
# Sample reconciliation in action
powershell -File automations/claude-accounts.ps1 -Action Status
# (If current_sessions != claude.exe count +/-1, next Get-NextAvailableAccount call self-heals)

powershell -File automations/mesh-coordinator.ps1 -Action List
# (Any lock past expires_utc gets purged on next Sweep)
```
