<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 365
-->
# fails-to-learn-doctrine-2026-05-24

> Universal fleet-wide doctrine for the fails-to-learn pattern.
> Binding for: `sinister-overseer` today + any future agent that proposes + applies fixes (per-project agents that auto-fix; auto-curators; future meta-agents).
> Operator (verbatim 2026-05-24 ~23:48Z): *"Fails with the project to learn how to fix the mistakes."*

## Why this exists

A standard monitor reports failures. A fails-to-learn agent CAPTURES every failure as training data and CONSULTS lessons before retrying. After enough operating time, the same mistake never gets tried the same way twice. This is the long-term moat for any auto-fix agent.

## The pattern (5 steps)

1. **Propose + apply** -- gate ships a fix.
2. **Observe** -- adapter-specific observation_check runs in post-apply window.
3. **Detect failure** -- observation_check returns False, OR target smoke test breaks, OR metric regression deepens after apply.
4. **Auto-revert** -- reversibility plan executes (git stash pop / file copy / config rollback).
5. **Capture lesson** -- write row to per-project + global lessons store.

## Lessons store schema (universal)

Two tables: per-project (sharded by attachment key) + fleet-wide (cross-project aggregator promotes here).

Per-project columns: `symptom_hash, symptom_summary, attempted_fix, why_failed, lesson, suggested_doctrine_update, occurrences, first_seen_utc, last_seen_utc, risk_classifier_override, transferable`.

Fleet-wide columns: `pattern_summary, source_projects, occurrence_total, promoted_utc, brain_entry_slug, composes_with`.

Concrete impl for sinister-overseer: SQLite at `projects/sinister-overseer/lessons.db`. Other lanes adopting the pattern may use JSONL or sqlite per their stack.

## Symptom hashing (canonical helper)

`symptom_hash` = SHA1 of normalized features (signal_type + adapter_class + key bucketed evidence). Bucketed magnitudes keep the hash stable across small variations of the same underlying issue.

## How proposer uses lessons (BINDING)

Every proposer call MUST consult lessons BEFORE generating:

1. Compute symptom_hash for current signal.
2. Query lessons matching hash.
3. If 3+ prior failures of same shape -> override risk_tier to CRITICAL regardless of base classifier.
4. If 1-2 prior failures -> bump risk_tier up one level.
5. If prior successes exist for similar shape -> bias toward that pattern.

## How apply gate uses lessons on failure (BINDING)

1. After auto-revert: compute symptom_hash + serialize failure.
2. UPSERT into per-project lessons (increment occurrences if hash+fix combo exists).
3. If occurrences >= 3: set risk_classifier_override = "critical".
4. Push fleet-update: `priority=normal kind=lesson slug=<lane> text="lesson captured: <summary>"`.

## Cross-project promotion (daily)

Scheduled task scans per-project lessons for patterns firing on >= 2 projects within last 30 days. Promotes transferable patterns to `_shared-memory/knowledge/<lane>-lessons-<topic>-<utc>.md` brain entries. Pushes notice via fleet-update channel.

## Anti-patterns named (5)

1. **Log the failure but skip consulting lessons next time** -- ban. Proposer MUST consult.
2. **Stuff the full failure log into the prompt** -- ban. Lessons rows < 500 chars summary; full log lives at `_shared-memory/<lane>/failure-archives/<utc>-<hash>.txt`.
3. **Treat every failure as unique** -- ban. Bucketed magnitudes + normalized features ensure related failures collapse to same hash.
4. **Edit lessons store by hand** -- ban. All writes through the lessons module so UPSERT logic + audit timestamps are consistent.
5. **Promote after 1 project** -- ban. Minimum 2 projects + 30-day window.

## The "fails WITH the project" piece (subtlety)

Operator said "fails WITH the project to learn", not "fails AT the project". The FAILURE itself is the training signal. The target project's response to the failed fix (smoke break, metric deepening) IS data captured in the lesson row. Future proposals can recognize "this fix tried before -> target responded by X -> avoid this fix UNLESS root cause Y is also addressed".

## CLI conventions

Lanes implementing this pattern should expose:

- `<agent> lessons --project <key>` -- list lessons for an attachment.
- `<agent> lessons --search <pattern>` -- search across all attachments + fleet.
- `<agent> lessons --archive <id>` -- archive a stale lesson with reason.
- `<agent> lessons --promote <id>` -- manually promote (otherwise aggregator does it).
- `<agent> aggregator --dryrun` / `--run` -- cross-project aggregator controls.

## Composes with

- `_shared-memory/knowledge/sinister-overseer-charter-2026-05-24.md` -- project charter (sibling)
- `_shared-memory/knowledge/overseer-token-efficiency-doctrine-2026-05-24.md` -- model-tier routing (sibling)
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` -- rule 4 self-audit; lessons ARE the audit trail
- `_shared-memory/knowledge/forever-improve-review-doctrine-2026-05-24.md` -- forever-improve operationalized for auto-fix agents
- `_shared-memory/knowledge/gradual-growth-memory-push-eve-exe-ready-2026-05-24.md` -- promoted patterns push via fleet-update + inbox
- `_shared-memory/knowledge/sanctum-scope-discipline-2026-05-24.md` -- promoted patterns are fleet-wide; satisfies the GLOBAL-or-LANE-TAGGED rule
- `_shared-memory/knowledge/mesh-coordination-and-resource-lifecycle-2026-05-24.md` -- every apply locks via mesh-coord
