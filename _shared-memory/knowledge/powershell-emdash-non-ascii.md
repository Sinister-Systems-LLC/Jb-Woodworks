> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: em-dash `—` in PS scripts without UTF-8 BOM breaks parsing

**Slug:** powershell-emdash-non-ascii
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 (cross-lane recurrence on LetsText launcher) by Sinister Sanctum
**Status:** fixed
**Tags:** powershell, encoding, utf-8, bom, pwsh-5

## Problem

PowerShell 5.1 reads source files as Windows-1252 by default unless the file has a UTF-8 BOM (Byte Order Mark). Any non-ASCII character — em-dash `—`, en-dash `–`, ellipsis `…`, smart-quotes `"` `"`, etc. — gets misinterpreted, breaking the parser.

Symptom:
```
At ...\script.ps1:899 char:73
+ ... /4  What's today's focus?  (one line — press Enter to skip)" $White
+                                                          ~
Unexpected token ')' in expression or statement.
```

The parser corrupts byte sequences mid-string-literal, then everything downstream fails to tokenize. Cascade of `Missing closing '}'` errors at unrelated lines further down.

## Why it happens

`—` (U+2014) encodes as 3 UTF-8 bytes (`E2 80 94`). Without a UTF-8 BOM at the start of the file, PowerShell 5.1 reads each byte as Windows-1252, which has `E2` = `â`, `80` = `€`, `94` = `"`. The string literal `"foo — bar"` becomes `"foo â€" bar"` (with embedded special chars that may include `"` interpreted as a closing quote, terminating the string mid-statement).

PowerShell 7 + uses UTF-8 by default and handles non-ASCII transparently. PowerShell 5.1 needs an explicit BOM.

## Fix or workaround

Two options:

### Option A — Save with UTF-8 BOM

In PowerShell ISE / VSCode / Notepad++, change the file's encoding to **UTF-8 with BOM**. Or programmatically:

```powershell
$path = 'D:\path\to\script.ps1'
$content = Get-Content $path -Raw -Encoding UTF8
[System.IO.File]::WriteAllText($path, $content, (New-Object System.Text.UTF8Encoding($true)))  # $true = with BOM
```

After this, PowerShell 5.1 reads the file as UTF-8 and non-ASCII chars render correctly.

### Option B — Replace non-ASCII with ASCII (safer for cross-tooling)

```powershell
$path = 'D:\path\to\script.ps1'
$content = Get-Content $path -Raw -Encoding UTF8
$newContent = ($content -replace '—', '-') -replace '–', '-' -replace '…', '...' -replace '"|"', '"' -replace ''|'', "'"
[System.IO.File]::WriteAllText($path, $newContent, (New-Object System.Text.UTF8Encoding($true)))
```

This is the safer long-term choice — even with a BOM, some downstream tools (git diff viewers, MD renderers, search-and-replace utilities) misbehave on non-ASCII. ASCII keeps everything portable.

## Sanctum-specific note

`start-sinister-session.ps1` had em-dashes in 13 places. All replaced + file resaved with BOM. The launcher now parses clean on first load. New PS files in Sanctum should use ASCII hyphens.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 07:30 by Sinister Sanctum (cross-lane on LetsText)
Same gotcha bit `D:\LetsText\automations\start-letstext-session.ps1` — 5 em-dashes (lines 1, 22, 255, 283, 289, 310), no BOM. Parser blew up at line 289 inside the `'imessage-bridge'` opening-phrase string ("Resume LetsText round 20 — iMessage Bridge..."). Symptom: `MissingEndCurlyBrace` cascade + `Unexpected token 'routes' in expression or statement`. Applied Option A (UTF-8 BOM, kept the em-dashes since they're cosmetic in display strings). Verified bytes 0–2 = `EF BB BF` post-fix. Smoke retest green. **The gotcha is fleet-wide — anyone copying the Sanctum launcher pattern to a sibling project needs to save with BOM or the launcher won't run.** Sibling-project takeaway: if you author a new themed PS1 in a different project's `automations/`, default-save it UTF-8-with-BOM upfront.

### 2026-05-19 01:50 by Sinister Sanctum
First hit while adding the SESSION SETUP wizard. The Sanctum-SectionHeader comment had `—` which broke parsing 200+ lines further down. Fixed by replace_all + BOM save. Parse-check went from 7 errors to 0.

## Related topics

- [powershell-readhost-empty-prompt](./powershell-readhost-empty-prompt.md)
