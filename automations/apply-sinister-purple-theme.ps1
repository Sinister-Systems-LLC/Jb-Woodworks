# apply-sinister-purple-theme.ps1 - propagate the Sinister Purple Obsidian theme
# (abstract + purple + glowing, with graph-view "mind" theming) to every _vault
# under D:\Sinister and D:\Sinister Sanctum.
#
# Operator-run. Idempotent (re-running just re-syncs the latest snippet).
#
# What it does per vault:
#   1. mkdir <vault>/.obsidian/snippets/ if missing
#   2. Copy sinister-purple.css from the canonical Sanctum location
#   3. Write/merge appearance.json:  accentColor=#a855f7, theme=moonstone, enabledCssSnippets+=sinister-purple
#   4. Write/merge app.json:         enabledCssSnippets+=sinister-purple
#
# Usage:
#   D:\Sinister Sanctum\automations\apply-sinister-purple-theme.ps1
#   D:\Sinister Sanctum\automations\apply-sinister-purple-theme.ps1 -DryRun

[CmdletBinding()]
param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'

$canonicalSnippet = 'D:\Sinister Sanctum\_vault\.obsidian\snippets\sinister-purple.css'
if (-not (Test-Path $canonicalSnippet)) {
    Write-Host "FAIL: canonical snippet not found: $canonicalSnippet" -ForegroundColor Red
    exit 1
}
Write-Host "Canonical snippet: $canonicalSnippet ($((Get-Item $canonicalSnippet).Length) B)" -ForegroundColor Cyan
Write-Host ""

# Discover every _vault on D: (skip the canonical one itself - already configured)
$vaults = @(
    'D:\Sinister Sanctum\_vault'
    'D:\Sinister\_vault'
) + (Get-ChildItem 'D:\Sinister\01_Projects\Sinister' -Directory -ErrorAction SilentlyContinue |
       Where-Object { Test-Path (Join-Path $_.FullName '_vault') } |
       ForEach-Object { Join-Path $_.FullName '_vault' })

Write-Host "Vaults discovered: $($vaults.Count)" -ForegroundColor Cyan
$vaults | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
Write-Host ""

$ok = 0
$skip = 0
$fail = 0

foreach ($vault in $vaults) {
    if (-not (Test-Path $vault)) {
        Write-Host "[SKIP] vault does not exist: $vault" -ForegroundColor DarkYellow
        $skip++
        continue
    }
    Write-Host "[$($vaults.IndexOf($vault)+1)/$($vaults.Count)] $vault" -ForegroundColor Yellow

    $obsidianDir = Join-Path $vault '.obsidian'
    $snippetsDir = Join-Path $obsidianDir 'snippets'
    $targetSnippet = Join-Path $snippetsDir 'sinister-purple.css'
    $appearancePath = Join-Path $obsidianDir 'appearance.json'
    $appPath = Join-Path $obsidianDir 'app.json'

    if ($DryRun) {
        Write-Host "  [DRY] would create $snippetsDir + copy snippet + update appearance.json + app.json" -ForegroundColor DarkGray
        $ok++
        continue
    }

    try {
        if (-not (Test-Path $snippetsDir)) {
            New-Item -ItemType Directory -Path $snippetsDir -Force | Out-Null
        }
        # Copy snippet (overwrite - latest from Sanctum is canonical)
        Copy-Item -LiteralPath $canonicalSnippet -Destination $targetSnippet -Force
        Write-Host "  copied snippet: $targetSnippet" -ForegroundColor Green

        # Merge appearance.json
        $appearance = if (Test-Path $appearancePath) {
            Get-Content $appearancePath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json -ErrorAction SilentlyContinue
        } else { [pscustomobject]@{} }
        if ($null -eq $appearance) { $appearance = [pscustomobject]@{} }
        $merged = @{
            accentColor          = '#a855f7'
            theme                = 'moonstone'
            baseFontSize         = 16
            cssTheme             = ''
            enabledCssSnippets   = @('sinister-purple')
            translucency         = $false
        }
        # Preserve any other fields the operator set
        foreach ($k in ($appearance | Get-Member -MemberType NoteProperty).Name) {
            if (-not $merged.ContainsKey($k)) {
                $merged[$k] = $appearance.$k
            }
        }
        # Ensure 'sinister-purple' is in the enabled list (don't drop existing snippets)
        if ($appearance.PSObject.Properties.Name -contains 'enabledCssSnippets') {
            $existing = @($appearance.enabledCssSnippets)
            if ('sinister-purple' -notin $existing) {
                $merged.enabledCssSnippets = ($existing + 'sinister-purple') | Select-Object -Unique
            } else {
                $merged.enabledCssSnippets = $existing | Select-Object -Unique
            }
        }
        $merged | ConvertTo-Json -Depth 5 | Set-Content $appearancePath -Encoding utf8
        Write-Host "  wrote appearance.json (accent=#a855f7, snippet enabled)" -ForegroundColor Green

        # Merge app.json - only ensure the snippet is listed
        $app = if (Test-Path $appPath) {
            Get-Content $appPath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json -ErrorAction SilentlyContinue
        } else { [pscustomobject]@{} }
        if ($null -eq $app) { $app = [pscustomobject]@{} }
        $appMerged = @{ enabledCssSnippets = @('sinister-purple'); cssTheme = '' }
        foreach ($k in ($app | Get-Member -MemberType NoteProperty).Name) {
            if (-not $appMerged.ContainsKey($k)) { $appMerged[$k] = $app.$k }
        }
        if ($app.PSObject.Properties.Name -contains 'enabledCssSnippets') {
            $existingApp = @($app.enabledCssSnippets)
            if ('sinister-purple' -notin $existingApp) {
                $appMerged.enabledCssSnippets = ($existingApp + 'sinister-purple') | Select-Object -Unique
            } else {
                $appMerged.enabledCssSnippets = $existingApp | Select-Object -Unique
            }
        }
        $appMerged | ConvertTo-Json -Depth 5 | Set-Content $appPath -Encoding utf8
        Write-Host "  wrote app.json (snippet enabled)" -ForegroundColor Green

        $ok++
    } catch {
        Write-Host "  FAIL: $($_.Exception.Message)" -ForegroundColor Red
        $fail++
    }
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Summary: $ok OK / $skip SKIP / $fail FAIL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open any vault in Obsidian - purple+glowing theme should auto-apply." -ForegroundColor Yellow
Write-Host "If a vault was already open, click Reload Without Saving or restart Obsidian." -ForegroundColor Yellow

if ($fail -gt 0) { exit 1 } else { exit 0 }
