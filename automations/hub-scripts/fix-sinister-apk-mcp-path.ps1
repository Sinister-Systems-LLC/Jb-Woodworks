# fix-sinister-apk-mcp-path.ps1 - one-shot operator script.
# Audit agent flagged 2026-05-18: ~/.claude/.mcp.json had sinister-apk's cwd
# pointing at C:\Users\Zonia\Desktop\Sinister-Snap-APK-\mcp-server (folder
# does not exist). Actual module location:
#   C:\Users\Zonia\Desktop\Kernel-SU-Setup\leo-version\mcp-server\sinister_apk_mcp\
#
# This script:
#  - Backs up .mcp.json (timestamped)
#  - Rewrites the sinister-apk cwd to the correct path
#  - Writes without BOM (PS 5.1 default writes BOM, breaks Python json.loads)

[CmdletBinding()]
param(
    [string]$McpJson = "$env:USERPROFILE\.claude\.mcp.json",
    [string]$NewCwd = 'C:\Users\Zonia\Desktop\Kernel-SU-Setup\leo-version\mcp-server',
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'fix-sinister-apk-mcp-path'

if (-not (Test-Path $McpJson)) {
    Write-Host "FAIL: $McpJson not found" -ForegroundColor Red
    Add-RunlogStep -Log $log -Name 'load' -Ok $false -Summary "missing $McpJson"
    Save-Runlog -Log $log -AutoClose $false | Out-Null
    exit 1
}

if (-not (Test-Path $NewCwd)) {
    Write-Host "FAIL: target path does not exist: $NewCwd" -ForegroundColor Red
    Add-RunlogStep -Log $log -Name 'verify-target' -Ok $false -Summary "missing $NewCwd"
    Save-Runlog -Log $log -AutoClose $false | Out-Null
    exit 1
}

# Backup
$bak = "$McpJson.bak.$(Get-Date -Format yyyyMMdd-HHmmss)"
Copy-Item $McpJson $bak -Force
Write-Host "Backup -> $bak" -ForegroundColor DarkGray

# Read + parse
try {
    $raw = [System.IO.File]::ReadAllBytes($McpJson)
    # Strip BOM if present
    if ($raw.Length -ge 3 -and $raw[0] -eq 0xEF -and $raw[1] -eq 0xBB -and $raw[2] -eq 0xBF) {
        $text = [System.Text.UTF8Encoding]::new($false).GetString($raw[3..($raw.Length-1)])
    } else {
        $text = [System.Text.UTF8Encoding]::new($false).GetString($raw)
    }
    $mcp = $text | ConvertFrom-Json
} catch {
    Write-Host "FAIL: parse $McpJson : $($_.Exception.Message)" -ForegroundColor Red
    Add-RunlogStep -Log $log -Name 'parse' -Ok $false -Summary $_.Exception.Message
    Save-Runlog -Log $log -AutoClose $false | Out-Null
    exit 1
}

if (-not $mcp.mcpServers.'sinister-apk') {
    Write-Host "sinister-apk not registered; nothing to fix" -ForegroundColor Yellow
    Add-RunlogStep -Log $log -Name 'check' -Ok $true -Summary 'not registered'
    Save-Runlog -Log $log -AutoClose $true | Out-Null
    exit 0
}

$oldCwd = $mcp.mcpServers.'sinister-apk'.cwd
Write-Host ("OLD cwd: {0}" -f $oldCwd)
Write-Host ("NEW cwd: {0}" -f $NewCwd) -ForegroundColor Green

if ($DryRun) {
    Write-Host "[DRY-RUN] no changes written" -ForegroundColor Yellow
    Add-RunlogStep -Log $log -Name 'dryrun' -Ok $true -Summary "would update cwd"
    Save-Runlog -Log $log -AutoClose $true | Out-Null
    exit 0
}

$mcp.mcpServers.'sinister-apk'.cwd = $NewCwd

# Atomic write without BOM
$json = ($mcp | ConvertTo-Json -Depth 10)
$tmp  = "$McpJson.tmp.$([guid]::NewGuid().Guid)"
[System.IO.File]::WriteAllBytes($tmp, [System.Text.UTF8Encoding]::new($false).GetBytes($json))
Move-Item -Path $tmp -Destination $McpJson -Force

Write-Host ""
Write-Host "[OK] sinister-apk cwd updated. Restart Claude Code." -ForegroundColor Green

Add-RunlogStep -Log $log -Name 'update-cwd' -Ok $true -Summary "$oldCwd -> $NewCwd"
Set-RunlogOutput -Log $log -Key 'old_cwd' -Value $oldCwd
Set-RunlogOutput -Log $log -Key 'new_cwd' -Value $NewCwd
Set-RunlogOutput -Log $log -Key 'backup' -Value $bak
Add-RunlogNextAction -Log $log -Action 'Operator: restart Claude Code so the corrected sinister-apk path takes effect.'
$manifestPath = Save-Runlog -Log $log -AutoClose $true
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray

if (-not $Quiet) { Start-Sleep -Seconds 4 }
exit 0
