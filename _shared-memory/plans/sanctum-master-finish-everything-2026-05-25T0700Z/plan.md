# Sanctum Master Plan — finish everything in flight (2026-05-25T07:00Z)

**Author:** RKOJ-ELENO :: 2026-05-25 (sanctum lane, master orchestration)
**Trigger:** operator `/loop create a plan to complete everything you need to complete` (2026-05-25T07:00Z)
**Scope:** sanctum lane high-level only (per `sanctum-scope-discipline-2026-05-24`). Lane-level work routed to lane owners, not duplicated here.
**Looping cadence:** dynamic /loop (next refresh ~25min); plan is rolling — re-pruned each fire.

## State of the world (snapshot 2026-05-25T07:00Z)

- **Branch:** `agent/sinister-sanctum/iter23-eve-polish-icon-mintty-2026-05-25` (shared with parallel sanctum execution lane)
- **Last 2 ships:** `0bab620` (iter-22 sub-G smoke-audit) + `39bf7d0` (iter-23 research swarm: 2 audits + 2 plans)
- **Parallel sanctum lane (iter-23 EXECUTION):** working eve.py items 61/65/66/67 + spawn-setup-wizard mintty fix + EVE.exe icon embed. Do NOT duplicate.
- **Open operator utterances `status=new`:** 45 (most addressed via doctrine; need sweep-ack pass)
- **Watchdog poke inbox:** 1+ unread

## Priority ladder (1 = highest)

### 1. UTTERANCE TRACKER SWEEP (housekeeping; small; high-signal)

45 `status=new` rows on `_shared-memory/operator-utterances.jsonl`, most are utterances from 2026-05-24 already addressed via CLAUDE.md hard-canonical blocks but never flipped to `resolved`.

- **Deliverable:** Python sweep script `automations/utterance_sweep_ack.py` that takes a mapping `{ts_utc → doctrine-or-deliverable-ref}` and flips status `new → acknowledged` in bulk with ack rows.
- **Pass criterion:** after run, `grep -c '"status":"new"' operator-utterances.jsonl` drops by ≥30; every newly-acknowledged row points to a real doctrine or shipped commit.
- **Owner:** sanctum master (this lane).
- **Effort:** ~30 min.
- **Risk:** low — no destructive ops; ack is append-style.

### 2. P0 OF VERSION-SNAPSHOT PLAN (scaffold only, no code)

Per `_shared-memory/plans/version-snapshot-system-2026-05-25/plan.md` rollout phase P0.

- **Deliverables (4 NEW files only, no live-code edits):**
  - `_shared-memory/version-snapshots/` (dir)
  - `_shared-memory/version-snapshots/EXCLUDE.txt` (anthropic-usage-cache + projects/ + OAuth secrets + *.bak* globs)
  - `_shared-memory/version-snapshots/README.md` (schema doc for manifest.json + binaries.zip + headline.md)
  - `_shared-memory/knowledge/version-snapshot-system-doctrine-2026-05-25.md` (brain doctrine entry)
  - `_shared-memory/knowledge/_INDEX.md` (one-row append)
- **Pass criterion:** all 4 files present; `_INDEX.md` row references new slug; no edits to `automations/version_snapshot.py`.
- **Owner:** sanctum master.
- **Effort:** ~20 min.
- **Risk:** low — additive only; `git rm` reverses.

### 3. P0 OF COMMAND-CENTER PLAN (loop+swarm default-on plumbing)

Per `_shared-memory/plans/multi-agent-control-center-2026-05-25/plan.md` rollout phase P0.

- **Deliverables (3 JSON edits + 1 PS1 hard-fallback flip):**
  - `automations/session-templates/agent-prefs.json`: add top-level `"default_modes": {"swarm": true, "loop": true, "loop_relentless": true}`
  - `automations/session-templates/projects.json`: add top-level `"fleet_default_modes": {"swarm": true, "loop": true, "loop_relentless": true}` fallback
  - `automations/start-sinister-session.ps1:1394`: flip `$defSwarm = $false` → `$true`; update precedence-ladder comment
  - `automations/start-sinister-session.ps1:1424`: flip prompt copy `[y/N]` → `[Y/n]` when `defSwarm=true`
- **Pass criterion:** spawn a synthetic project NOT in `projects.json` with `SINISTER_SKIP_MODES_PROMPT=1` → launch.sh exports `SINISTER_SWARM_MODE=1` AND `SINISTER_LOOP_MODE=1`.
- **Owner:** sanctum master.
- **Effort:** ~25 min.
- **Risk:** medium — start-sinister-session.ps1 is the hot path; verify with a dry-spawn before pushing.
- **Coordination:** parallel lane may also be touching this file — `mesh-coordinator.ps1 -Action Check -Focus 'automations/start-sinister-session.ps1'` before edit.

