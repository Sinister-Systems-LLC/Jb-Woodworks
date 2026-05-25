# Diagnose-Fleet-Freeze - investigate "agents randomly freeze + cmd windows wont close + comes back" pattern.
# Author: RKOJ-ELENO :: 2026-05-25
# Operator (2026-05-25T02:18Z ~22:55Z): "agents randomly just freeze and same for my cmd window like i cant close
# then it all comes back". Investigation-only by default (NO process kills, NO task disables). Surfaces findings.
#
# Usage:
#   powershell -File automations\diagnose-fleet-freeze.ps1                  # full diagnosis report
#   powershell -File automations\diagnose-fleet-freeze.ps1 -Format Json     # machine-readable
#   powershell -File automations\diagnose-fleet-freeze.ps1 -KillZombies -Confirm  # operator-explicit reap

[CmdletBinding()]
param(
    [ValidateSet('Text','Json')]
    [string]$Format = 'Text',
    [switch]$KillZombies,
    [switch]$Confirm,
    [int]$ZombieAgeHours = 4
)

$SanctumRoot = Split-Path -Parent $PSScriptRoot
$nowUtc = (Get-Date).ToUniversalTime()
$report = [ordered]@{
    schema = 'sinister.fleet-freeze-diagnosis.v1'
    ts_utc = $nowUtc.ToString('yyyy-MM-ddTHH:mm:ssZ')
    findings = @()
    process_summary = $null
    scheduled_task_issues = @()
    mcp_health = $null
    actions_taken = @()
    operator_actionable = @()
}

# -- 1. Process inventory ---------------------------------------------------
$allProc = Get-Process -ErrorAction SilentlyContinue
$bynme = $allProc | Where-Object { $_.ProcessName -match 'claude|powershell|pwsh|node|mintty|conhost|cmd|ollama|python' } |
    Group-Object ProcessName |
    ForEach-Object {
        $sum = ($_.Group | Measure-Object WorkingSet64 -Sum).Sum
        [pscustomobject]@{
            Name = $_.Name
            Count = $_.Count
            TotalMemMB = [math]::Round($sum / 1MB, 1)
            OldestAgeHrs = ($_.Group | Where-Object StartTime | ForEach-Object { ((Get-Date) - $_.StartTime).TotalHours } | Sort-Object -Descending | Select-Object -First 1)
        }
    } | Sort-Object Count -Descending
$report.process_summary = $bynme

if (($bynme | Where-Object { $_.Name -eq 'conhost' -and $_.Count -gt 30 })) {
    $report.findings += "RED: conhost.exe count > 30 (currently $((($bynme | Where-Object {$_.Name -eq 'conhost'}).Count))) - Windows console host pile. Each cmd/powershell/mintty launch creates one. Excess indicates spawn flood + slow shutdown."
}
if (($bynme | Where-Object { $_.Name -eq 'powershell' -and $_.Count -gt 8 })) {
    $report.findings += "RED: powershell.exe count > 8 (currently $((($bynme | Where-Object {$_.Name -eq 'powershell'}).Count))) - scheduled task pile-up. Suspect simultaneous-cadence scheduled tasks (every 5min)."
}
if (($bynme | Where-Object { $_.Name -eq 'claude' -and $_.Count -gt 5 })) {
    $report.findings += "ORANGE: claude.exe count > 5 (currently $((($bynme | Where-Object {$_.Name -eq 'claude'}).Count))) - Claude session pile-up. Each holds 4-6 MCP child processes."
}

# -- 2. Zombie detection ----------------------------------------------------
$zombies = $allProc | Where-Object {
    $_.ProcessName -match 'claude|mintty' -and
    $_.StartTime -and
    ((Get-Date) - $_.StartTime).TotalHours -gt $ZombieAgeHours
} | Sort-Object StartTime
$report.zombies = $zombies | ForEach-Object {
    [pscustomobject]@{
        Pid = $_.Id
        Name = $_.ProcessName
        StartTime = $_.StartTime.ToString('yyyy-MM-ddTHH:mm:ss')
        AgeHrs = [math]::Round(((Get-Date) - $_.StartTime).TotalHours, 1)
        MemMB = [math]::Round($_.WorkingSet64 / 1MB, 0)
    }
}
if ($zombies.Count -gt 0) {
    $report.findings += "INFO: $($zombies.Count) claude/mintty processes older than $ZombieAgeHours hr - likely stale sessions operator forgot to close."
}

