> **Author:** RKOJ-ELENO :: 2026-05-21
> **Audit:** Residual content under `D:\Sinister\01_Projects\` after Phase-3 migration (commit `55f7c7f`)
> **Mode:** Read-only — NO file moves, NO edits performed during audit

# D-Drive Final Reorg — `01_Projects/` Residual Audit

## Header

- **Date:** 2026-05-21
- **Total src dirs surveyed:** 12 (10 dirs + 3 RKOJ pointer files + 2 Inventions pointer files counted as 2 pointer groups)
- **Goal:** Determine which residual src dirs need MOVE / SKIP-then-RM / ARCHIVE before the operator's `D:\Sinister\` → `D:\Personal\` rename.

## Critical finding — junction-backed live source

Three Sanctum destination dirs use **NTFS junctions** that point back into `D:\Sinister\01_Projects\`. Moving or renaming the src side will break the live Sanctum project workspaces:

| Sanctum dst junction | Target (live backing) |
|---|---|
| `D:\Sinister Sanctum\projects\sinister-kernel-apk\source` | `D:\Sinister\01_Projects\Sinister\Sinister-APK` (3.6 GB, 14310 files) |
| `D:\Sinister Sanctum\projects\sinister-emulator-bundle\source` | `D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\source` (363 MB) |
| `D:\Sinister Sanctum\projects\sinister-bumble-emu\source` | `C:\Users\Zonia\Desktop\Sinister Bumble EMU.API\` (NOT under D:/Sinister — unaffected) |

**Recommendation:** For `Sinister-APK` + `Sinister-Emulator-Bundle`, the cleanest path is `robocopy /move` the backing dirs INTO their Sanctum project as real subdirs, then recreate the junctions inside Sanctum pointing at the new in-Sanctum locations. (Or simpler: `robocopy /move` and drop the junction entirely so `source/` is just a regular subdir.) Either way, do NOT `rm` the D:/Sinister side before the move — that destroys the working tree.

Additionally:
- `D:\Sinister Sanctum\projects\sinister-jokr\JOKR-Global\source\` (2077 files, 8.4 MB) is a **divergent partial copy** of `D:\Sinister\01_Projects\JOKR\JOKR-Global\source\` (19097 files, 470 MB). Sanctum-side is source-only (no `node_modules/`); D-Sinister side has full `node_modules/` build artifacts. Treat as DIVERGED.

## Verdict table

| Src path | Size MB | Files | Dest (if any) | Verdict | Recommended action |
|---|---:|---:|---|---|---|
| `JOKR/JOKR-Global/` | 470.02 | 19098 | `projects/sinister-jokr/JOKR-Global/` (12 MB, 2082 files) | DIVERGED | MOVE (overwrite Sanctum side) |
| `JOKR/Library-of-JOKR/` | 0 | 2 | none (source symlink → `C:\Users\Zonia\Desktop\Library-of-JOKR\`) | POINTER | ARCHIVE |
| `JOKR/Logo-Options/` | 0.02 | 11 | none | NEW | MOVE |
| `JOKR/_vault/` | 0 | 1 | none (Obsidian stub) | POINTER | ARCHIVE |
| `Sinister/Kernel-SU-Setup/` | 0 | 2 | none (source symlink → `C:\Users\Zonia\Desktop\Kernel-SU-Setup`) | POINTER | ARCHIVE |
| `Sinister/Library-of-Alexandria/` | 0 | 2 | none (source symlink → `C:\Users\Zonia\Desktop\Sinister Library Of Alexandria\`) | POINTER | ARCHIVE |
| `Sinister/Sinister-APK/` | 3718.86 | 14310 | `projects/sinister-kernel-apk/source` (Junction → here) | LIVE-BACKING | MOVE (then re-junction or drop junction) |
| `Sinister/Sinister-Bumble-EMU/` | 0 | 2 | `projects/sinister-bumble-emu/` (own dir, junction NOT to this src) | POINTER | ARCHIVE |
| `Sinister/Sinister-Emulator-Bundle/` | 362.79 | 46 | `projects/sinister-emulator-bundle/source` (Junction → `…/source/` subdir) | LIVE-BACKING | MOVE (then re-junction or drop junction) |
| `RKOJ/Sinister-Drone/` | 0.01 | 2 | none (CLAUDE.md + SESSION-START.md only) | POINTER | ARCHIVE |
| `RKOJ/Sinister-Mobile/` | 0.01 | 2 | none (CLAUDE.md + SESSION-START.md only) | POINTER | ARCHIVE |
| `RKOJ/CLAUDE.md` | — | 1 | none (operator doctrine pointer) | POINTER | ARCHIVE |
| `RKOJ/SESSION-START.md` | — | 1 | none | POINTER | ARCHIVE |
| `RKOJ/_README.md` | — | 1 | none | POINTER | ARCHIVE |
| `Inventions/CLAUDE.md` | — | 1 | none (cross-invention hub doctrine) | POINTER | ARCHIVE |
| `Inventions/SESSION-START.md` | — | 1 | none | POINTER | ARCHIVE |
| `_vault/_index.md` | — | 1 | none (Obsidian top-level stub) | POINTER | ARCHIVE |

**Verdict legend.** NEW = no Sanctum dest, must move to preserve content. DIVERGED = Sanctum has a partial / different copy — operator decides authoritative version. DUPE = byte-identical to Sanctum (none found in this audit). POINTER = doctrine/pointer file only, content lives elsewhere (operator vault on C: desktop, or already canonicalized in Sanctum). LIVE-BACKING = Sanctum junction depends on src — move-then-rejunction required, never `rm` first.

## Summary

| Verdict | Count | Action |
|---|---:|---|
| LIVE-BACKING | 2 | MOVE backing + rewrite junction (Sinister-APK, Sinister-Emulator-Bundle) |
| DIVERGED | 1 | MOVE-OVERWRITE (JOKR-Global — operator picks authoritative side) |
| NEW | 1 | MOVE (Logo-Options) |
| POINTER | 13 | ARCHIVE (doctrine files; no payload) |
| **Total** | **17** | — |

## Exact commands to execute (operator-gated)

All commands assume the operator has confirmed authoritative direction (specifically the JOKR-Global DIVERGED overwrite). Run from an elevated PowerShell.

### Step 0 — pre-flight: stop all agents that could be writing into the live junctions

```powershell
# verify no Sanctum agent has open handles on Sinister-APK or Sinister-Emulator-Bundle
Get-Process | Where-Object { $_.Path -like "*Sinister-APK*" -or $_.Path -like "*Sinister-Emulator-Bundle*" } | Format-Table
```

### Step 1 — LIVE-BACKING moves (junction-aware)

Drop the junctions FIRST, then `robocopy /move`, then either re-create the junction inside Sanctum or leave `source/` as a real dir.

```powershell
# Sinister-APK (3.7 GB)
Remove-Item "D:\Sinister Sanctum\projects\sinister-kernel-apk\source" -Force   # removes junction only
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-APK" "D:\Sinister Sanctum\projects\sinister-kernel-apk\source" /move /e /r:1 /w:1 /np

