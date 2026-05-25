<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 365
-->
# Topic: Branch convention 2026-05-25 — agent/<project-key>/<topic>-<utc-date>

Author: RKOJ-ELENO :: 2026-05-25
Slug: branch-convention-2026-05-25
First discovered: 2026-05-19 (original convention by Sinister Sanctum)
Last updated: 2026-05-25 by RKOJ-ELENO (added project-key routing +
auto-router + UTC date suffix)
Status: hard-canonical (operator-binding)
Tags: git, branch, multi-agent, lane-discipline, project-key,
auto-router, sanctum-push-policy

## Problem

The 2026-05-19 convention (`agent/<slug>/<topic>`) shipped without:

1. A project-key namespace tied to `projects.json` (slug drift across
   sessions led to `agent/sinister-tt-emu/...` vs
   `agent/sinister-tiktok-emu/...` divergence).
2. A UTC date suffix (operator couldn't scan branch lists by recency).
3. An auto-router script (every agent reinvented branch creation in
   their own cold-start prompt).
4. Composition with the push policy (agents pushed to whatever `origin`
   pointed at).

Operator 2026-05-25 ~00:50Z: *"you need to make like a detailed branch
work to have all the dif proejcts and make this auto happen and all
agents know what to do."*

## Fix

Canonical format (binding):

```
agent/<project-key>/<short-topic>-<utc-date>
```

- `<project-key>` = `key` field in `projects.json`.
- `<short-topic>` <= 30 chars, kebab-case.
- `<utc-date>` = `YYYY-MM-DD` UTC.

Auto-router: `automations/agent-branch-router.ps1`.

Push-policy enforcement: `automations/sanctum-push-policy.ps1`.

Doctrine doc: `docs/BRANCH-CONVENTION.md` (operator-facing).

## Composition

- Supersedes the project-key routing piece of
  `per-agent-branch-convention.md` (which stays valid for slug rules +
  the no-push-to-main + no-force-push principles).
- Composes with
  `_shared-memory/knowledge/single-repo-push-policy-2026-05-25.md` —
  branch convention defines NAMES, push policy defines TARGETS.
- Composes with `verify-head-before-commit-multi-agent.md` (shared-CWD
  safety) and `multi-agent-branch-contention-isolation-pattern.md`.

## Tested-or-untested

Smoke-tested 2026-05-25:

- `agent-branch-router.ps1 -ProjectKey sinister-sleight -Topic test -DryRun`
  -> prints intended branch + push commands without executing.
- `sanctum-push-policy.ps1 -Action Check` on Sanctum root -> OK.
- `sanctum-push-policy.ps1 -Action Audit` -> emits the audit table.

Acceptance: parse-clean + dry-run smoke pass. Production validation
deferred to next real spawn from EVE.exe.

## Discoveries (append-only, most-recent at top)

### 2026-05-25 by RKOJ-ELENO (sanctum-push-policy lane)
First write. Composed with single-repo-push-policy. Wired into
`start-sinister-session.ps1` as pre-spawn `agent-branch-router.ps1`
invocation.

## Related topics

- `single-repo-push-policy-2026-05-25` — push targets
- `per-agent-branch-convention` — 2026-05-19 original
- `verify-head-before-commit-multi-agent` — shared-CWD HEAD races
- `sanctum-auto-push` — daemon behavior
