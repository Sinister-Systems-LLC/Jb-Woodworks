# Branch Convention — fleet-wide

Author: RKOJ-ELENO :: 2026-05-25
Status: hard-canonical (operator-binding)
Composes with: `_shared-memory/knowledge/per-agent-branch-convention.md`
(2026-05-19 original) and supersedes for project-key routing details.

## Format (binding)

```
agent/<project-key>/<short-topic>-<utc-date>
```

- `<project-key>` MUST match a `key` field in
  `automations/session-templates/projects.json` (e.g. `sanctum`,
  `sinister-panel`, `sinister-sleight`, `kernel-apk`).
- `<short-topic>` <= 30 chars, kebab-case, ASCII only.
- `<utc-date>` = `YYYY-MM-DD` UTC of when the branch was created.

Examples:

```
agent/sinister-sleight/p1-data-layer-2026-05-25
agent/sanctum/push-policy-consolidation-2026-05-25
agent/sinister-panel/auto-add-friend-on-push-2026-05-24
agent/kernel-apk/ksu-detector-probe-2026-05-25
```

## Per-project prefix overrides

Some projects opt in to a different branch_prefix via `projects.json`
(field: `branch_prefix`). Honor it. Known cases:

| Project key | Branch prefix |
|---|---|
| rkoj | `agent/rkoj/` (umbrella; subsumes Forge/Term/Mind/Claw/Workstation) |
| sinister-os mobile sub-lane | `agent/sinister-os-mobile/` (post-consolidation 2026-05-24) |
| everything else | `agent/<project-key>/` (default) |

Long-lived feature branches that span >1 week and >1 agent MAY use
`feature/<topic>` — but the default for agent work is the per-agent
convention above. `feature/*` is rare.

## Push target (binding — composes with single-repo push policy)

- Every per-agent branch pushes to `origin` (= `Sinister-Sanctum`)
  EXCEPT the 3 carved-out projects (LetsText, Showmasters, JB Woodworks)
  which push to their own repos per `projects.json` `github` field.
- Branch names stay identical across repos (still
  `agent/<project-key>/...`).
- See `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md`.

## Merge-back

| Lane type | Merge mechanism |
|---|---|
| `sanctum` (this repo) | `agent/sanctum/*` -> `main` via `sanctum-auto-push.ps1` daemon (operator-authorized class-level) |
| Per-project agent (carve-out: Showmasters / JB / LetsText) | `agent/<key>/*` -> `main` via PR on THAT repo (operator-reviewed) |
| Per-project agent (everything else) | `agent/<key>/*` -> Sanctum `main` via `sanctum-auto-push.ps1` |
| `feature/*` long-lived | Operator-merged after multi-agent review |

## Auto-router

`automations/agent-branch-router.ps1` enforces the convention at spawn
time. It:

1. Reads project key from spawn args (or env `SINISTER_PROJECT_KEY`).
2. Generates the canonical branch name per the rules above.
3. Switches to it (creates if missing; preserves existing if already on
   a valid `agent/<key>/*` branch).
4. Pushes if local commits exist and remote is configured.
5. Refuses to push if the working remote `origin` URL doesn't match the
   policy in `projects.json` (delegates to `sanctum-push-policy.ps1`).

Invoke directly:

```powershell
& 'D:\Sinister Sanctum\automations\agent-branch-router.ps1' `
    -ProjectKey sinister-sleight `
    -Topic 'p1-data-layer' `
    -DryRun
```

`-DryRun` prints what it would do without executing.

## Pre-push enforcement

`automations/sanctum-push-policy.ps1` is wired into
`sanctum-auto-push.ps1` (post-2026-05-25) as a pre-push hook. If the
current repo's `origin` URL diverges from the policy, push aborts with
exit code 13.

## What NOT to do

- Push to `main` directly from an agent session. Always via the daemon.
- Force-push to any branch other than your own session branch (and even
  then only with explicit operator OK).
- Push to a remote that isn't in the project's `projects.json` `github`
  field (or the 3 carve-out remotes).
- Use ad-hoc branch names that don't follow `agent/<key>/<topic>-<date>`.

## Related docs

- `_shared-memory/knowledge/per-agent-branch-convention.md` — original
  2026-05-19 doctrine (still valid; this doc adds the `-<utc-date>`
  suffix + project-key routing + auto-router script).
- `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md` —
  push-target consolidation doctrine.
- `_shared-memory/knowledge/branch-convention-2026-05-25.md` — brain
  entry mirroring this doc.
- `PARALLEL-AGENT-COORDINATION.md` — file-level ownership zones.
