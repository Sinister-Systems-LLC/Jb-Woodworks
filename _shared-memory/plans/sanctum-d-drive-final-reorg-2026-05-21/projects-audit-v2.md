> **Author:** RKOJ-ELENO :: 2026-05-21
> **Audit:** Full pass over `D:\Sinister\01_Projects\Sinister\` (v1 covered only 5 of 14 subdirs)
> **Mode:** Read-only — NO file moves, NO edits performed during audit

# D-Drive Final Reorg — `01_Projects/Sinister/` v2 (all 14 subdirs + root doctrine)

## Header

- **Date:** 2026-05-21
- **Parent surveyed:** `D:\Sinister\01_Projects\Sinister\`
- **Total entries:** 14 subdirs + 2 root markdown files = 16 entries (table has 15 rows: 14 subdirs + 1 root-doctrine aggregate row)
- **Goal:** Before the operator renames `D:\Sinister\` → `D:\Personal\`, identify every entry that is a junction (keep / unbind), a duplicate of a Sanctum slot (verify and archive src), or unique content (migrate into Sanctum).
- **NTFS junction tooling used:** `Get-Item -Force | Attributes -band ReparsePoint`. `.Target` resolves the backing path.

## Critical correction vs. operator's brief

The operator brief stated `Sinister-APK\` and `Sinister-Emulator-Bundle\` are themselves junctions (`KNOWN LIVE-BACKING junction to projects/sinister-kernel-apk/source`). **That is the opposite of reality.**

- `D:\Sinister\01_Projects\Sinister\Sinister-APK\` is a **real directory** containing 3.72 GB / 14334 files. It also holds a nested `source@` junction back to itself in some places, but the dir itself is real.
- `D:\Sinister Sanctum\projects\sinister-kernel-apk\source` is the **junction**, with `Target = D:\Sinister\01_Projects\Sinister\Sinister-APK`.

Same pattern for Sinister-Emulator-Bundle, Sinister-Panel, Sinister-Snap-EMU, Sinister-TikTok-EMU. **The D:\Sinister\ side is the source-of-truth backing the Sanctum junctions.** Renaming the parent breaks all five Sanctum projects until the junctions are rewritten or the data is moved into Sanctum.

The seven remaining subdirs (RKA, Sandbox, TG, iMessage-Bridge, Snap-Signer, Workstation-Setup, sinister-helper) each contain only `_README.md`, `_vault/_index.md`, and a `source@` junction pointing OUT to `C:\Users\Zonia\Desktop\<name>\`. They are **POINTERS** to operator's Desktop — content lives elsewhere.

## Per-entry verdict table

Junction column key: `IN→D:\Sinister\…` means a Sanctum junction targets this dir (live-backing); `OUT→Desktop` means this dir contains a `source@` junction pointing out to Desktop (pointer shell); `—` means real content / no junction relationship.

| # | Entry | Type | Size MB | Files | Junction relationship | Sanctum equiv | Verdict | Recommended action |
|---|---|---|---:|---:|---|---|---|---|
| 1 | `Sinister-APK/` | real dir | 3718.89 | 14334 | IN← `Sanctum/projects/sinister-kernel-apk/source` | `projects/sinister-kernel-apk/` | LIVE-BACKING | Drop Sanctum junction, robocopy /MOVE into `projects/sinister-kernel-apk/source/`, then optionally re-create junction. |
| 2 | `Sinister-Emulator-Bundle/` | real dir (+ inner real `source/`) | 362.79 | 46 | IN← `Sanctum/projects/sinister-emulator-bundle/source` (target = inner `source/`) | `projects/sinister-emulator-bundle/` | LIVE-BACKING | Drop Sanctum junction, robocopy /MOVE the inner `source/` into Sanctum, then archive the now-empty shell parent + `migration-2026-05-19.log`. |
| 3 | `Sinister-Panel/` | real dir (+ inner real `source/`) | 1161.57 | 26919 | IN← `Sanctum/projects/sinister-panel/source` (target = inner `source/`) | `projects/sinister-panel/` | LIVE-BACKING | Same pattern as Bundle. Note: this dir also holds 8 top-level `.bat` operator scripts + a `scripts/` + `_handoffs/` dir not currently surfaced inside Sanctum — sweep those into `projects/sinister-panel/automations/` or similar before deleting the shell. |
| 4 | `Sinister-RKA/` | pointer shell | 0 | 2 | OUT→ `C:\Users\Zonia\Desktop\Sinister RKA GOOD\` (12.4 MB / 135 files) | none in Sanctum (no `projects/sinister-rka/`) | POINTER + ORPHAN-PRODUCT | Archive the shell; operator decides whether to introduce a `projects/sinister-rka/` slot in Sanctum (RKA daemon is a tracked product per `_status.md`). If yes — create slot, junction `source` → Desktop. If no — leave Desktop alone, just archive the shell. **OPERATOR-GATED.** |
| 5 | `Sinister-Sandbox/` | pointer shell | 0 | 2 | OUT→ `C:\Users\Zonia\Desktop\Sinister Sandbox\` (0.14 MB / 38 files) | none | POINTER | Archive shell; Desktop content stays where it is. Scratch space per `_README.md` — no need for a Sanctum slot. |
| 6 | `Sinister-Snap-EMU/` | real dir (+ inner real `source/`) | 1137.52 | 6850 | IN← `Sanctum/projects/sinister-snap-emu/source` (target = inner `source/`) | `projects/sinister-snap-emu/` | LIVE-BACKING | Same pattern as Bundle. Has 4 `migrate_paths*` log files + `migrate_paths.py` worth preserving in `_shared-memory/archive/`. |
| 7 | `Sinister-TG/` | pointer shell | 0 | 2 | OUT→ `C:\Users\Zonia\Desktop\Sinister TG\` (399.43 MB / 1069 files) | none | POINTER + ORPHAN-PRODUCT | Archive shell. Desktop has substantial content (399 MB) — operator decides whether `projects/sinister-tg/` deserves a Sanctum slot or stays Desktop-only. Not related to `sinister-crawler` (no such bot found). **OPERATOR-GATED.** |
| 8 | `Sinister-TikTok-EMU/` | real dir (+ inner real `source/`) | 4867.83 | 10107 | IN← `Sanctum/projects/sinister-tiktok-emu/source` (target = inner `source/`) | `projects/sinister-tiktok-emu/` | LIVE-BACKING | Same pattern as Bundle. Largest item in the audit; move time est. ~10–20 min. |
| 9 | `Sinister-Workstation-Setup/` | pointer shell | 0 | 2 | OUT→ `C:\Users\Zonia\Desktop\Sinister-Workstation-Setup\` (0.02 MB / 5 files) | partial overlap with `automations/window-manager/` but NOT same content (window-manager is the Sanctum-native RKOJ workbench Python source) | POINTER | Archive shell. Desktop content is 5 files — appears stale. NOT a duplicate of `automations/window-manager/`. |
| 10 | `Sinister-iMessage-Bridge/` | pointer shell | 0 | 2 | OUT→ `C:\Users\Zonia\Desktop\Sinister iMessage Bridge\` (0.78 MB / 298 files) | none | POINTER | Archive shell. Desktop stays. No Sanctum slot exists or appears needed. |
| 11 | `Snap-Signer/` | pointer shell | 0 | 2 | OUT→ `C:\Users\Zonia\Desktop\Snap Signer\` (29944.96 MB / 451282 files) | none (mcp.json references the Desktop path directly) | POINTER | Archive shell. The Desktop is the canonical 30 GB Snap Signer working dir; mcp.json already points there. NO Sanctum action needed. |
| 12 | `sinister-helper/` | pointer shell | 0 | 2 | OUT→ `C:\Users\Zonia\Desktop\sinister helper\` (180.07 MB / 788 files) | none | POINTER | Archive shell. Desktop stays. |
| 13 | `_vault/` | dir | 0 | 1 (`_index.md` only) | — | none (Obsidian-only) | POINTER | Archive single `_index.md` to `_shared-memory/archive/`. |
| 14 | `_README.md` + `_status.md` | doctrine (root files) | <1KB each | 2 | — | none (group-level doctrine — already superseded by Sanctum) | DOCTRINE-PRESERVE | Copy both to `_shared-memory/archive/d-sinister-01_Projects-pointers-2026-05-21/Sinister/` for posterity, then remove. They list 15 projects total but only 14 directories exist (Bumble-EMU + Kernel-SU-Setup + Library-of-Alexandria are referenced but live one level up). |

(Row 14 collapses both root markdown files; total accounting = 14 subdirs + 2 root files = 16 entries, 15 verdict rows as per brief.)

## Verdict breakdown

| Verdict | Count | Subdirs |
|---|---:|---|
| LIVE-BACKING (Sanctum junction depends on this) | 5 | Sinister-APK, Sinister-Emulator-Bundle, Sinister-Panel, Sinister-Snap-EMU, Sinister-TikTok-EMU |
| POINTER (shell with source@ → Desktop; no real payload) | 7 | Sinister-RKA, Sinister-Sandbox, Sinister-TG, Sinister-Workstation-Setup, Sinister-iMessage-Bridge, Snap-Signer, sinister-helper |
| POINTER-VAULT | 1 | `_vault/` |
| DOCTRINE-PRESERVE | 1 (= 2 files) | `_README.md`, `_status.md` |
| OPERATOR-GATED (within POINTER set above) | 2 | Sinister-RKA, Sinister-TG (both have substantial Desktop payloads + are listed as tracked products in `_status.md`) |
| DUPE (byte-identical to Sanctum) | 0 | — |
| NEW (unique content, no Sanctum equiv, must migrate) | 0 | — (every LIVE-BACKING already has a Sanctum slot via junction; every POINTER has its source-of-truth on Desktop) |

**Headline finding:** there is no NEW content to migrate. There are 5 LIVE-BACKING moves (junction-aware), 8 POINTER archives (cheap), and 2 operator-gated decisions about whether RKA + TG deserve their own Sanctum project slots.

## Exact-command script (safe operations only)

All commands run from elevated PowerShell. Stop any agent that may have open handles on the LIVE-BACKING dirs before Step 1 (see Step 0).

```powershell
# Step 0 — pre-flight: no agent owns open handles on LIVE-BACKING dirs
Get-Process | Where-Object {
  $_.Path -like "*Sinister-APK*" -or
  $_.Path -like "*Sinister-Emulator-Bundle*" -or
  $_.Path -like "*Sinister-Panel*" -or
  $_.Path -like "*Sinister-Snap-EMU*" -or
  $_.Path -like "*Sinister-TikTok-EMU*"
} | Format-Table Id, ProcessName, Path

