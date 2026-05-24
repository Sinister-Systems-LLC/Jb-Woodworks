# BAKE-PANEL-NOTES.md

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Subject:** `bake-panel.sh` audit + minimal safety fixes
> **Scope:** Idempotency + atomic-swap + bounded npm network calls + failure trap. No feature changes.

## What the script does (plain English)

- Locates the Sinister Panel Next.js dashboard source at `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/`.
- Copies it to a side-staging dir under `projects/sinister-os/build/_panel-staging/` (lane discipline: never edits the Panel source tree in-place).
- Overwrites the staging copy's `next.config.mjs` with one that sets `output: 'standalone'` and re-injects the `/api/*` rewrites pointing at `BACKEND_URL`.
- Runs `npm ci && npm run build` inside the staging dir to produce `.next/standalone/server.js` + assets.
- Copies the standalone bundle (server.js + minimal node_modules) plus `.next/static` + `public/` into the airootfs overlay at `source/iso-build/airootfs/srv/sinister-panel/` so `build.sh` can fold it into the ISO.

## What was fixed (specific lines + rationale)

All three fixes are commented inline with `# Safety fix 2026-05-24 (RKOJ-ELENO):` so future audits see the rationale next to the code.

1. **Atomic-swap into `$DEST` (lines 17-21, 73-91 of new file)** — Original script did `rm -rf "$DEST"` BEFORE the build artifacts were copied. If `cp` or build hiccuped, the operator was left with a destroyed prior-known-good bundle and a half-populated dest. Fix: build into `${DEST}.new` first, sanity-check `server.js` exists, then move prior `$DEST` to `${DEST}.old` and atomic-`mv` the new bundle in. Prior bundle stays recoverable from `${DEST}.old` until the next run.
2. **Failure trap (lines 24-35)** — Added an `EXIT` trap that prints the locations of `STAGING`, `DEST_NEW`, and `DEST` on non-zero exit so the operator immediately knows which dirs to inspect / clean up rather than silently inheriting half-built state on the next run.
3. **Bounded npm fetches (lines 53-58)** — Added `--fetch-retries=5 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000 --fetch-timeout=300000` to the `npm ci` call. The original call had no explicit retry / timeout, so a flaky registry could hang the script forever. Behavior on a healthy network is unchanged.

Things deliberately NOT changed:
- `set -euo pipefail` already present (line 13). Kept.
- `readlink -f "$0"` works fine on the operator's git-bash on Windows. Left alone.
- Hard-coded path with spaces (`Andrew Panel/Sinister Panel/`) is quoted correctly. Left alone.
- No comments removed. No behavior changed for the green-path success case.
- Author line untouched (already `RKOJ-ELENO :: 2026-05-24`).

## Verification this turn

```
$ bash -n source/iso-build/bake-panel.sh   # pre-edit
PARSE-OK
$ bash -n source/iso-build/bake-panel.sh   # post-edit
POST-EDIT PARSE-OK
$ wc -l bake-panel.sh
112 bake-panel.sh
```

shellcheck not installed on this Windows git-bash; could not run static lint pass. Future TODO: install shellcheck on operator's bash and re-run.

Panel source path resolves: `D:/Sinister Sanctum/projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/` exists and contains `app/ components/ lib/ middleware.ts next.config.mjs package.json public/`.

Current `airootfs/srv/sinister-panel/` is empty (clean slate). First run of fixed script will populate it; the `.old` rollback path will not exist until the second run.

## What still needs operator action before a real bake

1. **Node.js 20+ installed on the operator's machine** (Docker only runs `mkarchiso` per `build.sh`'s comment; the JS build runs on the host).
2. **Panel source must be in a buildable state** — `package.json` deps install cleanly with `npm ci`, and `npm run build` produces `.next/standalone/server.js`. A test `npm install && npm run build` from `projects/sinister-panel/source/Andrew Panel/Sinister Panel/panel/dashboard/` is the precondition smoke-test before invoking `bake-panel.sh`.
3. **Docker Desktop running** — only required for the subsequent `build.sh`; `bake-panel.sh` itself doesn't touch docker.
4. **Disk headroom** — `_panel-staging/` plus `airootfs/srv/sinister-panel/` plus `airootfs/srv/sinister-panel.old/` after swap can easily reach 500 MB-1 GB of node_modules + build output. Confirm `D:` has ~2 GB free before running.

## Exact command for the operator to test

From the project root (`D:\Sinister Sanctum\projects\sinister-os\`):

```bash
bash source/iso-build/bake-panel.sh
```

Expected end state on success:
- `source/iso-build/airootfs/srv/sinister-panel/server.js` exists.
- `source/iso-build/airootfs/srv/sinister-panel/.next/static/` populated.
- `source/iso-build/airootfs/srv/sinister-panel/public/` present (if Panel ships static assets).
- `build/_panel-staging/` retained for inspection.
- `source/iso-build/airootfs/srv/sinister-panel.new/` does NOT exist (got swapped in).
- `source/iso-build/airootfs/srv/sinister-panel.old/` exists only after the SECOND successful run.

Failure-mode receipt: trap prints all three paths so the operator can decide whether to `rm -rf` the `.new` dir or keep it for forensics.
