# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# log-knowledge.ps1 - operator-side append to the Sanctum brain.
# Triggered by C:\Users\Zonia\Desktop\Log-Knowledge.bat.

[CmdletBinding()]
param(
    [string]$Slug = '',
    [string]$Title = '',
    [string]$Status = '',
    [string]$Body = ''
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Log Knowledge (Sanctum brain)'

$BrainDir = 'D:\Sinister Sanctum\_shared-memory\knowledge'
if (-not (Test-Path $BrainDir)) { New-Item -ItemType Directory -Path $BrainDir -Force | Out-Null }

Write-Host ''
Write-Host '  ============================================' -ForegroundColor DarkMagenta
Write-Host '   THE SANCTUM BRAIN  (knowledge that grows)' -ForegroundColor Magenta
Write-Host '  ============================================' -ForegroundColor DarkMagenta
Write-Host ''
Write-Host '  Append a discovery / fix / workaround so every agent benefits.' -ForegroundColor Gray
Write-Host ''

if (-not $Slug) {
    Write-Host '  Topic slug (kebab-case, e.g. github-auth-workflow-scope)' -ForegroundColor White
    Write-Host '  Existing topics:' -ForegroundColor Gray
    Get-ChildItem -Path $BrainDir -Filter '*.md' | Where-Object { -not $_.Name.StartsWith('_') } | ForEach-Object {
        Write-Host ('    - ' + $_.BaseName) -ForegroundColor DarkGray
    }
    Write-Host ''
    $Slug = Read-Host '  slug'
}
$Slug = ($Slug -replace '[^a-zA-Z0-9-]', '-' -replace '-+', '-').Trim('-').ToLower()
if (-not $Slug) { Write-Host '  [ABORT] slug required.' -ForegroundColor Red; Start-Sleep 3; exit 2 }

$existing = (Test-Path (Join-Path $BrainDir "$Slug.md"))
if ($existing) {
    Write-Host ('  [OK] topic exists — appending discovery to ' + $Slug + '.md') -ForegroundColor Green
} else {
    Write-Host ('  [NEW] creating new topic ' + $Slug + '.md') -ForegroundColor Yellow
}

if (-not $Title) {
    Write-Host ''
    Write-Host '  One-line title (what is this discovery about?)' -ForegroundColor White
    $Title = Read-Host '  title'
}
if (-not $Title) { Write-Host '  [ABORT] title required.' -ForegroundColor Red; Start-Sleep 3; exit 3 }

if (-not $Status) {
    Write-Host ''
    Write-Host '  Status?' -ForegroundColor White
    Write-Host '    1) open         (discovered but no fix yet)' -ForegroundColor Gray
    Write-Host '    2) workaround   (workaround exists, not a real fix)' -ForegroundColor Gray
    Write-Host '    3) fixed        (real fix shipped — apply this automatically)' -ForegroundColor Gray
    Write-Host '    4) known-issue  (documented, confirmed, no fix)' -ForegroundColor Gray
    Write-Host '    5) (no change)  (just adding a discovery to existing topic)' -ForegroundColor Gray
    $sp = Read-Host '  choice [default=5 if existing, 1 if new]'
    $statusMap = @{ '1'='open'; '2'='workaround'; '3'='fixed'; '4'='known-issue'; '5'='' }
    if (-not $sp) { $sp = if ($existing) { '5' } else { '1' } }
    $Status = if ($statusMap.ContainsKey($sp)) { $statusMap[$sp] } else { $sp }
}

if (-not $Body) {
    Write-Host ''
    Write-Host '  Body (problem + finding + fix; multi-line; Ctrl+Z+Enter to finish)' -ForegroundColor White
    $bodyLines = @()
    while ($true) {
        $line = Read-Host
        if ($line -eq $null) { break }
        $bodyLines += $line
    }
    $Body = ($bodyLines -join "`n").TrimEnd()
}

# Post to local Sanctum Console API if it's up
$agent = if ($env:SINISTER_AGENT_NAME) { $env:SINISTER_AGENT_NAME } else { 'operator (manual)' }
$payload = @{
    slug = $Slug
    agent = $agent
    kind = 'discovery'
    title = $Title
    body = $Body
}
if ($Status) { $payload.new_status = $Status }

$consoleUp = $false
try {
    $null = Invoke-RestMethod -Uri 'http://127.0.0.1:5077/api/health' -TimeoutSec 1 -ErrorAction Stop
    $consoleUp = $true
} catch {}

if ($consoleUp) {
    Write-Host ''
    Write-Host '  Posting to Sanctum Console /api/knowledge/append...' -ForegroundColor DarkGray
    try {
        $res = Invoke-RestMethod -Uri 'http://127.0.0.1:5077/api/knowledge/append' -Method POST `
            -ContentType 'application/json' -Body ($payload | ConvertTo-Json -Depth 6) -TimeoutSec 5
        Write-Host ('  [OK] ' + $res.action + ' -> ' + $res.path) -ForegroundColor Green
    } catch {
        Write-Host ('  [WARN] Console rejected: ' + $_.Exception.Message + ' - falling back to direct write') -ForegroundColor Yellow
        $consoleUp = $false
    }
}

if (-not $consoleUp) {
    # Direct file write
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm')
    $filePath = Join-Path $BrainDir "$Slug.md"
    $newEntry = "### $ts by $agent`n$Body`n`n"
    if (Test-Path $filePath) {
        $text = Get-Content $filePath -Raw
        $pivot = $text.IndexOf('## Discoveries')
        if ($pivot -ge 0) {
            $insertAt = $text.IndexOf("`n", $pivot) + 1
            $insertAt = $text.IndexOf("`n", $insertAt + 1) + 1
            $newText = $text.Substring(0, $insertAt) + "`n" + $newEntry + $text.Substring($insertAt)
        } else {
            $newText = $text.TrimEnd() + "`n`n## Discoveries`n`n" + $newEntry
        }
        [System.IO.File]::WriteAllText($filePath, $newText, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  [OK] appended to $filePath" -ForegroundColor Green
    } else {
        $tmpl = @"
> **Author:** $agent :: $($ts.Split()[0])

# Topic: $Title

**Slug:** $Slug
**First discovered:** $ts by $agent
**Last updated:** $ts by $agent
**Status:** $(if ($Status) { $Status } else { 'open' })
**Tags:** (add tags)

## Problem

$Body

## Why it happens

(root cause TBD)

## Fix or workaround

(TBD)

## Discoveries (append-only log, most-recent at top)

### $ts by $agent
$Body
"@
        [System.IO.File]::WriteAllText($filePath, $tmpl, [System.Text.UTF8Encoding]::new($false))
        Write-Host "  [OK] created new topic: $filePath" -ForegroundColor Green
    }
}

# Runlog
$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) {
    . $runlogHelper
    $log = Start-Runlog -Script 'log-knowledge'
    Add-RunlogStep -Log $log -Name 'append' -Ok $true -Summary "$Slug :: $Title"
    Set-RunlogOutput -Log $log -Key 'slug' -Value $Slug
    Set-RunlogOutput -Log $log -Key 'title' -Value $Title
    $null = Save-Runlog -Log $log -AutoClose $true
}

Write-Host ''
Write-Host '  The Sanctum brain grew by one. Every future agent will read this.' -ForegroundColor DarkGray
Write-Host '  Window auto-closes in 4 seconds.' -ForegroundColor DarkGray
Start-Sleep -Seconds 4
exit 0
