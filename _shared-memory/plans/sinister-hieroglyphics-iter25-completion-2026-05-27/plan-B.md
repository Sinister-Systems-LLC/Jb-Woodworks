# Plan B — Sinister Hieroglyphics iter-25 -> completion (race-resilient)

> Author: RKOJ-ELENO :: 2026-05-27
> Triggered by operator directive (verbatim 2026-05-26T20:56Z): *"commit
> and push the iter-26 work create a planb to complete everything i said
> to do and keep working"*

## Why Plan B exists

Plan A (`plan.md`) assumes git commits land on the first attempt. In
practice, the kernel-apk-lane spawn lives in a sanctum monorepo that
is shared by ~20 concurrent Claude agents — every `git add` / `git
commit` / `git checkout` races against `.git/index.lock`, and a
parallel agent's `git checkout` mid-stage can sweep our staged files
into THEIR commit on THEIR branch. Observed this turn (verifiable
from reflog):

- Commit 65f1cda (intended hieroglyphics iter-25) landed on
  `agent/eve-exe/hive-genesis-petals-audit` with 3 sinister-term files
  swept in.
- Commit b508c9b (clean cherry-pick to hieroglyphics) got orphaned
  when a parallel `git checkout` reset the local branch ref.
- Commit 64c1a65 (re-cherry-pick) succeeded — but only after 3 lock
  contention rounds and a manual `git branch -f` to sync local to
  remote.

Plan B assumes EVERY git operation will race AT LEAST ONCE and bakes
recovery into the workflow.

## Core Plan B principles

1. **File-system is source of truth, git is eventual consistency.**
   Ship to disk first, verify via tests, then attempt commit. If
   commit races, the work is still durable on disk + can be re-staged
   from a different branch later.

2. **Idempotent commit script.** A small helper that:
   - Reads a list of "iter-N hgly paths" from a JSON manifest
   - Stashes anything else in the index
   - Stages ONLY the manifest paths
   - Commits with the canonical message
   - Pushes to `agent/sinister-hieroglyphics/...` explicitly (NOT current branch)
   - On any failure, dumps the staged tree to a `_quarantine/` directory
     so the work isn't lost when the parallel agent's `git reset` runs

3. **Branch-explicit pushing.** Always
   `git push origin <sha-or-HEAD>:refs/heads/agent/sinister-hieroglyphics/<branch>`
   — never `git push origin <branch>` (which pushes the locally-named
   branch, which may have been redirected by a parallel agent).

4. **Out-of-band trajectory writes.** The density JSONL trajectory
   accumulates rows in `_shared-memory/hgly-density-trajectory.jsonl`
   — that file is durable even when git is in a wedged state. The
   "track" call from loop_checkpoint.py works regardless of branch.

5. **Tests are the gate.** Acceptance test green + working-tree files
   correct = "shipped" for Plan B purposes, even if the commit is
   pending. The commit lands eventually via the relentless retry loop.

## Phase order (mirrors Plan A but with race-resilient steps)

| # | Phase | Acceptance | Commit strategy |
|---|---|---|---|
| **iter-26** ✅ on disk | loop_checkpoint -> density hook | 4/4 tests pass + live e2e grew JSONL 1→2 | retry until landed |
| **iter-27** | `_tpl_big_*` ×5 in `hgly_corpus_seed.py` | parse-clean on each generated program | retry until landed |
| **iter-28** | Re-`track`; document ratio delta in PROGRESS | trajectory has ≥3 rows | retry until landed |
| **iter-29** | `--by-category` flag on `hgly_density.py corpus` | new JSON shape with `categories` key + test | retry until landed |
| **iter-30** | Phase 9 swarm fanout via `sinister_swarm.py` | 5+ slice results all parse | retry until landed |
| **iter-31** | Phase 9.6 trainer-input projection | `hgly_trainer.py` dry-run emits ratio + loss | retry until landed |
| **iter-32** | Phase 9.7 monotonic-revert hook | synthetic regression -> revert verified | retry until landed |

