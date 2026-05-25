<!-- Author: RKOJ-ELENO :: 2026-05-23 -->
<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Project-root disk integrity (anti-archived-but-still-in-picker pattern)

> **Status:** doctrine, empirical, binding for picker maintenance.
> **Origin:** operator 2026-05-23 evening — Sinister Freeze launch failed (`cd /d/Sinister Sanctum/projects/sinister-freeze: No such file or directory`) because the project was archived 2026-05-21 (commit `1dfcb4e`) but never removed from `projects.json` picker rotation.

## What broke

Launcher boots a project from `projects.json`. The picker UI shows the project key. The cold-start phrase tells the spawned EVE to `cd <root>`. If `<root>` does not exist on disk, the spawn fails immediately — operator sees `[FAIL] could not cd to project root` in a terminal that closes seconds later.

The freeze case: operator asked 2026-05-21 to "remove sinister freeze" — the dir was moved to `_archive/sinister-freeze-removed-2026-05-21/sinister-freeze/` (preserving content for audit), but the `projects.json` entry stayed live, including in the `picker.visible_keys[]` rotation. 2026-05-23 evening operator clicked Sinister Freeze → broken cd → broken launch.

## The invariant

Every entry in `projects.json::projects[]` MUST have one of:

1. A `root` that resolves to an existing directory on disk, OR
2. NO `root` field at all (special-keys like `__autoresume__`, `__newproject__`, `general` are exempt — they don't `cd`).

Likewise, every entry in `picker.visible_keys[]` MUST correspond to a `projects[]` entry whose `root` exists.

When archiving a project:
- Either delete the `projects[]` entry entirely + remove from `picker.visible_keys[]`, OR
- Repoint `root` to the archive path (so the picker still works but enters the archived view), OR
- Leave the `projects[]` entry but remove from `picker.visible_keys[]` (so the project survives in code references like RKOJ agents_tab but doesn't appear in the operator-facing picker).

## Enforcement

`automations/canonical-protections-check.ps1` P8 protection (added 2026-05-23 evening) iterates every `projects[]` entry and verifies `root` exists. Fails are logged + surfaced to OPERATOR-ACTION-QUEUE.md.

Runs on every session start via the `.claude/settings.json` SessionStart hook (same wiring as P1-P7).

## Anti-patterns

1. **Archive-without-picker-update.** Moving a project dir to `_archive/` while leaving `projects[]` + `picker.visible_keys[]` references intact.
2. **Soft-delete in `projects[]`-only.** Removing `picker.visible_keys[]` entry but leaving `projects[]` entry with broken `root` — non-picker consumers (RKOJ agents_tab, sinister-eve, forge picker) still iterate `projects[]` and hit the broken cd.
3. **Path-string-instead-of-disk-check.** Trusting that `projects.json` is "consistent because it was reviewed by a human" — the check script provides the empirical anchor.
4. **Restoring without operator confirmation when their last request was "remove".** Freeze restoration this turn was acceptable because the operator's NEW message was "fix it" + the launch failure was real; but if operator had said "delete it permanently" we'd ask before restoring.

## Recovery procedure when P8 fires

1. Check `_shared-memory/canonical-protections-violations.log` for the missing-root list (`P8 missing roots:` section).
2. For each missing root, decide:
   - **Restore from archive** if the project should still be launchable (operator's freeze case 2026-05-23). `mv _archive/<archive-dir>/<proj> projects/<proj>`.
   - **Remove from picker + projects[]** if the project is truly retired. Edit `projects.json` to drop the entry from both `projects[]` and `picker.visible_keys[]`.
   - **Repoint root** if the project moved to a non-canonical location. Edit the entry's `root`.
3. Re-run `canonical-protections-check.ps1` to confirm.
4. Commit with explanation in commit body.

## Composes with

- `do-not-revert-operator-canonical-protections-2026-05-23.md` (same 4-layer enforcement model, this is P8).
- `launcher-v6-concise-rewrite-2026-05-23.md` (picker visibility separation pattern — the v6 split between `projects[]` and `picker.visible_keys[]` makes it CLEARER which is the picker rotation, but P8 ensures the underlying `projects[]` stays consistent).
- `sibling-active-launch-coordination-pattern` (when multiple agents touch projects.json, P8 fires early so divergence is visible).
- `forever-expanding-modular-architecture-doctrine` (append-only rule still applies — better to remove entries than leave broken ones).

## Tags

doctrine, empirical, binding, p8, project-root, projects-json, disk-integrity, picker, visible-keys, archived-still-in-picker, sinister-freeze, recovery-procedure, canonical-protections-check, sessionstart-hook, 2026-05-23
