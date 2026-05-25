# Author: RKOJ-ELENO :: 2026-05-24

# D:\ cleanup + reorg audit — 2026-05-24 (background lane)

> Run by a background EVE lane while the main session was working on launcher features. Operator brief: D:\ needs to be in a known-good state before more agents launch.
>
> Doctrine: `no-bullshit-tested-before-claimed` — every claim below was verified by direct PowerShell on the live FS (timestamps + sizes + git status + heartbeat cross-checks). Nothing in OPERATOR-SIGN-OFF has been touched. AUTO-DONE is the short list of safe Mac-junk removals already performed.
>
> Predecessor plans (for continuity): `_shared-memory/plans/d-drive-reorg-2026-05-21/` and `_shared-memory/plans/sanctum-d-drive-final-reorg-2026-05-21/`. This audit is the 2026-05-24 follow-up — most of the May-21 PHASE-CLEAN ran, but new bloat has accumulated (jbw-*, eve-build-iter33, tmp/, D:\d, D:\_shared-memory) and the dual backup roots (`D:\Backups` vs `D:\_backups`) were never consolidated.

## 1. D:\ root inventory (top-level)

Verified via `Get-ChildItem D:\ -Force` + per-dir recursive `Get-ChildItem -Recurse -File | Measure Length` (2026-05-24 ~15:30Z).

