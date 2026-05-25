<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-20

# Topic: Multi-agent branch contention — the isolation pattern for master-lane work

> Status: doctrine + empirical (root-caused this session)
> Tags: doctrine, multi-agent, branch-contention, isolation, git-reset-hard, working-tree-loss, shared-d-drive, canonical-3, canonical-10, master-lane, sibling-lane, hostile-checkout, race-condition, recovery
> First codified: 2026-05-20 (self-observed mid-session)
> Composes with: `canonical-10` (lane discipline) + `canonical-3` (per-agent branch) + `cross-agent-coordination` + `apk-ps1-grep-lock-contention` (sibling-pattern: file-handle contention)

## TL;DR

When 5+ parallel Claude Code sessions share the same D:\Sinister Sanctum\ workspace, a sibling-lane session can do `git checkout <their-branch>` + `git reset --hard HEAD` at ANY moment, which **deletes the master-lane agent's uncommitted working-tree edits** and switches HEAD to the sibling's branch. The master agent only finds out when its NEXT tool call sees the workspace in an unexpected state.

**Mitigation:** cut an isolated branch off `main` BEFORE writing significant master-lane work; commit FIRST then push; never trust the working tree to persist across multi-second pauses. Treat the shared workspace like an optimistic-locking database: stage + commit eagerly, push to lock in.

## The empirical failure (this session, 2026-05-20T23:30Z)