## iter-26 commit recovery flow (this turn)

If/when `.git/index.lock` clears:
1. `git reset HEAD` (clear any racing stages)
2. `git add automations/loop_checkpoint.py projects/sinister-hieroglyphics/tests/test_loop_checkpoint_hgly.py projects/sinister-hieroglyphics/PROGRESS.md _shared-memory/hgly-density-trajectory.jsonl _shared-memory/plans/sinister-hieroglyphics-iter25-completion-2026-05-27/plan.md _shared-memory/plans/sinister-hieroglyphics-iter25-completion-2026-05-27/plan-B.md`
3. `git status -- <those paths>` — verify ONLY those are staged
4. `git diff --cached --name-only` — if any non-listed file appears, `git reset HEAD <bad-file>`
5. `git commit -m '<iter-26 detailed format>'`
6. `git log -1 --name-only` — verify commit content
7. `git push origin HEAD:refs/heads/agent/sinister-hieroglyphics/iter24-token-density-measure-2026-05-26`
8. If push rejected (non-fast-forward), `git fetch origin` + `git branch -f` + retry

If commit lands on wrong branch (parallel-agent branch switch race):
1. Save SHA from `git log -1 --format=%H`
2. `git branch -f agent/sinister-hieroglyphics/iter24-token-density-measure-2026-05-26 origin/agent/sinister-hieroglyphics/iter24-token-density-measure-2026-05-26`
3. `git checkout agent/sinister-hieroglyphics/iter24-token-density-measure-2026-05-26`
4. `git cherry-pick --no-commit <saved-sha>`
5. Unstage non-hgly files: `git reset HEAD projects/sinister-term/ projects/sinister-overseer/ etc.`
6. `git commit -m '<re-cherry-pick message>'`
7. Push as step 7 above

## "Keep working" iter-27 prep (on disk, ready when commit clears)

While iter-26 commit waits, draft iter-27 (`_tpl_big_*` templates) on
disk:

- `automations/hgly_corpus_seed.py` — add 5 new templates between line
  570 (current `_tpl_recv_send`) and line 580 (TEMPLATES list end)
- Each template targets 50-150 LOC and combines 3-5 glyph categories
- Update TEMPLATES list to include them with names
  `big-memory-pool`, `big-concurrent-counter`, `big-sim-pipeline`,
  `big-matrix-multiply`, `big-io-pump`
- Run `hgly_corpus_seed.py gen --count 10 --kind mixed` to ensure new
  templates generate clean
- Run `hgly_density.py corpus` to re-measure with the new templates
  in the active rotation (corpus stays at 255; ratio shift reflects
  template mix change)

## Stop condition

Plan B is complete when:
- Plan A's stop condition is met (ratio < 0.40 OR honest asymptote
  documented; 5+ trajectory rows; trainer-input projection live)
- The cross-agent git-race doctrine entry is in `_shared-memory/knowledge/`
  with the recovery patterns from this turn baked in

## Race-resilience doctrine to write

After this iter, write
`_shared-memory/knowledge/sanctum-monorepo-git-race-recovery-doctrine-2026-05-27.md`:

1. Cross-agent contention happens; assume EVERY `git` op races
2. File-system durability + idempotent retry > one-shot commit attempts
3. Always `git push origin HEAD:refs/heads/<branch>` (never bare branch name)
4. `git ls-files <path>` is the trusted check for "is this file
   tracked on this branch RIGHT NOW"
5. Recovery from wrong-branch commit: `git branch -f` + cherry-pick
   `--no-commit` + selective unstage + re-commit
6. Composes with: `one-terminal-per-project-no-overlap-doctrine-2026-05-25`,
   `stale-git-lock-auto-cleanup-doctrine-2026-05-26`,
   `frequent-detailed-commits-per-agent-2026-05-25`.
