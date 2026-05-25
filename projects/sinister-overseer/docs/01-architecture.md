<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 01 -- Architecture (Sinister Overseer)

## High-level diagram (ASCII)

```
                                  +----------------------------------+
                                  |   EVE.exe Overseer menu          |
                                  |   (empty until operator attaches)|
                                  +-------------------+--------------+
                                                      |
                                       operator clicks "Attach Project"
                                                      v
+---------------------+      +---------------------+    +---------------------+
| Attached Project A  |      | Attached Project B  |    | Attached Project C  |
| (one watch loop)    |      | (one watch loop)    |    | (one watch loop)    |
+----------+----------+      +----------+----------+    +----------+----------+
           |                            |                          |
           +----------+ Signals +-------+--------+ Signals +-------+
                      v                          v
                +---------+               +---------+
                | EVENT   |               | EVENT   |
                |  BUS    |               |  BUS    |
                +----+----+               +----+----+
                     |                         |
                     v                         v
                +-------------+        +--------------+
                | DETECTOR    |        | DETECTOR     |
                | (Haiku-4.5) |        | (Haiku-4.5)  |
                +------+------+        +------+-------+
                       |                      |
                       v                      v
                +-------------+        +--------------+
                | TRIAGE      |        | TRIAGE       |
                | (Sonnet-4.6)|        | (Sonnet-4.6) |
                +------+------+        +------+-------+
                       |                      |
                       v                      v
                +-------------+        +--------------+
                | PROPOSER    |<------>| LESSONS DB   |
                | (Sonnet-4.6 |        | (per-project |
                | OR Opus-4.7)|        |  + global)   |
                +------+------+        +--------------+
                       |                      ^
                       v                      |
                +-------------+        +------+-------+
                | APPLY GATE  |------->| CROSS-PROJ   |
                | (auto-trivial OR     | AGGREGATOR   |
                |  operator-review)    | (daily run)  |
                +------+------+        +--------------+
                       |
                       v
              +-------------------+
              | TARGET PROJECT    |
              | mesh-coord lock + |
              | diff-before-write |
              | + reversibility   |
              +-------------------+
```

## Components (in detail)

### 1. EVE.exe Overseer menu

- New top-level menu entry. Empty list on first launch.
- "Attach Project" button -> picker -> selecting a project writes a row to `config/attached-projects.json` with `status=active` and spawns the watch loop.
- "Detach" button on a populated row -> stops the watch loop, sets `status=detached`.
- Populated rows expose a per-project sub-page (Outcome 2 in MISSION.md).
- Special launcher behavior: when operator picks `sinister-overseer` from Resume picker, EVE.exe asks "WHICH PROJECT would you like to begin overseer work for?" -- third-prompt question. Answer goes into `SINISTER_OVERSEER_TARGET_PROJECT` env.

### 2. Watch loop (per attached project)

- One LONG-RUNNING process per attached project. Not spawn-per-event.
- Polls signal sources at the project's configured cadence (5min chat / 30min file / 60min ML).
- Routes each signal through detector -> triage -> proposer -> apply gate.
- Heartbeats every 60s to `_shared-memory/heartbeats/sinister-overseer-<project-key>.json` so the fleet can see liveness.
- Honors per-attachment cost cap; downshifts model tier OR reduces polling cadence when approaching cap.

### 3. Adapter (per project type)

