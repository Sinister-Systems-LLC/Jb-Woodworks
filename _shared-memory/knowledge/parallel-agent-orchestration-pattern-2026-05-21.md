<!-- decay:
  category: fact
  confidence: 0.9
  reinforcements: 0
  half_life_days: 90
-->
> **Author:** RKOJ-ELENO :: 2026-05-21

# Topic: Parallel agent orchestration pattern — 24+ sub-agents safely in ~75 minutes

**Slug:** parallel-agent-orchestration-pattern-2026-05-21
**First discovered:** 2026-05-21 by EVE (Sinister Sanctum orchestration agent)
**Last updated:** 2026-05-21 by EVE
**Status:** known-good
**Tags:** parallel-agents, sub-agents, fan-out, race-condition, git-stash, pull-rebase, lane-discipline, commit-detection-polling, PROGRESS-log, cross-agent-broadcast

## Problem

How do you run 24+ parallel sub-agents on the same repo without churning the working tree into an unresolvable conflict pile? Sub-agents share one filesystem, one git index, one set of "hot" files (RKOJ.spec, forge/commands.py, RKOJ-entry.py). If two agents race on the same file the second one's commit fails — or worse, silently overwrites.

Concrete trigger (2026-05-21): the v0.6.0 → v1.1.0 RKOJ form-parity sweep needed 24+ agents in ~75 minutes (anthropic SDK direct-path + parallel tools + prompt caching + thinking panel + budget guard + JSONL journaling + 60+ slash commands + TUI default-mode + toolbar/statusbar + NiriWorkspaceGrid + Panel chrome theme + 8 D-drive reorg lanes). Naive fan-out = pull-the-pin chaos.

## Why it happens

Three forces in tension:

1. **Sub-agents are independent processes** — each has its own `Edit`/`Write` tool, its own working tree view, its own commit timestamp. They can't see each other's pending changes until they're committed.
2. **Some files are gravity wells** — `RKOJ.spec hiddenimports`, `forge/commands.py` (the slash-command registry), `RKOJ-entry.py` (the bootstrap) — every feature needs to touch them. If 5 agents add 5 new slash commands, all 5 want to edit `commands.py`.
3. **Git's commit graph is linear per branch** — two commits with the same parent on the same branch = the second one needs rebase. Pull-rebase before commit is the polite version. Force-push is the loud version.

## Fix — the 6-pattern playbook

### 1) Identify file contention zones up front

Before dispatching, list the "gravity well" files:

```
HOT FILES (one agent at a time):
- projects/rkoj/source/forge/commands.py     (slash command registry)
- projects/rkoj/source/RKOJ-entry.py         (bootstrap + arg parsing)
- projects/rkoj/RKOJ.spec                    (PyInstaller hiddenimports)
- automations/start-sinister-session.ps1     (launcher)
- automations/session-templates/projects.json (agent prefs)

WARM FILES (careful staging):
- projects/<lane>/source/forge/spawn/base.py
- projects/<lane>/CLAUDE.md

COLD FILES (parallel safe):
- _shared-memory/knowledge/*.md  (one slug per agent = no collision)
- _shared-memory/PROGRESS/*.md   (one file per agent = no collision)
- inventions/*.md
```

### 2) Lane discipline — one agent per hot file

Dispatch each hot-file edit to a SINGLE agent. If 5 slash commands need `commands.py`, batch them into one sub-agent's task list, not 5 parallel agents.

### 3) Pull-rebase before commit (always)

Every sub-agent's commit script ends:

```bash
git pull --rebase origin agent/<slug>/<topic> 2>/dev/null || true
git add <specific-files>
git commit -m "..." || (git stash && git pull --rebase && git stash pop && git commit -m "...")
```

The `|| (git stash...)` is the race-condition catcher. If two agents committed near-simultaneously, stash + pull + pop + commit recovers.

### 4) Commit-detection polling for sequential dependencies (Phase 2 → Phase 3)

When Phase 3 needs Phase 2's commit on disk (e.g., Phase 3 imports a module Phase 2 created), don't dispatch Phase 3 in parallel — poll for Phase 2's commit hash:

```bash
PHASE_2_FILE="projects/rkoj/source/forge/journaling.py"
until git log --all --oneline -- "$PHASE_2_FILE" | grep -q .; do sleep 3; done
# Now safe to dispatch Phase 3
```

Use Monitor tool with an until-loop (no leading-sleep block). This pattern shipped 5+ Phase-2-then-Phase-3 sequences this session.

### 5) PROGRESS log + cross-agent broadcast as coordination primitives

Every sub-agent writes to `_shared-memory/PROGRESS/<slug>.md` (append-only, most-recent at top) and emits a `_shared-memory/cross-agent/<timestamp>-<topic>.md` broadcast when they finish a milestone. The orchestrator polls these to know "Phase 2 is done; Phase 3 can dispatch."

This decouples orchestrator from sub-agent stdout — sub-agents finish whenever they finish, broadcast lands in a known location, orchestrator notices on next poll.

### 6) Git stash as the universal "wait, slow down" button

If a sub-agent finds the working tree dirty when it expected clean (race), `git stash` saves its work-in-progress, lets it `git pull --rebase`, then `git stash pop` reapplies. If pop conflicts, the agent reports up — never silently merges.

## Lessons learned (2026-05-21 sweep)

- **24 agents in ~75 minutes**: anthropic SDK lane (3 agents), TUI lane (4), slash commands lane (8), Niri grid lane (2), D-drive reorg lane (5), brain entries lane (2).
- **2 race conditions encountered**:
  1. RKOJ.spec hiddenimports — 2 agents added imports same minute; second got rejected; stash + pull-rebase + replay worked clean.
  2. forge/commands.py — 3 agents wanted to register slash commands; we serialized by dispatching one super-agent that batched all 3 instead of parallel.
- **0 force-pushes** required. Polite git everywhere.
- **PROGRESS log was the single source of truth** — once an entry landed there, orchestrator knew the lane was done.

## Anti-patterns to avoid

- DO NOT fan-out 5 agents to edit the same file in parallel. Batch them.
- DO NOT skip `git pull --rebase` — even one missed pull turns the next commit into a 3-way merge.
- DO NOT use force-push as a "fix." It silently overwrites sibling agent work.
- DO NOT poll with `sleep 30` between checks — use `Monitor` tool with `until` loop so you get a notification, not blocked time.

## Related topics

- [cross-agent-coordination](./cross-agent-coordination.md)
- [auto-mode-launcher-pattern](./auto-mode-launcher-pattern.md)
- [fleet-state-single-source](./fleet-state-single-source.md)
- [complete-everything-sweep-pattern](./complete-everything-sweep-pattern.md)
- [pyinstaller-tmp-race-condition-2026-05-21](./pyinstaller-tmp-race-condition-2026-05-21.md)