# Step 1 — LIVE-BACKING moves (5 dirs). Drop the junction with -Force (NO -Recurse), then robocopy /MOVE.
# NOTE: removing a junction with -Recurse will traverse it and delete the backing data — do NOT use -Recurse on junctions.

# 1a — Sinister-APK (3.72 GB; target = the dir ITSELF, not an inner source/)
Remove-Item "D:\Sinister Sanctum\projects\sinister-kernel-apk\source" -Force
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-APK" "D:\Sinister Sanctum\projects\sinister-kernel-apk\source" /move /e /r:1 /w:1 /np

# 1b — Sinister-Emulator-Bundle (363 MB; target = inner source/, parent shell becomes empty)
Remove-Item "D:\Sinister Sanctum\projects\sinister-emulator-bundle\source" -Force
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\source" "D:\Sinister Sanctum\projects\sinister-emulator-bundle\source" /move /e /r:1 /w:1 /np

# 1c — Sinister-Panel (1.16 GB; target = inner source/). Also sweep top-level .bat scripts + scripts/ + _handoffs/.
Remove-Item "D:\Sinister Sanctum\projects\sinister-panel\source" -Force
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Panel\source" "D:\Sinister Sanctum\projects\sinister-panel\source" /move /e /r:1 /w:1 /np
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Panel" "D:\Sinister Sanctum\projects\sinister-panel\automations" /move /e /r:1 /w:1 /np /xd source

