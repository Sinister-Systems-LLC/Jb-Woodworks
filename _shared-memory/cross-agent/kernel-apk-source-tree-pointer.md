# kernel-apk source-tree pointer

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Lane:** kernel-apk (EVE on Sinister Kernel APK)
> **Closes:** OPERATOR-ACTION-QUEUE 2026-05-24T19:30Z row option (b) — fresh clone authorized + executed; this lane chose (b) automatically per 2026-05-25 NO-OPERATOR-ADMIN-ACTIONS doctrine (operator does not need to pick a/b/c).

## Canonical Sanctum-side working dir

```
D:\Sinister Sanctum\projects\sinister-kernel-apk\source-v2\
```

- **Origin:** `https://github.com/Sinister-Systems-LLC/Sinister-APK.git`
- **Default branch:** `main` (currently at v0.92.5 — stale)
- **Active lane branch:** `agent/sinister-kernel-apk/crispy-cosmos-resume` (HEAD as of this writing: `d901f4c` — v0.97.45 P0 fix)
- **Size:** ~257 MB (full history)
- **Cloned:** 2026-05-25 ~06:00Z by kernel-apk lane via `gh repo clone Sinister-Systems-LLC/Sinister-APK D:/Sinister Sanctum/projects/sinister-kernel-apk/source-v2`

## Why source-v2 (not source/)

- `D:\Sinister Sanctum\projects\sinister-kernel-apk\source\source\` is the OLD clone — **corrupt** (`fatal: unable to read tree (3b3617a8b494e847cd4f21b0f8afb4046dfe5294)`; HEAD at `cda2e4e v0.97.9`; 4 missing tree objects + orphan tmp_pack per diagnose-lane fsck 2026-05-24T13:55Z).
- Repair-in-place is hard with missing tree objects + 8 versions of drift. Fresh clone was faster.
- The OLD path is **left alone** (no destructive cleanup) — operator can `rm -rf` it manually if/when desired.

## What's in source-v2 at HEAD

- v0.97.44 GitHub-side rollup including v0.97.13-v0.97.36 carry-forward
- v0.97.45 (this lane, 2026-05-25): P0 att_token capture fix — removed bogus `pidof` gate in `OfflineHarvest.fillBodyGaps` that was unconditionally skipping every stash read because Snap was backgrounded-but-alive at push time.

## What's NOT in source-v2 yet

- v0.97.45-v0.97.50 (per SESSION-END-STATE the "live ship" was at v0.97.50). If those commits exist anywhere, they're on operator's local machine and have **NOT** been pushed to origin. If/when operator pushes them, they'd land via the same agent branch (or main).

## Sibling-lane usage rules

- **diagnose lane:** when ssh-ing to a phone to verify a fix landed, target a build from `source-v2` (run `git log -1` to confirm commit hash matches APK installed on phone). Do NOT target the corrupt `source/source/` repo.
- **sanctum-mesh / sanctum-helper / any sub-agent:** when grepping kernel-apk source, use `source-v2/` paths. The old `source/source/` path will error on `git log` / `git status`; readable file content there is stale-by-design (v0.97.9).
- **kernel-apk lane future sessions:** `cd D:/Sinister Sanctum/projects/sinister-kernel-apk/source-v2 && git checkout agent/sinister-kernel-apk/crispy-cosmos-resume` — that is the lane's working branch.

## When this pointer needs updating

- If/when the canonical kernel-apk repo moves OR the agent branch is renamed OR a v0.98+ branching strategy lands. Otherwise stable.

## Composes with

- `_shared-memory/OPERATOR-ACTION-QUEUE.md` 2026-05-24T19:30Z row (closed by this pointer)
- `_shared-memory/OPERATOR-ACTION-QUEUE.md` 2026-05-24T20:18Z 🔴 CRITICAL row (P0 att_token fix shipped at `d901f4c` per this pointer; awaits diagnose-lane Hetzner verification)
- `_shared-memory/plans/kernel-apk-session-2026-05-24-master/SESSION-END-STATE.md` (P0 fix description matches)
- `_shared-memory/knowledge/automate-everything-no-operator-admin-2026-05-25.md` (this lane picked (b) automatically per the binding)
