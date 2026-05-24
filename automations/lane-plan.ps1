# lane-plan.ps1 — per-lane completion plan with TODO / IN-PROGRESS / DONE buckets.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Origin: operator hard-canonical 2026-05-24T16:57:59Z verbatim:
#   "i need the agents to create plans to complete everything that it needs to complete
#    so everything is done and no progress is lost at all"
#
# Each lane writes/updates _shared-memory/lane-plans/<slug>.md. Sections:
#   ## TODO   (work to complete)
#   ## IN-PROGRESS  (taken)
#   ## DONE   (verified shipped)
#
# Append-only on item creation; status flips edit-in-place. Item id = ts_utc.
# Stops progress loss because: every claim has a row, every row has a state,
# no row can vanish (append-only). Composes with no-bullshit doctrine
# (verbs at gate) + forever-improve (review hook).
#
# Usage:
#   powershell -File lane-plan.ps1 -Action Add      -Lane <slug> -Task "<text>" [-Priority high|normal|low]
#   powershell -File lane-plan.ps1 -Action Start    -Lane <slug> -Id <ts_utc>
#   powershell -File lane-plan.ps1 -Action Done     -Lane <slug> -Id <ts_utc> -Evidence "<commit-sha | path | smoke output>"
#   powershell -File lane-plan.ps1 -Action List     -Lane <slug> [-Status todo|in-progress|done|all]
#   powershell -File lane-plan.ps1 -Action Tally    [-Lane <slug>]   # cross-lane or single
#   powershell -File lane-plan.ps1 -Action Bootstrap -Lane <slug>    # create empty plan with template

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Add','Start','Done','List','Tally','Bootstrap')]
    [string]$Action,
    [string]$Lane = '',
    [string]$Task = '',
    [string]$Id = '',
    [string]$Evidence = '',
    [ValidateSet('high','normal','low','')]
    [string]$Priority = 'normal',
    [ValidateSet('todo','in-progress','done','all','')]
    [string]$Status = 'all',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$PlansDir = Join-Path $SanctumRoot '_shared-memory\lane-plans'
if (-not (Test-Path $PlansDir)) { New-Item -ItemType Directory -Path $PlansDir -Force | Out-Null }

function Get-PlanPath { param([string]$L) Join-Path $PlansDir "$L.md" }

function Ensure-Plan {
    param([string]$L)
    $p = Get-PlanPath $L
    if (Test-Path $p) { return $p }
    $author = "RKOJ-ELENO :: $((Get-Date).ToString('yyyy-MM-dd'))"
    @"
<!-- Author: $author -->
# Lane Plan :: $L

> Per-lane completion plan. Composes with operator-utterance-tracking + forever-improve + no-bullshit verbs.
> Each row: ``- [ ] <ts_utc> :: <priority> :: <task>``  (status moves between sections; never delete)

## TODO

## IN-PROGRESS

## DONE

"@ | Set-Content -LiteralPath $p -Encoding UTF8
    return $p
}

function Read-Plan {
    param([string]$P)
    if (-not (Test-Path $P)) { return @() }
    Get-Content -LiteralPath $P -Encoding UTF8
}

function Move-Row {
    param([string]$Lane, [string]$Id, [string]$FromSection, [string]$ToSection, [string]$EvidenceText = '')
    $p = Ensure-Plan -L $Lane
    $lines = @(Read-Plan -P $p)
    $newLines = @()
    $rowText = $null
    $inFrom = $false
    foreach ($ln in $lines) {
        if ($ln -match "^## $FromSection$") { $inFrom = $true; $newLines += $ln; continue }
        if ($ln -match "^## ") { $inFrom = $false }
        if ($inFrom -and $ln -match "^- \[[ x]\] $([Regex]::Escape($Id))") {
            $rowText = $ln
            continue
        }
        $newLines += $ln
    }
    if (-not $rowText) { Write-Error "no row $Id in $FromSection"; exit 2 }
    # Update checkbox state for done
    if ($ToSection -eq 'DONE') {
        $rowText = $rowText -replace '^- \[ \]', '- [x]'
        if ($EvidenceText) { $rowText += "  // evidence: $EvidenceText" }
    }
    # Insert under target section
    $finalLines = @()
    $inserted = $false
    foreach ($ln in $newLines) {
        $finalLines += $ln
        if (-not $inserted -and $ln -match "^## $ToSection$") {
            $finalLines += $rowText
            $inserted = $true
        }
    }
    if (-not $inserted) { Write-Error "target section $ToSection not found"; exit 2 }
    Set-Content -LiteralPath $p -Value $finalLines -Encoding UTF8
}

