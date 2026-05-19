# log-progress.ps1 - operator-side append to _shared-memory/PROGRESS/<agent>.md
# Triggered by C:\Users\Zonia\Desktop\Log-Progress.bat.

[CmdletBinding()]
param(
    [string]$Agent = '',
    [string]$Status = '',
    [string]$Title = '',
    [string]$Body = ''
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Log Progress'

$ProgressDir = 'D:\Sinister Sanctum\_shared-memory\PROGRESS'
if (-not (Test-Path $ProgressDir)) { New-Item -ItemType Directory -Path $ProgressDir -Force | Out-Null }

# Read available agents (from prefs registry if it exists)
$prefsPath = 'D:\Sinister Sanctum\automations\session-templates\agent-prefs.json'
$knownAgents = @()
if (Test-Path $prefsPath) {
    try {
        $prefs = Get-Content $prefsPath -Raw | ConvertFrom-Json
        if ($prefs.per_project) {
            foreach ($k in ($prefs.per_project | Get-Member -MemberType NoteProperty | Where-Object { $_.Name -notmatch '^_' }).Name) {
                $entry = $prefs.per_project.$k
                if ($entry.agent_name) { $knownAgents += $entry.agent_name }
            }
        }
    } catch {}
}

Write-Host ''
Write-Host '  =====================================' -ForegroundColor DarkMagenta
Write-Host '   LOG PROGRESS  (cross-agent feed)' -ForegroundColor Magenta
Write-Host '  =====================================' -ForegroundColor DarkMagenta
Write-Host ''

if (-not $Agent) {
    Write-Host '  Which agent are you logging for?' -ForegroundColor White
    if ($knownAgents.Count -gt 0) {
        $i = 1
        foreach ($a in $knownAgents) {
            Write-Host ("    {0}) {1}" -f $i, $a) -ForegroundColor Gray
            $i++
        }
        Write-Host "    C) custom - type a name" -ForegroundColor DarkGray
        Write-Host ''
        $ap = Read-Host '  choice or name'
        if ($ap -match '^\d+$') {
            $ai = [int]$ap - 1
            if ($ai -ge 0 -and $ai -lt $knownAgents.Count) { $Agent = $knownAgents[$ai] }
        } elseif ($ap -match '^[Cc]$') {
            $Agent = Read-Host '  agent name'
        } else { $Agent = $ap }
    } else {
        $Agent = Read-Host '  agent name'
    }
}
if (-not $Agent) { Write-Host '  [ABORT] agent required.' -ForegroundColor Red; Start-Sleep 3; exit 2 }

if (-not $Status) {
    Write-Host ''
    Write-Host '  Status?' -ForegroundColor White
    Write-Host '    1) started   2) shipped   3) blocked   4) paused   5) failed   6) note' -ForegroundColor Gray
    $sp = Read-Host '  choice [default=2 shipped]'
    $statusMap = @{ '1'='started'; '2'='shipped'; '3'='blocked'; '4'='paused'; '5'='failed'; '6'='note' }
    if (-not $sp) { $sp = '2' }
    $Status = if ($statusMap.ContainsKey($sp)) { $statusMap[$sp] } else { $sp }
}

if (-not $Title) {
    Write-Host ''
    Write-Host '  One-line title (what milestone?)' -ForegroundColor White
    $Title = Read-Host '  >'
}
if (-not $Title) { Write-Host '  [ABORT] title required.' -ForegroundColor Red; Start-Sleep 3; exit 3 }

if (-not $Body) {
    Write-Host ''
    Write-Host '  Body - 1-3 lines (Ctrl+Z + Enter to finish, or just Enter for none)' -ForegroundColor White
    $bodyLines = @()
    while ($true) {
        $line = Read-Host
        if ($line -eq $null) { break }
        if (-not $line -and $bodyLines.Count -eq 0) { break }
        $bodyLines += $line
    }
    $Body = ($bodyLines -join "`n").TrimEnd()
}

# Sanitize agent name to filename
$safe = ($Agent -replace '[^a-zA-Z0-9 \-_]', '').Trim()
if (-not $safe) { Write-Host '  [ABORT] invalid agent name.' -ForegroundColor Red; Start-Sleep 3; exit 4 }
$filePath = Join-Path $ProgressDir "$safe.md"

$ts = (Get-Date).ToString('yyyy-MM-dd HH:mm')
$entry = "## $ts - $($Status): $Title`n$Body`n`n"

if (Test-Path $filePath) {
    $existing = Get-Content $filePath -Raw
    $pivot = $existing.IndexOf("---`n")
    if ($pivot -lt 0) { $pivot = $existing.IndexOf("---") }
    if ($pivot -ge 0) {
        $head = $existing.Substring(0, $pivot + 4)
        $tail = $existing.Substring($pivot + 4)
        $new = $head + "`n" + $entry + $tail
    } else {
        $new = $existing.TrimEnd() + "`n`n" + $entry
    }
} else {
    $new = "# Agent: $Agent`n`nAppend-only progress log. Most recent at top.`n`n---`n`n$entry"
}
[System.IO.File]::WriteAllText($filePath, $new, [System.Text.UTF8Encoding]::new($false))

Write-Host ''
Write-Host "  [OK] $Status logged for $Agent" -ForegroundColor Green
Write-Host "  file: $filePath" -ForegroundColor DarkGray

# Runlog
$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) {
    . $runlogHelper
    $log = Start-Runlog -Script 'log-progress'
    Add-RunlogStep -Log $log -Name 'append' -Ok $true -Summary "$Agent :: $Status :: $Title"
    Set-RunlogOutput -Log $log -Key 'agent'  -Value $Agent
    Set-RunlogOutput -Log $log -Key 'status' -Value $Status
    Set-RunlogOutput -Log $log -Key 'title'  -Value $Title
    $null = Save-Runlog -Log $log -AutoClose $true
}

Write-Host ''
Write-Host '  Sanctum Console will reflect this on next refresh (within 30s).' -ForegroundColor DarkGray
Write-Host '  Window auto-closes in 4 seconds.' -ForegroundColor DarkGray
Start-Sleep -Seconds 4
exit 0
