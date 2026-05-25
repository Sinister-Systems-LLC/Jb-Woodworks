<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Resource refcount + sleep/wake doctrine

**Status:** proposed 2026-05-24 (sanctum lane, /loop). Builds on the bot-fleet `wake-on-demand-bot-dispatcher-2026-05-23.md`.
**Operator verbatim (2026-05-24T19:14Z):** *"make sure when our agents are closed that everything that agent is using is closed as well. UNLESS another agent is using something from that. then you wait until its done then close. do that with all things like our local agents have them sleep, turn off overall just be efficient and then seamless awaken when they are needed"*

## TL;DR

- Every resource (claude.exe child, mintty window, scrcpy stream, vault daemon, panel daemon, bot subproc) gets a **refcount**. Owners bump it on use; cleanup decrements.
- On agent-close, the agent decrements all the refcounts it bumped. The resource is **kept alive while ref > 0**, **torn down at ref == 0**.
- Idle resources (ref == 0 for `IDLE_TTL` seconds) **sleep** (process suspended OR fully exited, depending on cost-to-wake).
- Wake is on first refcount bump; latency budget < 1 s for "warm-suspend" resources, < 3 s for "cold-exit" resources.

## Cleanup semantics

| Owner action | Effect |
|---|---|
| Agent X spawns resource R | `R.refcount += 1`, `R.owners += {X}` |
| Agent X dies / closes | for each R in `R.owners[X]`: `R.refcount -= 1` |
| `R.refcount == 0` | start `IDLE_TIMER`; on expire → tear-down |
| Agent Y bumps R while idle-timer running | cancel timer, refcount += 1 |

**Concrete cases — what fixes 19:14Z complaint:**

- **claude-accounts.json `current_sessions`** — was a refcount but no decrement on crash. Fixed 2026-05-24 by `Reconcile-AccountSessions` (counts live `claude.exe` and clamps; runs on every `Get-NextAvailableAccount` call). Snapshot bug: 26 leases vs 3 live processes.
- **`spawned-windows.jsonl`** — append-only log of spawned PIDs. Reconcile should mark `closed_at_utc` when PID dies. (Open work.)
- **mintty / scrcpy keepalive** — currently always-on (scheduled task). For lanes where the phone is unused, this is wasted RAM. (Open work: refcount on `phone-pickedup` events.)

## Sleep / wake states

| State | Resource alive? | Resume latency |
|---|---|---|
| **HOT** | yes, processing | 0 ms |
| **WARM** (idle 0-30 s) | yes, no traffic | < 50 ms |
| **SUSPENDED** (idle 30 s - 5 min) | process suspended (`SuspendProcess` on Win32) | ~200-500 ms |
| **COLD** (idle > 5 min) | process exited | 0.5-3 s (cold start) |

`HOT_NEVER_SLEEP = {sanctum-bus, custodian-restart-loop, sanctum-auto-push-30min}` — these wake fast OR have side effects on the schedule.

## Composing doctrines

- **bot-fleet wake-on-demand** (2026-05-23) — same pattern, applied to the 13 specialist bots. This doctrine generalizes it to claude.exe + mintty + scrcpy + vault.
- **canonical-11 reversibility** — sleep is reversible; cold-exit reclaims memory; refcount-zero is the trigger.
- **no-bullshit rule 5 (forever-upgrade)** — every refcount fix has a measurable acceptance criterion (leases-vs-live diff ≤ 1, or wake-latency ≤ budget).

## Implementation order (3 turns, smallest-first)

1. **Done 2026-05-24** — `Reconcile-AccountSessions` drains stale claude.exe leases. CLI: `powershell -File automations\claude-accounts.ps1 -Action Reconcile`. Auto-runs on every spawn.
2. **Next** — `spawned-windows.jsonl` reaper: scan rows, mark `closed_at_utc` for dead PIDs, prune rows older than 7 d.
3. **Next** — `sinister-bus` idle-suspend: 5-min idle → SuspendProcess; bot-call wakes via NtResumeProcess; cold-exit at 30 min.

## Anti-patterns (NEVER)

- Polling refcounts in tight loops (use evented bumps).
- Cold-exiting a resource an agent is *actively waiting on* (always check `refcount` AND `last_use < grace`).
- Killing a resource without notifying owners (use the disowner API so owners can adapt).
- Treating `current_sessions` (or any refcount) as authoritative without periodic reconcile against process reality.

## Measurable pass criterion

- `current_sessions` total across accounts == `Get-Process claude | Measure-Object | %Count` (allow ±1 transient).
- Bot-fleet idle RAM < 200 MB total when no agent active (currently ~1.5 GB always-on).
- Cold-wake of a SUSPENDED bot < 500 ms; cold-start a COLD bot < 3 s.

Updated: 2026-05-24
