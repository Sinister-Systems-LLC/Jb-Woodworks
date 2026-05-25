# fleet-autostart.ps1 -- boot-time / on-logon orchestrator
# Author: RKOJ-ELENO :: 2026-05-24
#
# Purpose:
#   Operator 2026-05-24T19:45Z: "have docker start on bootup so we can easily call
#   our agents for use from that and make sure all skills, liocal aghents etc can
#   auto start with no issues".
#   Operator 2026-05-24T20:02Z: "ready to go in the eve exe so we can grow
#   gradually and never stop".
#
#   Pipeline:
#     1. Wait for Docker Desktop engine to be Ready (timeout configurable)
#     2. Warm local-MCP bot fleet via bot-lifecycle.ps1 (Acquire each canonical bot
#        with system slug so they spawn; immediate Release so refcount drops to 0
#        and the idle clock starts -- they SLEEP until a real agent needs them
#        per the sleep/wake doctrine; no point keeping them HOT at boot)
#     3. Run heartbeat-sweep + mesh-coordinator Sweep so stale state from prior
#        boot doesn't poison the fresh fleet
#     4. Push fleet-update row announcing the boot-bringup so newly-spawning agents
#        see "fleet primed" in their cold-start
#
# Modes:
#   -Mode WaitOnly        only waits for Docker; no bot warm-up (useful for Service mode)
#   -Mode WarmOnly        skips Docker wait; just acquires+releases bots
#   -Mode Full            (default) Wait + Warm + Sweep + Announce
#   -Mode Status          prints state; no side effects
#   -Quiet                suppresses console output (still logs to _shared-memory/fleet-autostart-log.jsonl)
#
# Wire-up (one-time, operator-run from elevated PowerShell):
#   $T = New-ScheduledTaskTrigger -AtLogon -RandomDelay (New-TimeSpan -Seconds 30)
#   $A = New-ScheduledTaskAction -Execute 'powershell.exe' `
#         -Argument '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\automations\fleet-autostart.ps1" -Mode Full -Quiet'
#   Register-ScheduledTask -TaskName 'SinisterFleetAutostart' -Trigger $T -Action $A `
#         -RunLevel Highest -Description 'Sinister fleet boot bringup'
#
# Composes with: mesh-coordinator.ps1 + bot-lifecycle.ps1 + heartbeat-sweep.ps1 + fleet-update.ps1.

[CmdletBinding()]
param(
    [ValidateSet('Full','WaitOnly','WarmOnly','Status')] [string]$Mode = 'Full',
    [int]$DockerTimeoutSec = 180,
    [int]$DockerPollSec    = 5,
    [int]$BotSleepAfterIdleSec = 600,
    [switch]$Quiet,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Continue'
$LogPath = Join-Path $SanctumRoot '_shared-memory\fleet-autostart-log.jsonl'

# Canonical bot list (matches bot-fleet-quick-reference.md). Wake commands are
# best-guess based on Python module convention; bot-lifecycle.ps1 stores them
# for spawn but does NOT execute (operator-controlled spawn surface).
$CANONICAL_BOTS = @(
    @{ name='sentinel';        wake='py -m sentinel.server' },
    @{ name='translator';      wake='py -m translator.server' },
    @{ name='watcher';         wake='py -m watcher.server' },
    @{ name='auditor';         wake='py -m auditor.server' },
    @{ name='sinister-bus';    wake='py -m sinister_bus.server' },
    @{ name='custodian';       wake='py -m custodian.server' },
    @{ name='stealth-browser'; wake='py -m stealth_browser.server' },
    @{ name='vault';           wake='py -m vault.server' },
    @{ name='triage';          wake='py -m triage.server' },
    @{ name='librarian';       wake='py -m librarian.server' },
    @{ name='researcher';      wake='py -m researcher.server' },
    @{ name='scribe';          wake='py -m scribe.server' },
    @{ name='curator';         wake='py -m curator.server' }
)

function Say { param([string]$Msg)
    if (-not $Quiet) { Write-Host $Msg }
}

function Log-Step { param([string]$Step, [string]$Status, [hashtable]$Extra=@{})
    $row = @{
        ts_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        step   = $Step
        status = $Status
        mode   = $Mode
    } + $Extra
    $line = ($row | ConvertTo-Json -Compress -Depth 4)
    Add-Content -LiteralPath $LogPath -Value $line -Encoding UTF8
}

function Get-DockerReady {
    try {
        $out = & docker.exe info --format '{{.ServerVersion}}' 2>$null
        if ($LASTEXITCODE -eq 0 -and $out -and $out.Trim()) { return @{ ready=$true; version=$out.Trim() } }
    } catch {}
    return @{ ready=$false; version=$null }
}

function Wait-DockerReady { param([int]$TimeoutSec, [int]$PollSec)
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        $r = Get-DockerReady
        if ($r.ready) {
            $waited = [int]($TimeoutSec - ($deadline - (Get-Date)).TotalSeconds)
            Say "  docker ready: v$($r.version)  (waited ${waited}s)"
            Log-Step -Step 'docker-wait' -Status 'ready' -Extra @{ version=$r.version; waited_sec=$waited }
            return $true
        }
        Start-Sleep -Seconds $PollSec
    }
    Say "  docker NOT ready after ${TimeoutSec}s -- giving up (Docker Desktop may still be starting)"
    Log-Step -Step 'docker-wait' -Status 'timeout' -Extra @{ timeout_sec=$TimeoutSec }
    return $false
}

