# RKOJ-ELENO :: 2026-05-23
# claude-account-watchdog.ps1 - Phase 3 of multi-account rotation.
#
# Runs every 5 min (scheduled task `SinisterAccountWatchdog`). Job:
#   1. Clear expired `rate_limited_until_utc` markers + log the recovery.
#   2. If we were in an all-limited state (sentinel file present) AND at least
#      one account is now available AND no claude.exe is running, fire the
#      `Sinister Start.bat --auto-resume` flow to bring the fleet back up.
#
# Designed to be FAST + IDEMPOTENT (well under 5s runtime). Never blocks.
# Logs to `_shared-memory/account-watchdog.log` (UTF-8, append-only).
#
# Install (operator-only): run `automations/install-account-watchdog-task.ps1`
# once to register the scheduled task. Watchdog file itself is never invoked
# directly from agent code -- only by Task Scheduler.

[CmdletBinding()]
param()

$ErrorActionPreference = 'Continue'   # never throw; watchdog must always finish
$WatchdogStartUtc = (Get-Date).ToUniversalTime()

# ----- locate Sanctum + dot-source the Phase 1 library ----------------------
$SanctumRoot = Split-Path -Parent $PSScriptRoot
if (-not $SanctumRoot -or -not (Test-Path $SanctumRoot)) {
    $SanctumRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
$LibPath          = Join-Path $SanctumRoot 'automations\claude-accounts.ps1'
$LogPath          = Join-Path $SanctumRoot '_shared-memory\account-watchdog.log'
$AllLimitedFlag   = Join-Path $SanctumRoot '_shared-memory\.all-accounts-were-limited'
$AutoResumeBat    = 'C:\Users\Zonia\Desktop\Sinister Start.bat'

function Write-WatchdogLog {
    param([string]$Message, [string]$Level = 'INFO')
    try {
        $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Add-Content -Path $LogPath -Value "[$ts] [$Level] $Message" -Encoding UTF8 -ErrorAction SilentlyContinue
    } catch {}
}

if (-not (Test-Path $LibPath)) {
    Write-WatchdogLog "lib missing at $LibPath; aborting" 'WARN'
    return
}

# Dot-source so we get Get-AccountsConfig, Save-AccountsConfig, etc.
try { . $LibPath } catch {
    Write-WatchdogLog "dot-source failed: $($_.Exception.Message)" 'ERROR'
    return
}

# ----- 1. clear expired rate-limit markers -----------------------------------
$cfg = $null
try { $cfg = Get-AccountsConfig } catch {
    Write-WatchdogLog "Get-AccountsConfig failed: $($_.Exception.Message)" 'ERROR'
    return
}

if (-not $cfg -or -not $cfg.accounts -or $cfg.accounts.Count -eq 0) {
    # no-op; watchdog has nothing to do
    return
}

$now = (Get-Date).ToUniversalTime()
$clearedAny = $false
foreach ($acct in $cfg.accounts) {
    if (-not $acct.rate_limited_until_utc) { continue }
    try {
        $until = [datetime]::Parse($acct.rate_limited_until_utc).ToUniversalTime()
        if ($until -le $now) {
            $acct.rate_limited_until_utc = $null
            $clearedAny = $true
            Write-WatchdogLog "account '$($acct.name)' rate-limit cleared (was until $($until.ToString('o')))" 'INFO'
        }
    } catch {
        # malformed timestamp - clear it defensively so we never get stuck
        $acct.rate_limited_until_utc = $null
        $clearedAny = $true
        Write-WatchdogLog "account '$($acct.name)' had malformed rate_limited_until_utc; cleared" 'WARN'
    }
}

if ($clearedAny) {
    try {
        $ok = Save-AccountsConfig -Config $cfg
        if (-not $ok) { Write-WatchdogLog 'Save-AccountsConfig returned false after clearing markers' 'WARN' }
    } catch {
        Write-WatchdogLog "Save-AccountsConfig threw: $($_.Exception.Message)" 'ERROR'
    }
}

# ----- 2. evaluate fleet wake-up condition ----------------------------------
# Wake up only if ALL of:
#   - sentinel `.all-accounts-were-limited` is present (operator/PS1 wrote it
#     when a spawn was rejected due to all-limited)
#   - at least one account is now available
#   - no claude.exe is currently running (we don't barge into an active session)

$wasAllLimited = Test-Path $AllLimitedFlag
if (-not $wasAllLimited) {
    # nothing to wake; we're done
    return
}

# Re-read config to use the post-clear state
try { $cfg = Get-AccountsConfig } catch {
    Write-WatchdogLog "re-read Get-AccountsConfig failed: $($_.Exception.Message)" 'ERROR'
    return
}

# Compute "is any account currently available" using same predicate as the lib
$anyAvailable = $false
foreach ($acct in $cfg.accounts) {
    if ([int]$acct.current_sessions -ge [int]$acct.max_sessions_concurrent) { continue }
    if ($acct.rate_limited_until_utc) {
        try {
            $u = [datetime]::Parse($acct.rate_limited_until_utc).ToUniversalTime()
            if ($u -gt $now) { continue }
        } catch {}
    }
    $anyAvailable = $true
    break
}

if (-not $anyAvailable) {
    # still all limited; leave sentinel in place + retry next tick
    return
}

# Is any claude.exe running? If yes, don't barge in.
$claudeRunning = $false
try {
    $procs = Get-Process claude -ErrorAction SilentlyContinue
    if ($procs -and $procs.Count -gt 0) { $claudeRunning = $true }
} catch {}

if ($claudeRunning) {
    Write-WatchdogLog 'fleet wake-up skipped: claude.exe already running' 'INFO'
    # consume the sentinel since the operator is already back online
    Remove-Item -Path $AllLimitedFlag -Force -ErrorAction SilentlyContinue
    return
}

# Conditions met: an account is back AND nothing is running AND we were all-limited.
# Fire the bat with --auto-resume so the launcher picks back up where it left off.
if (-not (Test-Path $AutoResumeBat)) {
    Write-WatchdogLog "auto-resume bat not found at $AutoResumeBat; cannot wake fleet" 'WARN'
    return
}

Write-WatchdogLog "fleet wake-up firing: invoking '$AutoResumeBat --auto-resume'" 'INFO'
try {
    # detached, non-blocking; we don't wait for the launcher
    Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', "`"$AutoResumeBat`"", '--auto-resume') `
                  -WindowStyle Hidden -ErrorAction Stop | Out-Null
    Remove-Item -Path $AllLimitedFlag -Force -ErrorAction SilentlyContinue
    Write-WatchdogLog 'fleet wake-up fired + sentinel cleared' 'INFO'
} catch {
    Write-WatchdogLog "fleet wake-up failed: $($_.Exception.Message)" 'ERROR'
}

# Total runtime under 5 sec guarantee: every external call uses ErrorAction
# SilentlyContinue + early-returns. No blocking IO beyond a single JSON read/write.
$elapsed = ((Get-Date).ToUniversalTime() - $WatchdogStartUtc).TotalSeconds
if ($elapsed -gt 4.5) {
    Write-WatchdogLog ("watchdog runtime {0:N2}s exceeded 4.5s soft cap" -f $elapsed) 'WARN'
}