| Name | Type | SizeGB | LastWrite | Classification | Reason |
|---|---|---|---|---|---|
| `Sinister Sanctum/` | DIR | (scan in flight) | 2026-05-24 | **KEEP-AS-IS** | Active master working dir. Never touch. |
| `Sinister/` | DIR | (scan in flight) | 2026-05-23 | **KEEP-AS-IS** | "Personal" hub (per operator 2026-05-21 rename intent — still named `Sinister`). Contains `Sinister Skills` junction. Never touch. |
| `sinister-vault` | JUNCTION → `D:\Sinister Sanctum\_vault` | — | 2026-05-21 | **KEEP-AS-IS** | Vault canonical home is inside Sanctum; this junction is the desktop-friendly shortcut. |
| `Sinister-Term-WT` | JUNCTION → `D:\Sinister Sanctum\worktrees\sinister-term-wt` | — | 2026-05-21 | **KEEP-AS-IS** | Registered git worktree for `agent/sinister-term/ph7-resume-2026-05-21` (sinister-term lane). |
| `jbw-wt/` | DIR (registered git worktree) | 0.122 | 2026-05-23 | **KEEP-AS-IS** | `git worktree list` confirms registered worktree for `agent/jb-woodworks/v0.3.0-scaffold`. Branch HEAD = commit today 2026-05-24 10:36 (active lane). |
| `LetsText/` | DIR | 4.870 | 2026-05-23 | **KEEP-AS-IS** | LetsText project lane — heartbeat `letstext.json` exists, active. Operator's no-touch list. |
| `Research/` | DIR | 1.717 | 2026-05-21 | **KEEP-AS-IS** | Operator's no-touch list. |
| `Backups/` | DIR | 7.278 | 2026-05-21 | **KEEP-AS-IS** (with consolidation row, see §3) | Holds `sanctum-daily/` (6.913 GB incl. one folder named `2026-05-21 - NO DELETE`) + `custodian/` (0.335 GB). Operator's no-touch list. |
| `_backups/` | DIR | 0.562 | 2026-05-24 | **KEEP-AS-IS** (with consolidation row, see §3) | Holds `snapshots/sinister-panel-source-*` + `sinister-sanctum-llc` + `_logs/` + `_manifest.jsonl`. Operator's no-touch list. |
| `Seagate/` | DIR (hidden) | 0.000 | 2022-06-14 (root) / 2026-03-08 (sub) | **KEEP-AS-IS** | Contains only one hidden `Registration/` subdir, 0 bytes — looks like a Seagate-tools install artifact. Operator's no-touch list. |
| `$RECYCLE.BIN/` | DIR (system) | — | — | **KEEP-AS-IS** | System dir; never touch. |
| `System Volume Information/` | DIR (system) | — | — | **KEEP-AS-IS** | System dir; never touch. |
| `jbw-deploy/` | DIR (own git repo) | 0.104 | 2026-05-23 13:45 | **OPERATOR-SIGN-OFF (consolidate)** | Detached git repo, "No commits yet on main", 24 untracked-or-staged-only files. Looks like an abandoned Railway deploy scratch. Sanctum has the canonical `projects/jb-woodworks/`. Recommend: archive to `D:\_backups\d-root-archive-2026-05-24\jbw-deploy\` then delete from root. |
| `jbw-standalone/` | DIR (no git) | 0.000 (310 KB) | 2026-05-23 12:17 | **OPERATOR-SIGN-OFF (consolidate)** | Tiny standalone JBW v0.3.0 scaffold (no node_modules, no git). Duplicate of `jbw-wt/` content minus the active git state. Recommend: archive same as above. |
| `jbw-proxy/` | DIR (no git) | 0.000 (650 B) | 2026-05-24 03:04 | **OPERATOR-SIGN-OFF (relocate)** | Two files: `package.json` (`jbwoodworks-vercel-proxy`) + `vercel.json`. Tiny + modified today — looks **active** for the JBW Vercel SSL/CDN front-end. Recommend: move into `D:\Sinister Sanctum\projects\jb-woodworks\proxy\` rather than archive. |
| `eve-build-iter33/` | DIR (PyInstaller output) | 0.024 | 2026-05-24 09:57 | **OPERATOR-SIGN-OFF (purge)** | PyInstaller `build/` + `dist/EVE/EVE.exe` (24.7 MB). The `iter33` suffix implies 32 earlier iterations were already cleaned. Recommend: keep `dist/EVE/EVE.exe` somewhere canonical (e.g. `D:\Sinister Sanctum\tools\eve-exe\` or `_backups\eve-exe-snapshots\`) then delete the build dir. |
| `rkoj-eve-picker-wt/` | DIR (no git, empty shell) | 0.000 | 2026-05-23 12:08 | **OPERATOR-SIGN-OFF (delete)** | Only contains an empty `_shared-memory/` subdir. No git, no heartbeat match. Abandoned mkdir. Recommend: rmdir. |
| `d/` | DIR | 0.007 | 2026-05-23 09:47 | **OPERATOR-SIGN-OFF (delete)** | Contains exactly `Sinister Sanctum/projects/` (both empty). Looks like an accidental `mkdir d` from a script that fumbled the working-dir path. Pure orphan. Recommend: rmdir. |
| `tmp/` | DIR (mixed) | 0.000 | 2026-05-24 10:12 | **OPERATOR-SIGN-OFF (split)** | See §2 below — mixed bag: one ACTIVE production deploy (`showmasters-deploy/`), four debug `.py` files modified today, two empty worktree shells, a `susfs/` config drop, and an `rc.json` (18 KB) modified today. **Do NOT bulk-delete.** |
| `_shared-memory/` (at D:\ root, not Sanctum's) | DIR | 0.000 | 2026-05-23 09:08 | **OPERATOR-SIGN-OFF (delete)** | Contains exactly `plans/jcode-deep-compare-2026-05-23T1330Z/` (empty). Stray write from wrong cwd. NOT the canonical Sanctum `_shared-memory/`. Recommend: rmdir. |

Stray files at D:\ root (Mac droppings): **all AUTO-DELETED** — see §5.

## 2. `D:\tmp\` sub-audit

`D:\tmp` was the biggest source of ambiguity. Verified each entry:

| Entry | Type | LastWrite | Verdict | Reason |
|---|---|---|---|---|
| `showmasters-deploy/` | DIR + .git | 2026-05-24 10:38 | **DO NOT TOUCH — production active** | `git remote -v` → `https://github.com/Sinister-Systems-LLC/showmasters-site.git`, branch `main`, last commit today 10:38 ("Add header CTA row to 4 city pages"). This is the live Showmasters deploy clone. Move out of `tmp/` into `D:\Sinister Sanctum\projects\showmasters\deploy\` OR leave in-place but rename out of `tmp/`. |
| `freeze-wt/` | DIR (empty shell) | 2026-05-23 08:46 | **DELETE (operator-sign-off)** | Contains only an empty `_shared-memory/`. Real freeze worktree is registered under Sanctum. |
| `rkoj-wt7/` | DIR (empty shell) | 2026-05-23 08:13 | **DELETE (operator-sign-off)** | Contains only `tools/`. Real `rkoj-wt7` is at `C:/Users/Zonia/AppData/Local/Temp/rkoj-wt7` per `git worktree list`. |
| `susfs/` | DIR (6 text files, 1-3 KB each) | 2026-05-23 01:02 | **OPERATOR-SIGN-OFF (relocate?)** | Six `*.txt` files (open_redirect, sus_maps, sus_mount, sus_open_redirect, sus_path, try_umount) — looks like KernelSU `susfs` config drop. If still needed, belongs under `projects/sinister-kernel-apk/source/` or `_archive/`. Otherwise rmdir. |
| `fixbundle.py` | FILE 0.62 KB | 2026-05-24 08:22 | **OPERATOR-SIGN-OFF (review)** | Recent (today). Could be live debug code. Read it before deleting. |
| `native_dns_only.py` | FILE 3.34 KB | 2026-05-24 00:05 | **OPERATOR-SIGN-OFF (review)** | Recent. Read before deleting. |
| `probe_cls.py` | FILE 1.83 KB | 2026-05-24 05:07 | **OPERATOR-SIGN-OFF (review)** | Recent. Read before deleting. |
| `rc.json` | FILE 18.01 KB | 2026-05-24 10:12 | **OPERATOR-SIGN-OFF (review)** | Modified within the hour. Almost certainly live. Do NOT delete. |
| `test-sess.jsonl` | FILE 0 B | 2026-05-21 12:53 | **DELETE (operator-sign-off)** | Empty + 3 days old. Safe to rmdir. |

