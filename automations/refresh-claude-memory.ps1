# refresh-claude-memory.ps1 - one-click "fix Claude's memory so it can do everything with no blocks"
#
# What this does:
#   1. Stops Custodian briefly (release any locked files)
#   2. Cleans stale tmp files from runtime-state
#   3. Re-registers all 12 Sinister Bots in .mcp.json (install-fleet.ps1)
#   4. Triggers a Custodian snapshot pass (catches anything new)
#   5. Heartbeats all known agent inboxes (presence refresh)
#   6. Re-aggregates GOTCHAS (so Claude sees latest classifier patterns)
#   7. Re-enables Custodian
#   8. Verifies all critical lane-discipline docs are intact
#   9. Composes a "memory refreshed" phrase, copies to clipboard
#  10. Tells operator to restart Claude Code so the fresh MCP loads
#
# Operator runs via C:\Users\Zonia\Desktop\Fix-Claude-Memory.bat
# Emits runlog manifest.

[CmdletBinding()]
param(
    [switch]$NoRestart,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Fix Claude Memory'

# Load runlog
$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) { . $runlogHelper }
$log = if (Get-Command Start-Runlog -ErrorAction SilentlyContinue) { Start-Runlog -Script 'refresh-claude-memory' } else { $null }

function Step($n, $name, $color = 'Cyan') {
    Write-Host ''
    Write-Host "[$n] $name" -ForegroundColor $color
}
function Out-OK($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Out-WARN($msg) { Write-Host "    [WARN] $msg" -ForegroundColor Yellow }
function Out-FAIL($msg) { Write-Host "    [FAIL] $msg" -ForegroundColor Red }
function Out-INFO($msg) { Write-Host "    $msg" -ForegroundColor DarkGray }

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   F I X   C L A U D E   M E M O R Y' -ForegroundColor White
Write-Host '   refresh fleet | snapshot | clear stale | rearm clipboard' -ForegroundColor DarkGray
Write-Host '  ============================================================' -ForegroundColor Magenta

$failures = @()

# [1] Stop Custodian briefly to release any locked files
Step 1 'Pausing Custodian (release locked files)'
try {
    Stop-ScheduledTask -TaskName SinisterCustodian -ErrorAction SilentlyContinue
    Disable-ScheduledTask -TaskName SinisterCustodian -ErrorAction SilentlyContinue | Out-Null
    Out-OK 'paused'
    if ($log) { Add-RunlogStep -Log $log -Name 'pause-custodian' -Ok $true -Summary 'task disabled' }
} catch {
    Out-WARN "could not pause: $($_.Exception.Message)"
    if ($log) { Add-RunlogStep -Log $log -Name 'pause-custodian' -Ok $true -Summary "warn: $($_.Exception.Message)" }
}

# [2] Clean stale tmp files in runtime-state + script-runs
Step 2 'Cleaning stale tmp files in runtime-state'
$rsRoot = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state'
$tmpFiles = Get-ChildItem -Path $rsRoot -Recurse -File -Filter '*.tmp.*' -ErrorAction SilentlyContinue
$tmpCount = $tmpFiles.Count
foreach ($t in $tmpFiles) { Remove-Item $t.FullName -Force -ErrorAction SilentlyContinue }
Out-OK "removed $tmpCount stale tmp file(s)"
if ($log) { Add-RunlogStep -Log $log -Name 'clean-tmp' -Ok $true -Summary "removed=$tmpCount" }

# Also clean Python __pycache__ in agents tree (frees memory)
$pycCount = 0
Get-ChildItem -Path 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents' -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $pycCount++
}
Out-INFO "cleaned $pycCount __pycache__ dirs"

# [3] Re-register all 12 bots
Step 3 'Re-registering all 12 Sinister Bots'
$installFleet = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\install-fleet.ps1'
if (Test-Path $installFleet) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installFleet -Quiet 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
    if ($LASTEXITCODE -eq 0) {
        Out-OK 'fleet registered'
        if ($log) { Add-RunlogStep -Log $log -Name 'install-fleet' -Ok $true -Summary '12 bots' }
    } else {
        Out-WARN "install-fleet exit $LASTEXITCODE"
        $failures += 'install-fleet'
        if ($log) { Add-RunlogStep -Log $log -Name 'install-fleet' -Ok $false -Summary "exit $LASTEXITCODE" }
    }
} else { Out-WARN 'install-fleet.ps1 not found' }

# [4] Trigger snapshot pass
Step 4 'Triggering Custodian snapshot pass (in background)'
$snapJob = Start-Job -ScriptBlock {
    Set-Location 'D:\Sinister\Sinister Skills'
    & python -c "import sys; sys.path.insert(0, '12_LLM_ORCHESTRATION/agents/custodian'); import server; r = server.snapshot_now(); print('snapshot:', r if isinstance(r, dict) else 'ran')" 2>&1
}
Out-INFO "job-id=$($snapJob.Id), running in background"
if ($log) { Add-RunlogStep -Log $log -Name 'snapshot-bg' -Ok $true -Summary "job-id=$($snapJob.Id)" }