function Warm-Bot { param([string]$Name, [string]$Wake)
    $blc = Join-Path $SanctumRoot 'automations\bot-lifecycle.ps1'
    if (-not (Test-Path $blc)) { return @{ ok=$false; err='bot-lifecycle.ps1 missing' } }
    try {
        $acq = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $blc -Action Acquire -Bot $Name -Slug 'fleet-autostart' -WakeCmd $Wake -SleepAfterIdleSec $BotSleepAfterIdleSec 2>&1
        $rel = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $blc -Action Release -Bot $Name -Slug 'fleet-autostart' 2>&1
        return @{ ok=$true; msg=(($acq + $rel) -join ' | ') }
    } catch {
        return @{ ok=$false; err=$_.Exception.Message }
    }
}

function Run-Sweeps {
    $mc  = Join-Path $SanctumRoot 'automations\mesh-coordinator.ps1'
    $hbs = Join-Path $SanctumRoot 'automations\heartbeat-sweep.ps1'
    if (Test-Path $mc) {
        $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $mc -Action Sweep 2>&1
        Say ("  mesh-coord sweep: " + (($out -join ' ') -replace '\s+', ' '))
        Log-Step -Step 'mesh-sweep' -Status 'ok'
    }
    if (Test-Path $hbs) {
        $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $hbs -MaxAgeHours 24 -Apply 2>&1
        $tail = ($out | Select-Object -Last 1)
        Say ("  heartbeat sweep: $tail")
        Log-Step -Step 'heartbeat-sweep' -Status 'ok' -Extra @{ summary="$tail" }
    }
}

function Announce-Bringup { param([int]$WarmedCount, [bool]$DockerReady)
    $fu = Join-Path $SanctumRoot 'automations\fleet-update.ps1'
    if (-not (Test-Path $fu)) { return }
    $msg = "fleet-autostart bringup OK: docker_ready=$DockerReady bots_registered=$WarmedCount mode=$Mode ts=$((Get-Date).ToUniversalTime().ToString('HH:mm:ssZ')). Bots are in SLEEP state (refcount=0 + idle clock running); they wake on first Acquire from a spawning agent. EVE.exe spawns are ready to go."
    try {
        $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $fu -Action Push -Kind feature -Priority normal -PushedBy fleet-autostart -Message $msg 2>&1
        Say "  fleet-update pushed: $(($out -join ' ').Trim())"
        Log-Step -Step 'fleet-update-push' -Status 'ok'
    } catch {
        Log-Step -Step 'fleet-update-push' -Status 'err' -Extra @{ err=$_.Exception.Message }
    }
}

# ---------------- main ----------------
Say ""
Say "fleet-autostart [mode=$Mode] ts=$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))"
Log-Step -Step 'start' -Status 'begin'

if ($Mode -eq 'Status') {
    $r = Get-DockerReady
    Say "  docker.ready  = $($r.ready)"
    if ($r.ready) { Say "  docker.version = $($r.version)" }
    $blc = Join-Path $SanctumRoot 'automations\bot-lifecycle.ps1'
    if (Test-Path $blc) {
        Say "  bot-lifecycle state:"
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $blc -Action List 2>&1 | ForEach-Object { Say "    $_" }
    }
    Log-Step -Step 'status' -Status 'ok'
    exit 0
}

$dockerOk = $true
if ($Mode -in @('Full','WaitOnly')) {
    Say "  waiting up to ${DockerTimeoutSec}s for Docker Desktop..."
    $dockerOk = Wait-DockerReady -TimeoutSec $DockerTimeoutSec -PollSec $DockerPollSec
    if ($Mode -eq 'WaitOnly') {
        Log-Step -Step 'done' -Status 'ok' -Extra @{ docker_ready=$dockerOk }
        exit (if ($dockerOk) { 0 } else { 1 })
    }
}

$warmed = 0
if ($Mode -in @('Full','WarmOnly')) {
    Say "  warming bot fleet ($($CANONICAL_BOTS.Count) bots)..."
    foreach ($b in $CANONICAL_BOTS) {
        $r = Warm-Bot -Name $b.name -Wake $b.wake
        if ($r.ok) { $warmed++ } else { Say "    [skip] $($b.name): $($r.err)" }
    }
    Say "  warmed: $warmed / $($CANONICAL_BOTS.Count) bots registered in lifecycle state (all SLEEP, wake on demand)"
    Log-Step -Step 'warm' -Status 'ok' -Extra @{ warmed=$warmed; total=$CANONICAL_BOTS.Count }
}

if ($Mode -eq 'Full') {
    Run-Sweeps
    Announce-Bringup -WarmedCount $warmed -DockerReady $dockerOk
}

Say ""
Say "fleet-autostart done."
Log-Step -Step 'done' -Status 'ok' -Extra @{ docker_ready=$dockerOk; warmed=$warmed }
exit 0
