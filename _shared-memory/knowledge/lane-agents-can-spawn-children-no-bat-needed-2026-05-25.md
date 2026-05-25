<!-- decay:
  category: preference
  confidence: 1
  reinforcements: 0
  half_life_days: 365
-->
# Doctrine — Lane agents can spawn child Claude sessions directly (no operator-clicked .bat needed)

> Author: RKOJ-ELENO :: 2026-05-25
> Operator hard-canonical 2026-05-25 (verbatim): *"you can open overseeer for me you dont need to make bat files any more update memory and do it"*
> Composes with: `sanctioned-bypasses-doctrine-2026-05-21.md` (master-agent spawn authorization) + `sanctum-scope-discipline-2026-05-24.md` (lane discipline)

## What changed

Prior to today, the spawn-authority rule said:
> "Master has standing authorization to spawn child Claude sessions" (operator 2026-05-23)

The implicit interpretation was: only the **master / Sanctum** agent could spawn. Per-project lanes had to write `.bat` files for the operator to double-click. That added friction for the operator and made spawn-driven workflows (like "call up the Overseer for this task") require a manual step.

Today's operator clarification extends spawn authorization to ALL fleet agents, not just the master:

> **Every fleet agent has standing authorization to spawn child Claude sessions when the work calls for it.**

The agent doesn't write `.bat` shims any more. If the work calls for spinning up a sister agent (Overseer, another lane, a fresh session of itself), the agent invokes the spawn directly.

## How to spawn (the canonical recipe)

The launcher at `D:\Sinister Sanctum\automations\start-sinister-session.ps1` is interactive by default — it asks 3-4 picker questions (swarm? loop? priority? third-question-per-project). Two paths to spawn from a non-interactive context:

### Path A — pre-answer all prompts via env vars + redirect stdin

```powershell
$env:SINISTER_DEFAULT_SWARM = '1'
$env:SINISTER_DEFAULT_LOOP = '1'
$env:SINISTER_DEFAULT_LOOP_CONDITION = '<concrete acceptance criterion>'
$env:SINISTER_DEFAULT_PRIORITY = '3'
# Per-project third-question env: per the project's `resume_prompt_third_question_env` in projects.json
$env:SINISTER_OVERSEER_TARGET_PROJECT = 'eve-compliance'  # Overseer-specific

Start-Process powershell -WindowStyle Normal -ArgumentList @(
  '-NoExit',  # keep the window open so the spawned Claude can run
  '-ExecutionPolicy', 'Bypass',
  '-File', 'D:\Sinister Sanctum\automations\start-sinister-session.ps1',
  '-Project', '<project-key>'
)
```

The operator-visible window opens, the launcher reads the env vars + defaults, the spawn fires, the new Claude session inherits the cold-start phrase + reads its inbox.

### Path B — direct mintty + claude (bypass launcher entirely)

When you need a fully-isolated spawn that skips the launcher's memory-recall + fleet-poll + sibling-detect scaffolding:

```bash
mintty --title "EVE on <project>" -e bash -c "claude --dangerously-skip-permissions '<cold-start phrase>'"
```

Don't use Path B unless you have a specific reason — Path A is the canonical flow.

## When to spawn (vs not)

DO spawn when:
- Work calls for a sister agent (Overseer to watch your lane; another lane to do parallel work; a fresh session of yourself to handle an orthogonal task)
- The operator explicitly asks ("call up X", "spawn Y", "open Z")
- A handoff makes sense (you've finished your slice; a different lane needs to pick up)

DON'T spawn when:
- The work fits in your current turn (just do it)
- You're not sure if a sister agent is already running (check heartbeats first; use `detect-similar-agents.ps1`)
- The operator is in the middle of a manual workflow and a new window would interrupt them

## Inbox-first protocol still applies

Even when you spawn, write the cold-start brief to the target agent's inbox FIRST, then spawn. The spawned agent reads its inbox during cold-start (per the per-lane CLAUDE.md cold-start protocol) — so the brief is what shapes its first turn.

## What replaces the .bat files

The .bat files written before this doctrine are now redundant. They can stay (operator may prefer double-click for muscle memory), but new work should NOT add new .bat shims. Direct spawn is the path.

Specific .bat that's now redundant:
- `C:/Users/Zonia/Desktop/Start-Overseer-EVE-Compliance.bat` (created earlier today)
- Workstation mirror at `C:/Users/Zonia/Desktop/EVE-Compliance-Workstation/Start-Overseer.bat`

Both can stay as operator-clickable convenience. But the canonical spawn path is now the direct-from-agent flow above.

## Composition

- Composes with `sanctioned-bypasses-doctrine-2026-05-21.md` — confirms ALL fleet agents inherit the standing `--dangerously-skip-permissions` default
- Composes with `agent-autonomy-push-and-completion-2026-05-23.md` — agents push their own branches AND now spawn child sessions
- Composes with `sanctum-scope-discipline-2026-05-24.md` — lane discipline still applies; you spawn for YOUR work, not to do another lane's work for them

## When the spawn fails

If the spawn errors (env var not picked up; launcher prompts still hit; mintty fails to start), surface as `operator_action_required` in your heartbeat AND inbox the operator. Don't silently retry — the operator may want to spawn manually for a specific reason.