# Sinister-Emulator-Bundle (363 MB)
Remove-Item "D:\Sinister Sanctum\projects\sinister-emulator-bundle\source" -Force
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\source" "D:\Sinister Sanctum\projects\sinister-emulator-bundle\source" /move /e /r:1 /w:1 /np
# parent shell dir at D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\ is then a POINTER — archive separately
```

### Step 2 — DIVERGED move (operator decides)

If Sanctum-side is authoritative (committed source), keep Sanctum and drop D-Sinister:

```powershell
# OPERATOR CONFIRM FIRST — destroys the 470 MB build tree (node_modules can be rebuilt with npm i)
Remove-Item "D:\Sinister\01_Projects\JOKR\JOKR-Global" -Recurse -Force
```

If D-Sinister is authoritative (live working tree with node_modules), overwrite Sanctum:

```powershell
Remove-Item "D:\Sinister Sanctum\projects\sinister-jokr\JOKR-Global" -Recurse -Force
robocopy "D:\Sinister\01_Projects\JOKR\JOKR-Global" "D:\Sinister Sanctum\projects\sinister-jokr\JOKR-Global" /move /e /r:1 /w:1 /np
```

### Step 3 — NEW move (Logo-Options)

```powershell
# 11 SVG logo files + README — drop into sinister-jokr (parent JOKR project)
robocopy "D:\Sinister\01_Projects\JOKR\Logo-Options" "D:\Sinister Sanctum\projects\sinister-jokr\Logo-Options" /move /e /r:1 /w:1 /np
```

### Step 4 — POINTER archives (13 entries)

Collect all pointer files / shell dirs into a single archive directory under `_shared-memory/archive/` for posterity, then remove the originals.

```powershell
$archive = "D:\Sinister Sanctum\_shared-memory\archive\d-sinister-01_Projects-pointers-2026-05-21"
New-Item -ItemType Directory -Path $archive -Force | Out-Null

# JOKR-side pointer / symlink-shell dirs
robocopy "D:\Sinister\01_Projects\JOKR\Library-of-JOKR" "$archive\JOKR\Library-of-JOKR" /move /e /r:1 /w:1 /np
robocopy "D:\Sinister\01_Projects\JOKR\_vault"          "$archive\JOKR\_vault"          /move /e /r:1 /w:1 /np

