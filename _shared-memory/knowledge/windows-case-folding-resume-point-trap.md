<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Windows case-folding vs git case-sensitivity — resume-point dir trap

> **Author:** RKOJ-ELENO :: 2026-05-21
> **Lane tags:** sanctum, forge, term, panel, kernel-apk (all lanes that call `resume-point-write.ps1`)
> **Discovered:** 2026-05-21 ~14:00Z by EVE on sanctum lane
> **Repro hash:** commit `7577a24` (the commit where `--only` silently dropped the resume-point because Windows had folded `sanctum/` to `Sanctum/` underneath git)
> **Status (added 2026-05-25 audit):** ✅ RESOLVED — Cure A shipped 2026-05-23T08:35Z. `Resolve-ResumePointDirName` is at `automations/resume-point-write.ps1:44` with full slug→display mapping (sanctum→Sinister Sanctum, forge→Sinister Forge, term→Sinister Term, panel→Sinister Panel, kernel-apk→Sinister Kernel APK, apk→Sinister Kernel APK, freeze→Sinister Freeze, rkoj→RKOJ Workstation, rkoj-workstation→RKOJ Workstation). The 6 "likely" affected-lane markers in the §Affected-lanes table below were SPECULATIVE at 2026-05-21 write time — they are now CONFIRMED resolved by the shipped function. Brain entry retained as historical anchor + repro recipe; Cure A is no longer a TODO.

## The trap in one sentence

`resume-point-write.ps1 -ProjectKey "sanctum"` creates a dir called `sanctum/` on disk; if `Sanctum/` already exists (different case), Windows silently writes the file INTO the existing `Sanctum/`, but git sees the path you asked for (`sanctum/`) and reports "pathspec did not match any file(s) known to git" or silently ignores the add.

## The full repro

