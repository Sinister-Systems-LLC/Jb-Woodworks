<!-- Author: RKOJ-ELENO :: 2026-05-24 -->
# 05 -- Fails-to-Learn

> Operator (verbatim 2026-05-24): *"Fails with the project to learn how to fix the mistakes."*

This is the most novel idea in the Overseer brief. A normal monitoring tool just reports. Overseer also LEARNS from its own failures, so the same mistake never gets tried the same way twice.

## The pattern (5 steps)

1. **Propose + apply** -- apply gate ships a fix.
2. **Observe** -- adapter observation_check runs in the post-apply window.
3. **Detect failure** -- observation_check returns False, OR target project smoke test breaks, OR a metric regression deepens after apply.
4. **Auto-revert** -- reversibility plan executes (git stash pop / file copy / config rollback).
5. **Capture lesson** -- write a row to `lessons.db`.

## Lessons DB schema (SQLite, P1)

```sql
-- per-project lessons (sharded by attachment)
CREATE TABLE lessons_<project_key> (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symptom_hash TEXT NOT NULL,           -- stable hash of symptom shape
    symptom_summary TEXT NOT NULL,         -- human-readable (< 200 chars)
    attempted_fix TEXT NOT NULL,           -- proposal id + summary
    why_failed TEXT NOT NULL,              -- observation_check failure mode
    lesson TEXT NOT NULL,                  -- 1-3 sentence takeaway
    suggested_doctrine_update TEXT,        -- optional brain entry hint
    occurrences INTEGER DEFAULT 1,
    first_seen_utc TEXT NOT NULL,
    last_seen_utc TEXT NOT NULL,
    risk_classifier_override TEXT,         -- if non-null, future proposals of same shape get this tier
    transferable INTEGER DEFAULT 0,        -- 1 if cross-project aggregator promoted this
    UNIQUE(symptom_hash, attempted_fix)
);

-- fleet-wide lessons (aggregator promotes here)
CREATE TABLE fleet_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_summary TEXT NOT NULL,         -- the transferable insight
    source_projects TEXT NOT NULL,         -- JSON list of project keys
    occurrence_total INTEGER NOT NULL,
    promoted_utc TEXT NOT NULL,
    brain_entry_slug TEXT,                 -- if promoted to _shared-memory/knowledge/
    composes_with TEXT                     -- JSON list of related doctrines
);
```

## Symptom hashing

`symptom_hash` = SHA1 of normalized (signal_type + adapter_class + key_evidence_features). Key evidence features are extracted by the adapter, NOT free-form. Example for chatbot latency regression:

```python
features = {
    "signal_type": "regression",
    "metric": "latency_p95",
    "model_route": "openrouter:cognitivecomputations/dolphin-mixtral-8x22b",
    "delta_direction": "increase",
    "magnitude_bucket": ">2x",  # bucketed, not raw
}
symptom_hash = sha1(json.dumps(features, sort_keys=True).encode()).hexdigest()[:16]
```

Bucketed magnitudes keep the hash stable across small variations of the same underlying issue.

## How the proposer uses lessons

On every proposer call:

1. Compute `symptom_hash` for the current signal.
2. Query `lessons_<project_key>` WHERE symptom_hash matches.
3. If matches exist:
   - Surface the top-3 prior attempts + outcomes in the proposer's prompt context (cached prefix slot).
   - If 3+ prior failures of same shape -> override risk_tier to CRITICAL automatically, regardless of base classifier.
   - If 1-2 prior failures -> bump risk_tier UP one level (low -> medium, medium -> high).
   - If prior successes exist for similar shape -> bias toward that proposal pattern.

## How the apply gate uses lessons on failure

1. After auto-revert: compute symptom_hash + serialize the failure.
2. UPSERT into `lessons_<project_key>` (increment occurrences if hash+fix combo already exists).
3. If occurrences >= 3: set risk_classifier_override = "critical" so it never auto-applies again.
4. Push fleet-update notice: `priority=normal kind=lesson slug=sinister-overseer text="lesson captured: <summary>"`.

## The "fails WITH the project" piece

Important nuance from the operator brief: "Fails WITH the project to learn how to fix the mistakes". Not "fails AT the project". Means: the FAILURE itself is the training signal. The target project's response to the failed fix (e.g. smoke test break, latency further degradation) IS data for Overseer.

So the lessons row captures NOT JUST what Overseer did wrong, BUT what the target project did in response (the symptom AFTER the failed fix). Future proposals can recognize "this fix tried before -> target project responded by X -> avoid this fix UNLESS root cause Y is also addressed".

## Anti-patterns named

1. **Logging the failure but not consulting lessons next time** -- ban. Proposer MUST consult lessons before proposing.
2. **Stuffing the full failure log into the prompt** -- ban. Lessons rows are < 500 chars summary; full log lives at `_shared-memory/overseer/failure-archives/<utc>-<hash>.txt`.
3. **Letting lessons rot** -- once a lesson hits 6 months without re-occurrence + the underlying code has changed, the lesson auto-archives.
4. **Treating every failure as unique** -- ban. Bucketed magnitudes + normalized features ensure related failures collapse to the same hash.
5. **Editing lessons.db by hand** -- ban. All writes go through `src/overseer/lessons.py` so the UPSERT logic + audit timestamps are consistent.

## CLI

- `overseer lessons --project <key>` -- list all lessons for an attachment.
- `overseer lessons --search <pattern>` -- search across all attachments + fleet.
- `overseer lessons --archive <id>` -- archive a stale lesson (with reason).
- `overseer lessons --promote <id>` -- manually promote to fleet_lessons (otherwise aggregator does it).

## Composes with

- `_shared-memory/knowledge/fails-to-learn-doctrine-2026-05-24.md` -- universal doctrine for the pattern.
- `06-cross-project-learning.md` -- aggregator that promotes patterns across projects.
- `03-watch-architecture.md` -- the apply gate + observation check that triggers lessons capture.
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (rule 4 self-audit; lessons ARE the audit trail).
- `_shared-memory/knowledge/forever-improve-review-doctrine-2026-05-24.md` (this is forever-improve operationalized for the Overseer-class agent).
