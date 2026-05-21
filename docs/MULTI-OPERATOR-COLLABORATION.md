# Multi-operator collaboration — Zonia ↔ ELENO partition + auto-push contract

> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-21
> **Status:** doctrine + scaffolded (operators must onboard ELENO to complete activation)
> **Authority:** operator directive 2026-05-21 verbatim: *"I need you to make sure we have good logic in place so i can work at same time with my partner ELENO. he will be running all of this on his system and we need to work in harmony. so in each project folder we have or create there needs to be a folder wiht his version and a folder with my version that are both linked to the main code base but in a systamatic manor."*

## The two operators

- **Zonia** (`zonia` / `me` / Sinister Sanctum primary operator) — runs on her workstation at `D:\Sinister Sanctum\`. Identity: `sinistersocks5g@gmail.com`.
- **ELENO** (`eleno` / partner operator) — runs on his own workstation. Mirror Sanctum clone at his own path (likely `D:\Sinister Sanctum\` if matching Zonia's layout, or wherever he sets `SINISTER_SANCTUM_ROOT`).

Both work on the same Sanctum codebase in lockstep via GitHub-mediated sync.

## The 3-folder partition per project

Every canonical project folder (`projects/<proj>/`) carries three subfolders:

```
projects/<proj>/
├── source/         ← SHARED CANONICAL CODEBASE (junction or real)
├── me/             ← Zonia's local-only working state
└── eleno/          ← ELENO's local-only working state
```

### What goes where

| Folder | Purpose | Tracked? | Examples |
|---|---|---|---|
| `source/` | The actual project code that both operators work on | YES (full tracking on project's own branch) | All source files, tests, docs, build configs |
| `me/` | Zonia's local configs, scratch experiments, in-progress notes she's not ready to commit | YES (file existence tracked) but contents partially gitignored | `me/scratch/` (gitignored), `me/local-config.json` (tracked if shareable), `me/NOTES.md` (tracked) |
| `eleno/` | ELENO's local configs, scratch, in-progress notes | YES + gitignored same as me/ | Same shape as me/ but ELENO-owned |

The `me/` and `eleno/` folders are tracked at the FOLDER level (so the partition shows up on GitHub) but their `scratch/` subfolders are gitignored to prevent thrash.

### Why both folders exist for both operators

Even though Zonia primarily uses `me/`, the `eleno/` folder exists on Zonia's clone too. Why:

1. **Visibility** — Zonia can see ELENO's checked-in configs (which agents he runs, which projects he's focused on) without pulling a separate branch.
2. **Conflict-free workspace** — when Zonia edits `me/` and ELENO edits `eleno/` concurrently, there are ZERO merge conflicts on `source/` because operator-specific state is partitioned by folder.
3. **Mirror symmetry** — on ELENO's clone, the same two folders exist; he uses `eleno/`. The agent identity flips based on `$env:SINISTER_OPERATOR_SLUG` (set per-machine).

## The branch model per project

Sanctum hosts one branch per project for shared canonical work:

| Branch | Purpose | Who pushes |
|---|---|---|
| `main` | Sanctum hub canonical | Operator-merged only |
| `project/<slug>/main` | Project canonical (e.g. `project/snap-emu/main`) | Operator-merged from agent topic branches |
| `agent/<agent-slug>/<topic>` | Per-agent topic branch | Agent pushes autonomously |

When an agent (Claude / Sanctum) makes a breakthrough commit:

1. Commit lands on `agent/<agent-slug>/<topic>` (per canonical-3).
2. Agent auto-pushes the topic branch to origin (no operator approval needed — topic branches are reversible).
3. Operator reviews + merges `agent/<agent-slug>/<topic>` → `project/<slug>/main` when ready.
4. Periodically, `project/<slug>/main` → `main` (Sanctum hub canonical) merges happen.

ELENO's agents follow the same convention but with `agent/eleno-<topic>/...` namespacing if needed (so we can tell who pushed what).

## Auto-push on breakthrough — commit-message convention

Any commit with one of these prefixes triggers auto-push of the topic branch to origin:

- `feat:` — new feature shipped
- `fix:` — bug fix shipped
- `breakthrough:` — significant architectural win or unblock
- `docs:` — doctrine or design doc
- `chore:` — chore but still pushable

Suffix tokens that block auto-push (operator-gate required):

- `[wip]` — work in progress, do NOT push
- `[draft]` — draft state, hold
- `[secret-pending]` — has unscrubbed secret, MUST scrub before push

The hook is implemented per-project in the agent's `CLAUDE.md` directives (or a project-level `.git/hooks/post-commit` script). Master writes the spec; sibling agents implement per-lane.

## Conflict resolution — who wins?

When both operators touch the SAME source/ file:

1. **Last-push-wins is FORBIDDEN.** Both edits matter.
2. **GitHub PR review** — whichever operator pushes second opens a PR that the other reviews. No force-pushes.
3. **In-person sync** — if both operators are actively working on overlapping files, coordinate via cross-agent inbox (`_shared-memory/inbox/me/` and `_shared-memory/inbox/eleno/`) BEFORE committing.
4. **Default precedence** — if no other signal exists, the operator whose name appears in the `Author:` line of the originating file's first commit has merge-tiebreak authority for that file.

## Cross-operator inbox

Each operator has an inbox at `_shared-memory/inbox/<operator-slug>/`:

- `_shared-memory/inbox/me/` — messages for Zonia
- `_shared-memory/inbox/eleno/` — messages for ELENO

Agents drop JSON or .md messages here when they need to escalate cross-operator. Schema matches the existing `sinister-bus.inbox-ask.v1` pattern.

## ELENO onboarding (operator-paced, future)

When ELENO joins:

1. Clone Sinister Sanctum repo to his workstation: `git clone https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git "D:\Sinister Sanctum"` (or wherever he sets `$env:SINISTER_SANCTUM_ROOT`).
2. Set his operator identity env var: `[Environment]::SetEnvironmentVariable("SINISTER_OPERATOR_SLUG", "eleno", "User")`.
3. Set his agent author identity: `git config user.name "ELENO (Sinister partner operator)"` + `git config user.email "<eleno's email>"`.
4. Run the bootstrap script (TBD — will write when ELENO is onboarded).
5. Pull all project branches: `git fetch --all`.
6. Set up local junctions for his project source paths (matching his disk layout).

## Coordination cadence (recommended)

- **Daily** — both operators check cross-agent inboxes at session start.
- **Weekly** — review project/<slug>/main branches together; merge agent topic branches.
- **Per-breakthrough** — agent pushes topic branch to origin immediately; operator reviews next session.

## What's master-actionable now (this turn)

1. ✅ Doctrine doc (this file).
2. ⏸ Per-project `me/` + `eleno/` folder creation (master executes — pure scaffold, no source-edit).
3. ⏸ Brain entry `multi-operator-eleno-collaboration-pattern.md` (master executes).
4. ⏸ Cross-agent ASKs to each sibling project agent to implement the auto-push hook (master writes spec, sibling owns implementation per canonical-10).
5. ⏸ Operator onboarding ELENO (operator-paced, blocked on ELENO's actual presence + decisions about his disk layout).

## What stays operator-paced

- ELENO's actual disk-side onboarding.
- Per-project `git config` defaults Zonia vs ELENO want (e.g. signing key, GPG commit signing).
- Conflict-resolution culture (who reviews whose PRs, how often, etc.) — this is a human protocol.

## Related topics

- `_shared-memory/knowledge/cross-agent-coordination.md`
- `_shared-memory/knowledge/per-agent-branch-convention.md`
- `_shared-memory/knowledge/multi-agent-branch-contention-isolation-pattern.md` (sibling pattern — within-machine concurrency)
- `_shared-memory/knowledge/sanctum-auto-push.md` (existing GitHub mirror daemon)
- `PARALLEL-AGENT-COORDINATION.md` (root)
