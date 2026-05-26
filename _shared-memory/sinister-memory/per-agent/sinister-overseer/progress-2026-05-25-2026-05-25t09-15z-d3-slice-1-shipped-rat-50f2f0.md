---
format_version: 2
author: RKOJ-ELENO
slug: sinister-overseer
heading_id: 2026-05-25-2026-05-25t09-15z-d3-slice-1-shipped-rat-50f2f0
saved_at: 2026-05-26T21:11:30Z
length: 3148
category: fact
confidence: 0.500
trust: medium
source: adoption-sweep
---

# sinister-overseer :: 2026-05-25T09:15Z -- D3 slice-1 SHIPPED: Rate-limit Adaptive Learning Overseer (sensor + learner + CLI + 11 tests)

**Shipped (verified):**

- `src/overseer/sensors/rate_limit.py` -- new file-tail sensor reading `_shared-memory/anthropic-throttle-events.jsonl`. Cadence 60s. Dedup-cache against re-emits. Inherits `_BaseSensor` for SensorBus parity; overrides `poll()` since this is file-based not script-based.
- `src/overseer/rate_limit_learner.py` -- `RateLimitLearner` class with rolling 1h/24h per-slot counts + mean-inter-arrival + recommendations engine. Rotation logic: count_1h>=3 OR last_429<5min -> rotate to highest-availability_score peer (skipping rate_limited / disabled / burn-window slots). No-viable-peer -> escalates as `quota_exhaustion_escalate` risk=high.
- Ledger persistence at `_shared-memory/overseer-rate-limit-learning.json` (schema_version `sinister.overseer.rate-limit-learner.v1`).
- New CLI subcommand: `python -m overseer rate-limit-status [--persist]` -- emits JSON summary + writes ledger.
- `sensors/__init__.py` re-exports `RateLimit429Event` + `RateLimitSensor`.
- `tests/test_rate_limit_learner.py` -- 11 cases: sensor read/dedup/missing/malformed, learner 1h/24h windowing, mean inter-arrival, rotation-to-best-peer, no-viable-peer escalation, burn-window peer exclusion, ledger persistence, quiet-when-no-burn.
- Overlap-guard claim registered: `python automations/agent_overlap_guard.py --register sinister-overseer overseer:rate-limit-learning` (TTL 2h).
- Stop-overlap ACK to sanctum: `_shared-memory/inbox/sanctum/20260525T0905Z-from-sinister-overseer-stop-overlap-acked.md`.

**Smoke (this turn):**
- `python -m pytest tests/ -v` -> **37/37 PASS** (4 smoke + 14 chatbot adapter + 11 rate-limit + 5 sensors/divergence + 3 contradictions, 241.49s)
- `python -m overseer rate-limit-status --persist` against LIVE `anthropic-throttle-events.jsonl` -> ingested 2 operator-b 429 events (sinister-os + sinister-overseer projects, ts 2026-05-25T08:42:52Z); ledger written with valid v1 schema; no recommendation fired (count_1h=2 < threshold 3 = correct conservative behavior).
- Live ledger file: `_shared-memory/overseer-rate-limit-learning.json` (434 bytes, valid JSON).

**In-flight (unverified):**
- Auto-rotate apply gate -- needs mesh-coord lock on `_shared-memory/oauth-slot-health.json` + a risk-aware action; queued for slice-2.
- Fix-template registration in adapters -- `rotate_oauth_slot` should land in a fleet-wide adapter or a new `FleetCoreAdapter`; queued.

**Open (queued):**
- D4: 4-account hive-mind round-robin (radar mode <=70% per acct) -- next slice.
- D5: Per-project ONE-CONSOLE discipline (max_claude_agents_per_project: 1).
- D8: Spawn missing-agent set (review projects.json for unstaffed lanes).
- Watch-loop wire-in (`src/overseer/watch.py` still P1 stub).
- TradingBotAdapter + ImageScannerAdapter slice-5 follow-ups.

**Refs:**
- Trigger inbox: `_shared-memory/inbox/sinister-overseer/20260525T0857Z-from-sanctum-stop-overlap-eve-ui.md`
- Sanctum plan: `_shared-memory/plans/sanctum-consolidate-stop-overlap-2026-05-25T0945Z/plan.md` (D3 item)
- Branch: `agent/sinister-overseer/chatbot-slice5-2026-05-25` (next commit ships D3 slice-1; auto-push still blocked by Gitea-down @ localhost:3000)
