<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 02 -- Token Efficiency (THE critical doc)

> Operator (verbatim 2026-05-24): *"I need a super efficient approach to this so we don't rape token use."*

This is the most important doc in the Overseer project. Every architectural choice and every adapter MUST honor it. If a future EVE session can pick ONE thing to read before changing Overseer code, this is the file.

## Top-line commitments

1. **Hard cap: $5/day cost-eq per attached project** (configurable, never bumped without operator action).
2. **Model-tier routing is mandatory**, not optional. The cheap-tier handles >= 95% of calls.
3. **Diff-not-full-state**: every call ships ONLY the signal diff, never the full project state.
4. **Stable prompt prefixes are cached** (Anthropic prompt caching: cached input ~10x cheaper).
5. **Per-project polling cadence is tuned for the project type**, not one-size-fits-all.
6. **Auto-throttle fires at 80% of cap**; hard suspend fires at 100% with operator notification.

## Model-tier routing table (BINDING)

| Operation | Tier | Model | Cost ratio* | Frequency budget | Notes |
|---|---|---|---|---|---|
| Heartbeat / liveness ping | n/a | NO MODEL CALL | $0 | every 60s | local code only; no LLM in the loop |
| Signal tail / scan | CHEAP | Haiku-4.5 | 0.10x | per-poll-cycle | cached system prompt; ships only the diff |
| Classify signal type | CHEAP | Haiku-4.5 | 0.10x | per signal | constrained-JSON output schema |
| Anomaly threshold compare | n/a | NO MODEL CALL | $0 | per signal | local math; numpy rolling stats |
| Triage (severity >= MEDIUM) | MEDIUM | Sonnet-4.6 | 1.0x | per medium+ signal | structured triage note |
| Propose fix (default) | MEDIUM | Sonnet-4.6 | 1.0x | per triaged signal | concrete diff or config change |
| Propose fix (architectural / multi-file refactor) | HIGH | Opus-4.7 | 5.0x | <= 5 calls/day/attachment | rate-limited HARD |
| Cross-project transferable-pattern detection | HIGH | Opus-4.7 | 5.0x | <= 1 call/day/global | daily aggregator only |
| Apply-gate risk-tier classification | CHEAP | Haiku-4.5 | 0.10x | per proposal | rule-based with LLM fallback |
| Post-apply observation | n/a | NO MODEL CALL | $0 | per apply | reads target project metrics; rule-based |

*Cost ratio relative to Sonnet-4.6 baseline = 1.0x. Per `token-analytics.ps1` cost model: Opus ~5x Sonnet; Haiku ~0.10x Sonnet.

**Rule:** if a future change wants to use Opus-4.7 for an operation NOT in the table above as HIGH tier, the change requires a brain entry justifying the upgrade.

## Why this matters (back-of-envelope)

If a chat-lane watch loop polls every 5 min = 288 polls/day. Each poll = 1 cheap-tier detector call.
- 288 * 0.10x = 28.8 Sonnet-equivalent calls/day for detector.
- Of those, ~10% fire as medium+ signals -> 28 triage calls (Sonnet) -> 28 * 1.0 = 28 Sonnet-eq.
- Of those, ~30% propose a fix -> 9 propose calls (Sonnet) -> 9 * 1.0 = 9 Sonnet-eq.
- Of those, ~5% escalate to Opus -> 0.4 Opus calls (rounded to <= 5 cap) -> say 1 Opus call -> 5 Sonnet-eq.
- **Total: ~71 Sonnet-equivalent calls/day** per chat lane.

If we assume average Sonnet call cost ~$0.02 (conservative with cached prompt + small diffs), that's ~$1.42/day per chat lane. Well under $5/day cap.

If detector calls go full price (no caching) and use Opus -> 288 * 5.0 = 1440 Sonnet-eq * $0.02 = $28.80/day per chat lane. **20x over budget.** This is why the routing table is BINDING.

## Polling cadence per project type

| Project type | Default polling | Rationale |
|---|---|---|
| Chat lane (chatbot, helpdesk, messaging) | 5 min | High signal volume; user-facing latency matters |
| File-based lane (most fleet projects) | 30 min | Lower signal volume; git commits + log lines are the main signals |
| ML training lane (training-loops, RL agents) | 60 min | Even lower signal volume; metrics tick on epoch boundaries |
| Production / financial lane (Sleight real-money mode) | 5 min | Critical surface; latency to detect issue matters |
| Kiosk / OS / shell lane (Sinister OS) | 60 min | Low signal volume; mostly daemon health |

Adapter declares its default cadence; operator can override per-attachment in `config/attached-projects.json`.

## Caching strategy (Anthropic prompt cache)

