# Brain Entry :: sinister_loop_core.py — unified looper primitive (2026-05-26)

> Author: RKOJ-ELENO :: 2026-05-26
> Lane: `sinister-looper` (iter-24)
> Operator directive (verbatim 2026-05-26): *"C:\Users\Zonia\Desktop\Github Input review this and how jcode does looping and make the best fastest and most efficient looper we can"*
> Status: shipped + smoke-tested

## What shipped

`D:\Sinister Sanctum\automations\sinister_loop_core.py` — single-file Python
primitive (~450 LOC) consolidating the looping mechanics that were duplicated
across 6+ files in `automations/`. Import-friendly + has CLI for smoke / probe /
operator / demo subcommands. **NO new deps beyond stdlib.**

## Primitives (7)

| # | Class | Source-citation | Replaces |
|---|---|---|---|
| 1 | `AdaptiveScheduler` | jcode `scheduler.rs:188-247, 260-267` | (no equivalent — net-new) |
| 2 | `BackoffHelper` | openhuman `useDaemonLifecycle.ts:60-62` | (no equivalent — net-new) |
| 3 | `UsageLog` | jcode `scheduler.rs:18-136` (24h rolling) | (no equivalent — net-new) |
| 4 | `HeartbeatProbe` | unifies 3 readers | loop-relentless-watchdog.ps1:50-51, loop_open_agents.py:100-124, overseer_loop_quality_agent.py |
| 5 | `OperatorActive` | net-new (fail-open at sinister-operator.json) | (no equivalent — was missing) |
| 6 | `LoopGuard` | jcode `runner.rs:917-959` (forced-end) | (no equivalent — net-new) |
| 7 | `swarm_fanout()` | wraps `sinister_swarm.py` | direct subprocess scattered |

## Smoke-test evidence

```
$ python automations/sinister_loop_core.py smoke
SMOKE OK: AdaptiveScheduler + BackoffHelper + UsageLog + HeartbeatProbe +
          OperatorActive + LoopGuard all green.

$ python automations/sinister_loop_core.py demo
  tick 1: interval=2.0s  multiplier=1.0
  tick 2: interval=2.0s  multiplier=1.0
  -> simulating rate-limit hit
  tick 3: interval=4.0s  multiplier=2.0       # 2x backoff ON
  tick 4: interval=4.0s  multiplier=2.0
  -> simulating successful cycle
  tick 5: interval=2.0s  multiplier=1.0       # reset OK

$ python automations/sinister_loop_core.py probe sanctum
sanctum: age=1735.0s alive=True (fresh window 1800s)

$ python automations/sinister_loop_core.py operator
operator marker missing -> fail-open ACTIVE
```

## How sub-agents fed this iter (FILE:LINE evidence)

3 parallel Explore sub-agents ran concurrently (full-relentless swarm fan-out).

### SUB-A (`Github Input` audit) — top 5 ADOPT-NOW
1. **dexter-main** `agent.ts:24-25` — `MAX_OVERFLOW_RETRIES=2, MAX_ITERATIONS=10`
2. **openhuman-main** `useDaemonLifecycle.ts:60-62` — `BASE * 2^(attempt-1)` capped → **adopted into BackoffHelper**
3. **Decepticon-main** `health.go:46-77` — deadline-based polling
4. **9router-master** `tray.js:140-145` — SIGTERM→800ms→SIGKILL escalation
5. **ACE Framework** `layer.py:337-349` — `run_in_loop()` vs `run_via_events()` toggle

### SUB-B (jcode loop parity) — top 5 ADOPT-NOW
1. **scheduler.rs:188-247** AdaptiveScheduler.calculate_interval → **PORTED**
2. **scheduler.rs:260-267** on_rate_limit_hit / on_successful_cycle → **PORTED**
3. **scheduler.rs:18-136** 24h rolling UsageLog → **PORTED**
4. **runner.rs:917-959** forced-end retry → **PORTED** into LoopGuard
5. **response_recovery.rs:56-80** text-wrapped tool-call recovery → queued (P1)

