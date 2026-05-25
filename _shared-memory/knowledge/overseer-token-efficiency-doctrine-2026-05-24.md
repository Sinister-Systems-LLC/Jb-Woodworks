<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# overseer-token-efficiency-doctrine-2026-05-24

> Universal token-efficiency doctrine for any Overseer-class lane.
> Binding for: `sinister-overseer` + any future meta-agent / agent-of-agents lane.
> Operator (verbatim 2026-05-24 ~23:48Z): *"I need a super efficient approach to this so we don't rape token use."*

## Why this exists

A long-running watch loop calling an LLM on every poll across N attached projects is the cheapest path to a runaway bill in the fleet. Without binding routing, even a 5-min chat poll on Opus-4.7 burns >= $28/day per attachment. With routing, the same loop burns <= $1.50/day per attachment. The 20x gap is the entire reason this doctrine exists.

## The 7 binding rules

### Rule 1 -- Hard cap per attached project

Default: **$5/day cost-eq per attached project.** Override only via operator-set value in `config/attached-projects.json` -> `attachments[*].cost_cap_usd_per_day`. NEVER silent. NEVER bumped at runtime without an audit row.

### Rule 2 -- Model-tier routing table is BINDING

| Operation | Tier | Model | Cost ratio | Notes |
|---|---|---|---|---|
| Heartbeat / liveness ping | n/a | NO MODEL CALL | $0 | local code only |
| Signal tail / scan / classify | CHEAP | Haiku-4.5 | 0.10x | cached system prompt; ships only the diff |
| Anomaly threshold compare | n/a | NO MODEL CALL | $0 | local numpy rolling stats |
| Triage (severity >= MEDIUM) | MEDIUM | Sonnet-4.6 | 1.0x | structured note |
| Propose fix (default) | MEDIUM | Sonnet-4.6 | 1.0x | concrete diff or config change |
| Propose fix (architectural / multi-file) | HIGH | Opus-4.7 | 5.0x | rate-limited <= 5/day/attachment |
| Cross-project transferable-pattern detection | HIGH | Opus-4.7 | 5.0x | <= 1 call/day/global |
| Apply-gate risk classification | CHEAP | Haiku-4.5 | 0.10x | rule-based with LLM fallback |
| Post-apply observation | n/a | NO MODEL CALL | $0 | local rule-based |

Adding a new operation requires updating this row OR justifying in a sibling brain entry.

### Rule 3 -- Cached prompt prefix structure

Every model call ships:

```
[CACHED PREFIX]
You are <agent> for attached project <KEY>. Adapter: <ADAPTER_CLASS>.
Policy: <RISK_TIERS_TABLE>.
Lessons context: <TOP_5_RECENT_LESSONS>.
[END CACHED PREFIX]

[VARIABLE PER CALL]
Signal: <SIGNAL_DIFF_ONLY>
Task: <DETECT|TRIAGE|PROPOSE>
[END VARIABLE]
```

Cached input ~10x cheaper than uncached on Anthropic API; per-call cost dominated by variable section.

### Rule 4 -- Diff-not-full-state policy

NEVER ship full target project state to the LLM. Ship: (a) diff vs last seen, (b) pointer to where full state lives, (c) on request, the cheap-tier detector expands a slice -- still not the full state.

### Rule 5 -- Per-project-type polling cadence

| Project type | Default polling | Rationale |
|---|---|---|
| Chat lane | 5 min | high signal volume; latency matters |
| File-based lane | 30 min | lower signal volume; commits + log lines |
| ML training lane | 60 min | metrics tick on epoch boundaries |
| Production / financial lane | 5 min | critical surface |
| Kiosk / OS lane | 60 min | daemon health |

Adapter declares default; operator can override per-attachment.

### Rule 6 -- Throttle at 80%, suspend at 100%

Watch loop reads cost burn from `automations/claude-usage-meter.ps1` every 5 min.

- >= 80% of daily cap: auto-throttle = drop polling cadence to next tier + suspend Opus calls for the rest of the day + log warn row.
- >= 100% of daily cap: hard suspend the watch loop until UTC midnight + push operator inbox notification.

### Rule 7 -- Self-monitoring

The Overseer-class agent is itself an attached project for the Sanctum lane (P5+ for sinister-overseer). The Sanctum lane runs token-analytics filtered by lane=sinister-overseer + drops a daily summary row to `OPERATOR-ACTION-QUEUE.md` IF fleet-wide spend exceeds (sum of caps + 10% headroom).

## Anti-patterns named (5)

1. **Spawn-per-event** -- one long-running watch loop per attached project; signals route within loop.
2. **Opus in the detector** -- detector is CHEAP tier only; Opus is rare hard-reasoning only.
3. **Full state in prompt** -- diff-only.
4. **Skipping the cached prefix** -- every call uses the standard prefix structure.
5. **Silent cap bump** -- all bumps logged + operator-visible.

## Verification commands

- `powershell -File "D:\Sinister Sanctum\automations\token-analytics.ps1" -Action ByProject -Days 1 | grep sinister-overseer`
- `powershell -File "D:\Sinister Sanctum\automations\token-analytics.ps1" -Action ByModel -Days 1 | grep sinister-overseer` -- expect Haiku >> Sonnet >> Opus
- `powershell -File "D:\Sinister Sanctum\automations\token-analytics.ps1" -Action WasteReport -Days 7 | grep sinister-overseer` -- expect ZERO context-bloat + ZERO tool-loop rows

## Composes with

- `_shared-memory/knowledge/token-efficiency-analytics-doctrine-2026-05-24.md` -- analytics primitive (Overseer is prime consumer)
- `_shared-memory/knowledge/oauth-pivot-max-quota-pooling-2026-05-24.md` -- Overseer uses OAuth pool, never ANTHROPIC_API_KEY direct
- `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md` -- project charter (sibling)
- `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md` -- pattern (sibling)
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (rule 4 self-audit; this doctrine IS the audit baseline for Overseer)
- `_shared-memory/knowledge/forever-improve-review-doctrine-2026-05-24.md` -- composes with the consolidation-summary mode when cost cap fires
