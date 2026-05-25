<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister Overseer :: Unified Improvement Engine (compilation doctrine)

> Operator hard-canonical 2026-05-24 ~23:55Z verbatim: *"in the overseer add all things for improving like the contradiction system and like the analyzer you used here ... complie it all into one thing and expand it"*.

## What it binds

The Sinister Overseer's improvement subsystems ship as ONE compiled engine, not six loose tools. Every improvement-class action (sensor poll, classify, diagnose, counter-argue, propose, apply, learn, cross-fertilize) lives in this engine. New improvement signals + fix templates EXPAND the engine (per `sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24` EXPAND-not-fork pattern, applied to logic instead of UI).

## The six slices (compiled)

1. **Sensors** -- `projects/sinister-overseer/src/overseer/sensors/analyzer.py` wraps existing Sanctum scripts (`token-analytics.ps1`, `claude-usage-meter.ps1`, `forever-improve.ps1`) + future siblings (heartbeats, commit deltas, watchdog) emit typed events.
2. **WatchBus** -- the `SensorBus` in `analyzer.py`: aggregates, de-duplicates, fans out.
3. **Detector** (`src/overseer/detector.py`) -- cheap-tier classify.
4. **Triage** (`src/overseer/triage.py`) -- medium-tier diagnose + draft `FixProposal`.
5. **Contradiction Engine** (`src/overseer/contradiction.py`) -- counter-arg + adversarial cycle + cross-project invariant check; verdict gates the proposer.
6. **Proposer + ApplyGate + LessonsStore + CrossProjectAggregator** (`src/overseer/proposer.py` + `gate.py` + `lessons.py`) -- high-tier rare; auto vs operator; lessons recorded; cross-project fan-out.

Per-project recipes live in `projects/sinister-overseer/config/improvement-recipe.json` (3 pre-attached prepared recipes: `eve-compliance`, `sinister-chatbot`, `sinister-sleight`).

## The pipeline in 8 lines

1. Sensors poll existing Sanctum scripts on configured cadences (5-60 min defaults).
2. Each sensor emits typed events onto the WatchBus, dedup + fan-out.
3. Detector (cheap-tier Haiku) classifies event-type + lane + severity.
4. Triage (medium-tier Sonnet) diagnoses + drafts FixProposal with risk + diff + evidence.
5. Contradiction Engine (cheap-tier counter-args; medium-tier on hold; medium-tier adversarial cycle quarterly) -- score above threshold rolls back; conflict escalates; mid score holds + re-reasons.
6. Proposer (high-tier Opus, RARE) finalizes diff only when triage punts to it.
7. ApplyGate auto-applies low-risk per recipe `auto_apply` rules; high-risk routes to operator inbox.
8. LessonsStore captures every outcome (win + loss); CrossProjectAggregator fans transferable lessons to similar adapters.

## Token-tier routing (per `docs/02-token-efficiency.md`)

| Stage | Tier | Why |
|---|---|---|
| Sensor poll | subprocess | zero LLM cost |
| Detector | cheap (Haiku-4.5) | classification is cheap-tier-suitable |
| Triage | medium (Sonnet-4.6) | diagnosis needs reasoning depth |
| Contradiction (per-fix) | cheap (Haiku-4.5) | 3 short questions, structured JSON |
| Contradiction (adversarial) | medium (Sonnet-4.6) | hindsight reasoning over historical context |
| Proposer | high (Opus-4.7) | reserved for hard-reasoning ONLY |
| LessonsStore | subprocess (sqlite) | zero LLM cost |

Per-attachment cap = $5/day cost-eq; recipe override per lane.

## Implementation status (P0 this turn)

- Scaffolded: 4 new files in `projects/sinister-overseer/` (`docs/08-contradiction-engine.md` + `docs/09-unified-improvement-engine.md` + `src/overseer/contradiction.py` + `src/overseer/sensors/analyzer.py`) + `tests/test_sensors.py` + `config/improvement-recipe.json` + `src/overseer/sensors/__init__.py` (re-exports).
- Smoke tests PASS this turn (3/3 in `test_sensors.py`).
- token-analytics.ps1 `-Action Json` verified returning valid JSON shape consumed by `TokenAnalyzerSensor`.
- Sibling-coordinated: mesh-coord lock registered + sibling's scaffold of README/CLAUDE/MISSION/docs/01-07/src/* preserved untouched; my additions are net-new files in untouched subdirs + APPEND-only edits to README + `_INDEX.md`.

## Live wiring milestones

| Phase | Deliverable | Done when |
|---|---|---|
| P0 (this iter) | Stubs + dataclasses + smoke tests | Verified above |
| P1 | Wire to OAuth-pooled cheap-tier client | `score_counter_argument` returns live 0-10 |
| P2 | adversarial_cycle live + lessons store write-back | Quarterly cron registered + lessons rows visible |
| P3 | Cross-project invariant DSL + adapter-declared invariants | Each adapter ships `INVARIANTS = [...]` |
| P4 | Recipe-driven fix templates auto-loaded into Triage | Triage stage reads recipe at startup |

## Pass criterion

1. All four new docs + 1 new JSON config ASCII-only (verified).
2. `python -m py_compile` clean on `contradiction.py` + `sensors/analyzer.py` (verified).
3. `python tests/test_sensors.py` PASS 3/3 (verified).
4. `automations/token-analytics.ps1 -Action Json` returns valid JSON with `scanned_at_utc` + `windows` + `by_project` fields (verified -- 306923 messages, 40 projects scanned at 2026-05-25T00:03:46Z).
5. Sibling's scaffold not clobbered (verified -- only ADDED net-new files + appended to README).

## Composes with

- `sinister-overseer-charter-2026-05-24` (sibling -- the project charter)
- `overseer-token-efficiency-doctrine-2026-05-24` (sibling -- the cost-cap math)
- `fails-to-learn-doctrine-2026-05-24` (sibling -- the lessons store schema)
- `contradiction-engine-doctrine-2026-05-24` (sibling -- the universal "contradict yourself" pattern)
- `token-efficiency-analytics-doctrine-2026-05-24` (the analyzer scripts the sensors wrap)
- `forever-improve-review-doctrine-2026-05-24` (forever-improve is itself a sensor in this engine)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (rule 7 -- past-tense verified events only)
- `mesh-coordination-and-resource-lifecycle-2026-05-24` (lock taken on shared file edits; lock released this turn)
- `gradual-growth-memory-push-eve-exe-ready-2026-05-24` (R1 + R2 -- this doctrine pushes to fleet-update + is EVE.exe-reachable via attached-projects recipe)

## Anti-patterns

1. Adding a new sensor without wiring it into the SensorBus (orphan sensor = no events emitted).
2. Bypassing the ContradictionEngine for "trivial" fixes (cost is bounded; engine ALWAYS fires).
3. Hard-coding fix templates inside Triage instead of recipe-driven (forks the engine per lane).
4. Letting recipes silently lower the contradiction threshold below 4 (anything below 4 means "rubber-stamp"; recipe diff requires operator-explicit-go per inbox).
5. Routing every lane to high-tier Opus by default (burns cost cap; defeats the routing).
6. Calling the engine "shipped" without smoke evidence (rule 1 + rule 2 of no-bullshit doctrine).

## Decay metadata

Category: `doctrine` (operator-stated).
Confidence: 1.0.
Half-life: 365 days.
Reinforcements: 1 (initial ship this turn).
