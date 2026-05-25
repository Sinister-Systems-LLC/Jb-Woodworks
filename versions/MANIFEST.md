<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
# Sinister Sanctum — Version Manifest (append-only)

Operator hard-canonical 2026-05-25 ~06:30Z: *"we need to satrt taking a versions appraoch to everything we do so we always have versions we can revret back to incase diaster strikes"*.

## SemVer scheme

`v<MAJOR>.<MINOR>.<PATCH>-<LABEL>`

| Bump | When |
|---|---|
| MAJOR | operator-declared era (e.g. v22 = first version-tagged iter; v23 = next big era) |
| MINOR | significant feature land (new subsystem, breaking change to `deploy/`, doctrine shift) |
| PATCH | incremental milestone (per-iter close, bugfix, polish) |
| LABEL | kebab-case slug describing the snapshot (`leo-ready`, `crash-fix`, `ui-polish`) |

## Why baseline is v22 (not v1)

Iter-22 was the **first iteration ever tagged for a version-based snapshot system**. Re-numbering as v1.0.0 would have collided with the existing `iter-N` notation that fleet PROGRESS / commits / brain rows use. Starting at v22 keeps the SemVer MAJOR number aligned with the iter number for human pattern-recognition (`v22.x.x` ⇔ iter-22, `v23.x.x` ⇔ iter-23, etc.).

## Manifest rows

| utc_ts | version | commit_sha | label | headline | revert_command |
|---|---|---|---|---|---|
| 2026-05-25T02:38Z | v22.0.0-leo-ready | 0bab62036a5d | leo-ready | Leo deployment baseline: deploy/ + UAC installer + EVE.exe auto-update + crash detector + hot-update + Sinister LINK | `git checkout v22.0.0-leo-ready` |

## Notes

- The legacy tag `leo-ready-2026-05-25-iter22` is a **human-friendly alias** pointing at the same era of work as `v22.0.0-leo-ready`. Both coexist; the SemVer tag is canonical for `version_snapshot.py` tooling, the dated tag is for humans skimming `git tag --list`.
- The first version-tagged iter was iter-22 because that's when the deploy/ folder + Leo handoff coalesced into a snapshottable baseline. Earlier iters are reachable via commit SHA in `_shared-memory/PROGRESS/Sinister Sanctum.md`, just not tagged.
- Append-only: NEVER edit or remove a row. To correct, add a new row noting the correction and tag a new version.
- Tooling: `python automations/version_snapshot.py --list` renders this table; `--create LABEL` appends a row + creates the tag.
