# `_shared-memory/version-snapshots/` — snapshot artifact root

**Author:** RKOJ-ELENO :: 2026-05-25
**Doctrine:** `_shared-memory/knowledge/version-snapshot-system-doctrine-2026-05-25.md`
**Plan:** `_shared-memory/plans/version-snapshot-system-2026-05-25/plan.md`

## What lives here

```
_shared-memory/version-snapshots/
├── EXCLUDE.txt                  ← glob excludes (see below)
├── README.md                    ← this file
├── restore-log.jsonl            ← append-only restore audit (created on first restore)
└── <version>/                   ← one dir per snapshot, e.g. v22.4.1-rt-test/
    ├── manifest.json            ← per-file SHA manifest
    ├── binaries.zip             ← compiled binaries (EVE.exe + _internal/ etc.)
    └── headline.md              ← commit subject + tagger + verify cmd
```

## `<version>/manifest.json` schema

```json
{
  "version": "v22.4.1-rt-test",
  "utc_ts": "2026-05-25T07:00:00Z",
  "head_sha": "<40-hex git sha>",
  "lane": "sanctum",
  "files": [
    { "path": "EVE.exe",                "sha256": "<64-hex>", "size": 2199040, "mode": 33188 },
    { "path": "automations/version_snapshot.py", "sha256": "<64-hex>", "size": 12345, "mode": 33188 }
  ]
}
```

Schema invariants (enforced by `version_snapshot.py snap` writer):
- `version` matches the git tag exactly (SemVer `v<M>.<m>.<p>-<label>`)
- `utc_ts` is RFC3339 with `Z` suffix
- `head_sha` is 40 lowercase hex chars
- `files[i].sha256` is 64 lowercase hex chars
- `files` is sorted by `path` (stable diffs across snapshots)
- Paths excluded by `EXCLUDE.txt` MUST NOT appear in `files[]`

## `<version>/binaries.zip` contract

Bundles ONLY binary artifacts (not source — source is in git):
- `EVE.exe` (repo root)
- `deploy/EVE.exe`
- `_internal/` (PyInstaller runtime, ~56 files / ~18 MB)
- `deploy/_internal/`
- `EVE.exe.sha256` (sidecar)
- `deploy/MANIFEST.txt`

Restored via `python automations/version_snapshot.py restore <version> --verify` — see plan §3 P3.

## `<version>/headline.md` template

```markdown
# <version>

**Tagger:** <git user>
**UTC:** <utc_ts>
**Head sha:** <40-hex>
**Commit subject:** <git log -1 --format=%s>

## Verify

```
python automations/version_snapshot.py restore <version> --verify
```

## Restore

```
python automations/version_snapshot.py restore <version>
```
```

## `restore-log.jsonl` schema (one row per restore)

```json
{
  "utc_ts": "2026-05-25T08:00:00Z",
  "version": "v22.4.1-rt-test",
  "sha": "<40-hex>",
  "lane": "sanctum",
  "pre_restore_head": "<40-hex>",
  "verify_pass": true,
  "files_checked": 152,
  "mismatches": []
}
```

## EXCLUDE.txt format

One glob per line, `#` for comments. Globs are matched via `fnmatch.fnmatch()` against the path RELATIVE to repo root. See `EXCLUDE.txt` for the canonical list.

## What this is NOT

- NOT a backup system. `binaries.zip` is regeneratable from a build; source lives in git.
- NOT a long-term archive. Old `binaries.zip` blobs may be pruned by a future `prune` subcommand (>90 days, >100 MB total). `manifest.json` rows stay forever as the SHA audit trail.
- NOT a replacement for `git tag`. Each snapshot creates a git tag; this dir adds the per-file SHA + binary bundle on top.

## Composes with

- `leo-deploy-folder-bootstrap-doctrine-2026-05-25` — `binaries.zip` includes `deploy/EVE.exe` + `deploy/_internal/` so a restore guarantees Leo's bring-up works.
- `no-bat-no-ps1-do-it-for-me-doctrine-2026-05-25` — Python only; schtask install is direct `schtasks.exe`, no wrapper.
- `safe-quality-loops-doctrine-2026-05-24` — restore always creates a `restore/<ver>-<ts>` branch (never rewrites main automatically).
