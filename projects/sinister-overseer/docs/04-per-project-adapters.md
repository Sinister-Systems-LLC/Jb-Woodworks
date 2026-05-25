<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 04 -- Per-Project Adapters

## What an Adapter is

An Adapter is a Python class that plugs into the generic watch loop and tells Overseer:

1. **SIGNAL_SOURCES** -- which of the source types in `03-watch-architecture.md` to consume + how to read them.
2. **POLLING_INTERVAL_SECONDS** -- default cadence (operator-overridable per-attachment).
3. **FIX_TEMPLATES** -- a catalog of pre-canonical fixes the proposer can pick from.
4. **AUTO_APPLY_RULES** -- which fix shapes are auto-applicable + at which risk tier.
5. **ESCALATION_PATH** -- which cross-agent inbox to write to when escalating.
6. **OBSERVATION_CHECKS** -- functions that verify a fix worked post-apply.
7. **COST_CAP_USD** -- override of the default $5/day if the adapter justifies a different number.

## Adapter base class

```python
# src/overseer/adapters/__init__.py (sketch)
class BaseAdapter:
    PROJECT_KEY: str = ""        # required, matches projects.json key
    POLLING_INTERVAL_SECONDS: int = 1800   # default 30 min
    COST_CAP_USD: float = 5.0
    SIGNAL_SOURCES: list[str] = []
    FIX_TEMPLATES: dict[str, dict] = {}
    AUTO_APPLY_RULES: dict[str, str] = {}    # fix_template_id -> risk_tier
    ESCALATION_INBOX: str = ""               # _shared-memory/inbox/<lane>/

    def collect_signals(self, since_utc: str) -> list[dict]:
        raise NotImplementedError
    def observation_check(self, fix_id: str) -> bool:
        raise NotImplementedError

REGISTRY: dict[str, type[BaseAdapter]] = {}

def register(cls):
    REGISTRY[cls.PROJECT_KEY] = cls
    return cls
```

## Adapter catalog (P0 scaffold)

### 1. `ChatbotAdapter` (for `sinister-chatbot`)

