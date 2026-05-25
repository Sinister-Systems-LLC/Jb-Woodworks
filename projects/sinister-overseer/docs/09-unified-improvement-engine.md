<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 09 :: Unified Improvement Engine (the compilation doc)

> Operator hard-canonical 2026-05-24 ~23:55Z verbatim: *"in the overseer add all things for improving like the contradiction system and like the analyzer you used here ... complie it all into one thing and expand it"*.

> Sibling docs: `01-architecture.md` (component layout), `02-token-efficiency.md` (cost cap math), `03-watch-architecture.md` (event pipeline), `05-fails-to-learn.md` (lessons store), `06-cross-project-learning.md` (cross-aggregator), `08-contradiction-engine.md` (adversarial self-test).
> Brain doctrine: `_shared-memory/knowledge/overseer-unified-improvement-engine-2026-05-24.md`.
> Config: `config/improvement-recipe.json`.

## What this doc is

The Sinister Overseer ships SIX subsystems that, on their own, each address one slice of "improve the fleet". This doc is the COMPILATION -- it explains how the slices fit together into one engine the operator can reason about as a single unit.

The slices:

| # | Slice | Code | Doc |
|---|---|---|---|
| 1 | Sensors | `src/overseer/sensors/analyzer.py` | this doc + `03-watch-architecture.md` |
| 2 | WatchBus | `src/overseer/sensors/analyzer.py` (`SensorBus`) | this doc |
| 3 | Detector | `src/overseer/detector.py` (sibling P0 stub) | `03-watch-architecture.md` |
| 4 | Triage | `src/overseer/triage.py` (sibling P0 stub) | `03-watch-architecture.md` |
| 5 | Contradiction Engine | `src/overseer/contradiction.py` | `08-contradiction-engine.md` |
| 6 | Proposer + ApplyGate + LessonsStore + CrossProjectAggregator | `src/overseer/proposer.py` + `gate.py` + `lessons.py` (sibling stubs) | `04-per-project-adapters.md` + `05-fails-to-learn.md` + `06-cross-project-learning.md` |

## The pipeline in one diagram

```
+---------------------------------------------------------------+
|                       SENSORS  (cheap-tier)                   |
|                                                               |
|  TokenAnalyzer  UsageMeter  ForeverImprove  Heartbeat  Commit |
|       |             |             |              |       |    |
|       +------+------+------+------+------+-------+-------+    |
|              v                                                |
|                          [ WatchBus ]   <-- dedup, fan-out    |
|                              |                                |
+------------------------------|--------------------------------+
                               v
                       +---------------+
                       |   Detector    |  cheap-tier (Haiku)
                       |  classify     |  -> Event type + lane + severity
                       +-------+-------+
                               |
                               v
                       +---------------+
                       |    Triage     |  medium-tier (Sonnet)
                       |  diagnose +   |  -> root cause + proposed FixProposal
                       |  propose      |
                       +-------+-------+
                               |
                               v
                  +-------------------------+
                  |  Contradiction Engine   |  cheap-tier counter-args
                  |  (counter-arg + score)  |  medium-tier on hold + adversarial
                  +------------+------------+
                               |
            +------------------+------------------+
            | verdict=rollback | verdict=hold     | verdict=escalate
            v                  v                  v
       LessonsStore       re-reason         OperatorInbox
            |             at medium               |
            |             ----------+             |
            |                       |             |
            +-----+   verdict=apply <-----------+ |
                  v                                v
            +------------+                  (operator decision)
            |  Proposer  |  high-tier (Opus) ONLY on hard-reasoning rebuilds
            +-----+------+
                  v
            +------------+
            | ApplyGate  |  low-risk -> auto; high-risk -> operator inbox
            +-----+------+
                  v
            +------------+
            | LessonsStore |  win + loss rows; consulted before next propose
            +------+-------+
                   |
                   v
        +-----------------------+
        | CrossProjectAggregator|  lessons fan-out to similar adapters
        +-----------------------+
```

## The pipeline in 8 lines (operator-readable)

