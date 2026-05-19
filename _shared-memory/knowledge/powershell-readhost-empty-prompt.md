> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: `Read-Host ""` crashes with "name cannot be null or empty"

**Slug:** powershell-readhost-empty-prompt
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** fixed
**Tags:** powershell, read-host, ui, pwsh-5

## Problem

PowerShell 5.1 crashes when given an empty string as the prompt:

```powershell
$pick = Read-Host ""
```

Error:
```
Read-Host : name cannot be null or empty.
At ...\start-sinister-session.ps1:685 char:13
+ $pick = Read-Host ""
+             ~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Read-Host], PSArgumentException
    + FullyQualifiedErrorId : Argument,Microsoft.PowerShell.Commands.ReadHostCommand
```

The launcher continues with `$pick = $null` and falls through to the default branch. From the operator's POV: they typed `2` to pick Snap EMU, but the launcher ignored them and acted as if they hit Enter.

## Why it happens

`Read-Host` requires either NO argument at all (zero-arg form) or a non-empty `-Prompt` parameter. Passing `""` or `''` raises ArgumentException because PowerShell's parameter binder treats it as "prompt name was set to empty" rather than "prompt name was omitted".

PowerShell 7 is more lenient but still warns. Stick to one of the safe forms below.

## Fix or workaround

```powershell
# GOOD: no argument
$pick = Read-Host

# GOOD: non-empty prompt
$pick = Read-Host 'choice'

# GOOD: single space prompt (when you don't want a label but need a non-empty arg)
$pick = Read-Host ' '

# BAD: empty string
$pick = Read-Host ""
$pick = Read-Host ''
```

If you want the prompt text on its OWN line (so the input cursor is on a new line), `Write-Host` the prompt first, then call `Read-Host` with a minimal placeholder:

```powershell
Write-Host "Selection [1-5/A/G, default=sanctum]" -ForegroundColor Magenta
$pick = Read-Host '  >'
```

## Sanctum-specific note

This bug was in `start-sinister-session.ps1` v6 at lines 685, 713, 1193. All three call sites fixed 2026-05-19 to use `Read-Host '  >'` (visual prompt indicator). Parse-check passes; live test confirmed picker accepts input.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 02:45 by Sinister Sanctum
Operator hit this on the project picker selection. Fixed by replacing `Read-Host ""` with `Read-Host '  >'`. Verified with `[System.Management.Automation.Language.Parser]::ParseFile` + a live operator screenshot.

## Related topics

- [powershell-emdash-non-ascii](./powershell-emdash-non-ascii.md)