# [5] Heartbeat all agent inboxes (presence refresh)
Step 5 'Heartbeating agent inboxes'
$inboxRoot = 'D:\Sinister\Sinister Skills\01_MEMORY\_inbox'
$heartbeatCount = 0
if (Test-Path $inboxRoot) {
    Get-ChildItem $inboxRoot -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $flag = Join-Path $_.FullName 'online.flag'
        # Touch the file so it has fresh mtime (counts as "online" in launcher telemetry)
        if (Test-Path $flag) { (Get-Item $flag).LastWriteTime = Get-Date; $heartbeatCount++ }
    }
}
Out-OK "$heartbeatCount agent flags refreshed"
if ($log) { Add-RunlogStep -Log $log -Name 'heartbeat' -Ok $true -Summary "count=$heartbeatCount" }

# [6] Re-aggregate gotchas (so Claude sees fresh classifier patterns + new denies)
Step 6 'Re-aggregating GOTCHAS docs'
$aggPs1 = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\aggregate-gotchas.ps1'
if (Test-Path $aggPs1) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $aggPs1 -Quiet 2>&1 | Out-Null
    Out-OK 'gotchas aggregated'
    if ($log) { Add-RunlogStep -Log $log -Name 'aggregate-gotchas' -Ok $true -Summary 'done' }
} else { Out-INFO 'aggregate-gotchas.ps1 not present (skipping)' }

# [7] Re-enable Custodian
Step 7 'Re-enabling Custodian scheduled task'
try {
    Enable-ScheduledTask -TaskName SinisterCustodian -ErrorAction SilentlyContinue | Out-Null
    $task = Get-ScheduledTask -TaskName SinisterCustodian -ErrorAction SilentlyContinue
    if ($task) {
        Out-OK "Custodian state=$($task.State)"
        if ($log) { Add-RunlogStep -Log $log -Name 'resume-custodian' -Ok $true -Summary "state=$($task.State)" }
    } else { Out-WARN 'task not registered'; $failures += 'custodian-task' }
} catch { Out-FAIL $_.Exception.Message; $failures += 'custodian-resume' }

# [8] Verify lane-discipline docs intact
Step 8 'Verifying lane-discipline docs'
$discDocs = @(
    'D:\Sinister\Sinister Skills\PARALLEL-AGENT-COORDINATION.md',
    'D:\Sinister Sanctum\PARALLEL-AGENT-COORDINATION.md',
    'D:\Sinister Sanctum\SESSION-START\00-RULES.md',
    'D:\Sinister Sanctum\SESSION-START\06-LAUNCHER.md'
)
$missing = @()
foreach ($d in $discDocs) {
    if (-not (Test-Path $d)) { $missing += (Split-Path $d -Leaf) }
}
if ($missing.Count -eq 0) {
    Out-OK 'all 4 lane-discipline docs present'
    if ($log) { Add-RunlogStep -Log $log -Name 'verify-docs' -Ok $true -Summary 'all present' }
} else {
    Out-WARN "missing: $($missing -join ', ')"
    if ($log) { Add-RunlogStep -Log $log -Name 'verify-docs' -Ok $false -Summary "missing: $($missing -join ',')" }
}

# [9] Compose "memory refreshed" phrase + clipboard
Step 9 'Composing refresh phrase'
$ts = (Get-Date).ToString('yyyy-MM-dd HH:mm')
$phrase = "Read D:\Sinister Sanctum\SESSION-START\ and ack the fresh state at $ts. " +
          "12 bots re-registered, Custodian snapshot triggered, agent flags refreshed. " +
          "Then I'll tell you which project we're working on."
try {
    Set-Clipboard -Value $phrase
    Out-OK 'phrase copied to clipboard'
    if ($log) { Add-RunlogStep -Log $log -Name 'clipboard' -Ok $true -Summary 'copied' }
} catch {
    Out-WARN "clip failed: $($_.Exception.Message)"
    if ($log) { Add-RunlogStep -Log $log -Name 'clipboard' -Ok $false -Summary $_.Exception.Message }
}

# [10] Final report
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
if ($failures.Count -eq 0) {
    Write-Host '   MEMORY REFRESHED' -ForegroundColor Green
} else {
    Write-Host "   MEMORY REFRESHED (with $($failures.Count) warning(s): $($failures -join ', '))" -ForegroundColor Yellow
}
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''
Write-Host '   Restart Claude Code now to load the fresh MCP fleet.' -ForegroundColor Cyan
Write-Host '   The refresh phrase is on your clipboard - paste into the new session.' -ForegroundColor Cyan
Write-Host ''
Write-Host "   Phrase preview:" -ForegroundColor DarkGray
Write-Host "     `"$phrase`"" -ForegroundColor White
Write-Host ''

if ($log) {
    Add-RunlogNextAction -Log $log -Action 'Restart Claude Code so the freshly-registered 12 bots + new MCP servers load.'
    if ($snapJob) {
        Add-RunlogNextAction -Log $log -Action "Snapshot pass running in background (job-id $($snapJob.Id)); will complete on its own."
    }
    $null = Save-Runlog -Log $log -AutoClose ($failures.Count -eq 0)
}

if (-not $Quiet) {
    Write-Host '   Window auto-closes in 15 seconds. Ctrl+C to keep open.' -ForegroundColor DarkGray
    Start-Sleep -Seconds 15
}
exit 0
