<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 06 -- Cross-Project Learning

> Operator (verbatim 2026-05-24): *"Make sure the overseer evolves across projects as it gets more projects under its belt."*

This is the long-term moat. Per-project lessons accumulate quickly. Cross-project lessons -- where a pattern observed in project A becomes a candidate fix or red-flag in project B -- compound over time and make Overseer smarter with every attachment.

## The aggregator (scheduled daily)

```
ONCE PER DAY (UTC midnight + 30 min):
    candidates = SELECT symptom_summary, count(distinct project_key) AS proj_count
                 FROM (UNION ALL lessons_<each_attached_project>)
                 WHERE last_seen_utc > now() - 30d
                 GROUP BY symptom_pattern_normalized
                 HAVING proj_count >= 2

    FOR each candidate:
        IF not already in fleet_lessons:
            INSERT fleet_lessons ROW
            PROMOTE: write _shared-memory/knowledge/overseer-lessons-<topic>-<utc>.md
            PUSH:   fleet-update.ps1 priority=normal kind=doctrine
                    slug=sinister-overseer
                    text="cross-project lesson promoted: <summary>"
```

## What counts as a "transferable pattern"

A symptom is transferable IF:

1. It fired on >= 2 different attached projects within the last 30 days.
2. The root cause classification matches (e.g. "credentials swap mid-spawn" applies to ANY project that spawns Claude sessions, not just one).
3. The lesson text is generalizable (does NOT reference project-specific paths or keys).
4. The risk_classifier_override (if any) is reasonable to apply fleet-wide.

The aggregator runs a CHEAP-tier classifier to decide if a candidate clears these gates. If marginal -> escalates to operator review (queues row in `OPERATOR-ACTION-QUEUE.md`) instead of auto-promoting.

## How promoted patterns get used

1. **Adapter registry hot-reload** -- adapters cache the top-N fleet_lessons in their prompt prefix. On promotion, the cache invalidates (next call rebuilds prefix).
2. **Triage stage** -- before generating a triage note, query fleet_lessons for matching symptoms; surface in context.
3. **Apply gate** -- if a fleet_lessons row has `risk_classifier_override = critical` and matches the proposed fix shape, override the risk tier even if local lessons table has no prior failures.

## Example transferable patterns (hypothetical, future)

| Pattern | Source projects | Lesson | Suggested doctrine |
|---|---|---|---|
| ANTHROPIC_API_KEY exported in OAuth-pool spawn | sinister-chatbot, sinister-sleight | exporting the key hijacks billing from Max quota to Console pay-as-you-go; ALWAYS unset before spawn | reuse `oauth-pivot-max-quota-pooling-2026-05-24` |
| polling cadence too aggressive on file-based lane | eve-compliance, generic | <30 min on file lanes triples cost without proportional signal improvement | adapter default 1800s is correct; reject overrides |
| credentials swap mid-spawn breaks session | every spawn pipeline | swap MUST be atomic + complete before `claude` starts | reuse `spawn-mesh-safety-4-fixes-2026-05-24` |
| mesh-coord lock TTL too short on shared-file edits | every editor | 5-min TTL too tight for files that take >5 min to edit; default 30 min | extend default; document explicit override pattern |

## Brain entry naming convention

Promoted patterns become brain entries at:
`_shared-memory/knowledge/overseer-lessons-<short-topic-slug>-<utc-date>.md`

Frontmatter:
```
<!-- Author: RKOJ-ELENO :: <date> -->
# overseer-lessons-<topic>-<date>

> Source projects: <comma-separated list>
> Occurrence total: <int>
> Promoted by Sinister Overseer cross-project aggregator <utc>
```

Body sections: Symptom + Failed Fixes (top 3) + Successful Fixes (if any) + Recommended Fix Order + Risk Tier Override + Composes With.

`_INDEX.md` row tagged: `doctrine, overseer-lesson, transferable-pattern, <source-projects>`.

## Anti-patterns named

1. **Promoting after 1 project** -- ban. Minimum 2 projects + 30-day window.
2. **Promoting without normalizing the lesson** -- ban. Lessons that reference project-specific paths/keys can't transfer.
3. **Letting fleet_lessons grow unbounded** -- patterns not re-observed in 90 days move to `_archive/`.
4. **Triggering on TRIVIAL-tier symptoms** -- ban. Aggregator filters to severity >= MEDIUM signals only.
5. **Bypassing operator-review on critical-tier promotions** -- ban. Anything that would override an existing brain doctrine MUST queue an operator-review row.

## CLI

- `overseer fleet-lessons` -- list promoted patterns + their composes-with hints.
- `overseer fleet-lessons --search <pattern>` -- search the global store.
- `overseer aggregator --dryrun` -- preview what would be promoted today without writing.
- `overseer aggregator --run` -- force aggregator run (normally cron).

## Composes with

- `05-fails-to-learn.md` -- source of the per-project lessons aggregator consumes.
- `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md` -- universal doctrine.
- `_shared-memory/knowledge/forever-improve-review-doctrine-2026-05-24.md` -- aggregator IS forever-improve operationalized fleet-wide.
- `_shared-memory/knowledge/gradual-growth-memory-push-eve-exe-ready-2026-05-24.md` -- promoted patterns push to fleet-update.jsonl + inbox per the gradual-growth doctrine.
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` -- promoted patterns are fleet-wide by definition; this satisfies the sanctum-brain-row "GLOBAL or LANE-TAGGED" rule.