# 1d — Sinister-Snap-EMU (1.14 GB; target = inner source/). Preserve migrate logs.
Remove-Item "D:\Sinister Sanctum\projects\sinister-snap-emu\source" -Force
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source" "D:\Sinister Sanctum\projects\sinister-snap-emu\source" /move /e /r:1 /w:1 /np
$arch = "D:\Sinister Sanctum\_shared-memory\archive\d-sinister-01_Projects-pointers-2026-05-21\Sinister\Sinister-Snap-EMU"
New-Item -ItemType Directory -Path $arch -Force | Out-Null
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU" $arch /move /e /r:1 /w:1 /np /xd source

# 1e — Sinister-TikTok-EMU (4.87 GB; target = inner source/). LARGEST move ~10–20 min.
Remove-Item "D:\Sinister Sanctum\projects\sinister-tiktok-emu\source" -Force
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU\source" "D:\Sinister Sanctum\projects\sinister-tiktok-emu\source" /move /e /r:1 /w:1 /np
$arch = "D:\Sinister Sanctum\_shared-memory\archive\d-sinister-01_Projects-pointers-2026-05-21\Sinister\Sinister-TikTok-EMU"
New-Item -ItemType Directory -Path $arch -Force | Out-Null
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU" $arch /move /e /r:1 /w:1 /np /xd source

