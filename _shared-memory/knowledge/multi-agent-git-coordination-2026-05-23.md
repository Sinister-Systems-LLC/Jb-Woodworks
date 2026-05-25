<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: correction
  confidence: 0.95
  reinforcements: 0
  half_life_days: 365
-->
# Multi-agent git coordination (2026-05-23 evening)

> **Status:** doctrine, standing-rule, binding for every EVE session that touches git.
> **Origin:** operator 2026-05-23 evening: "fix these issues and ensure all agents dont fuck with each other" + "take note there is another sanctum agent running to complete things". Two sanctum-lane agents racing on the same repo produced: (a) `index.lock` collision, (b) HEAD-switching mid-commit, (c) my commit landed on `agent/rkoj/next-slate-2026-05-23` instead of `agent/sinister-sanctum/anti-revert-doctrine-2026-05-23` because a sibling switched HEAD between my read and my stage.

## What went wrong

Two-process race on a single working tree:

1. Sanctum-A reads `git status` → branch X.
2. Sanctum-B `git checkout` → branch Y (HEAD now Y).
3. Sanctum-A `git add ...` → stages onto Y's index.
4. Sanctum-A `git commit` → commit lands on Y, NOT X.

Plus: when both processes hit `git add` simultaneously, the loser sees `fatal: Unable to create '.git/index.lock': File exists` and crashes.

This is a CROSS-LANE DISCIPLINE violation (canonical-10): each agent should commit only on its own `agent/<slug>/<topic>` branch.

## The fix — three layers

### Layer 1: never trust HEAD between operations

Any agent that runs `git add` MUST verify the current branch IMMEDIATELY before committing AND use an atomic chain:

```bash
# BAD (race window between checkout and add+commit):
git checkout my-branch
git add file
git commit -m "..."

# GOOD (one shell, single git invocation tree):
git checkout my-branch && git add file && git commit -m "..."
```

For a single-line commit-chain `cd "$REPO" && git checkout $BR && git add $FILES && git commit -m "$MSG"` — if any step fails, the whole chain aborts. No partial commits on the wrong branch.

### Layer 2: `git update-ref` for commit-without-checkout

When another agent's commit SHA happens to contain your work (because you committed on top of their state by accident), use `git update-ref` to ALIAS the commit onto your lane's branch:

```bash
git update-ref refs/heads/agent/<your-slug>/<topic> <SHA>
git push origin agent/<your-slug>/<topic>
```

This creates a NEW branch pointing at the existing commit. The original branch still has the SHA — both branches share. Other agents can sort their own branch by rebasing the alias off.

NO checkout needed. NO HEAD touching. Other agents' branch switches can't interfere.

### Layer 3: lock file convention

Before any multi-step git operation, take a per-agent lock:

```bash
LOCK="$REPO/_shared-memory/git-locks/<your-slug>.lock"
mkdir -p "$(dirname "$LOCK")"
# Atomic test-and-set
if ( set -o noclobber; echo "$$ $(date -Iseconds)" > "$LOCK" ) 2>/dev/null; then
    trap 'rm -f "$LOCK"' EXIT
    # ... do your git stuff ...
else
    # Another agent holds the lock; back off
    echo "git-lock held by $(cat "$LOCK")"
    exit 1
fi
```

Lock files live at `_shared-memory/git-locks/<slug>.lock`. Hold only during the active operation; release on exit (trap).

If two agents hit the lock at the same moment, one wins; the other backs off + retries after a short delay or surfaces "git lock held by <other-agent>, retrying in 30s".

## Anti-patterns

1. **`git checkout my-branch` then `git status` then `git add` then `git commit`** — four separate operations, three race windows. ALWAYS chain in one shell.
2. **Skipping branch verification before commit.** Always `git branch --show-current` in the same chain as the commit; if mismatch, abort.
3. **`git reset --hard HEAD~` on a sibling's branch.** Destructive on shared state. Use `git update-ref` to alias commits to your own branch instead.
4. **Force-pushing to clean up after a race.** Compounds the mess. Always create a NEW branch (alias the SHA) instead.
5. **Assuming the working tree is yours alone.** It is shared with every concurrent EVE session in the same repo dir.

## What this composes with

- `_shared-memory/knowledge/agent-autonomy-push-and-completion-2026-05-23.md` — per-agent branches push freely; main is operator-only via auto-push daemon.
- `_shared-memory/knowledge/verify-head-before-commit-multi-agent.md` (if it exists; if not, this entry supersedes).
- `PARALLEL-AGENT-COORDINATION.md` — ownership zones (this entry adds the git-mechanics-level discipline that complements the file-level zones).
- `automations/canonical-protections-check.ps1` — could optionally add a P9 check verifying current branch matches expected per-agent pattern (e.g. `agent/<slug>/*` for known slugs).

## Recovery procedure (when a commit lands on wrong branch)

If your commit `<SHA>` landed on `agent/<other-slug>/<topic>` instead of your `agent/<your-slug>/<topic>`:

```bash
# 1. Alias the commit onto your own branch (no checkout needed)
git update-ref refs/heads/agent/<your-slug>/<your-topic> <SHA>

# 2. Push your branch
git push origin agent/<your-slug>/<your-topic>

# 3. (Optional) ask the sibling's lane to drop the commit from THEIR branch
#    via interactive rebase or git reset, but ONLY if their branch is unpushed.
#    If pushed, leave it — both branches share the SHA harmlessly.
```

The SHA exists once in the object database; both branches can reference it. No duplication of work needed.

## Tags

doctrine, standing-rule, binding, multi-agent, git, coordination, race-condition,
index-lock, head-switching, cross-lane-discipline, canonical-10, recovery, lock-file,
update-ref, atomic-chain, branch-verification, 2026-05-23, operator-screenshot