### SUB-C (current stack audit) — top P0 issues
1. **Duplicate heartbeat readers** across `loop-relentless-watchdog.ps1:153-195` and `loop_open_agents.py:100-124` → **FIXED via HeartbeatProbe** (standardized 30-min fresh window)
2. **Duplicate checkpoint/revert** across 3 files → queued for next iter (checkpoint_manager.py)
3. **No operator-active check** — 24/7 burn → **FIXED via OperatorActive** (fail-open marker pattern)
4. **No jittered backoff** → **FIXED via BackoffHelper** (default jitter ±20%)
5. **Schtask 60s violates 270s cache window** → queued for next iter (jitter wrapper)
6. **6 PS1 files violate no-bat-no-ps1 doctrine** → queued: migration table emitted by SUB-C

## Telemetry sink (net-new)

Every primitive emits to `_shared-memory/looper-unified.jsonl` (best-effort
append-only) with structured rows: `{ts_utc, kind, ...fields}`. Kinds shipped:
- `rate-limit-backoff` (multiplier)
- `backoff-reset` (from_multiplier)
- `loop-guard-exit` (iters, duration_s, break_reason)
- `swarm-fanout-failed` / `swarm-fanout-missing`

This replaces 6+ scattered JSONLs (`quality-loop-log.jsonl`, `eve-training-loop.jsonl`,
`eve-crash-log.jsonl`, etc.) for the loop-mechanic class of events. Existing
JSONLs stay for their domain (training, crash) but loop telemetry now has a home.

## Why this is the fastest looper we can build (rationale)

- **No external deps** → import latency = stdlib only
- **AdaptiveScheduler** → only sleeps when budget allows; doubles wait on
  rate-limit (capped 64x); never wakes more than necessary
- **HeartbeatProbe.list_live()** → single `glob(*.json)` + mtime; O(n) where
  n = number of agent heartbeats (10s of files in practice)
- **OperatorActive fail-open** → no blocking IO when marker is missing
- **LoopGuard** → in-process context manager; no subprocess overhead
- **UsageLog.prune()** → atomic rewrite via tmp+replace; no lock contention
- **swarm_fanout()** → delegates to already-shipped sinister_swarm.py (which
  itself is jcode try_join_all parity per `loop-swarm-default-on-doctrine`)

## Migration path (per no-bat-no-ps1 doctrine)

P0 next-iter:
- `loop-relentless-watchdog.ps1` (437 LOC) → `sinister_watchdog.py` (import
  `sinister_loop_core.HeartbeatProbe`)
- `quality-monotonic-loop.ps1` (245 LOC) → `quality_loop.py` (import
  `LoopGuard` + `UsageLog`)

P1 next-iter:
- `cross-ref-loop.ps1` (332 LOC) → `cross_ref_audit.py` (add blocking enforcement
  via `LoopGuard.force_break("ceiling-hit")`)

## Composes with

- `loop-relentless-pursuit-2026-05-25` (rule 8: relentless tool-reach)
- `jcode-parity-loop-swarm-upgrades-2026-05-26` (extends ratchet)
- `we-have-the-source-read-it-doctrine-2026-05-25` (all 3 sub-agents READ source)
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` (this is the Python primitive
  to migrate .ps1 onto)
- `safe-quality-loops-doctrine-2026-05-24` (12 guardrails — LoopGuard enforces
  max_iters + max_seconds + progressless detection)
- `full-relentless-swarm-fanout-mindset-doctrine-2026-05-25` (3 parallel sub-agents
  this iter — ADOPT-NOW from each landed)

## Iter-25 P0 queue (next iter for sinister-looper lane)

1. **checkpoint_manager.py** — unify the 3 checkpoint/revert paths SUB-C flagged
2. **sinister_watchdog.py** — port loop-relentless-watchdog.ps1
3. **response_recovery** primitive — port jcode `response_recovery.rs:56-80`
4. **jittered schtask wrapper** — fix the 60s-cadence-violates-270s-cache issue
5. **operator heartbeat writer** — wire `start-sinister-session.ps1` to write
   `_shared-memory/heartbeats/sinister-operator.json` every 30s so the
   fail-open OperatorActive can actually go fail-closed
