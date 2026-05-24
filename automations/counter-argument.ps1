# counter-argument.ps1 -- challenge any claim from 3 angles before committing to a path
# Author: RKOJ-ELENO :: 2026-05-24
#
# Origin: operator hard-canonical 2026-05-24T16:06:32Z verbatim:
#   "i also need like a counter argument system so we contracdiuct ourself and find the best path
#    becasue we need to think at all angles and find best poath and keep expanding and self evoloving"
#
# Three angles per claim, always:
#   A -- STEELMAN: best possible defense of the claim
#   B -- RED-TEAM: most damaging attack on the claim
#   C -- ALTERNATIVE: a third path that supersedes both
#
# Actions:
#   Challenge -- append a new claim to the ledger; print 3-angle template the agent must fill in
#   List      -- show pending/resolved challenges, filter by lane
#   Resolve   -- pick best angle (a|b|c) + record the chosen path + reasoning
#   Stats     -- counts by lane + status
#
# Ledger: _shared-memory/counter-arguments.jsonl (lock-based append, same pattern as
#         operator-utterances + operator-ideas).

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Challenge','List','Resolve','Stats')]
    [string]$Action,

    [string]$Claim = '',
    [string]$Lane = '',
    [string]$Id = '',
    [ValidateSet('a','b','c','pending','resolved','all','')]
    [string]$Best = '',
    [string]$Status = '',
    [string]$Note = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$JsonlPath = Join-Path $SanctumRoot '_shared-memory\counter-arguments.jsonl'
$LockPath  = Join-Path $SanctumRoot '_shared-memory\.counter-arguments.lock'

function Acquire-Lock {
    param([string]$Path, [int]$TimeoutSec = 10)
    $start = Get-Date
    while ($true) {
        try {
            $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
            $fs.Close()
            return $true
        } catch {
            if (((Get-Date) - $start).TotalSeconds -gt $TimeoutSec) { return $false }
            Start-Sleep -Milliseconds 100
        }
    }
}

function Release-Lock {
    param([string]$Path)
    if (Test-Path $Path) { Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue }
}

function Read-Rows {
    if (-not (Test-Path $JsonlPath)) { return @() }
    $rows = @()
    Get-Content -LiteralPath $JsonlPath -Encoding UTF8 | ForEach-Object {
        if ($_.Trim()) { try { $rows += ($_ | ConvertFrom-Json) } catch { } }
    }
    return $rows
}

switch ($Action) {

    'Challenge' {
        if (-not $Claim) { Write-Error "Challenge requires -Claim"; exit 2 }
        $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        if (-not (Acquire-Lock -Path $LockPath -TimeoutSec 10)) { Write-Error "lock fail"; exit 2 }
        try {
            $row = [ordered]@{
                ts_utc          = $ts
                lane            = $Lane
                claim           = $Claim
                angle_a_steelman= ''
                angle_b_redteam = ''
                angle_c_alt     = ''
                best_path       = ''
                resolution_note = ''
                status          = 'pending'
                resolved_at_utc = $null
            }
            $json = $row | ConvertTo-Json -Compress -Depth 10
            $sw = [System.IO.StreamWriter]::new($JsonlPath, $true, [System.Text.UTF8Encoding]::new($false))
            $sw.WriteLine($json); $sw.Close()
        } finally { Release-Lock -Path $LockPath }
        Write-Output "challenge id=$ts"
        Write-Output ""
        Write-Output "----- Fill in three angles before committing to a path -----"
        Write-Output "CLAIM: $Claim"
        Write-Output ""
        Write-Output "A. STEELMAN -- best defense of the claim:"
        Write-Output "   (what makes this the right call? assume it's correct -- defend why)"
        Write-Output ""
        Write-Output "B. RED-TEAM -- most damaging attack on the claim:"
        Write-Output "   (what breaks it? hidden assumption? failure mode? what does it miss?)"
        Write-Output ""
        Write-Output "C. ALTERNATIVE -- a third path that supersedes A and B:"
        Write-Output "   (what would a different framing produce? composes the strengths of A and B?)"
        Write-Output ""
        Write-Output "Resolve with: counter-argument.ps1 -Action Resolve -Id $ts -Best a|b|c -Note '<reasoning>'"
    }

    'List' {
        $rows = Read-Rows
        if ($Status -and $Status -ne 'all') { $rows = $rows | Where-Object { $_.status -eq $Status } }
        if ($Lane) { $rows = $rows | Where-Object { $_.lane -eq $Lane } }
        if (-not $rows) { Write-Output "(no rows)"; return }
        $rows | Sort-Object ts_utc -Descending | ForEach-Object {
            $bestStr = if ($_.best_path) { $_.best_path } else { '?' }
            $preview = if ($_.claim.Length -gt 80) { $_.claim.Substring(0,80) + '...' } else { $_.claim }
            "{0}  {1,-10}  {2,-9}  best={3}  {4}" -f $_.ts_utc, $_.lane, $_.status, $bestStr, $preview
        }
    }

    'Resolve' {
        if (-not $Id) { Write-Error "Resolve requires -Id"; exit 2 }
        if (-not $Best -or $Best -notin @('a','b','c')) { Write-Error "Resolve requires -Best a|b|c"; exit 2 }
        $rows = Read-Rows
        $found = $false
        $newRows = @()
        foreach ($r in $rows) {
            if ($r.ts_utc -eq $Id) {
                $found = $true
                $r.best_path = $Best
                if ($Note) { $r.resolution_note = $Note }
                $r.status = 'resolved'
                $r.resolved_at_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
            }
            $newRows += $r
        }
        if (-not $found) { Write-Error "no row id=$Id"; exit 2 }
        if (-not (Acquire-Lock -Path $LockPath -TimeoutSec 10)) { Write-Error "lock fail"; exit 2 }
        try {
            $sw = [System.IO.StreamWriter]::new($JsonlPath, $false, [System.Text.UTF8Encoding]::new($false))
            foreach ($r in $newRows) { $sw.WriteLine(($r | ConvertTo-Json -Compress -Depth 10)) }
            $sw.Close()
        } finally { Release-Lock -Path $LockPath }
        Write-Output "resolved id=$Id best=$Best"
    }

    'Stats' {
        $rows = Read-Rows
        if (-not $rows) { Write-Output "(no rows)"; return }
        $byLane = $rows | Group-Object lane
        Write-Output "----- counter-argument stats -----"
        foreach ($g in $byLane) {
            $pending  = ($g.Group | Where-Object { $_.status -eq 'pending' }).Count
            $resolved = ($g.Group | Where-Object { $_.status -eq 'resolved' }).Count
            $bestA = ($g.Group | Where-Object { $_.best_path -eq 'a' }).Count
            $bestB = ($g.Group | Where-Object { $_.best_path -eq 'b' }).Count
            $bestC = ($g.Group | Where-Object { $_.best_path -eq 'c' }).Count
            "{0,-20}  pending={1}  resolved={2}  picks: a={3} b={4} c={5}" -f $g.Name, $pending, $resolved, $bestA, $bestB, $bestC
        }
    }
}
