# Stale Git Lock Auto-Cleanup — Doctrine 2026-05-26

> Author: RKOJ-ELENO :: 2026-05-26 (sinister-term lane)
> Composes with: `automate-everything-no-operator-admin-2026-05-25` · `safe-quality-loops-doctrine-2026-05-24` · `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25`

## Operator pain (verbatim 2026-05-26 ~21:30Z)

> "sometimes the terminals will just freeze for 1-10 minutes and then come back and keep working. i need things like these to stop happening"

## Root cause

Multiple concurrent Claude sessions in the same repo (every lane is rooted at `D:\Sinister Sanctum`) all serialize on `.git/index.lock`. When ANY of these dies without releasing the lock the file persists until manually removed:

1. Crashed `git clone` started by the link-ingest pipeline (e.g. cloning `openai/whisper` with `--depth 50` and the network stalls)
2. Killed mintty window mid-commit (operator clicks X)
3. `sanctum-auto-push.ps1` interrupted by a power event
4. PowerShell child timing out at the 60s tool boundary

Every later `git` op then blocks waiting for a lock that will never be released. A `git status` that should take 50ms takes the full 1-10 min timeout before failing.

## Canonical fix

`automations/clean-stale-git-locks.py` (Python per `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25`):

- Walks `.git/` for `index.lock`, `HEAD.lock`, `packed-refs.lock`, `config.lock`, `refs/**/*.lock`, `logs/**/*.lock`
- Removes any whose mtime is older than `--threshold-seconds` (default 120s)
- Appends every action to `_shared-memory/git-lock-cleanup.jsonl`
- Exit 0 always (never wedges the schtask scheduler)

Modes:
- `python automations/clean-stale-git-locks.py` — one sweep, exit 0
- `python automations/clean-stale-git-locks.py --dry-run` — show what would be removed
- `python automations/clean-stale-git-locks.py --loop --interval 30` — long-lived daemon variant

## Schtask registration (operator clicks nothing)

Register via `schtasks.exe` so it runs every minute regardless of which session is alive:

```
schtasks /Create /TN SinisterStaleLockCleaner /SC MINUTE /MO 1 ^
  /TR "python \"D:\\Sinister Sanctum\\automations\\clean-stale-git-locks.py\" --quiet" ^
  /F /RU SYSTEM
```

Threshold of 120s is conservative: a legitimate long-running git operation (e.g. push to a slow remote) won't be touched, but a stale lock that's been there for 2+ min IS swept.

## Safety rails

1. **Threshold floor of 10s** — clamped in code so a `--threshold-seconds 0` typo never nukes an active lock
2. **mtime-based, not access-time** — atime is unreliable on Windows
3. **Append-only log** — every removal recorded so we can audit "did the cleaner cause this missing-lock bug?"
4. **Skip on stat failure** — if we can't stat the file, leave it alone
5. **No process killing** — only file removal; no killing of held-locks-by-live-pids (those will release naturally)

## What this does NOT fix

- **Concurrent staging races** — two agents both running `git add` simultaneously may have staged work clobbered by whichever commits first. Real fix is per-agent worktrees (`git worktree add`) which is a deeper refactor.
- **Long-running clones holding the lock legitimately** — if a clone TRULY needs >2 min, this would yank its lock out. Threshold tunable; bump to 300s if needed.
- **Hung Claude tool calls** — those wedge the harness, not git. Different problem class.

## Brain index entry

Add to `_shared-memory/knowledge/_INDEX.md`:

| Date | Slug | Title |
|---|---|---|
| 2026-05-26 | stale-git-lock-auto-cleanup | Auto-removes >120s-stale .git/*.lock files; eliminates 1-10min terminal freezes |
