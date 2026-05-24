<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# Forever-improve review doctrine

**Status:** doctrine, standing-rule, binding, fleet-wide
**Created:** 2026-05-24
**Origin (operator verbatim 2026-05-24 evening):** *"i want everything we do to be like reviewed to see where we can imporve on things so we are forever expanding in the hin theh things we can do"*

## TL;DR

Every meaningful work product (commit, doctrine, script, doc, feature) automatically triggers a structured review pass that surfaces concrete improvement opportunities. The fleet forever-expands by always looking for the next refinement increment — within the quality-degradation limits of rule 8 of no-bullshit-tested-before-claimed-doctrine.

## Trigger conditions

Forever-improve fires at any of these checkpoints:

1. **Every commit** — after `git commit` lands, run `forever-improve.ps1 -Action ReviewCommit -Sha HEAD`.
2. **Every shipped feature** — when a deliverable graduates `acceptance-tested → shipped`, review the target.
3. **Every new doctrine** — when a `.md` lands in `_shared-memory/knowledge/`, review it.
4. **Every new script** — when a `.ps1` / `.py` / `.sh` lands in `automations/` or `tools/`, review it.
5. **Every meaningful work unit** — at end-of-turn (CLAUDE.md cold-start step 10), review the primary work product.

The review is a fast (≤ 5s) structured pass — not a deep audit. Findings drop into an append-only ledger; the agent acts on them in the next 3 lane-turns.

## What "review" means — the 5-question pass

Every review answers these five questions about the target:

| # | Question | Severity scale | Output |
|---|---|---|---|
| Q1 | Is this **complete**? Are there obvious unfinished sections, TODO markers, stub functions, or placeholder text? | minor / major | finding row |
| Q2 | Is this **consistent** with existing systems? Does it duplicate, contradict, or fork from established doctrines/scripts/patterns? | minor / major | finding row |
| Q3 | Is this the **simplest** version? Can it be shorter, fewer dependencies, less abstraction, less ceremony? | minor / major | finding row |
| Q4 | Is this **verifiable / testable**? Is there a smoke test, acceptance criterion, or measurable success metric? | minor / major | finding row |
| Q5 | What's the **next improvement increment**? One concrete, scoped follow-up the next lane-turn could ship. | suggestion | next_action row |

A review of N findings produces N improvement-log rows (1 per question that surfaces a finding) + 1 `next_action`. If a question has nothing to flag, omit it.

## Output format — improvement-log.jsonl

Append-only JSONL at `_shared-memory/improvement-log.jsonl`. One row per review.

```json
{
  "ts_utc": "2026-05-24T22:30:00Z",
  "target": "automations/eve-launcher/eve.py",
  "target_type": "script",
  "reviewer_slug": "sanctum",
  "findings": [
    {"severity": "minor", "area": "Q3-simplicity", "suggestion": "..."},
    {"severity": "major", "area": "Q4-verifiability", "suggestion": "..."}
  ],
  "next_action": "Add a --self-test flag to eve.py that runs a 5s smoke without spawning a window.",
  "status": "open",
  "acted_on_at": null,
  "dismissed_at": null,
  "dismissed_reason": null
}
```

Status transitions: `open → acted-on` (improvement landed; cite commit/file) OR `open → dismissed` (one-line reason required) OR `open → expired` (after 3 lane-turns with no action; forced via `-Action Drain`).

## Quality-gate composition (loop-quality-gate.ps1)

Forever-improve runs AT the same end-of-turn checkpoint as `loop-quality-gate.ps1` (when that gate exists; deferred to its owner), but with a different role:

- `loop-quality-gate` produces **stop signals** (quality is diminishing — halt expansion, consolidate)
- `forever-improve` produces **suggestions** (here are concrete refinements for the work just done)

When `loop-quality-gate` fires `DEGRADED` for the lane, `forever-improve` switches modes:
- Suppresses the 5-question pass for new features
- Instead surfaces the consolidation work to do (from rule 8 of no-bullshit doctrine: archive stale rows, rotate PROGRESS, prune queue, etc.)
- Writes a single `improvement-log` row of type `consolidation-required` with the specific signal that fired (`brain-rows>150`, `progress>300KB`, etc.)

## Sub-rule — improvements must be acted on within 3 lane-turns

Every `status: open` row has a 3-turn half-life. After 3 lane-turns (counted by `PROGRESS/<lane>.md` entries since the row was written) one of two things must happen:

1. **Act on it** — implement the suggestion; mark `status: acted-on` with a commit hash or file reference.
2. **Dismiss it** — explicit `status: dismissed` with a one-line `dismissed_reason` (e.g. "Out of scope for current laser-focus area").

If neither happens, `-Action Drain` forces `status: expired` (no rotting log). Operator can see at a glance: tally per-lane shows `open / acted-on / dismissed / expired` counts.

## Composes with

- **`no-bullshit-tested-before-claimed-doctrine-2026-05-23`** (rule 5: forever-upgrade — this doctrine is the *cadence* mechanism for rule 5; rule 8: quality-degradation limits — this doctrine respects the limits, doesn't override them).
- **`agent-continuity-no-long-naps-doctrine`** — improvements drained quickly so a returning agent doesn't inherit a 50-row open backlog.
- **`operator-utterance-tracking-doctrine-2026-05-24`** — same JSONL append-with-lock pattern (`improvement-log.lock` mirrors `.operator-utterances.lock`).
- **`do-not-revert-operator-canonical-protections-2026-05-23`** — cold-start step 10 is anti-revert protected (must be in CLAUDE.md, must reference `forever-improve.ps1`).

## Hard-stops (binding NEVERs)

1. **NEVER** run forever-improve on a target whose `loop-quality-gate` is `DEGRADED` for 3 consecutive turns. STOP the cycle for that lane; the lane must consolidate first. Forever-expand has limits (rule 8 of no-bullshit doctrine).
2. **NEVER** auto-act on a `major` finding without operator-visibility. Major findings get an `OPERATOR-ACTION-QUEUE` row.
3. **NEVER** let the log grow unbounded. `-Action Drain` runs at least once per fleet-wide cold-start. Expired rows stay (audit trail) but don't count toward the 3-turn limit.
4. **NEVER** review a target that doesn't exist or is empty. Reviewer must Read the file first; if empty, write a `consolidation-required` row instead of fabricating findings.

## Anti-patterns

1. Fabricated findings (e.g. claiming Q4 fails when there's already a smoke test in the same dir). Reviewer must Read, not guess.
2. Vague suggestions like "make it better" — every suggestion is concrete, scoped, and one-line-actionable.
3. Reviewing your own just-written line in the same turn (zero-gap self-review is theater). Wait at least one work unit; let the next turn's reviewer catch your drift.
4. Acting on a `minor` finding when a `major` is open in the same target (priority inversion).
5. Dismissing every finding as out-of-scope (the log becomes a graveyard). If >70% of a lane's findings dismiss, the lane has a focus problem.

## Self-application

This doctrine applies to EVE on Sanctum (this lane) FIRST. The next time Sanctum ships a meaningful work unit, run `automations/forever-improve.ps1 -Action Review -Target <work>` and surface the row. If the review surfaces a finding about THIS doctrine, that's the meta-validation.

## Status

scaffolded → parse-clean (markdown opens) → smoke-tested (CLI sample run + Tally returns valid count) → acceptance-tested (after 3 lane-turns of compliant forever-improve runs across ≥2 lanes) → shipped (operator confirms).

Current: **smoke-tested** at write time (CLI sample-run + Tally on same turn).
