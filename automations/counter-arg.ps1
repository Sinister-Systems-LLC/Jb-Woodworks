# counter-arg.ps1 — append a counter-argument row to _shared-memory/counter-arguments.jsonl
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T16:06:32Z:
#   "i also need like a counter argument system so we contracdiuct ourself and find
#    the best path becasue we need to think at [multiple angles]"
#
# Schema (matches existing rows from sinister-os-mobile + test-modes-verify lanes):
#   { ts_utc, lane, claim,
#     angle_a_steelman, angle_b_redteam, angle_c_alt,
#     best_path,        # 'a' | 'b' | 'c'
#     resolution_note, status, resolved_at_utc }
#
# Usage:
#   powershell -File counter-arg.ps1 -Lane my-lane `
#       -Claim 'X is the right call' `
#       -Steelman 'Why X is correct' `
#       -RedTeam 'Why X might be wrong' `
#       -Alt 'What we could do instead' `
#       -BestPath a -Resolution 'Why we went with a'
#
# Compose with: no-bullshit doctrine (R4 self-audit), forever-improve checkpoint.
# When an agent makes a non-trivial decision (architecture / scope / approach), log
# a counter-argument row BEFORE acting. The act of articulating the red-team often
# changes which path is best.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$Lane,
    [Parameter(Mandatory=$true)] [string]$Claim,
    [string]$Steelman = '',
    [string]$RedTeam  = '',
    [string]$Alt      = '',
    [ValidateSet('a','b','c','open')] [string]$BestPath = 'open',
    [string]$Resolution = '',
    [ValidateSet('open','resolved')] [string]$Status = 'open',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$file = Join-Path $SanctumRoot '_shared-memory\counter-arguments.jsonl'
$now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

if ($BestPath -eq 'open' -and $Status -eq 'resolved') { $Status = 'open' }
if ($Status -eq 'resolved' -and $BestPath -eq 'open') {
    Write-Host "ERROR: -Status resolved requires -BestPath a|b|c" -ForegroundColor Red
    exit 1
}

$row = [pscustomobject]@{
    ts_utc = $now
    lane = $Lane
    claim = $Claim
    angle_a_steelman = $Steelman
    angle_b_redteam  = $RedTeam
    angle_c_alt      = $Alt
    best_path = $BestPath
    resolution_note = $Resolution
    status = $Status
    resolved_at_utc = if ($Status -eq 'resolved') { $now } else { $null }
}
$json = $row | ConvertTo-Json -Compress -Depth 5

# Append with file lock for fleet safety
$mutex = New-Object System.Threading.Mutex($false, 'SinisterCounterArgMutex')
$acquired = $mutex.WaitOne(5000)
if (-not $acquired) {
    Write-Host "ERROR: could not acquire counter-args mutex in 5s" -ForegroundColor Red
    exit 1
}
try {
    Add-Content -LiteralPath $file -Value $json -Encoding UTF8
} finally {
    $mutex.ReleaseMutex() | Out-Null
    $mutex.Dispose()
}

Write-Host "logged counter-argument:" -ForegroundColor Cyan
Write-Host "  lane: $Lane"
Write-Host "  claim: $Claim"
Write-Host "  best: $BestPath  status: $Status"
Write-Host "  file: $file"
