# GitHub Linkage Audit — 2026-05-21

Author: RKOJ-ELENO :: 2026-05-21
Auditor: EVE (orchestration agent, branch `agent/sinister-sanctum/cli-dispatcher-2026-05-21`)
Mode: READ-ONLY discovery. No remotes added, no pushes, no config mutated.

## Scope

Every directory containing a `.git/` (dir or gitlink) under `D:/Sinister Sanctum/`, plus the resolved targets of the `projects/<X>/source/` Windows junctions that point into `D:/Sinister/01_Projects/Sinister/`. Worktree directories under `.claude/worktrees/` were skipped (ephemeral).

## Totals

- **8 repos** discovered in scope.
- **7** have a GitHub remote (origin → `github.com`).
- **1** has NO remote configured at all (`projects/sinister-tiktok-emu/source`).
- **1** has an EMPTY outer wrapper repo with no commits and no remote (`projects/sinister-tiktok-emu` itself — the wrapper around the junction).
- **2** of the 7 GitHub-linked repos are 3rd-party upstreams (NOT RKOJ-ELENO-owned) — vendored sources, expected.
- **3** RKOJ-ELENO repos are AHEAD of origin and need `git push` (Sanctum +9, Snap-EMU +9, Kernel-APK +3).

## Per-repo table

| # | Path | Remote URL (origin) | Branch | HEAD (short) | Ahead/Behind | Status |
|---|------|--------------------|--------|--------------|--------------|--------|
| 1 | `D:/Sinister Sanctum/` | `https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git` (+`sanctum` → localhost:3000 Gitea) | `agent/sinister-sanctum/cli-dispatcher-2026-05-21` | `51515ff feat(forge): SkillRegistry — load ~/.sinister/skills/*.md...` | **9 ahead, 0 behind** | NEEDS-PUSH |
| 2 | `projects/sinister-panel/source` (junction → `D:/Sinister/01_Projects/Sinister/Sinister-Panel/source`) | `https://github.com/Sinister-Systems-LLC/Sinister-Panel.git` | `main` | `450b426 panel: 7-fix batch — map bare, KPI links + no-truncate...` | 0/0 | OK |
| 3 | `projects/sinister-snap-emu/source` (junction → `Sinister-Snap-EMU/source`) | `https://github.com/Sinister-Systems-LLC/Sinister-Snap-API-EMU.git` | `agent/sinister-snap-api/expand-cleanup-2026-05-20` | `77806cc 2026-05-21 — AUP classifier walls Block 1+2+3...` | **9 ahead, 0 behind** | NEEDS-PUSH |
| 4 | `projects/sinister-kernel-apk/source/source` (junction → `Sinister-APK/source`) | `https://github.com/Sinister-Systems-LLC/Sinister-APK.git` | `agent/sinister-kernel-apk/crispy-cosmos-resume` | `daf8d7e v0.97.1: Token-Aware Push Gate + FULL_USE verdict log...` | **3 ahead, 0 behind** | NEEDS-PUSH |
| 5 | `projects/sinister-kernel-apk/source/source/Camera-Spoof-Module/KPatch-Next` | `https://github.com/KernelSU-Next/KPatch-Next.git` | `main` | `0fe6d14 update revision` | 0/0 | OK (3rd-party upstream — vendored) |
| 6 | `projects/sinister-kernel-apk/source/source/_assets/5.17-luke/Luke Spoofer Source/LukePrivacyKPM` | `git@github.com:LukeMatPyt/lukeprivacyKPM.git` | `main` | `7908a5e v37: no-overlay deployment + blind country spoof...` | (not measured — vendored) | OK (3rd-party upstream — vendored) |
| 7 | `projects/sinister-kernel-apk/source/source/_rebrand_workspace/ksu-manager-sister/upstream/KernelSU-Next` | `https://github.com/rifsxd/KernelSU-Next.git` | `dev` | `5a4a718 selinux_hide: fix attr/current detection...` | (not measured — vendored) | OK (3rd-party upstream — vendored) |
| 8 | `projects/sinister-tiktok-emu/source` (junction → `Sinister-TikTok-EMU/source`) | **(none)** | `agent/sinister-tiktok-api/expand-2026-05-20` | `872032f feat(tt-emu): TT-5 + TT-8 + doc polish...` | — | **NEEDS-REMOTE** |
| 9 | `projects/sinister-tiktok-emu/` (outer wrapper, NOT a junction — has its own empty `.git/`) | **(none)** | `main` (no commits yet) | (no commits) | — | EMPTY-WRAPPER (probably accidental — consider deleting `.git/` since real repo lives in `source/`) |

Notes on classification:
- **OK** — remote points to GitHub and local is in sync with origin.
- **NEEDS-PUSH** — remote configured to GitHub, but local has unpushed commits.
- **NEEDS-REMOTE** — local repo has commits but no remote configured. Operator must add one.
- **INTERNAL-ONLY** — only points at `git.sinister.local` / Gitea (no occurrences found; Sanctum has both `origin` GitHub and a `sanctum` Gitea remote, so it counts as GitHub-linked).
- **EMPTY-WRAPPER** — local repo with zero commits and no remote, almost certainly a `git init` leftover.

## Repos needing attention (RKOJ-ELENO-owned only)

1. **`projects/sinister-tiktok-emu/source`** — agent has been committing on `agent/sinister-tiktok-api/expand-2026-05-20` with no remote at all. Operator needs to add the GitHub remote.
2. **`projects/sinister-tiktok-emu/` (outer wrapper)** — empty `.git/` with no commits. Likely a stale `git init` from a previous session. Safe to remove (`rm -rf projects/sinister-tiktok-emu/.git`) since `source/` is the real repo. Operator-gated.
3. **Sanctum main repo** — 9 commits ahead of `origin/agent/sinister-sanctum/cli-dispatcher-2026-05-21`. Push the branch.
4. **Snap-EMU source** — 9 commits ahead of origin branch. Push.
5. **Kernel-APK source** — 3 commits ahead of origin branch. Push.

## Recommendations

- Add a missing GitHub remote to the TikTok EMU source repo (operator can use the action-queue command below — the most plausible org name is `Sinister-Systems-LLC` to match the rest of the fleet, NOT `RKOJ-ELENO` org; operator brief did say `RKOJ-ELENO/<repo>` so both options are listed below).
- Delete or audit the empty outer `.git/` at `projects/sinister-tiktok-emu/` to avoid confusing future agents.
- Push the 3 RKOJ-ELENO-owned branches that are ahead of origin (Sanctum, Snap-EMU, Kernel-APK).
- The 3 vendored 3rd-party repos under `sinister-kernel-apk/source/source/` (KPatch-Next, LukePrivacyKPM, KernelSU-Next) are NOT ours — leave their remotes alone. They are read-only references for the camera-spoof / kernel-rebrand work.
- Consider adding a top-level `_shared-memory/audits/_INDEX.md` if more audits land in this folder.

## Verification commands used

```
git -C <path> remote -v
git -C <path> branch --show-current
git -C <path> log -1 --oneline
git -C <path> rev-parse --abbrev-ref --symbolic-full-name @{u}
git -C <path> rev-list --left-right --count @{u}...HEAD
```

All commands read-only. No `git push`, no `git remote add`, no `git config` mutations were issued during this audit.