1. Sensors poll existing Sanctum scripts (`token-analytics.ps1`, `claude-usage-meter.ps1`, `forever-improve.ps1`, heartbeats, commit deltas) on configured cadences.
2. Each sensor emits typed events onto the `WatchBus`, which de-duplicates + fans out to subscribers.
3. The Detector classifies each event (cheap-tier) into event-type + affected lane + severity.
4. Triage (medium-tier) diagnoses root cause and drafts a `FixProposal` with risk + diff summary + evidence.
5. The Contradiction Engine asks 3 counter-argument questions (cheap-tier); high score -> rollback; conflict -> escalate; mid score -> hold + re-reason.
6. Survivors go to the Proposer (high-tier ONLY when needed) which finalizes the diff.
7. ApplyGate auto-applies low-risk; routes high-risk to the operator inbox.
8. Every outcome (win or loss) is written to LessonsStore; the CrossProjectAggregator fans transferable lessons to similar adapters.

## The contradiction engine in 3 lines

1. **Per fix**, score 0-10 via 3 counter-argument questions; rollback above threshold (default 6), hold at 4-6, apply at 0-3.
2. **Per quarter (or on demand)**, re-examine every applied fix for hindsight regressions; emit `Regression` rows.
3. **Per fix**, detect cross-project invariant collisions; any collision forces `escalate` to operator.

## Sensors wired (this iter)

| Sensor class | Wraps existing script | Default poll cadence | Emits |
|---|---|---|---|
| `TokenAnalyzerSensor` | `automations/token-analytics.ps1 -Action Json` | 60 min | `WasteEvent`, `RecommendationEvent` |
| `UsageMeterSensor` | `automations/claude-usage-meter.ps1 -Mode Json` | 5 min | `UsageHighEvent` |
| `ForeverImproveSensor` | `automations/forever-improve.ps1 -Action Tally -Json` | 30 min | `RotInLogEvent` |

Sibling sensors planned (`HeartbeatSensor`, `CommitDeltaSensor`, `WatchdogSensor`) live in P2 -- they slot onto the same `SensorBus` with no architectural change.

## Recipe-driven, per-project

Each attached lane gets a `config/improvement-recipe.json` row describing WHAT counts as an improvement in that lane and HOW the engine should respond. Example: `sinister-sleight` (trading bot) measures improvement as walk-forward Sharpe delta; `sinister-chatbot` measures improvement as response-quality regression vs `_shared-memory/operator-utterances.jsonl`; `eve-compliance` measures improvement as confusion-matrix shift in the image-scanner. The engine pipeline is identical; the SIGNALS the sensors emit + the FIX TEMPLATES the Triage stage draws from differ per recipe.

## Cost model (composes with `docs/02-token-efficiency.md`)

| Stage | Tier | Approx tokens / call | Approx calls / day / lane |
|---|---|---|---|
| Sensor poll | n/a (subprocess) | 0 LLM tokens | 96 (every 15 min avg) |
| Detector | cheap (Haiku) | ~500 in / 100 out | 1 per emitted event (~20-50 / day) |
| Triage | medium (Sonnet) | ~3000 in / 500 out | 1 per high/medium severity (~5-10 / day) |
| Contradiction (per fix) | cheap (Haiku) | ~800 in / 150 out | 1 per FixProposal (~5-10 / day) |
| Contradiction (adversarial) | medium (Sonnet) | ~2000 in / 400 out | 1 per quarter per past fix (~bursty) |
| Proposer | high (Opus) | ~5000 in / 1000 out | <= 1 / day / lane (rare hard-reasoning) |
| LessonsStore write | n/a (sqlite) | 0 | per outcome (~10-15 / day) |

Per-attachment budget cap = $5 cost-eq / day. Burn-projection at default cadence sits well below cap; sensors auto-throttle if the meter shows 80 percent of cap consumed before midnight UTC.

## Pass criterion

1. All sensor classes import + instantiate + `poll_all()` returns a `list` (smoke test PASS this turn).
2. The Contradiction Engine returns the documented verdict precedence (smoke test PASS this turn).
3. `improvement-recipe.json` schema is documented + 3 prepared recipes present (this turn).
4. P2 cron registers the adversarial cycle (every 90 days) + lessons-store write-back wired.
5. Cost cap honored end-to-end (verified via `claude-usage-meter.ps1` per-attachment row).

## What this doc does NOT cover

- Per-adapter implementation -- see `docs/04-per-project-adapters.md`.
- Token-tier routing rationale -- see `docs/02-token-efficiency.md`.
- Lessons schema -- see `docs/05-fails-to-learn.md`.
- Cross-project aggregator algorithm -- see `docs/06-cross-project-learning.md`.

This doc is the OPERATOR'S MAP of how the slices compose. The slice docs are the implementer's truth.
