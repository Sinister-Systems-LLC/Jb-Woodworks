# bot-lifecycle.ps1 — refcount-based sleep/wake manager for local MCP bots
# Author: RKOJ-ELENO :: 2026-05-24
#
# Purpose:
#   Operator 19:17Z: "make sure when our agents are closed that everything that
#   agent is using is closed aswell. UNLESS another agent is using something from
#   that. then you wait until its done then close. do that with all things like
#   our local agents have them sleep, turn off overall just be efficent and then
#   seamless awaken when they are needed."
#
#   Solution: refcount per bot. Acquire on need (incref, spawn if asleep),
#   Release on done (decref, mark sleepable if 0). Sweep periodically.
#
# State: _shared-memory/bot-lifecycle.json
#   {
#     "bots": {
#       "<bot-name>": {
#         "state": "asleep|awake|spawning|terminating",
#         "refcount": <int>,
#         "users": ["slug1", "slug2", ...],
#         "pid": <int|null>,
#         "spawned_utc": "...",
#         "last_used_utc": "...",
#         "idle_since_utc": "...|null",
#         "wake_cmd": "...",
#         "sleep_after_idle_sec": 300
#       }, ...
#     }
#   }
#
# Actions:
#   Acquire  -Bot -Slug [-WakeCmd]    incref; awakens if asleep (operator can wire WakeCmd later)
#   Release  -Bot -Slug               decref; if refcount=0 mark idle_since
#   Sweep    [-MaxIdleSec 300]        emit list of bots idle past threshold (caller chooses to kill)
#   Status                            full state dump
#   List                              compact table view
#
# Composes with mesh-coordinator.ps1 (fleet-mesh-foundation set), bot-fleet-quick-reference.md.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Acquire','Release','Sweep','Status','List')]
    [string]$Action,

    [string]$Bot = '',
    [string]$Slug = '',
    [string]$WakeCmd = '',
    [int]$MaxIdleSec = 300,
    [int]$SleepAfterIdleSec = 300,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$StatePath = Join-Path $SanctumRoot '_shared-memory\bot-lifecycle.json'

