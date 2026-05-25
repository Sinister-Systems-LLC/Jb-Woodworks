# Version-Snapshot System — Plan (iter-23 sub-3)

**Author:** RKOJ-ELENO :: 2026-05-25 (sanctum lane; sub-agent a8316b298e53d4203, persisted by sanctum master)
**Operator utterance:** 2026-05-25T06:33:48Z — *"we need to satrt taking a versions appraoch to everything we do so we always have versions we can revret back to incase diaster strikes."*

## Problem statement

Today the repo has ad-hoc tags (`leo-ready-2026-05-25-iter22`), reflog (local-only), an `EVE.exe.sha256` sidecar (one binary), a freshly-shipped `automations/version_snapshot.py` (SemVer tag + zip + revert PLAN-only), and `automations/auto_snapshot_on_milestone.py` (push-time trigger on `MILESTONE:` / iter-N close / deploy-folder touch). What's MISSING: per-file SHA manifest, one-command atomic restore with SHA verification, hourly silent cadence, exclusion globs to keep noise out of snapshots, per-lane scoping.

This plan EXTENDS the existing primitives so "revert to version X" is one command with a binary pass/fail verdict.

## Gap analysis

| Gap | Today | Needed |
|---|---|---|
| Per-file SHA manifest at snap | Only EVE.exe + deploy/ have sidecars | Repo-scoped `manifest.json` per snapshot |
| Atomic restore | `--revert` prints plan; operator pastes git cmd | `restore <ver> --verify` executes + verifies SHAs + writes log |
| Post-restore verification | None | Recompute SHAs vs `manifest.json`; fail-fast on mismatch |
| Hourly silent cadence | Only milestone-triggered | Add schtask hourly snap (patch bump, label=`auto-hourly`) |
| Exclusion list | `CRITICAL_PATHS` is allow-list only; no exclude | Explicit `EXCLUDE_GLOBS` applied during zip walk |
| Per-lane snap scope | Whole-repo only | Optional `--lane <slug>` narrows manifest |
| Restore log | None | `_shared-memory/version-snapshots/restore-log.jsonl` append-only |

## Proposed primitives (extends `automations/version_snapshot.py`)

1. **`snap [--label X] [--lane Y]`** — git tag (unchanged) + `versions/MANIFEST.md` row (unchanged) + NEW per-file `manifest.json` + NEW binary-only `binaries.zip` + NEW `headline.md` at `_shared-memory/version-snapshots/<ver>/`.
2. **`list [--limit N] [--lane Y]`** — extends `--list` with cross-ref to per-version `manifest.json` presence.
3. **`restore <ver> [--verify] [--dry-run] [--allow-dirty]`** — NEW. Executes atomic restore: dirty-check → fetch tags → save HEAD to restore-log → checkout to safety branch `restore/<ver>-<ts>` → unzip binaries.zip → verify all manifest SHAs → exit 0 iff all match.
4. **schtask `SinisterVersionSnapHourly`** — direct `schtasks.exe /Create` (no `.ps1` wrapper); runs `pythonw version_snapshot.py snap --label auto-hourly --bump patch --silent`; `--silent` skips when HEAD sha unchanged.

## File-touch plan (P0 = NEW files only, no live-code edits)

| New file | Description |
|---|---|
| `_shared-memory/version-snapshots/` | Root directory for per-version artifacts |
| `_shared-memory/version-snapshots/restore-log.jsonl` | Append-only restore audit log |
| `_shared-memory/version-snapshots/EXCLUDE.txt` | Glob exclude list (one per line) |
| `_shared-memory/version-snapshots/README.md` | Schema doc for `manifest.json` + `binaries.zip` + `headline.md` |
| `_shared-memory/knowledge/version-snapshot-system-doctrine-2026-05-25.md` | Brain doctrine entry |

Per-version paths (created at snap time): `<ver>/manifest.json`, `<ver>/binaries.zip`, `<ver>/headline.md`.