This sweep landed on `agent/sinister-os/ph1-bootstrap-2026-05-20` (prior turn's master branch). I made these edits:

1. `automations/start-sinister-session.ps1` — added `'auto'` BuiltinPhrase + modeOpts row + modeMap entry + custom-prompts renumber (~17 LOC).
2. `_shared-memory/knowledge/_INDEX.md` — added auto-mode-launcher-pattern row at top.
3. Created `_shared-memory/knowledge/auto-mode-launcher-pattern.md` (~150 LOC).
4. Created `D:\Sinister Sanctum\tools\session-launcher\Start-Sinister-Auto-Session.bat` (~50 LOC).

Smoke-tested the launcher (`-Mode auto -NoLaunch -Fast` exited 0; PSParser clean). Wrote a PROGRESS milestone for test.md.

Then `Bash` returned: `_shared-memory/PROGRESS/test.md: No such file or directory`.

Investigation via `git reflog`:

```
8f4f211 HEAD@{0}: reset: moving to HEAD       ← clobbered my uncommitted edits
8f4f211 HEAD@{1}: commit: retract: snap-emu-wsl-bg-detached-loop-dies entry
8d3e570 HEAD@{2}: checkout: moving from agent/sinister-panel/expand-resume-2026-05-20T1413Z to agent/sinister-snap-api/brain-expansion-2026-05-20
c0d2d7f HEAD@{3}: commit: panel: R11 ts-prune dead-code baseline report
05a3496 HEAD@{4}: commit: panel: brain refresh — localhost-routing + enrollment-buildconfig
493e783 HEAD@{5}: commit: panel: brain x5
acc950d HEAD@{6}: commit: panel: EXPAND-mode deliverables
c3162e6 HEAD@{7}: commit: panel: brain reconcile
5f98278 HEAD@{8}: checkout: moving from agent/sinister-snap-api/brain-expansion-2026-05-20 to agent/sinister-panel/expand-resume-2026-05-20T1413Z
```

A **panel-lane sibling session** had been doing 5 commits + 2 branch checkouts while I edited. At reflog @{0} a `reset: moving to HEAD` wiped the working tree. My uncommitted PS1 edits, INDEX edits, brain-entry file, and canonical-tree bat were ALL gone from disk. The Desktop bat (on `C:\`, outside the workspace) survived.

The previous turn's brain-index drift commit (be8726e) was on `agent/sinister-os/ph1-bootstrap-2026-05-20` and `git merge-base --is-ancestor be8726e HEAD` returned `NO` — meaning my own prior commit was no longer in HEAD's ancestry. The sibling's checkouts had moved HEAD past my commit.

## Why it happens

1. **Shared workspace.** All ~5 parallel sessions operate on D:\Sinister Sanctum\ — same git index, same working tree.
2. **Branch is process-global.** `git checkout` changes the working tree for ALL processes pointing at this repo. There's no per-session branch isolation.
3. **`git reset --hard HEAD` discards working-tree state.** When a sibling agent needs to clean their workspace (e.g. before pulling fresh main, or after a failed merge), they reset. The reset takes the WHOLE working tree, including OTHER agents' uncommitted edits.
4. **Tool calls aren't atomic across the sweep.** The master agent might `Read foo.md`, then 10 seconds later `Edit foo.md`. In those 10 seconds, the sibling can swap branches + reset + delete the file. The Edit then fails with "file does not exist" or worse, succeeds against a different branch's content.

## Mitigation: the isolation pattern

### Step 1 — Cut an isolated branch off main BEFORE significant work

```bash
git checkout main
git checkout -b agent/<your-slug>/<short-topic>-<date>
```

Why off `main`: it's a stable baseline. Sibling agents are checking each other's lane branches, not `main`. The `main` branch advances slowly (operator merges).

Why a fresh branch: even if a sibling does `git checkout sibling-branch && git reset --hard`, your local branch ref still points at your commit (only HEAD moved). You can `git checkout <your-branch>` to restore.

### Step 2 — Commit FIRST, then push, in small batches

The contention window is between edit and commit. Shrink it:

- Don't accumulate 5 file edits + a brain entry + a bat across multiple Bash calls THEN commit. The longer your working tree carries uncommitted work, the bigger the loss-target.
- Edit one logical unit → `git add` immediately → `git commit` immediately → `git push` immediately. The push is the durability boundary.
- If the work is multi-file and they really must commit together, do them all in one tool-call sequence with no intermediate Bash calls that another agent could schedule a checkout into.

### Step 3 — Verify branch + HEAD before EVERY commit

```bash
git branch --show-current   # am I on the branch I think I'm on?
git log --oneline -1        # is HEAD where I expect?
```

If branch or HEAD changed unexpectedly, recover via:

- `git stash` (saves uncommitted) → `git checkout <intended-branch>` → `git stash pop`
- OR `git checkout -b <new-isolated-branch>` (start fresh on isolated branch with current uncommitted work)

### Step 4 — Treat the working tree as ephemeral

- Don't `Read` a file 5 tool-calls before you need it; the disk may have changed by then.
- If a file you `Read`ed earlier seems to have moved/changed, re-read before `Edit`ing.
- If `Edit` returns "File has been modified since read", that's the contention signal — re-`Read` and re-do the `Edit`.

### Step 5 — Recovery when contention hits

If you discover mid-turn that your uncommitted work was clobbered:

1. **Don't panic-commit on the sibling's branch.** Check `git branch --show-current` first. Committing master-lane work on a sibling-lane branch violates canonical-10.
2. **`git checkout -b <isolated-branch>` off the most recent main commit.** Cherry-pick or re-apply only your work.
3. **The Desktop side persists.** Files on `C:\Users\Zonia\Desktop\` are outside the workspace and survive resets. Use those as recovery anchors.
4. **PROGRESS log + brain entry document the loss.** Even if the work itself is gone, the lesson goes into the brain.

## Anti-patterns

- **Editing across multiple agents on the same branch.** If sibling-A is on `agent/sinister-os/ph1-bootstrap-2026-05-20` AND master is also using it, contention is guaranteed. Master should cut a fresh `agent/sinister-sanctum/<own-topic>-<date>`.
- **Running `git checkout` for "convenience".** Every checkout is a potential reset target. Stay on your branch.
- **Pushing without verifying HEAD.** `git push -u origin <branch>` pushes whatever the LOCAL `<branch>` ref points at — NOT whatever's currently checked out. If you've been working on a different branch, the push doesn't include your commits.
- **Accumulating >30 min of uncommitted work.** The longer the window, the higher the loss probability when sibling activity is concurrent.
- **Assuming `git ls-files <path>` reflects reality.** It reflects the index, which may have been reset by a sibling. Cross-check with `git log --all -- <path>` + actual `ls`.
- **Trusting `git stash list` ordering.** Stashes can be made by sibling agents (`auto-stash by panel-lane post-R4-2026-05-20T1900Z` in this session's stash list). Identify yours by message before popping.

## Composes-with

| Doctrine | How it composes |
|---|---|
| `canonical-10` (lane discipline) | The sibling agent doing the reset wasn't violating canonical-10 — they were cleaning their own branch. The collision is structural to shared-workspace multi-agent. Canonical-10 stays valid; this doctrine adds the resilience layer. |
| `canonical-3` (per-agent branch) | The isolation pattern IS per-agent-branch + cut-from-main. Canonical-3 says "work on per-agent branch"; this says "cut it off main, not off sibling's HEAD". |
| `cross-agent-coordination` | Cross-agent messages can warn "I'm about to do a reset" but in practice that's unreliable (siblings move fast). Better to assume contention and isolate. |
| `apk-ps1-grep-lock-contention` | Sibling-pattern at the file-handle level (`mv`/`cp` fails because sibling holds recursive grep). Same family: shared resource + concurrent access + tool fails late. |
| `audit-shipped-not-flipped` | Contention-loss creates "shipped but not on disk" drift. The audit pattern catches it next cold-start. |

## Where it lives

| File | Role |
|---|---|
| This brain entry | Doctrine |
| `_shared-memory/PROGRESS/Sinister Sanctum.md::2026-05-20 23:35` | First empirical loss event |
| `_shared-memory/plans/sanctum-auto-2026-05-20T2340Z/master-plan.md::M1` | Scope-plan row that produced this entry |

## Related topics

- [`canonical-3-per-agent-branch`](./canonical-3-per-agent-branch.md) (if present)
- [`cross-agent-coordination`](./cross-agent-coordination.md)
- [`apk-ps1-grep-lock-contention`](./apk-ps1-grep-lock-contention.md)
- [`audit-shipped-not-flipped`](./audit-shipped-not-flipped.md)
- [`auto-mode-launcher-pattern`](./auto-mode-launcher-pattern.md)
- [`expand-mode-contract`](./expand-mode-contract.md)