function Utc-Now { return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") }
function Parse-Utc { param([string]$s) if (-not $s) { return $null }; return [DateTime]::Parse($s).ToUniversalTime() }

function Load-State {
    if (-not (Test-Path $StatePath)) { return @{ bots = @{} } }
    $raw = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8
    if (-not $raw -or -not $raw.Trim()) { return @{ bots = @{} } }
    $obj = $raw | ConvertFrom-Json
    # Convert to hashtable for mutation
    $H = @{ bots = @{} }
    if ($obj.bots) {
        $obj.bots.PSObject.Properties | ForEach-Object {
            $bH = @{}
            $_.Value.PSObject.Properties | ForEach-Object { $bH[$_.Name] = $_.Value }
            # Users: ensure array
            if ($bH.users -and -not ($bH.users -is [array])) { $bH.users = @($bH.users) }
            if (-not $bH.users) { $bH.users = @() }
            $H.bots[$_.Name] = $bH
        }
    }
    return $H
}

function Save-State { param($State)
    $json = $State | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText($StatePath, $json, [System.Text.UTF8Encoding]::new($false))
}

function Ensure-Bot { param($State, [string]$Name, [string]$WakeCmd, [int]$SleepAfter)
    if (-not $State.bots.ContainsKey($Name)) {
        $State.bots[$Name] = @{
            state                 = 'asleep'
            refcount              = 0
            users                 = @()
            pid                   = $null
            spawned_utc           = ''
            last_used_utc         = ''
            idle_since_utc        = $null
            wake_cmd              = $WakeCmd
            sleep_after_idle_sec  = $SleepAfter
        }
    }
    return $State.bots[$Name]
}

switch ($Action) {

    'Acquire' {
        if (-not $Bot -or -not $Slug) { Write-Host "ERR: -Bot and -Slug required"; exit 2 }
        $state = Load-State
        $b = Ensure-Bot $state $Bot $WakeCmd $SleepAfterIdleSec
        # Idempotent: same slug acquiring twice does not double-count
        if ($b.users -notcontains $Slug) {
            $b.users = @($b.users) + @($Slug)
            $b.refcount = [int]$b.refcount + 1
        }
        $b.last_used_utc = Utc-Now
        $b.idle_since_utc = $null
        if ($b.state -eq 'asleep') {
            $b.state = if ($b.wake_cmd) { 'spawning' } else { 'awake' }
            $b.spawned_utc = Utc-Now
        }
        Save-State $state
        Write-Host "OK: $Bot acquired by $Slug (refcount=$($b.refcount), state=$($b.state))"
        if ($b.state -eq 'spawning' -and $b.wake_cmd) {
            Write-Host "    wake_cmd ready: $($b.wake_cmd)"
        }
        exit 0
    }

    'Release' {
        if (-not $Bot -or -not $Slug) { Write-Host "ERR: -Bot and -Slug required"; exit 2 }
        $state = Load-State
        if (-not $state.bots.ContainsKey($Bot)) { Write-Host "NOTFOUND: bot $Bot unknown"; exit 1 }
        $b = $state.bots[$Bot]
        if ($b.users -notcontains $Slug) { Write-Host "NOOP: $Slug never acquired $Bot"; exit 0 }
        $b.users = @($b.users | Where-Object { $_ -ne $Slug })
        $b.refcount = [int]$b.refcount - 1
        if ($b.refcount -le 0) {
            $b.refcount = 0
            $b.idle_since_utc = Utc-Now
            # State stays 'awake' until Sweep decides to put it back to 'asleep'
        }
        Save-State $state
        Write-Host "OK: $Bot released by $Slug (refcount=$($b.refcount), users=[$(($b.users) -join ',')])"
        exit 0
    }

    'Sweep' {
        $state = Load-State
        $cutoff = (Get-Date).ToUniversalTime().AddSeconds(-$MaxIdleSec)
        $sleepable = @()
        foreach ($name in @($state.bots.Keys)) {
            $b = $state.bots[$name]
            if ($b.refcount -le 0 -and $b.idle_since_utc) {
                $idleSince = Parse-Utc $b.idle_since_utc
                if ($idleSince -and $idleSince -lt $cutoff) {
                    $sleepable += [PSCustomObject]@{
                        Bot     = $name
                        Pid     = $b.pid
                        IdleFor = [int]((Get-Date).ToUniversalTime() - $idleSince).TotalSeconds
                    }
                    # Flip to asleep marker; caller is responsible for actually killing the PID
                    $b.state = 'asleep'
                    $b.pid = $null
                }
            }
        }
        Save-State $state
        if ($sleepable.Count -eq 0) { Write-Host "OK: nothing to sleep (max-idle ${MaxIdleSec}s)"; exit 0 }
        Write-Host "SLEEPABLE: $($sleepable.Count) bot(s) idle past ${MaxIdleSec}s:"
        $sleepable | Format-Table -AutoSize | Out-String | Write-Host
        exit 0
    }

    'Status' {
        $state = Load-State
        $state | ConvertTo-Json -Depth 6 | Write-Host
        exit 0
    }

    'List' {
        $state = Load-State
        if ($state.bots.Count -eq 0) { Write-Host "no bots tracked"; exit 0 }
        $rows = @()
        foreach ($name in $state.bots.Keys) {
            $b = $state.bots[$name]
            $rows += [PSCustomObject]@{
                Bot      = $name
                State    = $b.state
                RefCount = $b.refcount
                Users    = ($b.users) -join ','
                LastUsed = $b.last_used_utc
            }
        }
        $rows | Sort-Object Bot | Format-Table -AutoSize | Out-String | Write-Host
        exit 0
    }
}
