<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# Version-snapshot disaster-recovery doctrine

> **Status:** binding for every fleet agent that touches `deploy/`, `automations/`, `CLAUDE.md`, or `_shared-memory/knowledge/`.
> **Date:** 2026-05-25
> **Composes with:** `frequent-detailed-commits-per-agent-2026-05-25` · `single-repo-push-policy-2026-05-25` · `leo-deploy-folder-bootstrap-2026-05-25` · `no-bullshit-tested-before-claimed-doctrine-2026-05-23` · `safe-quality-loops-doctrine-2026-05-24`

## Operator verbatim 2026-05-25 ~06:30Z

> *"we need to satrt taking a versions appraoch to everything we do so we always have versions we can revret back to incase diaster strikes"*

## TL;DR

Every meaningful push to `main` (and any milestone on an `agent/*` branch that lands on `main`) is reachable via a versioned tag inside 30 seconds, with a one-command revert path. `versions/MANIFEST.md` is the append-only source of truth; `automations/version_snapshot.py` is the tool; `automations/auto_snapshot_on_milestone.py` automates the common case.

## SemVer scheme

`v<MAJOR>.<MINOR>.<PATCH>-<LABEL>`

| Bump | When | Example |
|---|---|---|
| MAJOR | operator-declared new era | `v22 → v23` |
| MINOR | significant feature land / breaking deploy change / doctrine shift | `v22.0 → v22.1` |
| PATCH | per-iter close / bugfix / polish | `v22.0.0 → v22.0.1` |
| LABEL | kebab-case slug (`leo-ready`, `crash-fix`, `ui-polish`) | always present |

## MANIFEST schema

`versions/MANIFEST.md` is markdown with a single table; append-only.

```
| utc_ts | version | commit_sha | label | headline | revert_command |
```

Append-only invariants:

1. Never edit a row. To correct, append a new row + tag a new version.
2. Rows are ordered by `utc_ts` ascending.
3. `version` is unique. If a duplicate is detected, the tool exits 0 with `already-exists` (NEVER overwrites).
4. `revert_command` is always literal `git checkout <version>` (the simplest shape; other shapes documented in `versions/README.md`).

## 5 revert scenarios

1. **Full** — repo is OK but you want to go back in time → `git checkout <version>`.
2. **Single-file** — one file got clobbered → `git show <version>:<path> > <path>`.
3. **Subsystem** — one folder got clobbered → `git checkout <version> -- <path>...`.
4. **Pre-Leo** — Leo handoff regressed → `git checkout v22.0.0-leo-ready` (the canonical baseline).
5. **Nuke-and-snapshot** — repo is gone → `unzip versions/snapshots/<version>.zip` into a fresh directory.

## 6 anti-patterns

1. **Snapshot without manifest row** — orphan tag, no headline → MANIFEST is the source of truth; tag alone is insufficient.
2. **Unpushed tag** — local only → always `--push` (or `git push origin <tag>` after).
3. **Zip without SHA verify** — corrupted snapshot you discover during disaster → spot-check zip after creation.
4. **Overwriting an existing version** — tool refuses by design (`already-exists` exit 0). If you really need a re-tag, delete + recreate explicitly.
5. **Forgetting to bump after milestone push** — every milestone deserves a tag → `auto_snapshot_on_milestone.py` fixes the common case.
6. **Concurrent `git reset --hard` wiping uncommitted version-snapshot files** — REAL, happened iter-22 EXT2 (Sub-H's work was wiped by a parallel sanctum agent before commit). Mitigation: **commit version-snapshot files IMMEDIATELY upon creation, before any other work**. Treat version-snapshot artifacts as atomic-with-tag; never let them sit uncommitted while doing other parallel work.

## Pass criterion

- Every push to `main` is reachable via a versioned tag within **30 seconds** of the push (enforced by `auto_snapshot_on_milestone.py` invoked from `sanctum-auto-push.ps1`).
- Operator can revert with **1 command + 1 confirm** (e.g. `git checkout v22.0.0-leo-ready` + `y` if a prompt appears).
- `MANIFEST.md` reflects every tag; `versions/snapshots/` reflects every `--include-zip` invocation; no orphans.

## When to use which bump

- **MAJOR** — only when the operator declares a new era. Rare. Resets MINOR + PATCH to 0.
- **MINOR** — significant feature lands. Resets PATCH to 0.
- **PATCH** — default. When in doubt, bump patch. Cost of a tag is zero; under-tagging is the real risk.

## Tool contracts

`automations/version_snapshot.py`:
- `--create <label> [--bump major|minor|patch] [--include-zip] [--push] [--dry-run]`
- `--list` — pretty-print MANIFEST
- `--revert <version>` — print plan (NEVER executes; operator copies the command)
- `--diff <v1> <v2>` — `git diff --stat`
- Duplicate-tag handling: prints `already-exists` and exits 0 (no error)

`automations/auto_snapshot_on_milestone.py`:
- Detects milestone via 3 triggers (commit-prefix `MILESTONE:`, `iter-N CLOSE` regex, deploy/ or _internal/ touched)
- Bumps patch, creates tag, pushes, appends manifest
- Idempotent via `_shared-memory/.auto-snapshot-state.json` (HEAD-SHA cache)
- Logs every run to `_shared-memory/auto-snapshot-log.jsonl`

## Cross-references

- Operator quote (this row): `_shared-memory/operator-utterances.jsonl` 2026-05-25 ~06:30Z
- Tool: `automations/version_snapshot.py`
- Daemon helper: `automations/auto_snapshot_on_milestone.py`
- Manifest: `versions/MANIFEST.md`
- Operator README: `versions/README.md`
- Composes-with doctrines listed above
- First baseline: `v22.0.0-leo-ready` at commit `0bab62036a5d`

## Forever-improve hooks

When `versions/MANIFEST.md` grows past 50 rows, consolidate by archiving rows older than 90 days into `versions/_archive/MANIFEST-<year>-<quarter>.md` (the tags themselves are NEVER deleted; only the manifest view collapses).
