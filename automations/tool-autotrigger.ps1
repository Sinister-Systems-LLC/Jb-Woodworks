# tool-autotrigger.ps1 -- config-driven runner for cron-style sanctum tools
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T21:32Z (verbatim):
#   "most if not all of these tools to be automatic as to if and when the agent
#    needs or wants to use them"
#
# Reads _shared-memory/tool-autotrigger-config.json + fires each tool whose
# `schedule: cron:Nm/Nh/Nd` interval has elapsed since last fire. State at
# _shared-memory/tool-autotrigger-state.json (last-fire per tool).
#
# Schedule registration (one-time, operator OR system-script):
#   schtasks /Create /TN SinisterToolAutotrigger /SC MINUTE /MO 15 /F /RL LIMITED \
#     /TR "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass \
#          -File \"D:\Sinister Sanctum\automations\tool-autotrigger.ps1\" -Action Tick"
#
# Actions:
#   Tick     fire any tools whose cron interval has elapsed
#   Status   show last-fire per tool + next-fire estimate
#   Force    -Tool <name>  fire one tool immediately (ignores schedule)
#   List     show config (active tools + their schedules)

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [ValidateSet('Tick','Status','Force','List')] [string]$Action,
    [string]$Tool = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Continue'
$ConfigPath = Join-Path $SanctumRoot '_shared-memory\tool-autotrigger-config.json'
$StatePath  = Join-Path $SanctumRoot '_shared-memory\tool-autotrigger-state.json'
$AutoDir    = Join-Path $SanctumRoot 'automations'

function Utc-Now { return (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ') }
function Parse-Utc { param([string]$s) try { return [DateTime]::Parse($s).ToUniversalTime() } catch { return $null } }

function Parse-Schedule { param([string]$Sched)
    # cron:10m | cron:24h | cron:7d | event:* (events return $null seconds)
    if (-not ($Sched -match '^cron:(\d+)([mhd])$')) { return $null }
    $n = [int]$Matches[1]
    $unit = $Matches[2]
    switch ($unit) {
        'm' { return $n * 60 }
        'h' { return $n * 3600 }
        'd' { return $n * 86400 }
    }
    return $null
}

function Load-Config {
    if (-not (Test-Path $ConfigPath)) { Write-Host "ERR: $ConfigPath missing"; exit 1 }
    return (Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json)
}
function Load-State {
    if (-not (Test-Path $StatePath)) { return @{ last_fire = @{} } }
    $raw = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8
    if (-not $raw -or -not $raw.Trim()) { return @{ last_fire = @{} } }
    $obj = $raw | ConvertFrom-Json
    $h = @{ last_fire = @{} }
    if ($obj.last_fire) {
        $obj.last_fire.PSObject.Properties | ForEach-Object { $h.last_fire[$_.Name] = $_.Value }
    }
    return $h
}
function Save-State { param($State)
    $json = $State | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText($StatePath, $json, [System.Text.UTF8Encoding]::new($false))
}

function Tool-Script { param([string]$ToolName)
    return Join-Path $AutoDir ($ToolName + '.ps1')
}

function Fire-Tool { param($Trigger, $State)
    $script = Tool-Script $Trigger.tool
    if (-not (Test-Path $script)) {
        Write-Host ("  [skip] script missing: " + $script)
        return $false
    }
    $argList = @($Trigger.args)
    Write-Host ("  [fire] " + $Trigger.tool + "  args: " + ($argList -join ' '))
    try {
        $out = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $script @argList 2>&1 | Out-String
        $tail = ($out -split "`n" | Select-Object -Last 3) -join ' | '
        Write-Host ("         exit=$LASTEXITCODE  tail: " + $tail.Trim())
        $State.last_fire[$Trigger.tool] = Utc-Now
        Save-State $State
        return $true
    } catch {
        Write-Host ("         FAIL: " + $_.Exception.Message)
        return $false
    }
}

switch ($Action) {

    'Tick' {
        $cfg = Load-Config
        $state = Load-State
        $cronTriggers = @($cfg.triggers | Where-Object { $_.active -eq $true -and $_.schedule -like 'cron:*' })
        Write-Host ("tool-autotrigger TICK :: " + $cronTriggers.Count + " active cron triggers")
        $fired = 0
        foreach ($t in $cronTriggers) {
            $intervalSec = Parse-Schedule $t.schedule
            if ($intervalSec -eq $null) { continue }
            $last = $state.last_fire[$t.tool]
            $shouldFire = $false
            if (-not $last) {
                $shouldFire = $true
            } else {
                $lastDt = Parse-Utc $last
                if ($lastDt) {
                    $elapsedSec = ((Get-Date).ToUniversalTime() - $lastDt).TotalSeconds
                    if ($elapsedSec -ge $intervalSec) { $shouldFire = $true }
                } else {
                    $shouldFire = $true
                }
            }
            if ($shouldFire) {
                if (Fire-Tool $t $state) { $fired++ }
            }
        }
        Write-Host ("tool-autotrigger DONE  fired=$fired / " + $cronTriggers.Count)
        exit 0
    }

    'Status' {
        $cfg = Load-Config
        $state = Load-State
        $rows = @()
        foreach ($t in $cfg.triggers) {
            $last = $state.last_fire[$t.tool]
            $intervalSec = Parse-Schedule $t.schedule
            $nextStr = '(event)'
            if ($intervalSec -ne $null -and $last) {
                $lastDt = Parse-Utc $last
                if ($lastDt) {
                    $nextDt = $lastDt.AddSeconds($intervalSec)
                    $nextStr = $nextDt.ToString('yyyy-MM-ddTHH:mm:ssZ')
                }
            } elseif ($intervalSec -ne $null) {
                $nextStr = '(never fired)'
            }
            $obj = New-Object PSObject
            $obj | Add-Member -MemberType NoteProperty -Name 'Tool' -Value $t.tool
            $obj | Add-Member -MemberType NoteProperty -Name 'Schedule' -Value $t.schedule
            $obj | Add-Member -MemberType NoteProperty -Name 'Active' -Value $t.active
            $lastDisplay = if ($last) { $last } else { '(never)' }
            $obj | Add-Member -MemberType NoteProperty -Name 'LastFire' -Value $lastDisplay
            $obj | Add-Member -MemberType NoteProperty -Name 'NextFire' -Value $nextStr
            $rows += $obj
        }
        $rows | Format-Table -AutoSize | Out-String | Write-Host
        exit 0
    }

    'Force' {
        if (-not $Tool) { Write-Host "ERR: -Tool required"; exit 2 }
        $cfg = Load-Config
        $t = @($cfg.triggers | Where-Object { $_.tool -eq $Tool }) | Select-Object -First 1
        if (-not $t) { Write-Host "NOTFOUND tool=$Tool in config"; exit 1 }
        $state = Load-State
        if (Fire-Tool $t $state) { Write-Host "OK: forced $Tool"; exit 0 } else { exit 1 }
    }

    'List' {
        $cfg = Load-Config
        Write-Host ("tool-autotrigger-config :: " + $cfg.triggers.Count + " triggers")
        Write-Host ""
        foreach ($t in $cfg.triggers) {
            $tag = if ($t.active) { '[ACTIVE]' } else { '[off]   ' }
            Write-Host ("  $tag $($t.tool)  schedule=$($t.schedule)  purpose=$($t.purpose)")
        }
        Write-Host ""
        Write-Host ("Queued for event-hooks next iter: " + $cfg.queued_for_event_hooks_next_iter.Count + " triggers")
        exit 0
    }
}
