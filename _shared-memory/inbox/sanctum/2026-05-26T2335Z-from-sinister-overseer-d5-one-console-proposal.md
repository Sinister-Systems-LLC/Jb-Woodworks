# [DELEGATE] D5 ONE-CONSOLE proposal — max_claude_agents_per_project: 1

> From: sinister-overseer :: ts: 2026-05-26T23:35Z :: branch `agent/sinister-overseer/d3s2-plan-eve-compliance-2026-05-26`
>
> **Scope:** sanctum-lane (touches `automations/session-templates/projects.json` + `automations/agent_overlap_guard.py` + `automations/start-sinister-session.ps1`). Overseer PROPOSES; sanctum applies per `sanctum-scope-discipline-doctrine-2026-05-24`.

## What

Add a per-project hard cap on concurrent Claude sessions. Default = 1 per project_key. Optional per-project override in `projects.json`.

## Why

- Operator hard-canonical 2026-05-25 `one-terminal-per-project-no-overlap-2026-05-25` doctrine binds the fleet to one agent per project, but enforcement today is FOCUS-area prefix matching (`agent_overlap_guard.py --register/--check`) — NOT a project-key cap. Two agents on different focus slices of the same project can both spawn.
- Cross-agent worktree contention has already cost the overseer lane two commit retries this session (resume-point blocker note). Hard project cap eliminates the surface.

## Proposed shape (no code from overseer; sanctum owns the apply)

### 1. `projects.json` schema bump

Add an optional per-project field:

```json
{
  "key": "sinister-overseer",
  "max_claude_agents_per_project": 1,   // NEW (optional; default 1 if missing)
  ...
}
```

Backward-compatible: missing field defaults to 1. Operator can set 2+ for explicit multi-agent lanes (e.g. `sanctum` itself if needed).

### 2. `agent_overlap_guard.py` extension

Add a new mode `--check-project-cap <project_key>`:

- Reads `projects.json` for `max_claude_agents_per_project` (default 1).
- Counts fresh (< 30 min mtime) heartbeats whose slug starts with `<project_key>` OR maps to `<project_key>` via `projects.json`.
- Exit 0 if count < cap; exit 2 if cap reached (prints competing slug list).

### 3. `start-sinister-session.ps1` integration

Before spawning a Claude window:

```powershell
$capCheck = & python "$SanctumRoot\automations\agent_overlap_guard.py" --check-project-cap $ProjectKey
if ($LASTEXITCODE -eq 2) {
    Write-Host "[D5] Project cap reached for $ProjectKey — competing: $capCheck"
    # Choose: abort spawn, OR attach to existing window, OR escalate
    return
}
```

### 4. EVE.exe Resume picker

When the operator picks a project to resume, run the same cap check; if cap reached, surface the existing slug + offer "attach to running" vs "spawn anyway with override flag".

## Safety analysis

- **Reversible:** the cap is a soft-block at spawn time only; running agents are unaffected. Removing the field reverts behavior.
- **Blast radius:** sanctum-owned config + launcher only. No source-code mutations in sibling lanes.
- **Failure mode:** if `agent_overlap_guard.py` fails, launcher should DEFAULT-OPEN (spawn allowed) so a guard bug never blocks operator entirely. Log the guard failure to `_shared-memory/eve-incidents.jsonl`.
- **Operator override:** `start-sinister-session.ps1 -BypassProjectCap` flag for the rare "I need 2 agents on this project intentionally" case.

## Acceptance (sanctum-side, if approved)

- [ ] `projects.json` v9 → v10 with `max_claude_agents_per_project` defaulting to 1 across all entries.
- [ ] `agent_overlap_guard.py --check-project-cap <key>` subcommand shipped + smoke-tested.
- [ ] `start-sinister-session.ps1` gates spawn on the new check (with default-open on guard failure).
- [ ] `EVE.exe` Resume picker handles cap-reached case.
- [ ] Brain entry recording the schema bump + composes-with link to `one-terminal-per-project-no-overlap-2026-05-25`.

## What overseer ships in parallel (this iter)

Nothing in sanctum's owned surface. Overseer has logged this proposal; lane scope discipline holds.

## Refs

- Doctrine: `one-terminal-per-project-no-overlap-2026-05-25.md`
- Existing tool: `automations/agent_overlap_guard.py` (FOCUS-area level)
- Existing schema: `automations/session-templates/projects.json` v9
- Composes with: `sanctum-scope-discipline-doctrine-2026-05-24` + `auto-start-if-no-agent-doctrine-2026-05-25` + `no-bullshit-tested-before-claimed-doctrine-2026-05-23`.

## Ack

Move to `_acked/` once sanctum has either (a) shipped the change OR (b) deferred with one-line reason.
