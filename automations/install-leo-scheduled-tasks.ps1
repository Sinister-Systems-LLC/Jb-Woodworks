# install-leo-scheduled-tasks.ps1 - register every fleet scheduled task in one shot
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator hard-canonical 2026-05-25 ~01:35Z:
#   "make sure in the exe auto setup for leo we make sure mcp setup.
#    all bots docker installed and ready for use all shit like that we do.
#    the autonomy grant all taht"
#
# Wraps each install-*.ps1 task installer in sequence + reports PASS/FAIL.
# Idempotent (each installer is itself idempotent). -DryRun lists what would
# happen without actually registering.
#
# Tasks registered:
#   SinisterSanctumAutoPush  - push current branch every 30 min
#   SinisterAccountWatchdog  - poll for rate-limit recovery every 5 min
#   SinisterOAuthHealthPoll  - probe Anthropic OAuth health every 5 min
#   SinisterLinkPoll         - poll cross-machine state every 60s when linked
#   SinisterSanctumDailyBackup - daily auto-backup
#   SinisterSanctumDoctor    - daily sinister-doctor sweep
#   SinisterMemoryConsolidate - hourly memory consolidation
#
# Usage:
#   powershell -File install-leo-scheduled-tasks.ps1                 (interactive)
#   powershell -File install-leo-scheduled-tasks.ps1 -DryRun         (list, no action)
#   powershell -File install-leo-scheduled-tasks.ps1 -Skip task1,task2
#   powershell -File install-leo-scheduled-tasks.ps1 -Only task1,task2
#   powershell -File install-leo-scheduled-tasks.ps1 -UninstallAll   (remove all)

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$UninstallAll,
    [string[]]$Skip = @(),
    [string[]]$Only = @(),
    [string]$SanctumRoot = ''
)

$ErrorActionPreference = 'Continue'

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}
if (-not (Test-Path $SanctumRoot)) {
    Write-Host "  [FAIL] Sanctum root not found: $SanctumRoot" -ForegroundColor Red
    exit 2
}

$setupDir = Join-Path $SanctumRoot '_shared-memory\setup'
if (-not (Test-Path $setupDir)) { New-Item -ItemType Directory -Path $setupDir -Force | Out-Null }
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$logFile = Join-Path $setupDir ("leo-tasks-install-$ts.log")

function Write-Log {
    param([string]$Msg, [string]$Level = 'INFO')
    $line = ((Get-Date).ToUniversalTime().ToString('o')) + " [$Level] " + $Msg
    try { Add-Content -Path $logFile -Value $line -Encoding UTF8 } catch {}
    $col = switch ($Level) {
        'OK'    { 'Green' }
        'WARN'  { 'Yellow' }
        'FAIL'  { 'Red' }
        'STEP'  { 'White' }
        default { 'Gray' }
    }
    Write-Host ('  ' + $Msg) -ForegroundColor $col
}

# --- Banner ----------------------------------------------------------------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   INSTALL LEO SCHEDULED TASKS :: every fleet poller' -ForegroundColor White
if ($DryRun)       { Write-Host '   [DRY-RUN] no schtasks calls will execute' -ForegroundColor Cyan }
if ($UninstallAll) { Write-Host '   [UNINSTALL] every task will be removed' -ForegroundColor Yellow }
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''
Write-Log ("session-start :: sanctum=$SanctumRoot dryrun=$DryRun uninstall=$UninstallAll") 'STEP'

# Each task: name + installer script + supports -Uninstall flag
$tasks = @(
    @{
        name = 'SinisterSanctumAutoPush'
        installer = (Join-Path $SanctumRoot 'automations\install-auto-push-task.ps1')
        uninstaller = (Join-Path $SanctumRoot 'automations\uninstall-auto-push-task.ps1')
        purpose = 'auto-push current branch every 30 min'
    },
    @{
        name = 'SinisterAccountWatchdog'
        installer = (Join-Path $SanctumRoot 'automations\install-account-watchdog-task.ps1')
        uninstaller = $null
        purpose = 'rate-limit recovery poll every 5 min'
    },
    @{
        name = 'SinisterOAuthHealthPoll'
        installer = (Join-Path $SanctumRoot 'automations\install-oauth-health-poller.ps1')
        uninstaller = $null
        purpose = 'Anthropic OAuth health every 5 min'
        uninstallFlag = '-Uninstall'
    },
    @{
        name = 'SinisterLinkPoll'
        installer = (Join-Path $SanctumRoot 'automations\install-sinister-link-poller.ps1')
        uninstaller = $null
        purpose = 'cross-machine state poll every 60s'
        uninstallFlag = '-Uninstall'
    },
    @{
        name = 'SinisterSanctumDailyBackup'
        installer = (Join-Path $SanctumRoot 'automations\install-sanctum-daily-task.ps1')
        uninstaller = $null
        purpose = 'daily auto-backup'
    },
    @{
        name = 'SinisterSanctumDoctor'
        installer = (Join-Path $SanctumRoot 'automations\install-sinister-doctor-task.ps1')
        uninstaller = $null
        purpose = 'daily sinister-doctor sweep'
    },
    @{
        name = 'SinisterMemoryConsolidate'
        installer = (Join-Path $SanctumRoot 'automations\install-memory-consolidate-task.ps1')
        uninstaller = $null
        purpose = 'hourly memory consolidation'
    }
)

