<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: Per-agent branch convention so parallel Claude sessions don't collide

**Slug:** per-agent-branch-convention
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** workaround
**Tags:** git, branch, multi-agent, lane-discipline, coordination, sanctum-git

## Problem

The operator runs multiple Claude sessions in parallel — one per Sinister repo (Snap EMU, TikTok EMU, Panel, Kernel APK) plus the master orchestration lane. If two sessions push to the same branch (typically `main`), the second push either fast-forwards over work the first session hasn't merged yet, or is rejected for non-fast-forward, or — worst case — gets force-pushed and clobbers commits.

Even within a single repo, two sessions doing unrelated work on `main` race each other.

## Why it happens

Default git workflow assumes one developer per branch at a time. With N concurrent agents and one "default" branch, you've got an N-way race. `PARALLEL-AGENT-COORDINATION.md` already defines ownership zones (which files which session owns), but file-level ownership doesn't help when two sessions own different files in the SAME repo and both want to push.

## Fix or workaround

**Every Claude session works on its OWN branch.** Name format:

```
agent/<your-SINISTER_AGENT_NAME-slugified>/<short-topic>
```

### Slugify rules

- Lowercase
- ASCII only (drop accents, punctuation other than dash)
- Spaces -> dashes
- Squeeze repeated dashes

### Examples

| Agent name | Topic | Branch |
|---|---|---|
| `Sinister Snap API` | pure-api SS03 milestone | `agent/sinister-snap-api/pure-api-ss03` |
| `Sinister Sanctum` | master tooling v6 | `agent/sinister-sanctum/master-tooling-v6` |
| `Sinister TikTok EMU` | Argos port | `agent/sinister-tiktok-emu/argos-port` |
| `Sinister Panel` | Eve observations card | `agent/sinister-panel/eve-observations-card` |
| `Sinister Kernel APK` | KSU detector probe | `agent/sinister-kernel-apk/ksu-detector-probe` |

### Workflow (every agent, every session)

```bash
# 1) Make sure you're on the integration point the operator named (default: main)
git checkout main
git pull origin main

# 2) Branch
git checkout -b agent/sinister-snap-api/pure-api-ss03

# 3) Work normally. Commit often.

# 4) Push to BOTH remotes
git push -u origin agent/sinister-snap-api/pure-api-ss03

# Mirror to sanctum-git (self-hosted Gitea):
& "D:\Sinister Sanctum\automations\git-mirror.ps1" -Cmd push -ProjectKey snap-emu
# (the script will push the current branch — your agent branch)

# 5) DO NOT MERGE to main. Operator decides when.
```

### Single-pane view

```powershell
& "D:\Sinister Sanctum\automations\git-mirror.ps1" -Cmd status
```

Output (one row per project) shows:

- Current branch
- Local HEAD short SHA
- Sanctum-remote HEAD short SHA for that branch
- Origin (github) HEAD short SHA for that branch
- Divergence flags (`S` = sanctum differs, `G` = github differs)

Run this BEFORE you start a task and AFTER you push. If you see another agent's branch active in the same repo, mention it to the operator before you start touching shared files.

### What NOT to do

- Push to `main` from an agent session — only the operator (or master orchestration on explicit instruction) does that.
- Force-push (`-f` / `--force` / `--force-with-lease`) — never, unless the operator says so.
- Merge another agent's branch into your branch without operator OK — even a clean fast-forward.
- Delete another agent's remote branch — even if it looks "stale" / "abandoned". Operator's call.

### What to DO when blocked

If you need code from another agent's branch:

1. Run `git-mirror status` to confirm which branch / which SHA.
2. Ask the operator: "I need to pull `agent/sinister-tiktok-emu/argos-port` into my branch — OK?"
3. On operator confirmation: `git merge agent/sinister-tiktok-emu/argos-port`.
4. Note the merge in your `_shared-memory/PROGRESS/<your-agent>.md`.

## Tested-or-untested

Convention authored 2026-05-19 alongside the `sanctum-git` rollout. First real cross-agent test will happen the next time two sessions touch the same repo — operator should flag any divergence in `Codex-Review` if conflicts arise.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 by Sinister Sanctum
First write. Convention is `agent/<slug>/<topic>` — chosen over alternatives (`<initials>/...`, `feature/...`, `lane/...`) because:
- `agent/` prefix groups all session branches under one namespace in tree views.
- The agent slug makes ownership obvious without needing a separate codeowners file.
- The `<topic>` segment is free-form so the operator can scan branch lists like a TODO board.

Mirror tool was sized to push the CURRENT branch (not a hardcoded `main`), so following this convention "just works" — agents do their normal `git checkout -b`, then call `git-mirror push`, and the tool figures out the branch from `rev-parse --abbrev-ref HEAD`.

## Related topics

- [gitea-self-host](./gitea-self-host.md) — the Gitea instance that hosts the other remote
- [github-auth-workflow-scope](./github-auth-workflow-scope.md) — github.com pain points that motivated this
- See also: `D:\Sinister Sanctum\PARALLEL-AGENT-COORDINATION.md` (file-level ownership zones — complementary to this branch-level discipline)
