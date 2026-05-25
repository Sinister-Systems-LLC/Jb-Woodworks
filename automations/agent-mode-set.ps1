# agent-mode-set.ps1 — flip swarm/loop mode on an already-running agent (or all agents).
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24:
#   "i need swarm and loop options in bat file per project as well or a way to do
#    it in the agents i have open"
#
# What this does (two layers, both fire):
#   1. Writes _shared-memory/agent-modes/<slug>.json  — the durable mode-flag file
#      future tooling (heartbeat-write, per-turn hook) can read.
#   2. Logs an operator-utterance via log-operator-utterance.ps1 with tag "mode-flip"
#      and the target slug. Cold-start step 8 + Rule 9 inbox-poll mean every agent
#      surfaces fresh operator-utterances at turn-open and adopts the directive.
#
# Usage:
#   powershell -File agent-mode-set.ps1 -Slug kernel-apk -Swarm on -Loop on
#   powershell -File agent-mode-set.ps1 -Slug all -Swarm off -Loop on
#   powershell -File agent-mode-set.ps1 -Slug sanctum -Swarm toggle
#
# Values for -Swarm / -Loop: on | off | toggle | (omitted = no change)

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$Slug,
    [ValidateSet('on','off','toggle','')] [string]$Swarm = '',
    [ValidateSet('on','off','toggle','')] [string]$Loop  = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$Reason = ''
)

$ErrorActionPreference = 'Stop'

if (-not $Swarm -and -not $Loop) {
    Write-Host "Nothing to do (-Swarm and -Loop both omitted). Pass at least one." -ForegroundColor Yellow
    exit 1
}

$ModesDir = Join-Path $SanctumRoot '_shared-memory\agent-modes'
if (-not (Test-Path $ModesDir)) { New-Item -ItemType Directory -Path $ModesDir -Force | Out-Null }

function Resolve-Slugs {
    param([string]$Requested)
    if ($Requested -eq 'all' -or $Requested -eq '*') {
        $hbDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
        if (-not (Test-Path $hbDir)) { return @() }
        return @(Get-ChildItem -Path $hbDir -Filter '*.json' -File | ForEach-Object { $_.BaseName })
    }
    return @($Requested)
}

function Apply-Change {
    param([bool]$Current, [string]$Op)
    switch ($Op) {
        'on'     { return $true }
        'off'    { return $false }
        'toggle' { return (-not $Current) }
        default  { return $Current }
    }
}

$targets = Resolve-Slugs -Requested $Slug
if ($targets.Count -eq 0) {
    Write-Host "No slugs resolved from '$Slug'. (heartbeats dir empty?)" -ForegroundColor Yellow
    exit 1
}

$nowUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$summaryRows = @()

foreach ($s in $targets) {
    $file = Join-Path $ModesDir "$s.json"
    $prev = @{ swarm = $false; loop = $false }
    if (Test-Path $file) {
        try {
            $raw = Get-Content $file -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($raw.PSObject.Properties.Name -contains 'swarm') { $prev.swarm = [bool]$raw.swarm }
            if ($raw.PSObject.Properties.Name -contains 'loop')  { $prev.loop  = [bool]$raw.loop }
        } catch {}
    }
    $next = @{
        swarm = (Apply-Change -Current $prev.swarm -Op $Swarm)
        loop  = (Apply-Change -Current $prev.loop  -Op $Loop)
        set_by_operator_at_utc = $nowUtc
        set_via = 'agent-mode-set.ps1'
        slug = $s
        reason = $Reason
    }
    $json = $next | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($file, $json, [System.Text.UTF8Encoding]::new($false))
    $summaryRows += [PSCustomObject]@{
        slug = $s
        swarm_prev = $prev.swarm; swarm_next = $next.swarm
        loop_prev  = $prev.loop;  loop_next  = $next.loop
    }
}

# Layer 2: log operator-utterance so already-running agents surface it.
$slugList = ($summaryRows | ForEach-Object { $_.slug }) -join ','
$modeDescParts = @()
if ($Swarm) { $modeDescParts += "swarm=$Swarm" }
if ($Loop)  { $modeDescParts += "loop=$Loop" }
$modeDesc = $modeDescParts -join ' '
$utterText = "[mode-flip] target_slugs=[$slugList]  $modeDesc"
if ($Reason) { $utterText += "  reason='$Reason'" }

$logScript = Join-Path $SanctumRoot 'automations\log-operator-utterance.ps1'
if (Test-Path $logScript) {
    try {
        & $logScript -SessionSlug 'agent-mode-set' -MessageFull $utterText -Tags "mode-flip,$slugList" | Out-Null
        Write-Host "  logged operator-utterance for mode flip." -ForegroundColor DarkGray
    } catch {
        Write-Host "  (warn) operator-utterance log failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Mode flip applied (durable + utterance broadcast):" -ForegroundColor Cyan
$summaryRows | Format-Table -AutoSize
Write-Host ""
Write-Host "Affected agents will surface the directive on their next turn-open (per cold-start step 8 + Rule 9 inbox-poll)."
Write-Host "Mode files written to: $ModesDir"
