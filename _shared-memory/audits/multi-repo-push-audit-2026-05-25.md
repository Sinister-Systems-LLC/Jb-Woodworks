# Multi-Repo Push Audit — 2026-05-25

Author: RKOJ-ELENO :: 2026-05-25
Slug: sanctum-push-policy
Trigger: operator hard-canonical 2026-05-25 ~00:50Z — single-repo push policy + 3 carve-outs.

## Policy (binding)

- Default push target for every project = `Sinister-Sanctum` (origin =
  https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git).
- Allowed carve-outs (KEEP their own remote):
  - LetsText (operator-private repo, lives at `D:\Personal\LetsText`)
  - Showmasters (its own GitHub repo)
  - JB Woodworks (its own GitHub repo)
- Everything else = consolidate into Sanctum.

## Audit table — `D:\Sinister Sanctum\` root + every `projects/*` subdir

| Project | Path | Embedded `.git` | `origin` URL | Policy verdict |
|---|---|---|---|---|
| Sanctum (root) | `D:\Sinister Sanctum\` | YES (root) | `Sinister-Systems-LLC/Sinister-Sanctum.git` + `jbw-deploy` (push) + `sanctum` (Gitea mirror) | OK (canonical) |
| sinister-chatbot | `projects/sinister-chatbot/` | YES | `Sinister-Systems-LLC/Sinister-Panel.git` | VIOLATION — should push to Sanctum |
| sinister-panel/source | `projects/sinister-panel/source/` | YES | `Sinister-Systems-LLC/Sinister-Panel.git` | VIOLATION — consolidate into Sanctum |
| sinister-snap-emu/source | `projects/sinister-snap-emu/source/` | YES | `Sinister-Systems-LLC/Sinister-Snap-API-EMU.git` | VIOLATION — consolidate (no carve-out) |
| sinister-tiktok-emu (root + source) | `projects/sinister-tiktok-emu/` + `/source/` | YES (both) | (no remote configured on either) | UNCLEAR — likely VIOLATION; pending operator clarification |
| jb-woodworks | `projects/jb-woodworks/` | NO (regular folder) | n/a (commits go to Sanctum root) | OK — but registry says push to `Sinister-Systems-LLC/Jb-Woodworks` |
| showmasters/site | `projects/showmasters/site/` | NO (regular folder) | n/a (commits go to Sanctum root) | OK — but registry says push to `Sinister-Systems-LLC/Showmasters` |
| All other `projects/*` | regular folders | NO | n/a | OK (commit into Sanctum root) |

## Important nuance — JB Woodworks + Showmasters

The 3 carve-outs (LetsText / Showmasters / JB Woodworks) currently exist
as REGULAR FOLDERS inside Sanctum, not as embedded git repos. Their files
commit to Sanctum's `.git/` today. To honor the carve-out (push files to
THEIR repo, not Sanctum's), one of these patterns must hold:

1. Files live ONLY in the standalone external repo + a junction/clone
   points into Sanctum from outside (current model for LetsText:
   `D:\Personal\LetsText`, external_root=true in registry).
2. Per-project deploy push (current model for jb-woodworks: Sanctum has
   a remote called `jbw-deploy` pointing at the JB repo; specific paths
   pushed via subtree or filter).

Sanctum root currently carries `jbw-deploy` as a remote — that lane is
the active mechanism. Showmasters needs verification.

## Sinister Panel — state

- `projects/sinister-panel/source/` IS an embedded git repo (has `.git/`).
- Last 5 commits (most recent first):
  - `8e933ae` merge: agent/sinister-panel/auto-add-friend-on-push-2026-05-24
  - `881c176` panel: auto-fire add-friend(andrewt407) on every PanelPusher push
  - `aa2fde6` merge: agent/sinister-panel/ban-checker-truth-fix-2026-05-24
  - `b02430a` merge: agent/sinister-panel/rka-licenses-2026-05-24
  - `4b87b41` panel: ban-checker truth fix — drop misleading grpc claim
- Remote = `https://github.com/Sinister-Systems-LLC/Sinister-Panel.git`.
- Files are ALREADY in Sanctum tree under `projects/sinister-panel/source/`
  — not missing. The issue is the embedded `.git/` which routes pushes to
  the standalone Sinister-Panel GitHub repo instead of Sanctum's repo.

## Sinister Chatbot — state

- `projects/sinister-chatbot/` IS an embedded git repo.
- `origin` points at `Sinister-Systems-LLC/Sinister-Panel.git` (same as
  Panel — they share the codebase at the standalone level).
- Same consolidation pattern applies.

## Recommended actions (DO NOT EXECUTE without operator approval)

| # | Action | Affected | Reversibility |
|---|---|---|---|
| A | Remove `projects/sinister-panel/source/.git/` so files commit to Sanctum's root `.git/`. Files survive; only the inner repo metadata is removed. | sinister-panel | REVERSIBLE — keep backup of `.git/` dir; can be restored |
| B | Remove `projects/sinister-chatbot/.git/` (same logic). | sinister-chatbot | REVERSIBLE — same as A |
| C | Decide fate of `sinister-snap-emu/source/.git/` (Snap-API-EMU repo) — operator may or may not want this as a carve-out. | sinister-snap-emu | REVERSIBLE — same as A |
| D | Decide fate of `sinister-tiktok-emu/.git/` (no remote configured — likely orphan local) — probably safe to remove. | sinister-tiktok-emu | REVERSIBLE |
| E | Confirm `projects/showmasters/site/` push target — currently has no `.git`; if files should land on standalone Showmasters repo, add a `showmasters-deploy` remote pattern like `jbw-deploy`. | showmasters | NON-DESTRUCTIVE (add only) |

## Verification one-liner

After any change, run:

```powershell
& 'D:\Sinister Sanctum\automations\sanctum-push-policy.ps1' -Action Audit
```

That prints a fresh table identical to the one above.

## Files referenced

- `D:\Sinister Sanctum\automations\session-templates\projects.json` (registry; per-project `github` field is the canonical policy source)
- `D:\Sinister Sanctum\automations\sanctum-auto-push.ps1` (daemon)
- `D:\Sinister Sanctum\automations\sanctum-push-policy.ps1` (NEW — enforcement helper)
- `D:\Sinister Sanctum\docs\BRANCH-CONVENTION.md` (NEW — branch doctrine)
- `D:\Sinister Sanctum\_shared-memory\knowledge\branch-convention-2026-05-25.md` (NEW — brain entry)
- `D:\Sinister Sanctum\_shared-memory\knowledge\single-repo-push-policy-2026-05-25.md` (NEW — brain entry)
