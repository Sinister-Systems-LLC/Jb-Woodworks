# Author: RKOJ-ELENO :: 2026-05-25
#
# sinister-headless.ps1 -- canonical NEVER-VISIBLE PowerShell wrapper
#
# Operator hard-canonical 2026-05-25T02:25Z verbatim:
#     "this fucking powershell winddow keeps poping up stop all shit like this
#      from happening. if you need things like this make a fucking tool or
#      system to use our sinister term in a headless way"
#
# This is the canonical way to invoke any .ps1 / cmd / process that should NOT
# show a window. Composes with:
#   - no-visible-powershell-windows-doctrine-2026-05-25 (this file IS the tool)
#   - sinister-bus / sinister-term-history (logs every invocation for forensic
#     recall even though no window is visible)
#   - sanctioned-bypasses-doctrine-2026-05-21 (we may still run dangerously-
#     skip-permissions etc, but never with a popup)
#
# Usage:
#     # Run a script silently and wait for exit code
#     powershell -NoProfile -File automations\sinister-headless.ps1 `
#         -Script automations\mesh-coordinator.ps1 -Args @('-Action','Sweep')
#
#     # Run a one-liner silently
#     powershell -NoProfile -File automations\sinister-headless.ps1 `
#         -Command 'Get-Process claude | Measure-Object | %{ $_.Count }'
#
#     # Detach and continue (fire-and-forget; output captured to log)
#     powershell -NoProfile -File automations\sinister-headless.ps1 `
#         -Script automations\sanctum-auto-push.ps1 -Detach
#
# Why -WindowStyle Hidden isn't enough on its own:
#   * Some scheduled-task actions still flicker a window briefly on cold-start
#     while the host elevates / loads .NET
#   * Direct `powershell.exe -File X.ps1` from .lnk / .bat / explorer keeps the
#     console alive even when -WindowStyle Hidden is requested IF the parent
#     is a console host that already has a visible window
#   * The proper fix is to launch via `Start-Process -WindowStyle Hidden` with
#     a redirected stdout/stderr to a log -- which is what THIS wrapper does
#
# Every invocation appends one JSON row to
#   _shared-memory/sinister-term-history/headless-invocations.jsonl
# so the operator can grep / audit what's been running silently.