# Sinister-side pointer / symlink-shell dirs
robocopy "D:\Sinister\01_Projects\Sinister\Kernel-SU-Setup"      "$archive\Sinister\Kernel-SU-Setup"      /move /e /r:1 /w:1 /np
robocopy "D:\Sinister\01_Projects\Sinister\Library-of-Alexandria" "$archive\Sinister\Library-of-Alexandria" /move /e /r:1 /w:1 /np
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Bumble-EMU"   "$archive\Sinister\Sinister-Bumble-EMU"   /move /e /r:1 /w:1 /np

# RKOJ-side pointer files + empty-shell subproject dirs
robocopy "D:\Sinister\01_Projects\RKOJ\Sinister-Drone"  "$archive\RKOJ\Sinister-Drone"  /move /e /r:1 /w:1 /np
robocopy "D:\Sinister\01_Projects\RKOJ\Sinister-Mobile" "$archive\RKOJ\Sinister-Mobile" /move /e /r:1 /w:1 /np
Move-Item "D:\Sinister\01_Projects\RKOJ\CLAUDE.md"         "$archive\RKOJ\CLAUDE.md"
Move-Item "D:\Sinister\01_Projects\RKOJ\SESSION-START.md"  "$archive\RKOJ\SESSION-START.md"
Move-Item "D:\Sinister\01_Projects\RKOJ\_README.md"        "$archive\RKOJ\_README.md"
robocopy "D:\Sinister\01_Projects\RKOJ\_vault"             "$archive\RKOJ\_vault"             /move /e /r:1 /w:1 /np

# Inventions-side pointer files
Move-Item "D:\Sinister\01_Projects\Inventions\CLAUDE.md"        "$archive\Inventions\CLAUDE.md"
Move-Item "D:\Sinister\01_Projects\Inventions\SESSION-START.md" "$archive\Inventions\SESSION-START.md"

# Top-level vault stub
robocopy "D:\Sinister\01_Projects\_vault" "$archive\_vault" /move /e /r:1 /w:1 /np
```

### Step 5 — verify + remove the now-empty `01_Projects/` parent

```powershell
Get-ChildItem "D:\Sinister\01_Projects\" -Recurse -Force | Format-Table FullName, Length
# expected: only empty parent dirs (JOKR\, Sinister\, RKOJ\, Inventions\) — verify before remove
Remove-Item "D:\Sinister\01_Projects\" -Recurse -Force
```

After Step 5, `D:\Sinister\` should be empty of Sinister-project content and is safe to rename `D:\Personal\` (queued as operator task #15).

## Cross-references

- Phase-3 baseline (5 projects already migrated): commit `55f7c7f` — cell-network, dashboard-skeleton, eve, jokr (sinister-jokr without JOKR-Global subdir), letstext
- Related plan file: `D:\Sinister Sanctum\_shared-memory\plans\sanctum-d-drive-final-reorg-2026-05-21\plan.md`
- Junction-handling background: junctions on Windows survive normal `Remove-Item` IF you target the junction itself (not `-Recurse` through it). Always remove the junction with `Remove-Item <junction-path> -Force` (no `-Recurse`) BEFORE moving the backing dir, or `robocopy /move` will traverse the junction and move the live data twice.
- POINTER files' content is preserved in `_shared-memory/archive/d-sinister-01_Projects-pointers-2026-05-21/` for any future reference. Operator's authoritative `_vault/*.md` notes referenced by `RKOJ/CLAUDE.md` live at `D:\Sinister\01_Projects\RKOJ\_vault\*.md` — those ARE the goldmine and are included in the archive set.

## Notes for operator decision

1. **JOKR-Global DIVERGED direction.** Sanctum-side `sinister-jokr/JOKR-Global/source/` (2077 files, 8.4 MB) is source-only, matches a fresh git checkout. D-Sinister side (19097 files, 470 MB) is the running build with `node_modules/` installed. **Recommendation:** keep Sanctum (source-of-truth), `rm -rf` D-Sinister, rebuild node_modules in-place inside Sanctum with `npm i`. This converges everything under Sanctum and lets `npm i` be the rebuild step.

2. **Sinister-APK move risk.** This is the largest item by far (3.7 GB, 14310 files). The move will take 5-15 minutes on a local-disk robocopy. Operator should NOT have any kernel-apk agent running during the move (`agent/sinister-kernel-apk/*` branches in `worktrees/`).

3. **Operator's `_vault/*.md` goldmine.** `RKOJ/_vault/Car.md`, `Drone.md`, `EVE.md`, etc. are referenced as "the goldmine — read these first" by the RKOJ doctrine. The archive in Step 4 preserves them, but the operator may prefer to copy these into `_shared-memory/knowledge/operator-vault/` instead of archiving them under the generic pointers archive — they're high-signal research notes, not just doctrine.
