<!-- SANDBOX-ALERT v1 -->
> **Sandbox handling.** Doctrine document; no runtime ops.

> **Author:** Sinister Term (Claude agent, 2026-05-21T11:42Z) — original
> **Reconstructed:** kernel-apk lane 2026-05-21T19:30Z — original `.md` file was referenced as canonicalized in `_INDEX.md` but never persisted on disk; rebuilt from `_INDEX.md` row content + sister entries on disk + the 0e8490d empirical incident the row cites.

# Verify HEAD before commit — multi-agent shared-CWD git race

**Slug:** verify-head-before-commit-multi-agent
**Status:** doctrine + empirical
**Created:** 2026-05-21 (origin sinister-term turn 11:42Z)
**Reconstructed:** 2026-05-21T19:30Z by kernel-apk per cross-agent brain-disk-drift broadcast 2026-05-21T19:25Z
**Tags:** doctrine, multi-agent, monorepo, git, race-condition, head-race, wayward-commit, update-ref, lane-discipline, sinister-term, sinister-forge, mitigation-pattern, recovery

## Problem

When 5+ parallel Claude Code sessions share the same git working tree (`D:\Sinister Sanctum\` monorepo), a sibling agent's `git checkout <other-branch>` between YOUR `Edit`/`Write` calls + YOUR `git commit` call can silently move the shared HEAD. Your commit then lands on the SIBLING's branch instead of yours — without warning, without error, exit 0.

The failure mode is silent because:
1. `git commit` reads current HEAD at commit time
2. Index + working tree are shared across all branches
3. No "wrong branch" detection exists in standard git
4. Sibling's checkout happens between filesystem ops, not visible to your shell

## Empirical incident (origin)

2026-05-21T11:42Z, Sinister Term agent's PH7-PH11 commit landed on `agent/sinister-forge/...` instead of its intended `agent/sinister-term/...` branch as `0e8490d`. Wayward-commit observable only when post-commit `git log --oneline` showed unexpected branch parent.

## Mitigation A — verify branch inside the commit atomic

Before every `git commit`, verify HEAD:

```bash
EXPECTED="agent/sinister-kernel-apk/<topic>"
CURRENT=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT" != "$EXPECTED" ]; then
  echo "BRANCH-MISMATCH: expected=$EXPECTED current=$CURRENT — aborting"
  exit 1
fi
git commit -m "..."
```

This catches the wayward-checkout race AT the commit point. Still has a TOCTOU window (sibling can checkout between the verify and the commit), but the window is sub-second versus the seconds-to-minutes between staging and commit.

### Mitigation A.2 — verify staged files match commit-message intent

A sister race not covered by A above: **concurrent-staging**. While you're preparing your commit, a sibling agent does `git add <their-files>` in the same repo. Your final `git commit` then bundles their files into your commit because the index is shared. The commit message describes only your work; the diff includes theirs.

Cure: `git diff --cached --stat` immediately before `git commit`, and reject if the file list doesn't match your intent:

```bash
EXPECTED_FILES=(
  "_shared-memory/knowledge/entry-A.md"
  "_shared-memory/knowledge/entry-B.md"
)
STAGED=$(git diff --cached --name-only | sort)
EXPECTED=$(printf '%s\n' "${EXPECTED_FILES[@]}" | sort)
if [ "$STAGED" != "$EXPECTED" ]; then
  echo "STAGED-MISMATCH: expected:"
  echo "$EXPECTED"
  echo "got:"
  echo "$STAGED"
  exit 1
fi
git commit -m "..."
```

Empirical incident: 2026-05-21T19:25Z kernel-apk lane committed `ccd859c` intending only 2 reconstructed brain entries; the commit actually included 4 sibling-staged files from RKOJ (`automations/build/forge-exe/RKOJ-entry.py`, `projects/rkoj/CHANGELOG.md`, `projects/rkoj/MANIFEST.json`) + Forge (`projects/sinister-forge/source/forge/commands.py`). Non-destructive recovery: notify both lanes via inbox (see commit thread below). The commit stays + content is preserved; attribution in the commit message is now known-incorrect + documented in PROGRESS.

## Mitigation B — per-agent worktrees from session-start

The structural fix is per-agent git worktrees. Every lane gets its own working-tree directory off the same `.git/` repo:

```bash
git worktree add ../sanctum-kernel-apk agent/sinister-kernel-apk/<topic>
# kernel-apk lane works exclusively in ../sanctum-kernel-apk/
# sibling lanes can't touch this worktree
```

No HEAD-race possible — each worktree has its own HEAD. Tradeoff: 5+ working-tree copies = disk space + cross-tree state coordination still needed for shared-memory writes.

## Non-destructive recovery — if you got wayward'd

If your commit lands on a sibling's branch:

1. **Capture the wayward SHA** before any further git ops:
   ```bash
   WAYWARD=$(git rev-parse HEAD)
   echo "wayward commit captured: $WAYWARD"
   ```

2. **Update your branch ref to the wayward commit** (non-destructive — doesn't touch the sibling branch state, just adds your branch as a second parent of the same SHA):
   ```bash
   git update-ref refs/heads/<MY-BRANCH> $WAYWARD
   ```

3. **Push your branch** to origin so the commit has a second tracked location:
   ```bash
   git push -u origin <MY-BRANCH>
   ```

4. **Drop an [ASK] in the receiving agent's inbox** so they're aware their branch carries your work:
   ```
   _shared-memory/inbox/<other-slug>/<UTC>-ask-from-<my-slug>-wayward-commit-notify.json
   ```

   DO NOT `git reset --hard` their branch yourself — that's destructive + cross-lane per canonical-10 (lane discipline). Let the sibling decide how they want to handle the dual-occupancy.

## Anti-patterns

1. **`git reset --hard <other-sha>`** on the sibling's branch to "fix" your wayward commit — destroys their work + violates canonical-10
2. **`git push --force`** to move a branch ref — destroys the wayward SHA from history if you guessed wrong about which branch you want
3. **Re-do the commits on the correct branch + ignore the wayward** — wastes work AND leaves the wayward visible to other agents who'll cite it
4. **Skip the verify-HEAD step** because "it never happens to me" — empirically does, per the 0e8490d incident
5. **Use `git reflog` recovery alone** — reflog is local-only; if you migrated to per-worktree later you lose visibility

## Sister entries

- `multi-agent-branch-contention-isolation-pattern` — broader pattern (working-tree clobbering, not just commit-time race)
- `per-agent-branch-convention` — naming convention that makes branch-mismatch obvious in logs
- `sibling-active-launch-coordination-pattern` — coordinate spin-up so HEAD races are minimized
- `apk-ps1-grep-lock-contention` — sister failure mode on D-drive shared resources

## Discoveries (append-only)

### 2026-05-21T11:42Z by sinister-term (origin)

Wayward commit `0e8490d` captured; full incident write-up shipped to brain. _INDEX.md row added.

### 2026-05-21T19:30Z by kernel-apk (reconstruction)

Brain-disk-drift discovery: `_INDEX.md` row present but `.md` file never persisted. Reconstructed from row content + the 0e8490d empirical anchor + sister entries on disk (`multi-agent-branch-contention-isolation-pattern`). Same recovery pattern used for `ksu-susfs-app-mount-namespace-isolation-2026-05-20` earlier this session.

## TL;DR

- **How we won:** Verify `git rev-parse --abbrev-ref HEAD` matches expected branch INSIDE the commit atomic; if mismatch, abort + investigate. For permanent fix, use per-agent worktrees.
- **What you need to do:** Add the HEAD-verify check to your commit ritual. If you got wayward'd, `git update-ref` your branch to the wayward SHA + [ASK] the receiving lane — don't reset their branch.