## Rollout phases

- **P0:** scaffold + doctrine (this plan + 4 placeholder files); no code edits; reversible by `git rm`.
- **P1:** extend `version_snapshot.py` `snap` subcommand with `manifest.json` + `binaries.zip` + `headline.md` writers.
- **P2:** add `restore --verify` subcommand; `--revert` becomes alias for `restore --dry-run --no-verify` (back-compat).
- **P3:** install `SinisterVersionSnapHourly` schtask via direct `schtasks.exe /Create`; `--silent` skip-if-unchanged.
- **P4:** add `LANE_PATHS` table + `--lane` filter; per-lane snap-at-session-start integration.

## Pass criterion (5 binary checks — all must exit 0)

1. **Snap-mutate-restore round-trip on EVE.exe.** snap → record SHA → mutate EVE.exe → restore → recompute SHA → must equal recorded → exit 0.
2. **`manifest.json` schema valid.** keys `{version, utc_ts, head_sha, files}` + every `files[i].sha256` is 64 hex chars.
3. **Restore-log row written.** last row has `verify_pass: true` + 40-hex `pre_restore_head`.
4. **Exclusions honored.** `python -m zipfile -l <ver>/binaries.zip` lists ZERO entries matching any glob in `EXCLUDE.txt`.
5. **Hourly schtask present + idempotent.** `schtasks /Query` shows Ready; `snap --silent` exits 0 with empty stdout when HEAD sha unchanged.

## Anti-patterns (DO NOT)

1. **Do NOT checkpoint `_shared-memory/anthropic-usage-cache.default.json`** — mutates every Claude call; bloats snapshots. Add to `EXCLUDE.txt`.
2. **Do NOT snapshot `projects/` junction targets.** Use `os.walk(followlinks=False)` + `is_symlink()`/`is_junction()` skip.
3. **Do NOT snapshot OAuth credentials or `*.bak*` files.** `_shared-memory/claude-accounts.json*` + `forge-bridge-token.txt` + `*.json.bak-*` → `EXCLUDE.txt` + secret-scan guard.
4. **Do NOT `git reset --hard` from restore.** Create `restore/<ver>-<ts>` branch via `git checkout <ver> -b restore/...`; print but don't execute reset.
5. **Do NOT block on push failures.** `--push` best-effort; `sanctum-auto-push.ps1` retries next cycle.
6. **Do NOT prune `versions/MANIFEST.md` rows.** Append-only. Zip pruning (>90 days) handled by separate `prune` subcommand (P5+) that touches only `binaries.zip`, never `manifest.json`.

## Effort estimate

- P0: ~250 LOC docs, 30 min (single planner — this plan).
- P1: +120 LOC in `version_snapshot.py`, 45 min (parallelizable: A writes manifest, B writes zip walker).
- P2: +90 LOC, 45 min (parallelizable: A writes restore flow, B writes verifier).
- P3: +20 LOC + 1 schtasks call, 15 min.
- P4: +60 LOC + LANE_PATHS table, 60 min (embarrassingly parallel per lane).

**Total:** ~290 LOC code + ~250 LOC docs; ~3.25 hr single-agent / ~1.5 hr with 3-way parallel.

## Composes with

- `leo-deploy-folder-bootstrap-doctrine-2026-05-25` — `binaries.zip` bundles `deploy/EVE.exe` + `deploy/_internal/` so restore guarantees Leo's bring-up still works.
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` — Python only; schtask install is direct `schtasks.exe`, no wrapper.
- `safe-quality-loops-doctrine-2026-05-24` — reversibility wall: restore always creates a branch.
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — pass criterion must execute before claiming.
- `frequent-detailed-commits-per-agent-2026-05-25` — each phase lands as its own commit (Shipped/Smoke/Refs).

(Full extended plan available in sub-agent transcript a8316b298e53d4203; this file is the actionable summary for execution iter.)
