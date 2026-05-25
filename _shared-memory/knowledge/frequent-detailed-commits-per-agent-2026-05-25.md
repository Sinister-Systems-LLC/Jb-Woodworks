# Frequent + detailed commits per agent (operator hard-canonical 2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25
**Status:** binding for every spawned fleet agent
**Composes with:** `sanctum-auto-push.ps1` daemon + `single-repo-push-policy-2026-05-25.md` + `branch-convention-2026-05-25.md` + `sinister-link-doctrine-2026-05-25.md`

## Operator verbatim (2026-05-25 ~01:25Z)

> "make sure to push again once eve is done and i need the pushes with detailed committs to happen often per agent running baked into memory with no issues that connects connects wiht leo"

## Rule

Every spawned fleet agent SHALL commit + push its in-progress work to its agent branch (`agent/<project-key>/<topic>-<date>`) on the following triggers:

1. **Per deliverable.** After each shipped + smoke-tested deliverable -- one commit, detailed message.
2. **Every 10 minutes** while actively producing (auto-push daemon's existing cadence remains; agent adds explicit commits in between when shipping).
3. **Before any agent self-termination** (resume-point write triggers a final commit).
4. **On loop iteration end** (every `loop-mode` cycle completing one deliverable triggers a commit).

## Commit message format (detailed, not generic)

```
<slug>: <verb> <subject> (iter N)

Shipped:
- <file path 1> -- <one-line summary>
- <file path 2> -- <one-line summary>

Smoke:
- <test 1>: <PASS/FAIL>
- <test 2>: <PASS/FAIL>

Refs:
- operator utterance ts: <utc>
- fleet-update id: <id>
- mesh-coord lock: <focus>
- composes with: <prior brain entry>

Co-Authored-By: EVE (Sinister Sanctum orchestration agent) <noreply@anthropic.com>
```

Rationale: when Leo (or operator on a different machine) pulls the agent branch, the commit log reads like a play-by-play. No git archaeology required.

## Anti-patterns (forbidden)

- One mega-commit at end of session ("session work 2026-05-25"). Never. Many small commits, one per deliverable.
- Generic messages ("wip", "update", "fix"). Detail or don't commit.
- Squash-merge that erases the per-deliverable trail. Use merge commits or rebase preserving messages.
- Committing without pushing. Auto-push daemon catches most cases but agents should also explicitly push after each deliverable when on an agent branch.
- Committing across project boundaries in one commit (e.g. sleight + overseer + sanctum changes squashed). Stage per-project, commit per-project.

## How the auto-push daemon enforces

`automations/sanctum-auto-push.ps1`:
1. Polls every 30 minutes (existing).
2. NEW: agents can fire it explicitly between intervals via `-Action PushNow -Slug <slug>` (NON-BLOCKING; queues the push if a sibling daemon is mid-push).
3. NEW: pre-push policy hook (`sanctum-push-policy.ps1`) refuses out-of-policy pushes (exit 13).
4. On agent branches, pushes existing commits without staging anything new (lane owns its own staging per `agent-autonomy-push-and-completion-2026-05-23.md`).
5. On `main`, stages + commits + pushes (sanctum lane owns main).

## How Sinister LINK consumes this

`sinister-link.ps1 -Action Sync` (cadence: 60s when linked) does:
1. `git fetch --all --prune` -- pulls peer's pushed commits + branches.
2. `git pull --rebase origin <current-branch>` if on a shared branch.
3. Updates `_shared-memory/sinister-link-health.json` with peer's HEAD shas per agent branch.
4. If peer is on the same agent branch (e.g. both editing `agent/sinister-sleight/p1-data-layer-2026-05-25`), warns about merge-conflict risk.

Since agents commit + push frequently with detailed messages, the LINK pull is ALWAYS recent. Peer can see what just shipped on the other machine within ~60s after each deliverable.

## Double-work prevention via commit cadence

When operator and Leo are both spawning agents:
1. Each agent's spawn writes a heartbeat with `current_branch + last_commit_sha`.
2. `sinister-link.ps1 -Action Sync` pulls peer's heartbeats too.
3. `detect-similar-agents.ps1` extended to surface peer heartbeats in the cold-start phrase (TODO: P1).
4. If peer's recent commit message contains "[PARTIAL]" or "[BLOCK]" tags, sibling agent skips that subtask.

## Smoke / verification

- `sanctum-auto-push.ps1 -Action Status` should report last 5 pushes with shas + branches + per-slug commit counts.
- Brain entry indexed in `_shared-memory/knowledge/_INDEX.md`.
- This rule is monitored by overseer's `forever-improve` sensor: if any agent commits less than 1x per shipped deliverable, surfaces as a P2 recommendation.
