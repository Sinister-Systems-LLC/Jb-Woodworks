<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Branch checkout silently undoes doctrine (pre-doctrine-HEAD branch-cut hazard)

> **Status:** doctrine, observed, binding
> **Origin:** rkoj-lane resume session 2026-05-23T06:25Z. Switched to the previously-cut branch `agent/rkoj/complete-without-operator-2026-05-23` (HEAD `b9e89dc`) to continue work — and the working tree's `CLAUDE.md` immediately reverted to the 6-step cold-start (no understand-anything pre-call, no DO-NOT-REVERT block) because that branch was cut BEFORE the anti-revert doctrine commit `73c628b` landed.

## The hazard

The six canonical session-start protections (`bypassPermissions`, `dangerously-skip-permissions` allow, `understand-anything` plugin enabled, CLAUDE.md cold-start steps 0/2/3, brain entries indexed) are codified in files that:

- live in working-tree paths (`CLAUDE.md`, `~/.claude/settings.json`, `.claude/settings.json`)
- get **silently rewritten by `git checkout`** when switching to any branch whose tip predates the doctrine commit

The `canonical-protections-check.ps1` SessionStart hook catches this on the NEXT session start — but the CURRENT session has already been running against the regressed working tree and may have read CLAUDE.md before the regression became visible.

## Empirical trace (2026-05-23T06:25Z)

| Step | Tool | Effect |
|---|---|---|
| 1 | `git checkout agent/rkoj/complete-without-operator-2026-05-23` | switched HEAD `73c628b → b9e89dc` |
| 2 | system reminder fired: *"D:\Sinister Sanctum\CLAUDE.md was modified, either by the user or by a linter"* | the modification was git itself, not a user/linter — but Claude Code's modification detector classified it generically |
| 3 | observed in-message diff | CLAUDE.md now reads "Cold-start in 6 steps" (the pre-doctrine version), no DO-NOT-REVERT block, no understand-anything step 0 |
| 4 | recovery | `git checkout agent/sinister-sanctum/anti-revert-doctrine-2026-05-23` → CLAUDE.md restored; then `git checkout -b agent/rkoj/next-slate-2026-05-23` to cut a fresh rkoj branch from the doctrine HEAD |

## The pattern (binding for every lane)

**Always cut new per-agent branches off the latest doctrine HEAD, not off a stale pre-doctrine branch.**

```bash
# WRONG — resurrects a pre-doctrine branch + silently reverts CLAUDE.md
git checkout agent/<slug>/<old-topic-from-yesterday>

# RIGHT — cut fresh from latest doctrine HEAD
git checkout <branch-with-latest-doctrine>     # e.g. agent/sinister-sanctum/anti-revert-doctrine-2026-05-23
git checkout -b agent/<slug>/<new-topic-today>
```

If you MUST switch to an existing pre-doctrine branch (e.g. to recover in-progress work), immediately rebase or fast-forward-merge the doctrine commit into it BEFORE doing any other work:

```bash
git checkout agent/<slug>/<pre-doctrine-branch>
git merge --no-edit <doctrine-HEAD-ref>        # or `git rebase <doctrine-HEAD-ref>`
# now CLAUDE.md + .claude/settings.json + brain entries are back to doctrine state
```

## Why the SessionStart hook isn't enough

`automations/canonical-protections-check.ps1` runs at **session start**. The branch-checkout hazard fires **mid-session** when an agent navigates away from the doctrine HEAD. So the hook catches the regression for the next spawn, not for the current one.

Three secondary defenses for the current session:

1. **Detect the system reminder** — when Claude Code fires *"CLAUDE.md was modified, either by the user or by a linter"* and you didn't ask for that edit, treat it as a possible doctrine-regression event. Grep the working-tree CLAUDE.md for the DO-NOT-REVERT marker; if missing, you regressed.
2. **Always verify HEAD before substantive work** — `git rev-parse HEAD` + `head -5 CLAUDE.md`. Three seconds; catches the case before any other change cascades.
3. **Make agents cut new branches off the current HEAD by default** — never resurrect stale per-agent branches. The 0455Z forward-plan for rkoj named `agent/rkoj/complete-without-operator-2026-05-23` as the branch but that branch was cut at the pre-doctrine HEAD. The 0621Z forward-plan corrects this by cutting `agent/rkoj/next-slate-2026-05-23` off the doctrine HEAD.

## Anti-patterns

1. **Resurrect a stale per-agent branch from yesterday** — silently regresses doctrine even though the docstring on the branch says it's the same lane.
2. **Trust the system reminder phrasing** — *"the user or a linter"* misses the git-checkout case; assume it could be git too.
3. **Skip `git rev-parse HEAD` after branch switch** — the working tree change is the only visible signal; a tight loop of edits will bury it under tool output.
4. **Patch CLAUDE.md back manually after a regression** — let `git checkout` of the doctrine commit do the restoration; manual splicing diverges from the canonical reference.

## Recovery procedure (single-session, one-liner)

If a branch checkout regressed CLAUDE.md:

```bash
git checkout <doctrine-branch-or-tag>     # restores all 6 protections
git checkout -b agent/<your-slug>/<new-short-topic>     # new branch off restored HEAD
# proceed with work; old pre-doctrine branch can stay or be deleted
```

## Composability

- `do-not-revert-operator-canonical-protections-2026-05-23` — the canonical six-protection doctrine that THIS pattern protects against an additional regression vector for.
- `multi-agent-branch-contention-isolation-pattern` — per-agent branch hygiene; reinforces "cut fresh, don't resurrect stale".
- `sanctum-mirror-orphan-corruption-pattern-2026-05-23` — related git-discipline lesson.
- `sanctioned-bypasses-doctrine-2026-05-21` (2026-05-23 evening block) — defines the protections this pattern shields.
- `agent-autonomy-push-and-completion-2026-05-23` — explains why per-agent branches now push freely (so a fresh cut isn't a coordination cost).

## Tags (for INDEX.md)

doctrine, observed, binding, git-checkout, branch-cut, pre-doctrine-head, claude-md-regression, settings-json-regression, working-tree, system-reminder, the-user-or-a-linter, rev-parse-head-verify, fresh-cut-from-doctrine-head, fast-forward-merge-doctrine, rkoj-lane-empirical-anchor, 2026-05-23