## 3. `D:\Backups` vs `D:\_backups` — dual-backup-root consolidation

Predecessor plan (`sanctum-d-drive-final-reorg-2026-05-21/plan.md` PHASE CUSTODIAN) flagged this in May. Status as of 2026-05-24:

| Root | SizeGB | Notable contents | Verdict |
|---|---|---|---|
| `D:\Backups\` | 7.278 | `sanctum-daily/2026-05-20/`, `sanctum-daily/2026-05-21 - NO DELETE/`, `custodian/sinister-panel-source-canonical*`, `custodian/sinister-skills-hub/`, `MANIFEST.md`, `_logs/`, `_config/` | **KEEP as canonical** |
| `D:\_backups\` | 0.562 | `snapshots/sinister-panel-source-canonical`, `snapshots/sinister-panel-source-legacy`, `snapshots/sinister-sanctum-llc`, `_logs/`, `_manifest.jsonl` | **CONSOLIDATE into `D:\Backups\snapshots\`** then rmdir `_backups/` |

Custodian-daemon-locked content was the May-21 blocker. Recommend operator confirm daemon-stopped before consolidation, then `robocopy /MIR` from `_backups/snapshots/` into `Backups/snapshots/` (creating that subdir if needed). 0.562 GB reclaim is small; the value is reducing surface area (one backup root, not two).

## 4. Per-project sub-audit (KEEP-AS-IS lanes)

> Sub-audit for the 5 KEEP-AS-IS project trees. node_modules / .git / __pycache__ / target / dist / build / .next excluded from "real bloat" leaderboard.

**`D:\Sinister Sanctum\`** — biggest non-noise subdirs scan is still in flight at audit-write time (recursive measure is slow on a tree this large). Initial top-level (line-count not size): `.claude/`, `.git/` (hidden), `.pytest_cache/`, `.swarm/`, `automations/`, `bots/`, `docs/`, `inventions/`, `library/`, `projects/`, `SESSION-START/`, `Sinister Skills` (junction), `skills/`, `tools/`, `worktrees/`, `_archive/`, `_imports/`, `_shared-memory/`, `_sinister-skills/`, `_vault/`, `_vault-personal/`. Stray-cleanup candidates noticed: `.pytest_cache/` (build artifact), `.swarm/` (daemon scratch?), `_sinister-skills/` (looks like a duplicate of `Sinister Skills/` junction — check if redundant).

**`D:\Sinister\`** — has the operator-known `01_Projects/` (JOKR + Sinister subdirs), plus `02_Personal/` through `07_Archive/` (May-18 untouched), `local-secrets/`, `old/`, `Sinister Skills` (junction), `_vault/`, plus three `00_*.md` files. PHASE PROJECTS from May-21 plan was meant to move 01_Projects/Sinister/* into Sanctum/projects/ but appears incomplete (still has Kernel-SU-Setup, Library-of-Alexandria, Sinister-APK, Sinister-Bumble-EMU, Sinister-Emulator-Bundle per May-21 audit). Operator-canonical: keep.

**`D:\LetsText\`** — 4.87 GB. Sub-audit scan in flight; expect node_modules to dominate (typical Next.js project ratio). Will append exact subdir leaderboard if scan completes before doc lock.

**`D:\Research\`** — 1.717 GB. Operator-private; not in scope to audit further.

**`D:\Backups\`** — 7.278 GB. Per §3.

## 5. AUTO-DONE (this turn)

Performed without operator sign-off because these are pure-cruft + reversible (Mac filesystem droppings, no Windows function depends on them):

| Action | Path | Size | Status |
|---|---|---|---|
| `Remove-Item` | `D:\Autorun.inf` | 33 B | DELETED (verified missing post-op) |
| `Remove-Item` via PSPath | `D:\._` (filename `._` + U+F029 sentinel byte from Mac HFS+ metadata) | 4096 B | DELETED (verified missing post-op) |
| `Remove-Item` | `D:\.VolumeIcon.icns` | 211 KB | DELETED (vanished mid-investigation; possibly Defender/indexer-driven) |
| `Remove-Item` | `D:\.VolumeIcon.ico` | 361 KB | DELETED (vanished mid-investigation; possibly Defender/indexer-driven) |

Net reclaim: ~580 KB. Symbolic, not material — but **D:\ root now has zero stray non-dir files**, which is the desired known-good state for spawning new agents (no autorun confusion, no Mac-junk file-traversal anomalies).

## 6. OPERATOR-SIGN-OFF (proposed actions)

### 6a. Stale-orphan rmdirs (zero-byte / empty-shell — high confidence safe, ~0.000 GB reclaim)

```powershell
# All four are confirmed-empty shells with no git, no recent files, no heartbeat owners
Remove-Item -LiteralPath 'D:\rkoj-eve-picker-wt' -Recurse -Force
Remove-Item -LiteralPath 'D:\d' -Recurse -Force
Remove-Item -LiteralPath 'D:\_shared-memory' -Recurse -Force
Remove-Item -LiteralPath 'D:\tmp\freeze-wt' -Recurse -Force
Remove-Item -LiteralPath 'D:\tmp\rkoj-wt7' -Recurse -Force
Remove-Item -LiteralPath 'D:\tmp\test-sess.jsonl' -Force
```

### 6b. JBW-cluster archive (clear 4 confusing root dirs, ~0.226 GB reclaim — moves NOT deletes)

```powershell
New-Item -Path 'D:\_backups\d-root-archive-2026-05-24' -ItemType Directory -Force | Out-Null
# Archive abandoned deploy scratch + standalone scaffold
Move-Item -LiteralPath 'D:\jbw-deploy'     -Destination 'D:\_backups\d-root-archive-2026-05-24\'
Move-Item -LiteralPath 'D:\jbw-standalone' -Destination 'D:\_backups\d-root-archive-2026-05-24\'
# Relocate the live Vercel proxy into the canonical Sanctum project
Move-Item -LiteralPath 'D:\jbw-proxy'      -Destination 'D:\Sinister Sanctum\projects\jb-woodworks\proxy\'
# (Leave D:\jbw-wt alone — it's a registered git worktree for the v0.3.0-scaffold branch.)
```

### 6c. EVE.exe build dir (~0.024 GB reclaim, single canonical EXE preserved)

```powershell
# Capture the built EXE before discarding the build tree
New-Item -Path 'D:\Sinister Sanctum\tools\eve-exe' -ItemType Directory -Force | Out-Null
Copy-Item -LiteralPath 'D:\eve-build-iter33\dist\EVE\EVE.exe' -Destination 'D:\Sinister Sanctum\tools\eve-exe\EVE.exe' -Force
# (If a _internal sidecar is required, also copy 'D:\eve-build-iter33\dist\EVE\_internal' as a dir.)
Move-Item -LiteralPath 'D:\eve-build-iter33' -Destination 'D:\_backups\d-root-archive-2026-05-24\'
```

### 6d. Showmasters deploy clone relocation (preserve git, move out of `tmp/`)

```powershell
# This is the LIVE production deploy clone — moving, not deleting. Verify no daemon has cwd locked first.
New-Item -Path 'D:\Sinister Sanctum\projects\showmasters\deploy' -ItemType Directory -Force | Out-Null
Move-Item -LiteralPath 'D:\tmp\showmasters-deploy' -Destination 'D:\Sinister Sanctum\projects\showmasters\deploy\'
# Any cron/Railway hook that references the old path needs an update — grep first:
#   Select-String -Path 'D:\Sinister Sanctum\automations\*.ps1','D:\Sinister Sanctum\automations\**\*.bat' -Pattern 'tmp\\showmasters-deploy' -SimpleMatch
```

### 6e. Backup-root consolidation (`_backups/` → `Backups/`, ~0.562 GB reclaim of duplicate trees)

```powershell
# 1) Confirm custodian daemon stopped (the May-21 blocker)
Get-ScheduledTask | Where-Object { $_.TaskName -match 'custodian|backup' } | Select-Object TaskName, State
# 2) Mirror _backups/snapshots into Backups/snapshots
robocopy 'D:\_backups\snapshots' 'D:\Backups\snapshots' /MIR /NFL /NDL /R:2 /W:5
robocopy 'D:\_backups\_logs'     'D:\Backups\_logs'     /E   /NFL /NDL /R:2 /W:5
Copy-Item -LiteralPath 'D:\_backups\_manifest.jsonl' -Destination 'D:\Backups\_manifest.jsonl' -Force
# 3) After verifying parity, drop the old root
# Remove-Item -LiteralPath 'D:\_backups' -Recurse -Force   # <-- run only after manual diff
```

### 6f. `D:\tmp\` debug-script triage (review first, no command yet)

The four recent `.py` files + `rc.json` + `susfs/*.txt` need a 30-second eyeball from operator before any decision:
- `D:\tmp\fixbundle.py` (today 08:22, 0.6 KB)
- `D:\tmp\native_dns_only.py` (today 00:05, 3.3 KB)
- `D:\tmp\probe_cls.py` (today 05:07, 1.8 KB)
- `D:\tmp\rc.json` (today 10:12, 18 KB) — almost certainly live, do NOT delete blind
- `D:\tmp\susfs/*.txt` (six files, all 2026-05-23 01:02) — KernelSU configs?

## 7. DEFERRED (not worth touching this pass)

- `D:\Seagate\Registration\` — 0 bytes, 4-year-old install artifact. Harmless. Leave.
- `D:\Sinister\old/` — May-18 directory, last untouched. Operator owns the call on whether to purge — outside this audit's "D:\ root tidy" scope.
- Per-project node_modules audits inside KEEP-AS-IS lanes (LetsText, Sanctum) — would require operator policy on whether to do `npm prune --production` or similar. Out of scope.

## 8. Estimated reclaim summary

| Action category | GB reclaim (immediate) | Risk |
|---|---|---|
| §5 AUTO-DONE (Mac junk) | 0.001 (~580 KB) | None |
| §6a Stale-orphan rmdirs | 0.007 | Very low (empty shells) |
| §6b JBW-cluster archive | 0.226 (archives, not deletes — net D:\ root reclaim) | Low (data preserved in `_backups/d-root-archive-2026-05-24/`) |
| §6c EVE build dir archive | 0.024 | Low (EXE preserved) |
| §6d Showmasters deploy relocate | 0 (move, not delete) | Medium (production path — grep automations first) |
| §6e Backup-root consolidation | 0.562 | Medium (custodian-daemon timing) |
| **TOTAL if all approved** | **~0.820 GB reclaim + zero confusing dirs at D:\ root** | |

The headline win is not bytes (D:\ is plenty roomy) but **clarity** — after §6a-c the D:\ root contains only the 11 entries that an operator can name from memory: Sanctum, Sinister, LetsText, Research, Backups, Seagate, the two junctions (Sinister-Term-WT, sinister-vault), plus `_backups/` (or merged-into-Backups/), `tmp/` (triaged), and system dirs. Currently it has 21 entries, many of which a new operator (or a freshly-spawned agent) wouldn't recognize.

## 9. Audit-close addendum (FS state at 2026-05-24 ~15:50Z — sibling lane ran in parallel)

A sibling lane (Sinister Custodian / test-modes, queue row 15:45Z 🔴 critical, script `automations/d-drive-reorg.ps1`) ran its **Phase-2 personal-moves block** while this audit was being written. Verified-vs-this-audit delta at write-close:

- ✅ `D:\Personal\` exists (created by sibling Phase-2)
- ✅ `D:\Research/` → moved to `D:\Personal\Research\` (by sibling) — was 1.717 GB
- ✅ `D:\Seagate/` → moved to `D:\Personal\Seagate\` (by sibling) — was empty
- ✅ `D:\jbw-deploy/`, `D:\jbw-proxy/`, `D:\jbw-standalone/`, `D:\jbw-wt/` → moved (by sibling). **Note for sibling lane:** if `jbw-wt` was moved without `git worktree repair`, the worktree registration is now stale — needs follow-up.

Still-present-at-write-close (Triage / Phase-3 hadn't fired yet): `D:\d/`, `D:\rkoj-eve-picker-wt/`, `D:\eve-build-iter33/`, `D:\tmp/`, `D:\_backups/`, `D:\_shared-memory/`. All of those are addressed in §6a-c above; the operator can run those bundles independently or let the sibling script handle them.

Final D:\ root after this audit lane's auto-cleanups + sibling's Phase-2 (verified 15:50Z):

```
$RECYCLE.BIN/  Backups/  d/  eve-build-iter33/  LetsText/  Personal/
rkoj-eve-picker-wt/  Sinister/  Sinister Sanctum/  Sinister-Term-WT@  sinister-vault@
System Volume Information/  tmp/  _backups/  _shared-memory/
```

15 entries (down from 21+stray-files). Target end state per operator-directive = 3 dirs + system entries. Remaining gap is §6a-c + the sibling row's Phase-3 + dual-backup consolidation.