1. Tracked dir `_shared-memory/resume-points/Sanctum/` exists in git (committed earlier with title-case key).
2. EVE calls `powershell -File resume-point-write.ps1 -ProjectKey "sanctum"` (lowercase slug, kebab convention).
3. PowerShell creates `_shared-memory\resume-points\sanctum\` — but on NTFS this is the SAME inode as `Sanctum/` (case-folded by the filesystem).
4. The new JSON file lands at `_shared-memory/resume-points/Sanctum/2026-05-21T<UTC>.json` on disk (git's case-sensitive name view).
5. EVE tries `git add "_shared-memory/resume-points/sanctum/2026-05-21T<UTC>.json"` (lowercase).
6. Git reports `pathspec 'sanctum/...' did not match any file(s) known to git` because git knows the dir as `Sanctum`.
7. `git commit --only "<lowercase path>"` errors with the same message.

The trap is mute in this case because the file IS persisted to the right inode — it's just git that can't find it via the wrong-case spec.

## Cures

### Cure A (recommended): standardize ProjectKey case in `resume-point-write.ps1`

The launcher passes `-ProjectKey` based on the caller's whim ("sanctum" / "Sinister Sanctum" / "Sanctum"). The script should pick ONE canonical on-disk dir name per slug and use only that. Reasonable canonical = title-case display name (`Sinister Sanctum`, `Sinister Forge`, etc.) since that's already used in `PROGRESS/Sinister X.md` and `git ls-tree` shows half the resume-point dirs use the title-case convention.

Patch shape (untested):

```powershell
function Resolve-ResumePointDir {
    param([string]$Root, [string]$ProjectKey)
    $known = @{
        'sanctum'        = 'Sinister Sanctum'
        'forge'          = 'Sinister Forge'
        'term'           = 'Sinister Term'
        'panel'          = 'Sinister Panel'
        'kernel-apk'     = 'Sinister Kernel APK'
        'apk'            = 'Sinister Kernel APK'
        'freeze'         = 'Sinister Freeze'
        'rkoj'           = 'RKOJ Workstation'
        'rkoj-workstation' = 'RKOJ Workstation'
    }
    $key = $ProjectKey.Trim().ToLower()
    if ($known.ContainsKey($key)) { return Join-Path $Root "_shared-memory\resume-points\$($known[$key])" }
    # default: leave caller's case alone
    return Join-Path $Root "_shared-memory\resume-points\$ProjectKey"
}
```

After that, every lane lands its resume-point under the SAME tracked dir name regardless of what slug the launcher passes.

### Cure B (immediate sidestep): commit with the on-disk case

When `git add "sanctum/..."` fails, ALWAYS try `git add "Sanctum/..."` (or whatever case git tracks). `git ls-tree HEAD <parent>` shows the canonical case git knows.

### Cure C (last resort): `git mv` to lowercase

If a team decides the slug-form (`sanctum/`) is canonical, run `git mv "Sinister Sanctum" "sanctum"` once, commit, and forget. On Windows this requires the `--cached` flag or a two-step (`-f sanctum.tmp` then `-f sanctum`) because the filesystem can't distinguish the cases.

DO NOT do Cure C without lane-wide coordination — it'll break every other lane's resume-point-write callers until they update.

## Why this didn't surface earlier

- The v1.1 + v1.2 bugfixes covered `latestPlanDir` regex + `Resolve-InboxSlug` slugification. They did NOT touch the on-disk RESUME-POINT DIR name.
- Sanctum lane historically used `Sinister Sanctum` (display) because the PROGRESS log path was the model.
- When kebab-slug usage spread (post-2026-05-21 `sinister-cli` umbrella + jcode-swarm parity), `sanctum/` became the new convention but the resume-point dir resolution was never updated.

## Pattern (compose with other brain entries)

- See **`multi-agent-branch-contention-isolation-pattern`** for the broader "two sibling agents on the same branch" gotcha. This trap stacks: sibling A writes the dir in title-case, sibling B writes in kebab, Windows folds them into one inode, git sees them as different paths.
- See **`forever-expanding-modular-architecture-doctrine`** — yet another reason to standardize ONE canonical disk layout per lane.
- See **`resume-point-discipline`** (CONTRACT 7) for why the dir needs to be ONE name, not two.

## Detection (cheap, recommended)

Add a one-liner to `resume-point-write.ps1` end-of-run:

```powershell
$canonical = Resolve-ResumePointDir -Root $SanctumRoot -ProjectKey $ProjectKey
$tracked = (& git ls-tree HEAD "_shared-memory/resume-points/" 2>$null) -split "`n" |
    Where-Object { $_ -match "resume-points/(.+)$" } |
    ForEach-Object { $matches[1].Trim() }
if ($tracked -and ($tracked -notcontains (Split-Path $canonical -Leaf))) {
    Write-Host "[resume-point-write] WARN: dir '$canonical' is not tracked under any known case. git may reject add. Tracked variants: $($tracked -join ', ')" -ForegroundColor Yellow
}
```

That single warning would have caught this turn's silent-drop.

## Affected lanes — all resolved by Resolve-ResumePointDirName (2026-05-23)

- `sanctum/` vs `Sanctum/` vs `Sinister Sanctum/` — ✅ resolved (maps to `Sinister Sanctum`)
- `forge/` vs `Sinister Forge/` — ✅ resolved (maps to `Sinister Forge`)
- `term/` vs `sinister-term/` vs `Sinister Term/` — ✅ resolved (maps to `Sinister Term`)
- `panel/` vs `Sinister Panel/` — ✅ resolved (maps to `Sinister Panel`)
- `kernel-apk/` vs `Sinister Kernel APK/` — ✅ resolved (`kernel-apk` AND `apk` both map to `Sinister Kernel APK`)
- `apk/` vs `Sinister Kernel APK/` — ✅ resolved (same — aliased to `kernel-apk` slot)
- `rkoj/` vs `rkoj-workstation/` vs `RKOJ Workstation/` — ✅ resolved (both `rkoj` and `rkoj-workstation` map to `RKOJ Workstation`)

## Next action — DONE

Cure A is shipped at `automations/resume-point-write.ps1:44`. This brain entry is now historical anchor + repro recipe; the function is the canonical resolver going forward.

(Original 2026-05-21 recommendation: title-case display name. Adopted in shipped function.)
