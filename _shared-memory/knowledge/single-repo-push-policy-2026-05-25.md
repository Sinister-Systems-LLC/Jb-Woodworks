<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 365
-->
# Topic: Single-repo push policy 2026-05-25 — Sanctum is the default; 3 carve-outs

Author: RKOJ-ELENO :: 2026-05-25
Slug: single-repo-push-policy-2026-05-25
First discovered: 2026-05-25 by RKOJ-ELENO
Last updated: 2026-05-25 by RKOJ-ELENO
Status: hard-canonical (operator-binding)
Tags: git, push, remote, policy, sanctum, consolidation, carve-out,
panel, letstext, showmasters, jb-woodworks

## Problem

Multiple Sinister projects historically had their own GitHub repos
(Sinister-Panel, Sinister-Snap-API-EMU, Sinister-TikTok-API-EMU, etc.).
Operator 2026-05-25 ~00:50Z directive: *"make sure the only fodler we
are pushing to is the the sinister sanctum. no sinister panel pushing
to the panel no. make sure all those files from the sinister panel
github are in the sanctum organized and concise. lets text will have
their own. showmasters will, jb will. but nothing else. everything
needs to be sinister sanctum then."*

Today (audit 2026-05-25):
- `projects/sinister-panel/source/.git/` -> Sinister-Panel repo (VIOLATION)
- `projects/sinister-chatbot/.git/` -> Sinister-Panel repo (VIOLATION)
- `projects/sinister-snap-emu/source/.git/` -> Snap-API-EMU repo (VIOLATION)
- `projects/sinister-tiktok-emu/.git/` + `/source/.git/` -> no remote (orphan)

## Policy (binding)

| Lane | Push target |
|---|---|
| Sanctum (root) | `Sinister-Systems-LLC/Sinister-Sanctum` (origin) |
| Every other project except 3 carve-outs | `Sinister-Systems-LLC/Sinister-Sanctum` (origin) |
| LetsText | own repo (operator-private, external_root=true) |
| Showmasters | own repo (`Sinister-Systems-LLC/Showmasters`) |
| JB Woodworks | own repo (`Sinister-Systems-LLC/Jb-Woodworks`; current model = `jbw-deploy` remote on Sanctum root) |

## Enforcement

`automations/sanctum-push-policy.ps1`:

- `-Action Check` — checks the current dir's `origin` URL against the
  policy in `projects.json`. Exit 0 = OK, exit 1 = violation.
- `-Action Audit` — prints the full audit table for all projects.
- Wired into `sanctum-auto-push.ps1` post-2026-05-25 as a pre-push hook.

## Consolidation recommendations (DO NOT EXECUTE without operator OK)

For each VIOLATION row above:

1. Back up the `.git/` dir to `_archive/embedded-repos/<key>-<utc>.git/`.
2. Remove the embedded `.git/` so files commit to Sanctum's root.
3. Stage all surviving files via `sanctum-auto-push.ps1`.

Surfaced as OPERATOR-ACTION-QUEUE rows; do not auto-execute.

## Composition

- `branch-convention-2026-05-25` defines NAMES, this policy defines TARGETS.
- `sanctum-auto-push` reads this policy via the pre-push hook.
- `per-project-bot-adoption-playbook-2026-05-23` (still valid) defines
  per-project ownership; this policy adds the push-target column to it.

## Tested-or-untested

Smoke-tested 2026-05-25:

- `sanctum-push-policy.ps1 -Action Audit` runs against operator's repo
  and emits a table identical to `_shared-memory/audits/multi-repo-push-audit-2026-05-25.md`.
- `sanctum-push-policy.ps1 -Action Check` on Sanctum root -> exit 0 OK.
- Synthetic-violation test (point a temp working dir at a non-policy
  remote URL): exit 1, error message printed.

## Discoveries (append-only, most-recent at top)

### 2026-05-25 by RKOJ-ELENO (sanctum-push-policy lane)
First write. Inventory shows 4 embedded-repo violations. Sinister Panel
files already live in Sanctum tree at `projects/sinister-panel/source/`
— consolidation is metadata-only (remove inner `.git/`), no clone needed.

## Related topics

- `branch-convention-2026-05-25` — name format
- `sanctum-auto-push` — daemon
- `per-project-bot-adoption-playbook-2026-05-23` — per-project ownership
- `gitea-self-host` — self-hosted Gitea mirror (orthogonal)