switch ($Action) {
    'Bootstrap' {
        if (-not $Lane) { Write-Error "Bootstrap requires -Lane"; exit 2 }
        $p = Ensure-Plan -L $Lane
        Write-Output "plan: $p"
    }
    'Add' {
        if (-not $Lane -or -not $Task) { Write-Error "Add requires -Lane + -Task"; exit 2 }
        $p = Ensure-Plan -L $Lane
        $ts = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $row = "- [ ] $ts :: $Priority :: $Task"
        $lines = @(Read-Plan -P $p)
        $out = @()
        $inserted = $false
        foreach ($ln in $lines) {
            $out += $ln
            if (-not $inserted -and $ln -match '^## TODO$') {
                $out += $row
                $inserted = $true
            }
        }
        Set-Content -LiteralPath $p -Value $out -Encoding UTF8
        Write-Output "added id=$ts"
    }
    'Start' {
        if (-not $Lane -or -not $Id) { Write-Error "Start requires -Lane + -Id"; exit 2 }
        Move-Row -Lane $Lane -Id $Id -FromSection 'TODO' -ToSection 'IN-PROGRESS'
        Write-Output "started id=$Id"
    }
    'Done' {
        if (-not $Lane -or -not $Id) { Write-Error "Done requires -Lane + -Id"; exit 2 }
        if (-not $Evidence) { Write-Error "Done requires -Evidence (commit-sha / path / smoke output)"; exit 2 }
        Move-Row -Lane $Lane -Id $Id -FromSection 'IN-PROGRESS' -ToSection 'DONE' -EvidenceText $Evidence
        Write-Output "done id=$Id"
    }
    'List' {
        if (-not $Lane) { Write-Error "List requires -Lane"; exit 2 }
        $p = Get-PlanPath $Lane
        if (-not (Test-Path $p)) { Write-Output "(no plan for $Lane)"; return }
        if ($Status -eq 'all') { Get-Content -LiteralPath $p -Encoding UTF8 | Write-Output; return }
        $secMap = @{ 'todo' = 'TODO'; 'in-progress' = 'IN-PROGRESS'; 'done' = 'DONE' }
        $target = $secMap[$Status]
        $inSec = $false
        Get-Content -LiteralPath $p -Encoding UTF8 | ForEach-Object {
            if ($_ -match "^## $target$") { $inSec = $true; Write-Output $_; return }
            if ($_ -match '^## ') { $inSec = $false }
            if ($inSec -and $_ -match '^- \[') { Write-Output $_ }
        }
    }
    'Tally' {
        $files = if ($Lane) { @(Get-PlanPath $Lane) | Where-Object { Test-Path $_ } } else { Get-ChildItem -Path $PlansDir -Filter '*.md' | ForEach-Object { $_.FullName } }
        Write-Output "----- lane-plan tally -----"
        $tot = @{ todo = 0; inprog = 0; done = 0 }
        foreach ($f in $files) {
            $laneName = [System.IO.Path]::GetFileNameWithoutExtension($f)
            $todo = 0; $inprog = 0; $done = 0; $cur = ''
            Get-Content -LiteralPath $f -Encoding UTF8 | ForEach-Object {
                if ($_ -match '^## (TODO|IN-PROGRESS|DONE)$') { $cur = $Matches[1] }
                elseif ($_ -match '^- \[') {
                    switch ($cur) {
                        'TODO'        { $todo++ }
                        'IN-PROGRESS' { $inprog++ }
                        'DONE'        { $done++ }
                    }
                }
            }
            $tot.todo += $todo; $tot.inprog += $inprog; $tot.done += $done
            "{0,-22}  todo={1,3} in-progress={2,3} done={3,3}" -f $laneName, $todo, $inprog, $done
        }
        "{0,-22}  todo={1,3} in-progress={2,3} done={3,3}" -f 'TOTAL', $tot.todo, $tot.inprog, $tot.done
    }
}
