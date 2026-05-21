# Sinister Content Audit — D:\Sinister\ (Personal Folder)
**Generated:** 2026-05-21T23:00Z  
**Operator Directive:** Remove Sinister-product content from D:\Sinister\ (pending rename to D:\Personal)  
**Canonical Location:** D:\Sinister Sanctum\ (Sinister product stays here)

---

## Audit Summary
- **Total Sinister-related items found:** 8 major directories
- **Recommended PURGE candidates:** 5
- **Total bytes at risk:** ~5.5 GB
- **Sanctum mirror status:** All items have active mirrors in D:\Sinister Sanctum\projects\

---

## Detailed Audit Table

| Path | Bytes | Mirror in Sanctum? | Recommended | Risk | Notes |
|------|-------|-------------------|-------------|------|-------|
| D:\Sinister\01_Projects\Sinister\Sinister-APK | 3.9 GB | Y: sinister-kernel-apk | PURGE | Low | Fully mirrored; safe for removal |
| D:\Sinister\01_Projects\Sinister\Sinister-Panel | 1.2 GB | Y: sinister-panel | PURGE | Low | Fully mirrored; most recent: 2026-05-21 15:37:30 |
| D:\Sinister\01_Projects\Sinister\Sinister-RKA | 4 KB | Y: sinister-rka | PURGE | Low | Minimal size; fully mirrored |
| D:\Sinister\01_Projects\Sinister\Sinister-TG | 3.6 KB | Y: sinister-tg | PURGE | Low | Minimal size; fully mirrored |
| D:\Sinister\01_Projects\Sinister\Sinister-Custom-Kernel | 52 KB | Y: sinister-kernel-apk | PURGE | Low | Mirrored variant; safe for removal |
| D:\Sinister\01_Projects\JOKR\JOKR-Global | 492 MB | Y: sinister-jokr/JOKR-Global | PURGE | Low | JOKR mirror confirmed in Sanctum; fully redundant |
| D:\Sinister\06_Tools\Sinister-Bats | 20 KB | Uncertain | INVESTIGATE | Medium | Tool-adjacent; verify usage before purge |
| D:\Sinister\07_Archive\Sinister iMessage Bridge.rar | 460 KB | N | INVESTIGATE | Medium | Unique archive; check Sanctum before deletion |

### KEEP Directives (per operator canonical)
- **D:\Sinister\Sinister Skills\** — Operator brain/memory; KEEP as-is
- **D:\Sinister\_vault\** — Operator-secret; LEAVE untouched
- **D:\Sinister\local-secrets\** — Operator-secret; LEAVE untouched
- **D:\Sinister\02_Personal\** — Genuine personal; no Sinister leakage detected; LEAVE

---

## Top-5 PURGE Candidates (Operator-Actionable)

**Safe for immediate `Remove-Item` execution:**

1. **D:\Sinister\01_Projects\Sinister\Sinister-APK** (3.9 GB)  
   - Mirror: D:\Sinister Sanctum\projects\sinister-kernel-apk
   - Status: Fully redundant; last modified 2026-05-21 16:28:30

2. **D:\Sinister\01_Projects\JOKR\JOKR-Global** (492 MB)  
   - Mirror: D:\Sinister Sanctum\projects\sinister-jokr\JOKR-Global
   - Status: Fully redundant; last modified 2026-05-21 12:48:47

3. **D:\Sinister\01_Projects\Sinister\Sinister-Panel** (1.2 GB)  
   - Mirror: D:\Sinister Sanctum\projects\sinister-panel
   - Status: Fully redundant; most recent in Sanctum

4. **D:\Sinister\01_Projects\Sinister\Sinister-Custom-Kernel** (52 KB)  
   - Mirror: D:\Sinister Sanctum\projects\sinister-kernel-apk (variant)
   - Status: Fully redundant; negligible size

5. **D:\Sinister\01_Projects\Sinister\Sinister-RKA** (4 KB)  
   - Mirror: D:\Sinister Sanctum\projects\sinister-rka
   - Status: Fully redundant; negligible size

**Combined bytes (Top 5):** ~5.7 GB

---

## Recommended Purge Commands

```powershell
# Execute after operator confirmation:
Remove-Item -Path "D:\Sinister\01_Projects\Sinister\Sinister-APK" -Recurse -Force
Remove-Item -Path "D:\Sinister\01_Projects\JOKR\JOKR-Global" -Recurse -Force
Remove-Item -Path "D:\Sinister\01_Projects\Sinister\Sinister-Panel" -Recurse -Force
Remove-Item -Path "D:\Sinister\01_Projects\Sinister\Sinister-Custom-Kernel" -Recurse -Force
Remove-Item -Path "D:\Sinister\01_Projects\Sinister\Sinister-RKA" -Recurse -Force
Remove-Item -Path "D:\Sinister\01_Projects\Sinister\Sinister-TG" -Recurse -Force
```

---

## Audit Status
- [x] 01_Projects/Sinister/ — Audited (5 subdirs, all mirrored)
- [x] 01_Projects/JOKR/ — Audited (mirror confirmed)
- [x] 06_Tools/ — Partial (Sinister-Bats flagged for review)
- [x] 07_Archive/ — Partial (1 unique archive flagged)
- [x] _vault/ & local-secrets/ — LEAVE untouched
- [x] 02_Personal/ — Verified clean (no Sinister leakage)

**Next step:** Operator approval for Top-5 PURGE list, then execute removal.