# Apply Only / Skip filters
if ($Only.Count -gt 0) {
    $tasks = @($tasks | Where-Object { $Only -contains $_.name })
}
if ($Skip.Count -gt 0) {
    $tasks = @($tasks | Where-Object { $Skip -notcontains $_.name })
}

$results = [ordered]@{}

foreach ($t in $tasks) {
    $name = $t.name
    Write-Host ''
    Write-Log ("---- task: $name ----") 'STEP'
    Write-Log ("purpose: " + $t.purpose) 'INFO'

    $installer = $t.installer
    if (-not (Test-Path $installer)) {
        Write-Log ("installer missing: $installer") 'WARN'
        $results[$name] = 'NO-INSTALLER'
        continue
    }

    if ($DryRun) {
        if ($UninstallAll) {
            if ($t.uninstaller) {
                Write-Log "[DRY-RUN] would run: powershell -File $($t.uninstaller)" 'INFO'
            } elseif ($t.uninstallFlag) {
                Write-Log "[DRY-RUN] would run: powershell -File $installer $($t.uninstallFlag)" 'INFO'
            } else {
                Write-Log "[DRY-RUN] would run: schtasks /Delete /TN $name /F" 'INFO'
            }
        } else {
            Write-Log "[DRY-RUN] would run: powershell -File $installer" 'INFO'
        }
        $results[$name] = 'DRY-RUN'
        continue
    }

    if ($UninstallAll) {
        try {
            if ($t.uninstaller -and (Test-Path $t.uninstaller)) {
                & powershell -NoProfile -ExecutionPolicy Bypass -File $t.uninstaller 2>&1 |
                    Tee-Object -Append -FilePath $logFile | Out-Null
            } elseif ($t.uninstallFlag) {
                & powershell -NoProfile -ExecutionPolicy Bypass -File $installer $t.uninstallFlag 2>&1 |
                    Tee-Object -Append -FilePath $logFile | Out-Null
            } else {
                & schtasks /Delete /TN $name /F 2>&1 | Out-Null
            }
            $results[$name] = if ($LASTEXITCODE -eq 0) { 'UNINSTALLED' } else { "UNINSTALL-EXIT-$LASTEXITCODE" }
            Write-Log ($results[$name]) (if ($LASTEXITCODE -eq 0) { 'OK' } else { 'WARN' })
        } catch {
            Write-Log ('uninstall threw: ' + $_.Exception.Message) 'FAIL'
            $results[$name] = 'UNINSTALL-ERR'
        }
        continue
    }

    # Install path
    try {
        Write-Log ("running: powershell -File $installer") 'STEP'
        & powershell -NoProfile -ExecutionPolicy Bypass -File $installer 2>&1 |
            Tee-Object -Append -FilePath $logFile | Out-Null
        $rc = $LASTEXITCODE
        if ($rc -eq 0) {
            Write-Log ('installer exit=0 OK') 'OK'
            $results[$name] = 'INSTALLED'
        } else {
            Write-Log ("installer exit=$rc (non-zero; review log)") 'WARN'
            $results[$name] = "EXIT-$rc"
        }
    } catch {
        Write-Log ('installer threw: ' + $_.Exception.Message) 'FAIL'
        $results[$name] = 'INSTALL-ERR'
    }
}

# --- Summary ---------------------------------------------------------------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   SUMMARY' -ForegroundColor White
Write-Host '  ============================================================' -ForegroundColor Magenta
foreach ($k in $results.Keys) {
    $v = $results[$k]
    $col = switch -Wildcard ($v) {
        'INSTALLED'      { 'Green' }
        'UNINSTALLED'    { 'Green' }
        'DRY-RUN'        { 'Cyan' }
        'NO-INSTALLER'   { 'Yellow' }
        'EXIT-*'         { 'Yellow' }
        '*ERR'           { 'Red' }
        default          { 'Gray' }
    }
    Write-Host ("    {0,-28} : {1}" -f $k, $v) -ForegroundColor $col
}
Write-Host ''
Write-Host ('  Log: ' + $logFile) -ForegroundColor DarkGray
Write-Host ''
Write-Log 'session-end' 'OK'
exit 0