[CmdletBinding(DefaultParameterSetName='Script')]
param(
    [Parameter(Mandatory=$true, ParameterSetName='Script')]
    [string]$Script,

    [Parameter(Mandatory=$true, ParameterSetName='Command')]
    [string]$Command,

    [Parameter(ParameterSetName='Script')]
    [string[]]$ScriptArgs = @(),

    [switch]$Detach,
    [string]$LogPath = '',
    [int]$TimeoutSec = 0,
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'

# Resolve log destination
if (-not $LogPath) {
    $logDir = Join-Path $SanctumRoot '_shared-memory\sinister-term-history\headless-logs'
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    $stamp = (Get-Date -Format 'yyyyMMddTHHmmssZ')
    $tag = if ($Script) { (Split-Path -Leaf $Script) -replace '\.ps1$','' } else { 'inline' }
    $LogPath = Join-Path $logDir "$stamp-$tag.log"
}

# Build the powershell.exe argument list. CRITICAL: -WindowStyle Hidden + -NoProfile
# + -ExecutionPolicy Bypass; spawned via Start-Process which is the only way to
# truly suppress the console host on Windows.
$psArgs = @('-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-NonInteractive')

if ($PSCmdlet.ParameterSetName -eq 'Script') {
    $scriptPath = $Script
    if (-not (Test-Path $scriptPath)) {
        # Try resolving relative to SanctumRoot
        $alt = Join-Path $SanctumRoot $Script
        if (Test-Path $alt) {
            $scriptPath = $alt
        } else {
            Write-Error "Script not found: $Script (tried $alt)"
            exit 2
        }
    }
    $psArgs += @('-File', $scriptPath)
    if ($ScriptArgs -and $ScriptArgs.Count -gt 0) {
        $psArgs += $ScriptArgs
    }
    $invocationKind = 'script'
    $invocationTarget = $scriptPath
} else {
    $psArgs += @('-Command', $Command)
    $invocationKind = 'command'
    $invocationTarget = $Command
}

# Append-row to the invocation log
function Write-InvocationLog {
    param([hashtable]$Row)
    try {
        $jsonl = Join-Path $SanctumRoot '_shared-memory\sinister-term-history\headless-invocations.jsonl'
        $dir = Split-Path -Parent $jsonl
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $line = ($Row | ConvertTo-Json -Compress -Depth 5)
        Add-Content -Path $jsonl -Value $line -Encoding utf8
    } catch {
        # Logging failures must NEVER block the actual invocation.
    }
}

$startTs = (Get-Date).ToUniversalTime().ToString('o')
$pidLaunched = 0
$rc = -1
$elapsed = 0.0

try {
    if ($Detach) {
        # Fire-and-forget: spawn hidden, return immediately.
        $p = Start-Process -FilePath 'powershell.exe' -ArgumentList $psArgs `
                            -WindowStyle Hidden `
                            -RedirectStandardOutput $LogPath `
                            -RedirectStandardError "$LogPath.err" `
                            -PassThru
        $pidLaunched = $p.Id
        $rc = 0
        Write-InvocationLog @{
            ts_utc        = $startTs
            kind          = $invocationKind
            target        = $invocationTarget
            mode          = 'detach'
            pid           = $pidLaunched
            log           = $LogPath
        }
        Write-Host "headless: detached pid=$pidLaunched log=$LogPath"
        exit 0
    } else {
        # Synchronous: wait for exit, capture rc.
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $procArgs = @{
            FilePath               = 'powershell.exe'
            ArgumentList           = $psArgs
            WindowStyle            = 'Hidden'
            RedirectStandardOutput = $LogPath
            RedirectStandardError  = "$LogPath.err"
            PassThru               = $true
            NoNewWindow            = $false
        }
        $p = Start-Process @procArgs
        $pidLaunched = $p.Id
        if ($TimeoutSec -gt 0) {
            if (-not $p.WaitForExit($TimeoutSec * 1000)) {
                $p.Kill()
                $rc = 124
                $sw.Stop()
                $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 2)
                Write-InvocationLog @{
                    ts_utc     = $startTs
                    kind       = $invocationKind
                    target     = $invocationTarget
                    mode       = 'sync-timeout'
                    pid        = $pidLaunched
                    rc         = $rc
                    elapsed_s  = $elapsed
                    log        = $LogPath
                }
                Write-Host "headless: TIMEOUT after ${TimeoutSec}s (killed pid=$pidLaunched)"
                exit $rc
            }
        } else {
            $p.WaitForExit()
        }
        $sw.Stop()
        $rc = $p.ExitCode
        $elapsed = [math]::Round($sw.Elapsed.TotalSeconds, 2)
        Write-InvocationLog @{
            ts_utc     = $startTs
            kind       = $invocationKind
            target     = $invocationTarget
            mode       = 'sync'
            pid        = $pidLaunched
            rc         = $rc
            elapsed_s  = $elapsed
            log        = $LogPath
        }
        # Echo brief status to caller (one line). Detail is in the log.
        if ($rc -eq 0) {
            Write-Host "headless: OK ${elapsed}s (pid=$pidLaunched log=$LogPath)"
        } else {
            Write-Host "headless: rc=$rc ${elapsed}s (pid=$pidLaunched log=$LogPath)"
        }
        exit $rc
    }
} catch {
    Write-InvocationLog @{
        ts_utc     = $startTs
        kind       = $invocationKind
        target     = $invocationTarget
        mode       = 'error'
        error      = $_.Exception.Message
    }
    Write-Error "headless: launch failed: $($_.Exception.Message)"
    exit 1
}
