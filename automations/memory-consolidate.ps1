# Sinister Sanctum :: nightly memory consolidation cron
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
# Purpose: jcode background-consolidation parity. Runs `forge-memory consolidate`
#   across every namespace under _shared-memory/forge-memory/ then appends a
#   summary line to _shared-memory/consolidate-history.jsonl. Idempotent;
#   safe to run multiple times per day.

param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$Namespace = '',          # empty = all namespaces
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$startUtc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

$memRoot   = Join-Path $SanctumRoot '_shared-memory\forge-memory'
$bridgeDir = Join-Path $SanctumRoot 'tools\forge-memory-bridge'
$logPath   = Join-Path $SanctumRoot '_shared-memory\consolidate-history.jsonl'

function Write-Status($msg, $color = 'White') {
    if (-not $Quiet) { Write-Host "[memory-consolidate] $msg" -ForegroundColor $color }
}

if (-not (Test-Path $memRoot)) {
    Write-Status "forge-memory root not found: $memRoot" 'Yellow'
    Write-Status "Nothing to consolidate. Exiting clean." 'DarkGray'
    exit 0
}

# Pick namespaces
if ($Namespace) {
    $namespaces = @($Namespace)
} else {
    $namespaces = Get-ChildItem -Path $memRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notlike '_*' } |
        Select-Object -ExpandProperty Name
}

if (-not $namespaces -or $namespaces.Count -eq 0) {
    Write-Status "no namespaces under $memRoot" 'DarkGray'
    exit 0
}

Write-Status "starting consolidation @ $startUtc" 'Cyan'
Write-Status "namespaces: $($namespaces -join ', ')" 'DarkGray'
if ($DryRun) { Write-Status "DRY RUN — no changes will be written" 'Yellow' }

# Try to call forge-memory CLI. If not installed (`pip install -e .` not done),
# fall back to invoking the module directly via python.
$cliCmd  = (Get-Command 'forge-memory' -ErrorAction SilentlyContinue)
$pythonCmd = (Get-Command 'python' -ErrorAction SilentlyContinue)
if (-not $cliCmd -and -not $pythonCmd) {
    Write-Status "neither 'forge-memory' nor 'python' on PATH; cannot consolidate" 'Red'
    exit 2
}

$summary = @{
    _author     = 'RKOJ-ELENO :: 2026-05-21'
    started_utc = $startUtc
    dry_run     = $DryRun.IsPresent
    namespaces  = @{}
}

foreach ($ns in $namespaces) {
    Write-Status "consolidating namespace: $ns" 'White'
    $args = @('consolidate', '--namespace', $ns)
    if ($DryRun) { $args += '--dry-run' }

    try {
        if ($cliCmd) {
            $out = & forge-memory @args 2>&1 | Out-String
        } else {
            # Use python -m forge_memory_bridge with the same args
            $out = & python -m forge_memory_bridge @args 2>&1 | Out-String
        }
        # The CLI prints a JSON summary; capture parse + record.
        try {
            $parsed = $out | ConvertFrom-Json -ErrorAction Stop
            $summary.namespaces[$ns] = @{
                scanned          = $parsed.scanned
                duplicates_found = $parsed.duplicates_found
                merged           = $parsed.merged
                ok               = $true
            }
            Write-Status "  -> scanned=$($parsed.scanned) dupes=$($parsed.duplicates_found) merged=$($parsed.merged)" 'Green'
        } catch {
            $summary.namespaces[$ns] = @{ ok = $false; raw = $out.Trim() }
            Write-Status "  -> non-JSON output (raw stored)" 'Yellow'
        }
    } catch {
        $summary.namespaces[$ns] = @{ ok = $false; error = $_.Exception.Message }
        Write-Status "  -> ERROR: $($_.Exception.Message)" 'Red'
    }
}

$summary.finished_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

# Append to history
New-Item -ItemType Directory -Force -Path (Split-Path $logPath) | Out-Null
$jsonLine = ($summary | ConvertTo-Json -Depth 8 -Compress)
Add-Content -Path $logPath -Value $jsonLine -Encoding UTF8

Write-Status "logged -> $logPath" 'DarkGray'
Write-Status "done." 'Cyan'
exit 0
