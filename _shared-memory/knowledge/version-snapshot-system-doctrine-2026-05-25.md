<!-- decay:
  category: preference
  confidence: 1
  reinforcements: 0
  half_life_days: 365
-->
# Version-snapshot system doctrine (2026-05-25)

**Author:** RKOJ-ELENO :: 2026-05-25
**Status:** scaffold (P0); P1-P4 pending per plan.
**Plan:** `_shared-memory/plans/version-snapshot-system-2026-05-25/plan.md`
**Composes with:** `leo-deploy-folder-bootstrap-doctrine-2026-05-25` · `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` · `safe-quality-loops-doctrine-2026-05-24` · `no-bullshit-tested-before-claimed-doctrine-2026-05-23` · `frequent-detailed-commits-per-agent-2026-05-25`

## Operator verbatim trigger

> 2026-05-25T06:33:48Z: *"we need to satrt taking a versions appraoch to everything we do so we always have versions we can revret back to incase diaster strikes."*

## TL;DR

Snapshot every meaningful state of the repo (per-file SHA manifest + binary bundle + git tag) so any prior version is recoverable in one command with a binary pass/fail verdict. Extends existing `automations/version_snapshot.py` (SemVer + tag + zip + revert-plan-only) with: per-file `manifest.json`, executing `restore --verify`, hourly silent schtask, exclusion globs, per-lane scoping.

## Pass criterion (5 binary checks — all must exit 0)

1. **Snap-mutate-restore round-trip on EVE.exe.** Mutating EVE.exe then `restore --verify` brings SHA back; exit 0.
2. **`manifest.json` schema valid.** Keys `{version, utc_ts, head_sha, files}` + every `files[i].sha256` is 64 hex chars.
3. **`restore-log.jsonl` row written.** Last row has `verify_pass: true` + 40-hex `pre_restore_head`.
4. **Exclusions honored.** `python -m zipfile -l <ver>/binaries.zip` lists ZERO entries matching any glob in `EXCLUDE.txt`.
5. **Hourly schtask present + idempotent.** `schtasks /Query /TN SinisterVersionSnapHourly` shows Ready; `snap --silent` exits 0 with empty stdout when HEAD sha unchanged.

## Binding for every fleet agent

- When shipping a milestone (Leo handoff / EVE.exe rebuild / brain doctrine ratification): tag a snapshot via `python automations/version_snapshot.py snap --label <milestone>` BEFORE the next destructive op.
- Never delete a `<version>/manifest.json` row from `_shared-memory/version-snapshots/`. Append-only.
- Restore is always to a NEW branch (`restore/<ver>-<ts>`), never overwrites `main` or active agent branches.
- The 6 anti-patterns in the plan §7 are binding: no checkpointing of `anthropic-usage-cache`, no walking `projects/` junctions, no snapshotting OAuth secrets, no `git reset --hard` from restore, no blocking on push failures, no rewriting `MANIFEST.md` rows.

## Rollout status

- **P0 (this commit):** scaffold complete (`EXCLUDE.txt` + `README.md` + this doctrine + `_INDEX.md` row).
- **P1:** extend `version_snapshot.py snap` with `manifest.json` + `binaries.zip` + `headline.md` writers — PENDING.
- **P2:** add `restore --verify` subcommand — PENDING.
- **P3:** install `SinisterVersionSnapHourly` schtask — PENDING.
- **P4:** per-lane scoping (`--lane <slug>` + `LANE_PATHS` table) — PENDING.

Each phase ships as its own commit on the agent branch per `frequent-detailed-commits-per-agent-2026-05-25` (Shipped/Smoke/Refs format).
