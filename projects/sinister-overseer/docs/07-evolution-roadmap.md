<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 07 -- Evolution Roadmap (6 phases)

| Phase | Name | Status | Exit criteria |
|---|---|---|---|
| P0 | Scaffold | THIS TURN -- scaffolded | Project dir + 7 docs + registry entry + pre-attach config + brain entries + PROGRESS row |
| P1 | Single-project watcher | next | One attached project's watch loop runs continuously for 24h within cost cap; one trivial proposal auto-applies; one medium proposal queues operator review |
| P2 | Multi-project pool | after P1 | All 3 pre-attached projects active; per-attachment cost caps holding; fleet-health view shows 3 healthy heartbeats |
| P3 | Fails-to-learn store | after P2 | lessons.db schema live; 1 induced failure captured + observed bumping risk tier on retry |
| P4 | Cross-project aggregator | after P3 | First transferable pattern promoted to brain; daily aggregator schtask Ready |
| P5 | Self-training (overseer trains chatbot to train itself) | after P4 | Chatbot ML feedback loop demonstrates >= 10% improvement attributable to overseer-proposed prompt + memory tuning |
| P6 | Fleet autonomous mode | after P5 | Operator-explicit-go to flip default RISK_TIER auto-apply ceiling from LOW -> MEDIUM; risk-tier HIGH + CRITICAL still operator-gated forever |

## P0 -- Scaffold (this turn)

**Deliverables:**

- [x] `projects/sinister-overseer/` directory with all subdirs + 7 docs
- [x] `pyproject.toml` (deps DECLARED, not installed)
- [x] `.env.example` + `.gitignore`
- [x] `src/overseer/` package stub + adapter stubs + CLI stub
- [x] `tests/test_smoke.py` (3 tests)
- [x] `config/attached-projects.json` (3 lanes status=`prepared`)
- [x] Registry row in `automations/session-templates/projects.json` (key=sinister-overseer, cyan accent, tier=3, swarm+loop true, picker.visible_keys)
- [x] Brain entries (charter + token-efficiency doctrine + fails-to-learn doctrine) indexed in `_INDEX.md`
- [x] PROGRESS row at `_shared-memory/PROGRESS/Sinister Overseer.md`
- [x] Cross-agent inbox notes to eve-compliance + sinister-chatbot + sinister-sleight
- [x] OPERATOR-ACTION-QUEUE row pointing at the activation flow
- [x] Fleet-update HIGH priority push
- [x] Mesh-coord lock acquired at start + released at end

## P1 -- Single-project watcher (smallest possible end-to-end loop)

**Pick:** `sinister-sleight` (lowest signal volume + easiest to simulate signals).

**Deliverables:**

- [ ] Implement `src/overseer/watch.py` real loop (no longer stub)
- [ ] Implement `TradingBotAdapter.collect_signals` reading paper-PnL CSV + heartbeat
- [ ] Implement detector calling Anthropic Haiku-4.5 via SDK with cached prefix
- [ ] Implement triage + proposer (Sonnet-4.6)
- [ ] Implement apply gate at TRIVIAL + LOW tiers ONLY (medium+ defer to P2)
- [ ] Wire cost-burn read from `claude-usage-meter.ps1`
- [ ] 24h continuous run within $5 cap
- [ ] One auto-applied trivial proposal (e.g. doc typo) with mesh-coord lock + diff-before-write + reversibility plan
- [ ] One medium proposal queued to operator inbox (NOT auto-applied)
- [ ] Smoke test: `python -m overseer dryrun --project sinister-sleight` runs one cycle without errors

**Acceptance test:**
```
overseer attach --project sinister-sleight
# watch loop starts; heartbeat appears in _shared-memory/heartbeats/sinister-overseer-sinister-sleight.json
# wait 24h
overseer status
# expect: signals_processed_since_start > 0, cost_burn_today_usd < 5.0
```

## P2 -- Multi-project pool

**Deliverables:**

- [ ] Spawn 3 concurrent watch loops (one per pre-attached lane).
- [ ] Implement `ChatbotAdapter` + `ImageScannerAdapter` (full signal collection).
- [ ] Concurrent mesh-coord lock test: 3 loops on 3 different files; never overlap.
- [ ] Heartbeat aggregator view in EVE.exe Overseer menu (per-project rows + global rollup).
- [ ] Per-attachment cost-cap independently enforced.

**Acceptance test:**
```
overseer list
# expect: 3 attachments active; all under cap; heartbeats <60s old
overseer status --all
# expect: signals_processed_since_start > 0 for all three
```

## P3 -- Fails-to-learn store

**Deliverables:**

- [ ] `src/overseer/lessons.py` SQLite store + UPSERT logic
- [ ] Symptom hashing function
- [ ] Proposer queries lessons before generating
- [ ] Apply gate writes lessons on failure
- [ ] Induce 3 synthetic failures on sinister-sleight (test-only proposal that intentionally fails its observation_check)
- [ ] Verify 4th retry of same shape auto-escalates to operator review

**Acceptance test:**
```
overseer lessons --project sinister-sleight
# expect: 3 rows for the synthetic failure pattern; occurrences=3
overseer dryrun --project sinister-sleight --inject-symptom synthetic-failure
# expect: risk_tier=critical, no auto-apply, operator review queued
```

## P4 -- Cross-project aggregator

**Deliverables:**

- [ ] `src/overseer/aggregator.py` (daily run; cron via schtasks `SinisterOverseerAggregator`)
- [ ] fleet_lessons table + UPSERT
- [ ] Promotion to `_shared-memory/knowledge/overseer-lessons-<topic>-<utc>.md`
- [ ] Fleet-update push on promotion
- [ ] `_INDEX.md` row appended automatically

**Acceptance test:**
```
# Manually induce same symptom on 2 different attachments
overseer aggregator --dryrun
# expect: at least 1 candidate listed
overseer aggregator --run
# expect: brain entry written; _INDEX.md row appended; fleet-update row pushed
```

## P5 -- Self-training (overseer trains chatbot to train itself)

**Deliverables:**

- [ ] ChatbotAdapter ingests 30 days of ML feedback labels
- [ ] Overseer proposes prompt + memory-policy + model-tier adjustments (Opus-4.7 architectural proposal; rate-limited)
- [ ] Operator approves -> chatbot ships
- [ ] Measure: feedback label rate, sentiment trend, churn over 30-day post-ship window
- [ ] Criterion: >= 10% improvement vs pre-ship baseline

**Acceptance test:** measurable improvement in chatbot's own feedback metrics attributable to overseer-proposed change (A/B if feasible).

## P6 -- Fleet autonomous mode

**Deliverables:**

- [ ] Operator-explicit-go message in `_shared-memory/inbox/sinister-overseer/` with content "GO AUTONOMOUS <tier> <expiry-date>".
- [ ] Default auto-apply ceiling moves LOW -> MEDIUM (still operator-gated for HIGH + CRITICAL).
- [ ] Fleet-wide rollout to all attached projects.
- [ ] Quarterly review checkpoint -- operator can revert ceiling at any time.

**Anti-roadmap notes:** P6 NEVER auto-applies HIGH or CRITICAL. NEVER autonomously promotes itself further than operator has approved. NEVER goes beyond the daily cost cap. NEVER edits `~/.claude/.mcp.json` or `~/.claude/settings.json` or `_vault/`.
