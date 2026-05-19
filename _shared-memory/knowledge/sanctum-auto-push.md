> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: Sanctum auto-push daemon — 30-min GitHub mirror

**Slug:** sanctum-auto-push
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** fixed
**Tags:** github, push, scheduled-task, daemon, mirror, sanctum, automation, standing-rule

## Problem

Operator wanted `D:\Sinister Sanctum\` to live-mirror to GitHub (`Sinister-Systems-LLC/Sinister-Sanctum`, **private** repo) every 30 min without operator click-through. Skip the push when nothing has changed.

## Why it matters

- The Sanctum is the workstation; any edit (by master, by an automation, or directly by the operator) should land on GitHub within 30 min for off-machine backup + cross-machine continuity (Hetzner ops, mobile review).
- Doing it as a daemon decouples persistence from any specific agent's session — even if no Claude session is open, the daemon keeps mirroring.
- Skipping on no-change keeps the commit graph readable + avoids needless network traffic.

## Fix / system shipped

Three pieces:

1. **`automations\sanctum-auto-push.ps1`** — the daemon. Branch-guard (only `main`), lock file at `_shared-memory\.auto-push.lock`, fetch + `git rev-list origin/main..HEAD` activity check, `git status --porcelain` working-tree check, staged-diff secret-regex (sk-ant-, sk_live_, OPENAI_API_KEY=, BEGIN PRIVATE KEY, ghp_, github_pat_), `git add -A` + `git commit -F <msgfile>` (chore message with top-10 changed paths), `git push origin main`. Logs every run (UTC, action, detail) to `_shared-memory\auto-push.log` with rotation at 2 MB.
2. **`automations\install-auto-push-task.ps1`** — registers the `SinisterSanctumAutoPush` Windows scheduled task. Repeats every 30 min indefinitely; `MultipleInstances = IgnoreNew`; runs as interactive user when logged on (keeps SSH key + credential helper available).
3. **`automations\uninstall-auto-push-task.ps1`** — counterpart kill switch.

Plus three Desktop bats:

- `Sanctum-Auto-Push-Status.bat` — shows task state + tails the last 20 log lines.
- `Sanctum-Auto-Push-Pause.bat` — `Disable-ScheduledTask`.
- `Sanctum-Auto-Push-Resume.bat` — `Enable-ScheduledTask`.

## How it behaves

| State | Daemon does | Exit code |
|---|---|---|
| Working tree clean + no unpushed commits | Logs `skipped \| no-activity`, exits | 1 |
| On a non-`main` branch | Logs `skipped \| not-on-target-branch`, exits (won't auto-commit on agent branches — they belong to their agents) | 1 |
| Lock file < 25 min old | Logs `skipped \| lock-held`, exits | 2 |
| Lock file > 25 min old | Removes stale lock, proceeds (defensive against hung run) | (continues) |
| Working tree dirty | Stages, runs secret regex, commits with chore message, pushes | 0 |
| Local commits ahead of origin (e.g. master agent committed manually then left) | Pushes existing commits without making a new one | 0 |
| Secret regex tripped | `git reset HEAD`, logs `aborted \| secret-regex-tripped`, exits — NEVER pushes | 12 |
| Push rejected by server | Logs `error \| push-failed`, exits; next tick retries | 11 |

## Safety rails (defense-in-depth)

1. `.gitignore` already blocks secrets at the file-class level (`.env*`, `*.pem`, `*.key`, `credentials*`, `yurikey*.xml`, `**/keybox/*.xml`, `_backups/`, `_logs/`, `runtime-state/`, etc.).
2. The daemon's regex scan on the staged diff catches any secret literal that slipped past `.gitignore`.
3. GitHub's push-protection (default-on for private repos) is the third layer if something still gets through.
4. **Never force-push.** If history diverges, the daemon errors and waits for operator intervention rather than overwriting.
5. **Branch guard.** Auto-commit only on `main`. Per-agent branches (`agent/<name>/<topic>`) are pushed by their owning sessions, not by the daemon. This pairs with canonical-rule 3 (per-agent branch discipline).

## Operator-facing controls

| Want to... | Use |
|---|---|
| See status + recent log | `Sanctum-Auto-Push-Status.bat` |
| Pause without removing the task | `Sanctum-Auto-Push-Pause.bat` |
| Resume | `Sanctum-Auto-Push-Resume.bat` |
| Force a run right now | `Start-ScheduledTask -TaskName SinisterSanctumAutoPush` |
| Uninstall entirely | `D:\Sinister Sanctum\automations\uninstall-auto-push-task.ps1` |
| See full log history | `D:\Sinister Sanctum\_shared-memory\auto-push.log` (+ `.log.1` rotation) |

## What the daemon does NOT do

- Doesn't push product-repo source under `projects/<repo>/source/` (those are already covered by nested `.gitignore`s + lane-discipline rule 10).
- Doesn't push to the `sanctum` remote (local Gitea); that's a separate mirror handled by `tools\sanctum-git\` flows when needed.
- Doesn't write to any other branch — only `main`.
- Doesn't run as SYSTEM — runs as the interactive user, so SSH keys / `gh` credential helper / keyring are accessible.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 ~07:30 by Sinister Sanctum
First shipped. Operator directive: "push the current state of the sanctum to this github and make it auto push every 30 minutes. dont if no activity has been done. ... you have complete control to do this without me." Repo: `Sinister-Systems-LLC/Sinister-Sanctum` (Private). First push used HTTPS + gh CLI credential helper (token scopes: gist, read:org, repo). `workflow` scope was needed because `.github/workflows/bots-smoke.yml` ships in the tree — see [github-auth-workflow-scope](./github-auth-workflow-scope.md) for the scope-refresh detail.

## Related topics

- [github-auth-workflow-scope](./github-auth-workflow-scope.md) — gh OAuth scope quirk for `.github/workflows/*` pushes
- [per-agent-branch-convention](./per-agent-branch-convention.md) — why the daemon guards on `main` only
- [gitea-self-host](./gitea-self-host.md) — the parallel Gitea mirror (handled separately)