Every Overseer call ships with a STABLE PROMPT PREFIX that is cache-eligible:

```
[CACHED PREFIX]
You are Sinister Overseer for attached project <KEY>. Your job is to
classify / triage / propose. Adapter type: <ADAPTER_CLASS>. Policy:
<RISK_TIERS_TABLE>. Lessons context: <TOP_5_RECENT_LESSONS_FOR_THIS_PROJECT>.
[END CACHED PREFIX]

[VARIABLE PER CALL]
Signal: <SIGNAL_DIFF_ONLY>
Task: <DETECT|TRIAGE|PROPOSE>
[END VARIABLE]
```

- The cached prefix changes ONLY when adapter type or top-5 lessons change.
- Top-5 lessons rotate on lesson commit -> we accept the cache invalidation; lessons commits are rare (1-3/day per project).
- Per-call cost is dominated by the variable section, not the cached section.
- Anthropic cached input is ~10x cheaper than uncached input -> we get ~9x effective per-call cost reduction on the prefix tokens.

## Diff-not-full-state policy

NEVER ship the full target project state to the LLM. Always ship:

1. The diff vs the last seen state (file diff, metric delta, log lines NEW since last poll).
2. A short pointer to where the full state lives (path / log file / metric name) so the LLM can request expansion if needed.
3. If expansion is requested, the cheap-tier detector calls again with the expanded slice, NOT the entire state.

This is a hard rule. Violators get caught by `automations/token-analytics.ps1` waste-pattern "context-bloat".

## Hard cap enforcement (auto-throttle + suspend)

- Per attachment, daily cost-eq is computed from `claude-usage-meter.ps1` filtered by lane=sinister-overseer + attachment-key.
- Watch loop reads this counter every 5 minutes.
- At >= 80% of daily cap: auto-throttle = (a) drop polling cadence to next tier (5min -> 30min OR 30min -> 60min), (b) suspend Opus-4.7 calls for the rest of the day, (c) log a warn row.
- At >= 100% of daily cap: hard suspend the watch loop until UTC midnight; push notification row to `_shared-memory/inbox/operator/<utc>-overseer-cap-hit.md`.
- Operator can override: `overseer apply --bump-cap <attachment-key> <new-cap-usd>`. Bumps are LOGGED for audit.

## Self-monitoring (Overseer overseen)

Overseer's own watch loop is itself an attached project for the Sanctum lane (P5+). The Sanctum lane runs `automations/token-analytics.ps1` filtered by lane=sinister-overseer + drops a daily summary row to `OPERATOR-ACTION-QUEUE.md` IF the fleet-wide Overseer spend exceeds (sum of caps + 10% headroom).

## Anti-patterns named

1. **Spawning a new Claude session per signal** -- ban. One long-running watch loop per attached project; signals routed within loop.
2. **Calling Opus-4.7 in the detector** -- ban. Detector is CHEAP tier only.
3. **Shipping the full target project state to the LLM** -- ban. Diff-only.
4. **Skipping the cached prefix** -- ban. Every call uses the standard prefix structure.
5. **Bumping the cap silently** -- ban. All cap bumps logged + operator-visible.
6. **Polling faster than the project's adapter default** -- ban without an operator-set override in `config/attached-projects.json`.
7. **Adding a new operation that calls a model without listing it in the routing table above** -- ban. Routing table is BINDING.

## Verification commands

- `powershell -File "D:\Sinister Sanctum\automations\token-analytics.ps1" -Action ByProject -Days 1 | grep sinister-overseer`
- `powershell -File "D:\Sinister Sanctum\automations\token-analytics.ps1" -Action BySession -Days 1 | grep sinister-overseer-`
- `powershell -File "D:\Sinister Sanctum\automations\token-analytics.ps1" -Action ByModel -Days 1 | grep sinister-overseer` -- expect Haiku >> Sonnet >> Opus
- `powershell -File "D:\Sinister Sanctum\automations\token-analytics.ps1" -Action WasteReport -Days 7 | grep sinister-overseer` -- expect ZERO context-bloat + ZERO tool-loop rows on attached projects

## Composes with

- `automations/token-analytics.ps1` (measurement primitive)
- `automations/claude-usage-meter.ps1` (per-session sampler)
- `automations/claude-oauth-accounts.ps1` (Overseer uses round-robin pool; never ANTHROPIC_API_KEY)
- `_shared-memory/knowledge/token-efficiency-analytics-doctrine-2026-05-24.md` (fleet-wide token doctrine; Overseer is the prime consumer)
- `_shared-memory/knowledge/oauth-pivot-max-quota-pooling-2026-05-24.md` (Max quota pooling; Overseer benefits from the shared pool)
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (rule 4 self-audit; Overseer's own cost is audited daily)
