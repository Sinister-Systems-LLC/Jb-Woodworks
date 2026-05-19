# install-mcp-servers.ps1 - add the operator-reviewed MCP servers to ~/.claude/.mcp.json
#
# Adds (per docs/MCP-NEW-SERVERS.md master rec):
#   1. Playwright          - browser automation (complements stealth-browser)
#   2. Context7            - live library docs (kills hallucinations)
#   3. Sequential thinking - reasoning scaffold
#   4. KG memory           - cross-session persistent knowledge graph
# DEFERRED: Codex (needs custom OpenAI wiring; operator-decided to skip for now)
#
# Backs up the existing .mcp.json before modifying. Idempotent: skips servers
# already present.
#
# Operator MUST restart Claude Code after running this so the new servers load.

[CmdletBinding()]
param(
    [string]$McpPath = "$env:USERPROFILE\.claude\.mcp.json",
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Install MCP Servers'

$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) { . $runlogHelper }
$log = if (Get-Command Start-Runlog -ErrorAction SilentlyContinue) { Start-Runlog -Script 'install-mcp-servers' } else { $null }

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   I N S T A L L   M C P   S E R V E R S' -ForegroundColor White
Write-Host '   Playwright | Context7 | Sequential | KG-Memory' -ForegroundColor DarkGray
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''

if (-not (Test-Path $McpPath)) {
    Write-Host "[FAIL] $McpPath not found. Is Claude Code installed?" -ForegroundColor Red
    if ($log) { Save-Runlog -Log $log -AutoClose $false | Out-Null }
    exit 1
}

# Backup
$backup = "$McpPath.bak-$((Get-Date).ToString('yyyyMMddTHHmmss'))"
if (-not $DryRun) {
    Copy-Item $McpPath $backup -Force
    Write-Host "  [OK] backup -> $backup" -ForegroundColor Green
} else {
    Write-Host "  [DRY] would back up -> $backup" -ForegroundColor DarkGray
}

# Read existing
$json = Get-Content $McpPath -Raw | ConvertFrom-Json
if (-not $json.mcpServers) {
    Write-Host "[FAIL] .mcp.json has no mcpServers key" -ForegroundColor Red
    if ($log) { Save-Runlog -Log $log -AutoClose $false | Out-Null }
    exit 2
}

# Define new servers
$newServers = [ordered]@{
    'playwright' = [ordered]@{
        command = 'npx'
        args = @('-y', '@playwright/mcp@latest')
    }
    'context7' = [ordered]@{
        command = 'npx'
        args = @('-y', '@upstash/context7-mcp@latest')
    }
    'sequential-thinking' = [ordered]@{
        command = 'npx'
        args = @('-y', '@modelcontextprotocol/server-sequential-thinking')
    }
    'memory' = [ordered]@{
        command = 'npx'
        args = @('-y', '@modelcontextprotocol/server-memory')
        env = @{
            MEMORY_FILE_PATH = 'D:\Sinister\Sinister Skills\01_MEMORY\_kg-memory\graph.json'
        }
    }
}

$added = @()
$skipped = @()
foreach ($name in $newServers.Keys) {
    if ($json.mcpServers.$name) {
        Write-Host "  [SKIP] $name already present" -ForegroundColor DarkGray
        $skipped += $name
        if ($log) { Add-RunlogStep -Log $log -Name "check-$name" -Ok $true -Summary 'already present' }
    } else {
        if (-not $DryRun) {
            $json.mcpServers | Add-Member -MemberType NoteProperty -Name $name -Value ([pscustomobject]$newServers[$name])
        }
        Write-Host "  [ADD ] $name" -ForegroundColor Green
        $added += $name
        if ($log) { Add-RunlogStep -Log $log -Name "add-$name" -Ok $true -Summary 'added' }
    }
}

# Ensure KG memory dir exists
$kgDir = 'D:\Sinister\Sinister Skills\01_MEMORY\_kg-memory'
if (-not (Test-Path $kgDir)) {
    if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $kgDir | Out-Null }
    Write-Host "  [OK] created $kgDir for kg-memory persistence" -ForegroundColor Green
}

# Write back
if (-not $DryRun) {
    $newJsonText = $json | ConvertTo-Json -Depth 10
    [System.IO.File]::WriteAllText($McpPath, $newJsonText, [System.Text.UTF8Encoding]::new($false))
    Write-Host ''
    Write-Host "  [OK] wrote $McpPath" -ForegroundColor Green
} else {
    Write-Host ''
    Write-Host '  [DRY-RUN] no changes written' -ForegroundColor Yellow
}

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host "   SUMMARY: $($added.Count) added, $($skipped.Count) skipped" -ForegroundColor Cyan
Write-Host '  ============================================================' -ForegroundColor Magenta
if ($added.Count -gt 0) {
    Write-Host ''
    Write-Host '   ACTION REQUIRED: RESTART CLAUDE CODE to load the new servers.' -ForegroundColor Yellow
    Write-Host '   On first use, npx will fetch each package (Playwright ~150 MB Chromium).' -ForegroundColor DarkGray
    if ($log) {
        Add-RunlogNextAction -Log $log -Action "Restart Claude Code so new MCP servers ($($added -join ', ')) load."
        Add-RunlogNextAction -Log $log -Action 'On first use of Playwright, npx will download Chromium (~150 MB).'
    }
}
Write-Host ''

if ($log) { $null = Save-Runlog -Log $log -AutoClose ($added.Count -gt 0) }

if (-not $Quiet) {
    Write-Host '  Window auto-closes in 15s. Ctrl+C to keep open.' -ForegroundColor DarkGray
    Start-Sleep -Seconds 15
}
exit 0
