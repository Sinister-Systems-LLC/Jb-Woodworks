# Topic: PowerShell 5.1 cannot parse Unicode box-drawing chars (U+2588/2557/etc.) even with UTF-8 BOM

**Slug:** powershell-unicode-blockdraw-parse-fail
**First discovered:** 2026-05-19 13:30 by Sinister Sanctum master agent (Claude)
**Last updated:** 2026-05-19 13:35 by Sinister Sanctum master agent
**Status:** workaround
**Tags:** powershell, encoding, utf-8, bom, unicode, box-drawing, ascii-art, logo, ps1, parser

## Problem

A PowerShell 5.1 (`powershell.exe`, Windows default) script that contains Unicode box-drawing characters in string literals fails to parse with errors like:

```
Unexpected token '...' in expression or statement.
Unrecognized token in source text.
Not all parse errors were reported. Correct the reported errors and try again.
```

Specifically observed with characters from the Box Drawing block (U+2500..U+257F) and the Block Elements block (U+2580..U+259F) — e.g. `█` (U+2588), `╔` (U+2554), `╗` (U+2557), `║` (U+2551), `╝` (U+255D), `═` (U+2550), `╚` (U+255A).

Adding a UTF-8 BOM to the file (`[System.Text.UTF8Encoding]::new($true)`) **does NOT fix it**. The bytes parse cleanly as UTF-8 but the PS 5.1 lexer still chokes downstream.

## Why it happens

Windows PowerShell 5.1's lexer / parser was written against the .NET Framework 4.x runtime in an era when the default console code page was OEM (CP437 / CP850) and the script encoding default was Windows-1252. When parsing a `'string literal'`, the lexer correctly reads the UTF-8 bytes WITH BOM as Unicode codepoints, BUT some non-BMP-edge codepoints in the Box Drawing / Block Elements ranges trip up tokenizer state machines that confuse them with operator-adjacent characters. The result is a cascade of false "unexpected token" errors AFTER the problematic literal even though the rest of the script is clean.

Em-dashes (`—`, U+2014) behave differently — those parse cleanly WITH BOM (covered by sibling topic `powershell-emdash-non-ascii.md`). The Box Drawing / Block Elements range is the new failure mode.

PowerShell 7+ (`pwsh.exe`) on .NET 7+ handles these correctly. But operator scripts run via `powershell.exe -NoProfile -ExecutionPolicy Bypass -File <ps1>` are always PS 5.1 on Windows 10/11.

## Fix or workaround

**Never embed Unicode box-drawing / block-element characters in a PS 5.1 script.** Use ASCII characters instead. The canonical pattern is the `##` block letter style:

```powershell
# WORKS in PS 5.1 (no BOM needed)
$logo = @(
    '       ####      #####    ##   ##   ######  ',
    '         ##     ##   ##   ##  ##    ##   ## ',
    '         ##     ##   ##   ## ##     ##   ## ',
    '         ##     ##   ##   ####      ######  ',
    '         ##     ##   ##   ## ##     ####    ',
    '   ##    ##     ##   ##   ##  ##    ##  ##  ',
    '    #####        #####    ##   ##   ##   ## '
)
foreach ($line in $logo) { Write-Host $line -ForegroundColor Magenta }
```

vs.

```powershell
# FAILS in PS 5.1 (parser errors even with UTF-8 BOM)
$logo = @(
    '         ██╗   ██████╗  ██╗  ██╗ ██████╗ ',
    '         ██║  ██╔═══██╗ ██║ ██╔╝ ██╔══██╗',
    ...
)
```

If you genuinely need rich Unicode line-drawing in a console launcher (smooth borders, table separators, etc.), three alternatives:

1. **Use ASCII fallbacks:** `+----+`, `|`, `=`, `-`, `#`, `:`. These render the same regardless of code page.
2. **Render via Write-Host with .NET strings built at runtime** (e.g. `[char]0x2588` per char) — emits codepoints that the console can render even if the source file can't tokenize them. Slower + uglier code.
3. **Switch to PowerShell 7+** (`pwsh.exe`). Project-side decision; can't be assumed on operator machines.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum master agent
Caught when shipping JOKR Panel launcher v1 (`D:\Sinister\01_Projects\JOKR\JOKR-Global\source\automations\start-jokr-session.ps1`). The block-letter logo used U+2588/2557/2554/etc. for crisp rendering. PS 5.1 refused to parse with 10+ "Unexpected token" errors at + after the logo block. Adding UTF-8 BOM via `[System.Text.UTF8Encoding]::new($true)` did NOT fix it — file had `EF BB BF` at byte 0 yet parser still choked. Workaround applied: replaced the entire logo with ASCII-only `##` block letters (matching the LetsText/Sinister launcher style). Re-smoke-tested green.

Pairs with sibling topic `powershell-emdash-non-ascii.md` (em-dash works WITH BOM; box-drawing needs ASCII replacement). Together these form the "non-ASCII in PS 5.1" rule of thumb:
- Em-dashes / curly quotes / smart punctuation: add UTF-8 BOM, ship as-is.
- Box-drawing / block-element / CJK / heavy emoji: replace with ASCII.

## Tools that should know this rule

- `start-sinister-session.ps1` (already ASCII-only block logo)
- `start-letstext-session.ps1` (already ASCII-only `##` letters)
- `start-jokr-session.ps1` (fixed in this session)
- Any future themed-session launcher (Snap-EMU / TikTok-EMU / RKA / Bumble / Sinister Panel side)
- `D:\Sinister Sanctum\docs\THEMED-SESSION-LAUNCHER.md` — should reference this gotcha

## Related

- `powershell-emdash-non-ascii.md` (em-dash + BOM)
- `powershell-readhost-empty-prompt.md` (Read-Host quirk)
