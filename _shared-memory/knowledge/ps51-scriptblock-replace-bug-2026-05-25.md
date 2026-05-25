<!-- Author: RKOJ-ELENO :: 2026-05-25 -->
<!-- decay:
  category: correction
  confidence: 1.0
  reinforcements: 0
  half_life_days: 365
-->

# PowerShell 5.1 stringifies scriptblock substitutions in `-replace` — DO NOT USE

**Created:** 2026-05-25
**Updated:** 2026-05-25
**Lane:** Sanctum
**Severity:** P0 (broke EVE spawn-setup-wizard mintty window with `exit 126` for operator at ~01:52Z; root-caused 02:00Z)

## The bug

```powershell
$bashPath = $WinPath -replace '\\','/' -replace '^([A-Z]):', { '/' + $args[0].Groups[1].Value.ToLower() }
```

This idiom — scriptblock as the second argument to `-replace` — only works in **PowerShell 7+** (PSCore). On **Windows PowerShell 5.1** (the OS-bundled host this fleet runs on by default; `$PSVersionTable.PSVersion = 5.1.19041.6456`), the scriptblock is silently converted to its string form via `.ToString()`. The literal text `' / ' + $args[0].Groups[1].Value.ToLower()` becomes the replacement string.

Result: a Windows path like `D:\Sinister Sanctum` produces the bash path `' / ' + $args[0].Groups[1].Value.ToLower() /Sinister Sanctum` instead of `/d/Sinister Sanctum`. When that string is then handed to `mintty -- /bin/bash`, bash treats `/` (the slash before `+`) as a path → `/: Is a directory` → `exit 126`.

## Operator-visible symptom

Mintty window opens, instantly shows:
```
/bin/bash / + $args[0].Groups[1].Value.ToLower() /Users/Zonia/AppData/Lo...
/: /: Is a directory
/bin/bash: Exit 126.
```
Window stays open because `--hold error` keeps failed-spawn windows visible (per prior canonical fix).

## Reproduction (smoke)

```powershell
'D:\Sinister Sanctum' -replace '\\','/' -replace '^([A-Z]):', { '/' + $args[0].Groups[1].Value.ToLower() }
# PS 5.1 output: ' / ' + $args[0].Groups[1].Value.ToLower() /Sinister Sanctum   (BAD)
# PS 7   output: /d/Sinister Sanctum                                            (good)
```

## Canonical fix (PS 5.1-safe)

Use explicit `-match` + manual concat (or string substring):

```powershell
$bashPath = if ($WinPath -match '^([A-Za-z]):(.*)$') {
    '/' + $Matches[1].ToLower() + ($Matches[2] -replace '\\', '/')
} else {
    $WinPath -replace '\\', '/'
}
```

This works on both PS 5.1 and PS 7+, no behaviour drift.

## Where it was found (2026-05-25 audit)

- `automations\spawn-setup-wizard.ps1:136` — FIXED 2026-05-25T01:55Z (RKOJ-ELENO / sanctum)
- `automations\spawn-setup-wizard.ps1:184` — FIXED 2026-05-25T01:55Z (RKOJ-ELENO / sanctum)
- `automations\eve-bulk-oauth-login.ps1` — already fixed by a sibling agent earlier (comment block at line 243 explains the same root cause and applies the explicit `-match` pattern; preserved as a prior reference)
- `automations\claude-accounts.ps1:569` — uses `.Groups[1].Value.ToLower()` but in a normal `-match` body, NOT inside `-replace` scriptblock. Correct usage. NO bug.

Grep guard for future audits:
```bash
grep -rn "Groups\[1\]\.Value\.ToLower" automations/ | grep -v "^[^:]*:[^:]*: *#"
# any -replace '...', { ... } hit that survives the comment filter is a regression
```

## Composes with

- `sanctum-launcher-spawn-mintty-args` (the title-arg bug fixed earlier in the same operator-spawn-failure category — same blast pattern: launcher produces a malformed shell command, mintty silently fails or shows exit 126)
- `no-bullshit-tested-before-claimed-doctrine-2026-05-23` — rule 2 (test before claiming) would have caught this; sibling shipped wizard without an actual end-to-end mintty spawn smoke test.

## Anti-pattern (DO NOT do)

```powershell
# WRONG on PS 5.1:
$x -replace 'pattern', { $args[0].Value.ToUpper() }

# RIGHT on PS 5.1:
$re = [regex]'pattern'
$x = $re.Replace($x, { param($m) $m.Value.ToUpper() })   # [regex]::Replace overload accepts MatchEvaluator delegate

# OR (simpler, no regex eval):
if ($x -match 'pattern') { $x = $x -replace 'pattern', $Matches[0].ToUpper() }
```

The `[regex]::Replace` overload is the cleanest cross-version path when you need a true callback.

## Future-proof guard (CI lint)

Add to `automations/canonical-protections-check.ps1` as protection #7:
```powershell
$bad = Select-String -Path 'automations\*.ps1' -Pattern "-replace '[^']*',\s*\{" -List
if ($bad) { Write-Error "PS 5.1 scriptblock-in-replace regression: $($bad.Path)"; exit 1 }
```
(Carry out as a follow-up; not blocking this fix.)
