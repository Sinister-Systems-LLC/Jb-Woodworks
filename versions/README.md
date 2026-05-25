<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# `versions/` — disaster-recovery snapshots

Operator hard-canonical 2026-05-25 ~06:30Z: *"we need to satrt taking a versions appraoch to everything we do so we always have versions we can revret back to incase diaster strikes"*.

## What lives here

| Path | Purpose |
|---|---|
| `MANIFEST.md` | Append-only table of every tagged version + commit SHA + revert command |
| `snapshots/*.zip` | Optional binary backup of `deploy/` + `automations/` + `CLAUDE.md` + brain (only when `--include-zip`) |
| `README.md` | This file — operator-facing how-to |

## How to read MANIFEST

Each row = one tagged version. Columns:

- **utc_ts** — when the row was appended (NOT when the commit was made)
- **version** — `v<MAJOR>.<MINOR>.<PATCH>-<LABEL>` (SemVer)
- **commit_sha** — 12-char short SHA the tag points at
- **label** — short human slug
- **headline** — one-line summary of what's in this snapshot
- **revert_command** — copy-paste this to go back

## When to bump what

- **MAJOR** (`v22 → v23`) — operator declares a new era; rare; resets MINOR + PATCH to 0
- **MINOR** (`v22.0 → v22.1`) — significant feature lands (new subsystem, breaking deploy/ change, new doctrine)
- **PATCH** (`v22.0.0 → v22.0.1`) — incremental milestone (iter close, bugfix, polish)

Rule of thumb: when in doubt, **bump patch**. The cost of a tag is zero; under-tagging is the real risk.

## When to include `--include-zip`

- **Yes** — at MAJOR or MINOR boundaries, and any `deploy/`-touching milestone
- **Yes** — before a known-risky refactor (so a single `unzip` can restore)
- **No** — for plain PATCH commits where the tag is sufficient

## How to revert — 4 shapes

### (a) Full revert (go back in time entirely)

```bash
git fetch --tags
git checkout v22.0.0-leo-ready    # detached HEAD; safe to inspect
git switch -c recover/v22.0.0     # if you want to keep working from here
```

### (b) Single-file recovery (one file got nuked)

```bash
git show v22.0.0-leo-ready:CLAUDE.md > CLAUDE.md
```

### (c) Subsystem extract (one folder got nuked)

```bash
git checkout v22.0.0-leo-ready -- deploy/ automations/eve-launcher/
```

### (d) Snapshot zip (the repo is gone — but the zip survived)

```bash
mkdir _restored && cd _restored
unzip ../versions/snapshots/v22.0.0-leo-ready.zip
```

## Snap-create cheat sheet

```bash
# Most common: per-iter close, patch bump
python automations/version_snapshot.py --create "iter23-close" --bump patch --push

# Big feature landed: minor bump + zip
python automations/version_snapshot.py --create "multi-agent-launcher" --bump minor --include-zip --push

# Dry-run first to see the plan
python automations/version_snapshot.py --create "test" --dry-run

# List everything
python automations/version_snapshot.py --list

# Print revert plan (does NOT execute)
python automations/version_snapshot.py --revert v22.0.0-leo-ready

# Diff between two versions
python automations/version_snapshot.py --diff v22.0.0-leo-ready v22.1.0-foo
```

## Auto-snapshot on milestone

`automations/auto_snapshot_on_milestone.py` fires when HEAD commit:
- starts with `MILESTONE:`, OR
- matches `iter-N CLOSE`, OR
- touched `deploy/` or `_internal/`

Wire it into `sanctum-auto-push.ps1` as a one-line addition AFTER the push step:

```powershell
python automations/auto_snapshot_on_milestone.py
```

Idempotent; HEAD-SHA cached in `_shared-memory/.auto-snapshot-state.json`; each run appends a JSON line to `_shared-memory/auto-snapshot-log.jsonl`. (Not actually edited into the PS1 by this commit — too risky given parallel-agent activity. Edit when the lane is quiet.)

## Anti-pattern reminders (full list in doctrine)

1. Snapshot without manifest row — orphan tag, no headline → MANIFEST is source of truth.
2. Unpushed tag — local only → always `--push`.
3. Zip without verifying SHA — corrupted snapshot → spot-check zip after creation.
4. Overwriting an existing version — the tool refuses; if you really need a re-tag, delete + recreate explicitly.
5. Forgetting to bump after milestone push — solved by `auto_snapshot_on_milestone.py`.
6. **Concurrent `git reset --hard` wiping uncommitted version-snapshot files** — REAL, happened iter-22 EXT2. Mitigation: commit version-snapshot files IMMEDIATELY upon creation.

Full doctrine: `_shared-memory/knowledge/version-snapshot-disaster-recovery-doctrine-2026-05-25.md`.