# -- 3. Scheduled task audit ------------------------------------------------
$st = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -match 'Sinister|Sanctum|EVE|RKOJ|Forge|Loop|Watchdog' }
foreach ($t in $st) {
    $info = Get-ScheduledTaskInfo -TaskName $t.TaskName -TaskPath $t.TaskPath -ErrorAction SilentlyContinue
    if (-not $info) { continue }
    $exec = ($t.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" } | Select-Object -First 1)
    $hidden = ($exec -match '-WindowStyle\s+Hidden|-w\s+hidden|-WindowStyle\s+hidden')
    $running = ($t.State -eq 'Running')
    $err = ($info.LastTaskResult -ne 0 -and $info.LastTaskResult -ne 267009 -and $info.LastTaskResult -ne 267011 -and $info.LastTaskResult -ne 267014)
    $issue = $null
    if (-not $hidden -and $exec -match 'powershell|pwsh') { $issue = 'NOT_HIDDEN' }
    if ($err) { $issue = 'FAILING (LastResult=' + $info.LastTaskResult + ')' }
    if ($running -and $info.LastRunTime -lt (Get-Date).AddHours(-1)) { $issue = 'STUCK_RUNNING > 1h' }
    if ($issue) {
        $report.scheduled_task_issues += [pscustomobject]@{
            Name = $t.TaskName
            State = $t.State
            LastResult = $info.LastTaskResult
            Issue = $issue
            Exec = if($exec.Length -gt 100){$exec.Substring(0,100)+'...'}else{$exec}
        }
    }
}
if ($report.scheduled_task_issues.Count -gt 0) {
    $report.findings += "ORANGE: $($report.scheduled_task_issues.Count) scheduled tasks have issues (NOT_HIDDEN / FAILING / STUCK_RUNNING)."
}

# -- 4. Ollama health -------------------------------------------------------
$ollamaSvc = Get-Service -Name 'Ollama*' -ErrorAction SilentlyContinue
$ollamaHttp = $null
try {
    $ollamaHttp = (Invoke-WebRequest -Uri 'http://localhost:11434/api/version' -UseBasicParsing -TimeoutSec 2).Content
} catch {}
$report.mcp_health = [pscustomobject]@{
    OllamaService = if($ollamaSvc){$ollamaSvc.Status}else{'NOT_REGISTERED'}
    OllamaHttp200 = ($null -ne $ollamaHttp)
    OllamaVersion = $ollamaHttp
}
if (-not $ollamaSvc -and -not $ollamaHttp) {
    $report.findings += "RED: Ollama not reachable (no service + no HTTP). 13 local bots (librarian/sentinel/triage/etc) will silent-fail."
} elseif (-not $ollamaSvc -and $ollamaHttp) {
    $report.findings += "ORANGE: Ollama running as user-mode process (no Windows service). Scheduled tasks running as SYSTEM may not reach it."
}

# -- 5. Operator actionables ------------------------------------------------
if ($zombies.Count -gt 5) {
    $report.operator_actionable += "RUN: powershell -File automations\diagnose-fleet-freeze.ps1 -KillZombies -Confirm  (reaps $($zombies.Count) stale sessions older than $ZombieAgeHours hr)"
}
if ($report.scheduled_task_issues | Where-Object Issue -eq 'NOT_HIDDEN') {
    $report.operator_actionable += "PATCH: add '-WindowStyle Hidden' to scheduled tasks listed under NOT_HIDDEN above (use Set-ScheduledTask -Argument)"
}
if ($report.scheduled_task_issues | Where-Object Issue -like 'FAILING*') {
    $report.operator_actionable += "INVESTIGATE: failing scheduled tasks - read their log files (typically _shared-memory/logs/ or per-script log dir)"
}
if (-not $ollamaSvc) {
    $report.operator_actionable += "FIX: register Ollama as a Windows service (sc.exe create Ollama binPath='C:\\Program Files\\Ollama\\ollama.exe serve') OR move bots to user-context scheduled tasks"
}

# -- 6. Optional kill (only with -KillZombies -Confirm) ---------------------
if ($KillZombies -and $Confirm) {
    foreach ($z in $zombies) {
        try {
            Stop-Process -Id $z.Id -Force -ErrorAction Stop
            $report.actions_taken += "KILLED pid=$($z.Id) name=$($z.ProcessName) age_hrs=$([math]::Round(((Get-Date) - $z.StartTime).TotalHours, 1))"
        } catch {
            $report.actions_taken += "FAILED_KILL pid=$($z.Id): $($_.Exception.Message)"
        }
    }
}

# -- 7. Emit ---------------------------------------------------------------
if ($Format -eq 'Json') {
    $report | ConvertTo-Json -Depth 6
    return
}

Write-Host '=== Sinister Fleet Freeze Diagnosis ===' -ForegroundColor Cyan
Write-Host "ts: $($report.ts_utc)`n"

Write-Host '--- Findings ---' -ForegroundColor Yellow
foreach ($f in $report.findings) {
    $color = if($f.StartsWith('RED')){'Red'}elseif($f.StartsWith('ORANGE')){'DarkYellow'}else{'Gray'}
    Write-Host "  $f" -ForegroundColor $color
}
Write-Host ''
Write-Host '--- Process summary ---' -ForegroundColor Yellow
$report.process_summary | Format-Table -AutoSize | Out-String | Write-Host
if ($report.zombies.Count -gt 0) {
    Write-Host "--- Zombies (claude/mintty older than $ZombieAgeHours hr) ---" -ForegroundColor Yellow
    $report.zombies | Format-Table -AutoSize | Out-String | Write-Host
}
if ($report.scheduled_task_issues.Count -gt 0) {
    Write-Host '--- Scheduled task issues ---' -ForegroundColor Yellow
    $report.scheduled_task_issues | Format-Table -AutoSize | Out-String | Write-Host
}
Write-Host '--- MCP / Ollama health ---' -ForegroundColor Yellow
$report.mcp_health | Format-List | Out-String | Write-Host
Write-Host '--- Operator-actionable ---' -ForegroundColor Yellow
foreach ($a in $report.operator_actionable) { Write-Host "  - $a" -ForegroundColor White }
if ($report.actions_taken.Count -gt 0) {
    Write-Host '--- Actions taken this run ---' -ForegroundColor Green
    foreach ($a in $report.actions_taken) { Write-Host "  $a" -ForegroundColor Green }
}
Write-Host ''
Write-Host "Saved JSON: D:\Sinister Sanctum\_shared-memory\diagnostics\fleet-freeze-$($nowUtc.ToString('yyyy-MM-ddTHHmmss'))Z.json"

$diagDir = Join-Path $SanctumRoot '_shared-memory\diagnostics'
if (-not (Test-Path $diagDir)) { New-Item -ItemType Directory -Force -Path $diagDir | Out-Null }
$jsonPath = Join-Path $diagDir ("fleet-freeze-{0}Z.json" -f $nowUtc.ToString('yyyy-MM-ddTHHmmss'))
$report | ConvertTo-Json -Depth 6 | Out-File -FilePath $jsonPath -Encoding utf8