- Each project has an adapter class (in `src/overseer/adapters/`).
- Adapter declares: SIGNAL_SOURCES (where to look) + FIX_TEMPLATES (what fixes are pre-canonical) + AUTO_APPLY_RULES (what's safe to ship without operator) + ESCALATION_PATH (which cross-agent inbox to use when escalating).
- Adapter is plugged into the watch loop at attach time. Watch loop is generic; adapter is specific.
- Adapter REGISTRY in `src/overseer/adapters/__init__.py` -- maps project key -> adapter class.

### 4. Event bus (in-process)

- Lightweight publish-subscribe within the watch loop process.
- Signal sources are publishers; detector is the primary subscriber.
- No external queue (Redis / RabbitMQ); keeps deployment trivial. If we need cross-process later, swap to file-tail + sentinel-lock per existing fleet pattern.

### 5. Detector (Haiku-4.5)

- For each incoming signal: classify as {regression, anomaly, stall, drift, smell, cost-burn, doctrine-violation, user-data-signal}.
- Output: one short JSON row with classification + severity + cite-evidence-summary. Cheap-tier model.
- Cache the system prompt (stable per attachment); each call ships only the signal-diff. Diff-not-full-state policy.

### 6. Triage (Sonnet-4.6)

- For severity >= MEDIUM signals: produce a structured triage note (root cause hypothesis + 1-3 candidate fixes + risk ranking).
- LESSONS DB consulted BEFORE generating the triage; if a prior failure of the same shape exists, it's surfaced as context to the model.

### 7. Proposer (Sonnet-4.6 default; Opus-4.7 rare)

- For triaged candidate fixes: produce a concrete proposal (diff or config change OR a delegated instruction for the target lane's per-project agent).
- Opus-4.7 only fires for: multi-file architectural refactors OR cross-project transferable-pattern proposals (the rare hard-reasoning cases).
- Daily rate-limit per attachment on Opus-4.7 calls (default <= 5; tunable).

### 8. Apply gate

- Classifies each proposal: RISK_TIER in {trivial, low, medium, high, critical}.
- Per-tier action:
  - TRIVIAL (e.g. typo in doc) -> auto-apply after mesh-coord lock + diff-before-write
  - LOW (e.g. config flag flip with documented rollback) -> auto-apply after lock + 5-min observation window
  - MEDIUM (e.g. code change in non-critical surface) -> 4-hour operator-review window, then auto-apply if no objection
  - HIGH (e.g. credentials / production-deploy / financial / kill-switch) -> operator inbox row required; NEVER auto-applies
  - CRITICAL (e.g. fix that has failed 3+ times before; or production trading; or NCMEC reporting flip) -> operator inbox row REQUIRED + explicit "GO" signature
- Every apply ships with a REVERSIBILITY PLAN (git diff stash OR snapshot OR config rollback).

### 9. Lessons DB

- SQLite at `lessons.db` (gitignored).
- Per-project tables + a global `fleet_lessons` table.
- Schema (P1): symptom_hash (text), symptom_summary (text), attempted_fix (text), why_failed (text), lesson (text), suggested_doctrine_update (text), occurrences (int), first_seen_utc (text), last_seen_utc (text), risk_classifier_override (text nullable).
- Read by proposer; written by apply gate on failure.

### 10. Cross-project aggregator

- Scheduled task: runs daily.
- Scans `fleet_lessons` table for patterns that fired on >= 2 attached projects.
- Promotes transferable patterns to `_shared-memory/knowledge/overseer-lessons-<topic>-<date>.md` brain entries.
- Pushes promotion notice via `automations/fleet-update.ps1 -Action Push -Priority normal -Kind doctrine -Slug sinister-overseer`.
- Adapter registry consults aggregated patterns on every triage call (cached prompt prefix).

## Data flow examples

### Example 1 -- chatbot regression

1. ChatbotAdapter polls `/chatter` logs every 5 min.
2. Detects: P95 latency for model X jumped 800ms -> 2400ms over rolling 1h.
3. Detector classifies: regression, severity=MEDIUM.
4. Triage notes: probable cause = OpenRouter routing fallback firing; candidate fixes = (a) pin provider, (b) bump retry budget, (c) downshift to backup model.
5. Proposer drafts: config change to `OPENROUTER_PROVIDER_ORDER` env in chatbot's `.env`.
6. Apply gate: RISK_TIER = low (env config, documented rollback). Auto-apply after mesh-coord lock.
7. Post-apply observation: latency P95 returns to <= 1200ms within 5 min. Apply marked successful.

### Example 2 -- Sleight kill-switch state stuck

1. TradingBotAdapter polls Sleight's risk-manager state every 30 min.
2. Detects: kill-switch state ALWAYS visible flag is OFF (should always be ON per Sleight CLAUDE.md rule 1).
3. Detector classifies: doctrine-violation, severity=CRITICAL.
4. Triage notes: doctrine reference + prior occurrence count from lessons DB.
5. Proposer drafts: re-enable flag + add a regression test.
6. Apply gate: RISK_TIER = critical (financial surface). Operator inbox row REQUIRED. Auto-apply BLOCKED.
7. Operator reviews + sends "GO" inbox message -> apply proceeds.

## Token-efficiency notes (see docs/02-token-efficiency.md for full)

- Detector calls are the bulk of traffic -> Haiku-4.5 with cached prompt prefix; per-call cost dominated by signal-diff size.
- Triage + proposer fire only on severity >= MEDIUM signals -> 1-2 orders of magnitude less frequent.
- Opus-4.7 is rate-limited per attachment.
- Per-attachment cap fires the auto-throttle before the operator notices a bill.

## Non-goals (P0)

- No web dashboard (sub-page in EVE.exe is enough at P0).
- No external message queue.
- No multi-machine distribution (single-workstation only at P0).
- No third-party telemetry sinks (Datadog / Grafana) -- everything writes to `_shared-memory/` and EVE.exe reads it.