- **POLLING_INTERVAL_SECONDS:** 300 (5 min) -- chat lane
- **SIGNAL_SOURCES:**
  - log_tail (`projects/sinister-chatbot/leo_dev/backend/logs/*.log`)
  - metric_endpoint (latency P95 per model from chatbot's metrics surface)
  - user_data (feedback labels JSONL at `projects/sinister-chatbot/leo_dev/backend/data/ml-feedback.jsonl`)
  - config_smell (scan `.env` for ANTHROPIC_API_KEY export vs OAuth-pool)
  - cost_burn (claude-usage-meter filtered by lane=sinister-chatbot)
- **FIX_TEMPLATES:**
  - `route_provider_pin` -- LOW risk (env change)
  - `route_model_swap` -- LOW risk (env change)
  - `retry_budget_bump` -- LOW risk (env change)
  - `prompt_template_tune` -- MEDIUM risk (file change)
  - `nsfw_route_guardrail_tighten` -- MEDIUM risk (file change)
  - `per_fan_memory_policy_change` -- HIGH risk (data-affecting)
  - `train_ml_feedback_replay` -- HIGH risk (training run)
- **OBSERVATION_CHECKS:**
  - `latency_p95_under_baseline_within_5min(model)`
  - `feedback_label_rate_did_not_drop()`
  - `nsfw_route_violation_count_unchanged_or_lower()`
- **ESCALATION_INBOX:** `_shared-memory/inbox/sinister-chatbot/`
- **First-fire focus:** per-fan memory hit-rate + NSFW-route guardrail violations + ML feedback labels backlog + latency P95 per OpenRouter model

### 2. `ImageScannerAdapter` (for `eve-compliance`)

- **POLLING_INTERVAL_SECONDS:** 1800 (30 min) -- file-based lane with chunky signals
- **SIGNAL_SOURCES:**
  - metric_endpoint (per-agency moderation throughput from compliance panel)
  - user_data (admin good-catch / bad-catch labels)
  - log_tail (`backend/logs/image-moderation.log`)
  - drift (vision-model flagged-vs-cleared ratio KS-test on rolling 7d window)
  - config_smell (NCMEC reporting envelope not auto-drafting on confirmed CSAM)
  - cost_burn (vision-model API spend per agency)
- **FIX_TEMPLATES:**
  - `threshold_tune` -- LOW risk (config flag flip)
  - `prompt_template_tune` -- MEDIUM risk (vision-model prompt change)
  - `agency_override_add` -- MEDIUM risk (per-agency rule add)
  - `provider_swap_vision` -- HIGH risk (switch Claude Haiku -> Sightengine etc; cost + accuracy impact)
  - `ncmec_report_auto_draft_enable` -- CRITICAL risk (regulatory; requires operator-go)
  - `ncii_takedown_route_enable` -- CRITICAL risk (regulatory; requires operator-go)
- **OBSERVATION_CHECKS:**
  - `admin_label_agreement_rate_not_lower(agency)`
  - `false_positive_rate_under_threshold()`
  - `vision_model_cost_within_per_agency_budget()`
- **ESCALATION_INBOX:** `_shared-memory/inbox/eve-compliance/`
- **First-fire focus:** vision-model drift on flagged-vs-cleared deltas + per-agency moderation throughput + admin-review queue lag

### 3. `TradingBotAdapter` (for `sinister-sleight`)

- **POLLING_INTERVAL_SECONDS:** 300 (5 min) -- financial surface, latency to detect matters
- **SIGNAL_SOURCES:**
  - metric_endpoint (paper-PnL daily CSV)
  - drift (model KS-test for direction-classifier on rolling 30d features)
  - heartbeat (sleight watch loop alive)
  - config_smell (kill-switch state file ALWAYS visible == ON)
  - log_tail (`projects/sinister-sleight/logs/*.log`)
  - process (alpaca-paper-trade daemon liveness)
  - cost_burn (data-feed API spend)
- **FIX_TEMPLATES:**
  - `polling_cadence_tune` -- LOW risk (config flag)
  - `risk_cap_re_assert` -- LOW risk (re-write known-good config)
  - `model_retrain_schedule` -- MEDIUM risk (queue retrain job)
  - `strategy_param_tune` -- MEDIUM risk (param JSON change)
  - `kill_switch_reassert_on` -- HIGH risk if currently OFF (someone flipped it; investigate first)
  - `real_money_kill` -- HIGH risk
  - `real_money_enable` -- CRITICAL risk (operator-explicit-go required + GO REAL-MONEY signature per Sleight doctrine)
- **OBSERVATION_CHECKS:**
  - `kill_switch_state_visible_and_correct()`
  - `paper_pnl_within_strategy_envelope()`
  - `drift_ks_test_passing()`
- **ESCALATION_INBOX:** `_shared-memory/inbox/sinister-sleight/`
- **First-fire focus:** paper-PnL daily delta vs strategy expectation + model drift KS-test + kill-switch state ALWAYS visible + walk-forward retrain queue

### 4. `SnapPanelAdapter` (for `sinister-panel`; NOT pre-attached at P0 -- operator-named example only)

- **POLLING_INTERVAL_SECONDS:** 600 (10 min) -- panel + phone fleet
- **SIGNAL_SOURCES:**
  - log_tail (`leo_dev/backend/logs/snap-events.log`)
  - process (per-phone scrcpy + adb-reverse health)
  - metric_endpoint (Snap version detection from EMU lane)
  - heartbeat (per-phone agent stall)
  - drift (Snap UI selectors drift detector)
- **FIX_TEMPLATES:**
  - `phone_adb_reverse_restart` -- LOW risk (restart subprocess)
  - `phone_factory_reset_queue` -- HIGH risk (operator click)
  - `snap_version_selector_remap` -- MEDIUM risk (selector JSON update)
  - `snap_apk_re_push` -- MEDIUM risk (re-install apk on phone)
  - `auto_solve_snap_update` -- MEDIUM risk (this is the operator's brief example: "detect when a phone has an issue or snap updates and auto solve the issue push the fix or update")
- **OBSERVATION_CHECKS:**
  - `phone_adb_reachable()`
  - `snap_action_smoke_passes()`
- **ESCALATION_INBOX:** `_shared-memory/inbox/sinister-panel/`
- **First-fire focus:** (operator must explicitly attach this lane; not in P0 pre-attach list)

### 5. `GenericAdapter` (fallback for any other project key)

- **POLLING_INTERVAL_SECONDS:** 3600 (60 min) -- generic fallback
- **SIGNAL_SOURCES:**
  - heartbeat (whatever the lane writes to `_shared-memory/heartbeats/<lane>.json`)
  - log_tail (best-effort grep of `_shared-memory/PROGRESS/<lane>.md` for "FAIL" / "ERROR" / "TODO")
  - cost_burn (claude-usage-meter filtered by lane)
  - config_smell (scan project root for `.env`, `settings.json` anti-patterns)
- **FIX_TEMPLATES:**
  - `log_level_tune` -- LOW risk
  - `polling_self_throttle` -- LOW risk
  - `progress_row_archive` -- LOW risk (PROGRESS hygiene)
  - `_no_action_default` -- log only; no fix proposed without operator review
- **OBSERVATION_CHECKS:**
  - `heartbeat_resumed()`
- **ESCALATION_INBOX:** `_shared-memory/inbox/<project-key>/`
- **First-fire focus:** generic; operator-only adapter -- escalates virtually everything to operator rather than auto-applying

## Adapter selection at attach time

```
attach <project-key>
  -> look up REGISTRY[<project-key>] -- if found, use that adapter
  -> if not found: use GenericAdapter with project-key recorded
  -> operator can override via: attach <project-key> --adapter <adapter-class-name>
```

## Adding a new adapter

1. Create `src/overseer/adapters/<adapter_name>.py`.
2. Subclass `BaseAdapter`; set required class attributes; implement `collect_signals` + `observation_check`.
3. Apply `@register` decorator (or add to REGISTRY explicitly).
4. Add adapter spec to this doc.
5. Add tests under `tests/test_<adapter_name>.py` (P2+).
6. Brain entry under `_shared-memory/knowledge/overseer-adapter-<name>-<date>.md` if the adapter is novel-pattern.

## Adapter version schema

Each adapter declares `SCHEMA_VERSION: int`. When the watch loop starts, it logs the schema version. If `config/attached-projects.json` records an attachment with a schema_version older than the adapter's current, the watch loop refuses to start AND surfaces an operator inbox row recommending a migration.