# Step 2 — POINTER shells (5 unambiguous; RKA + TG are gated below)
$archive = "D:\Sinister Sanctum\_shared-memory\archive\d-sinister-01_Projects-pointers-2026-05-21\Sinister"
New-Item -ItemType Directory -Path $archive -Force | Out-Null

# Each shell holds a source@ junction OUT to Desktop. Remove the junction with -Force (no -Recurse), then move the shell.
foreach ($d in @("Sinister-Sandbox","Sinister-Workstation-Setup","Sinister-iMessage-Bridge","Snap-Signer","sinister-helper")) {
  $j = "D:\Sinister\01_Projects\Sinister\$d\source"
  if (Test-Path -LiteralPath $j) { Remove-Item -LiteralPath $j -Force }
  robocopy "D:\Sinister\01_Projects\Sinister\$d" "$archive\$d" /move /e /r:1 /w:1 /np
}

# Step 3 — POINTER-VAULT + doctrine root files
robocopy "D:\Sinister\01_Projects\Sinister\_vault" "$archive\_vault" /move /e /r:1 /w:1 /np
Move-Item "D:\Sinister\01_Projects\Sinister\_README.md" "$archive\_README.md"
Move-Item "D:\Sinister\01_Projects\Sinister\_status.md" "$archive\_status.md"

# Step 4 — verify the parent is empty (only RKA + TG should remain if operator deferred those)
Get-ChildItem "D:\Sinister\01_Projects\Sinister\" -Force | Format-Table FullName

# Step 5 — only after operator clears Step 4, remove the empty parent
# Remove-Item "D:\Sinister\01_Projects\Sinister\" -Recurse -Force
```

## Operator-gated items (do NOT execute without explicit approval)

1. **Sinister-RKA** — `_status.md` lists this as an active tracked product (RKA daemon, Yurikey51 cert deadline 2026-05-24). Desktop source is 12.4 MB / 135 files at `C:\Users\Zonia\Desktop\Sinister RKA GOOD\`. **Decision:** create `D:\Sinister Sanctum\projects\sinister-rka\` slot and re-junction `source/` → Desktop? Or leave Desktop-only and just archive the D:/Sinister shell? Operator must pick before Step 5.

2. **Sinister-TG** — Desktop source is **399 MB / 1069 files** at `C:\Users\Zonia\Desktop\Sinister TG\`. Substantial payload; `_status.md` lists status as `⚪ unknown / not recently touched`. **Decision:** same fork as RKA — promote to Sanctum slot or archive the shell?

3. **Sinister-Panel orphan content** (covered in Step 1c above but worth surfacing). The Panel dir has 8 top-level `.bat` operator scripts + a `scripts/` dir + a `_handoffs/` dir that are NOT inside `source/` and therefore NOT currently visible through the Sanctum junction. Decision: include them inside `projects/sinister-panel/automations/` (Step 1c does this), or leave them out and archive separately?

4. **JOKR-Global DIVERGED** — carried over from v1 audit. Not in `01_Projects/Sinister/` scope (lives at `01_Projects/JOKR/`) so excluded here, but still pending operator's authoritative-side pick.

## Cross-references

- v1 audit (5-of-14 partial): `D:\Sinister Sanctum\_shared-memory\plans\sanctum-d-drive-final-reorg-2026-05-21\projects-audit.md`
- Plan file: `D:\Sinister Sanctum\_shared-memory\plans\sanctum-d-drive-final-reorg-2026-05-21\plan.md`
- Sanctum projects index: `D:\Sinister Sanctum\projects\` (17 Sanctum slots; 5 currently junction-backed by `01_Projects/Sinister/`)
- Junction safety doctrine: `Remove-Item <junction> -Force` (NO `-Recurse`). `-Recurse` traverses the junction and deletes the backing data. `robocopy /MOVE` is safe because it operates on the resolved target.
- After all LIVE-BACKING moves complete, each Sanctum project's `source/` is a real directory (no junction). The Sanctum `projects/<slug>/source/` paths still resolve, paths in `.bat` / `.ps1` / `.py` files are unchanged, builds unaffected.
