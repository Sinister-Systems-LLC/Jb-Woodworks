# sweep-revert-detected-dupes.ps1 -- one-shot cleanup of dupe [REVERT-DETECTED] rows
# Author: RKOJ-ELENO :: 2026-05-25
# Iter 18 follow-up to the canonical-protections-check.ps1 dedup patch (iter 17).
# Removes existing dupes + inserts one SUMMARY row noting the consolidation.

[CmdletBinding()]
param([string]$SanctumRoot = 'D:\Sinister Sanctum')

$ErrorActionPreference = 'Stop'
$q = Join-Path $SanctumRoot '_shared-memory\OPERATOR-ACTION-QUEUE.md'
$raw = Get-Content -LiteralPath $q -Raw -Encoding UTF8
$priorCount = ([regex]::Matches($raw, '## \[REVERT-DETECTED\]')).Count
Write-Host "Prior [REVERT-DETECTED] rows: $priorCount"

# Multiline regex: match the header line + following lines until next '## ' or EOF
$pattern = '(?ms)^## \[REVERT-DETECTED\][^\n]*\n(?:(?!^## ).*\n?)*'
$cleaned = [regex]::Replace($raw, $pattern, '')

$summary = @'

## 2026-05-25T00:02Z -- RESOLVED -- [REVERT-DETECTED] noise consolidation (16 dupe rows swept)

> Author: RKOJ-ELENO :: 2026-05-25 (sanctum-mesh-foundation iter 18)

Sub-agent audit 2026-05-24T23:50Z found 16 [REVERT-DETECTED] rows in this queue with only 3 unique failure signatures (P12 jcode-parity-real-fails + P13 every-lane-has-resume-point + P8 projects.json paths). Cron fires every ~10 min; without dedup the queue accumulated identical rows.

**Iter 17 patch (canonical-protections-check.ps1):** compares current fail signature against most-recent [REVERT-DETECTED] block; skip-writes when identical. Prevents future dupes.

**Iter 18 sweep (this row):** removed all 16 existing dupe rows from this queue. Going forward only signature-change events produce new rows.

If [REVERT-DETECTED] rows reappear, that means a NEW or CHANGED canonical-protection signature surfaced -- worth operator attention.

---
'@

$cleaned = $cleaned -replace '(?m)(\*\*Color key:\*\* .*?--- *\r?\n)', ('${1}' + $summary)
[System.IO.File]::WriteAllText($q, $cleaned, [System.Text.UTF8Encoding]::new($false))
$postCount = ([regex]::Matches((Get-Content $q -Raw), '## \[REVERT-DETECTED\]')).Count
Write-Host "Sweep complete. Post-sweep [REVERT-DETECTED] rows: $postCount"
Write-Host "Removed: $($priorCount - $postCount)"