### 4. EVE-BAT-PS1 AUDIT FOLLOWUP — 9 DELETE candidates

Per `_shared-memory/audits/eve-bat-ps1-audit-2026-05-25.md`.

- **Deliverable:** generate the 9 specific DELETE candidates with per-file Grep evidence of zero references; single commit removing them OR queue under operator review if any look ambiguous.
- **Pass criterion:** 9 files in DELETE list each have a Grep-zero-refs paste; commit reverts cleanly via `git revert`.
- **Owner:** sanctum master.
- **Effort:** ~30 min.
- **Risk:** medium — `git mv` to `_archive/` instead of delete is the safer first move.

### 5. EVE-UI 5 MINOR FIXES (queue for execution lane)

Per `_shared-memory/audits/eve-ui-flow-audit-2026-05-25.md`. All <5 LOC each.

- **Deliverable:** cross-agent inbox row to parallel sanctum execution lane (already touching eve.py) at `_shared-memory/inbox/sanctum/2026-05-25T07-eve-ui-5-fixes.json` referencing the audit file and specifying the 5 patch points (file:line). Do NOT edit eve.py myself — execution lane owns it.
- **Pass criterion:** inbox row written + parallel lane acks.
- **Owner:** sanctum master (just the inbox hand-off).
- **Effort:** ~5 min.
- **Risk:** none.

### 6. FOREVER-IMPROVE CHECKPOINT (cold-start step 10)

Per CLAUDE.md cold-start step 10.

- **Deliverable:** `powershell -File automations/forever-improve.ps1 -Action ReviewCommit -Sha HEAD` over recent ships (0bab620 + 39bf7d0). Surface top-severity findings to PROGRESS row.
- **Pass criterion:** review output captured; any R0-R1 findings auto-fixed this turn OR R2+ queued.
- **Owner:** sanctum master.
- **Effort:** ~10 min.
- **Risk:** none.

### 7. STALE RESUME-POINTS SWEEP (`_shared-memory/resume-points/Sinister Sanctum/`)

20-row cap per lane per the cap rule; per-spawn writes ~1 row, so this naturally caps. Just verify cap is intact.

- **Deliverable:** `ls _shared-memory/resume-points/Sinister\ Sanctum/ | wc -l` ≤ 20.
- **Pass criterion:** count check.
- **Owner:** sanctum master.
- **Effort:** ~2 min.
- **Risk:** none.

## Out-of-scope (route to lane owner)

- eve.py item 61 (centered menu), 65 (Enter binding), 66 (animations live), 67 (100% real cleanup) → parallel sanctum execution lane (already in flight per heartbeat).
- spawn-setup-wizard mintty exit 126 fix → same parallel lane.
- EVE.exe icon embed + rebuild → same parallel lane.
- Per-project bugfixes (kernel-apk, sinister-os, sinister-panel, etc.) → respective lanes.

## Execution order (this /loop fire's TODO)

1. Item #1 — utterance sweep (high signal, low risk; clears 45 stale rows)
2. Item #2 — version-snapshot P0 scaffold (no code, additive)
3. Item #3 — command-center P0 plumbing (with mesh-coord lock)
4. Item #5 — inbox hand-off to parallel lane (5 min)
5. Item #6 — forever-improve review (10 min)
6. Item #4 — 9 DELETE candidates (move to `_archive/` first, not delete)
7. Item #7 — resume-point cap check

Each item ships as its own commit per `frequent-detailed-commits-per-agent-2026-05-25` doctrine (Shipped/Smoke/Refs format).

## Loop discipline

- Per `loop-relentless-pursuit-doctrine-2026-05-25`, ship ≥1 item per fire; do NOT end turn while items remain queueable.
- Each fire: re-check parallel lane heartbeat to avoid duplicate work.
- Re-prune this plan each fire: completed items struck through; new utterances added at top.
- If queue empties: re-poll `fleet-updates.jsonl` for cross-lane work; if still empty, ScheduleWakeup 1500s and rest.

## Composes with (doctrine)

- `loop-relentless-pursuit-doctrine-2026-05-25` (relentless variant of LOOP MODE)
- `sanctum-scope-discipline-2026-05-24` (high-level only)
- `safe-quality-loops-doctrine-2026-05-24` (12 guardrails)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` (precise verbs + same-turn evidence)
- `frequent-detailed-commits-per-agent-2026-05-25` (Shipped/Smoke/Refs format)
- `single-repo-push-policy-2026-05-25` (sanctum branch only)
