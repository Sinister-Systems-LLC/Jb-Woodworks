<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Overseer lessons from first-fire audit (sinister-term, 2026-05-25)

> Folded from `_shared-memory/knowledge/overseer-audit-sinister-term-2026-05-25.md`. These are the operating lessons the Overseer should carry into every subsequent audit.

## Lesson 1: ALWAYS `git status --short` before the first commit of an audit

If foreign-lane files appear staged, ABORT and surface to operator rather than committing through them. Root cause in first audit: Overseer's `git add cli.py && git commit` committed 41 unrelated sibling-staged files because `git commit` (no path arg) commits the whole index, not just the just-added file.

## Lesson 2: Prefer `git commit --only <path>` over `git add <path> && git commit`

The `--only` pathspec on the commit guarantees scope even if the index has other dirty entries. This is the canonical pattern for audit-driven commits.

## Lesson 3: Detect stale sibling git processes before entering a commit cluster

If `tasklist | grep git.exe` shows a process older than 30 minutes, the `.git/index.lock` may be OS-pinned to that process. The auto-push daemon's 30-min cadence + a single hung git invocation can block Overseer commits indefinitely. Mitigation: schedule audit commits to fire on the heartbeat-quiet window between auto-push ticks.

## Lesson 4: TRIVIAL/LOW apply; MEDIUM/HIGH propose -- this charter held under pressure

In the first audit, 2 LOW findings (firefox-bridge path env-var + outdated banner) were auto-applied; 4 MEDIUM findings (orphan entry-point, DRY refactor, inert IPC scaffold, test coverage gaps) were surfaced to operator. Held the line; operator gets a sane review queue, not a wall of speculative diffs.

## Lesson 5: Smoke evidence in the same turn as the fix is non-negotiable

Per no-bullshit rule 2. Even if a commit can't land (sibling lock), the smoke evidence (pytest 3/3 PASS) is recorded in the audit doc so a future operator + future Overseer iteration can verify the fix BEHAVIOR even when the COMMIT didn't materialize.

## Lesson 6: Contradiction-engine scoring takes <10s and prevents 90% of rollback churn

Per `docs/08-contradiction-engine.md`. Apply: (1) hostile reviewer's strongest argument; (2) edge case missed; (3) future-operator-a-year-out perspective. If sum/3 > 6, ROLL BACK. Both first-audit fixes scored 2/10 and 3/10 -- the bar caught nothing this round, but the discipline of running it primes muscle memory.

## Lesson 7: Mesh-coord lock-and-release IS the audit boundary

Lock at audit-start with TTL <= 1800s; release at audit-end. If audit overruns the TTL, RE-REGISTER rather than letting auto-purge silently re-open the lane to another agent. The first audit acquired/released cleanly; this pattern should be the floor for every future audit.

## Lesson 8: Cost reporting in the audit doc itself

First audit cost $0.15--0.30 cost-eq -- ~3--6% of the $5/day Overseer cap. Per `docs/02-token-efficiency.md` self-monitoring, every audit doc gets a "Token cost of this audit" section so the per-attachment burn-rate is visible to the daily sanctum check.

## Composes with

- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (rules 1, 2, 4)
- `_shared-memory/knowledge/frequent-detailed-commits-per-agent-2026-05-25.md` (one-commit-per-fix discipline)
- `_shared-memory/knowledge/mesh-coordination-and-resource-lifecycle-2026-05-24.md` (check/register/release)
- `projects/sinister-overseer/docs/05-fails-to-learn.md` (lessons-store schema)
- `projects/sinister-overseer/docs/08-contradiction-engine.md` (rollback threshold)
