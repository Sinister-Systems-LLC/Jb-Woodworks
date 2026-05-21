# Sinister Sanctum :: Claude Code hooks + plugin-cache cleanup
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
# Purpose: when Claude Code starts misbehaving (corrupted plugin cache or
# broken local hooks), wipe both directories so Claude Code rebuilds them
# fresh on next launch. Safe-by-default (uses SilentlyContinue for missing
# paths) + interactive press-any-key exit so the operator sees the result.

# Requires -Version 3.0

Write-Host "Fixing Claude Code hook and cache paths..." -ForegroundColor Cyan

# Define the paths based on user profile
$cachePath = Join-Path $env:USERPROFILE ".claude\plugins\cache"
$hooksPath = Join-Path $env:USERPROFILE ".claude\hooks"

# Remove the corrupted cache directory
if (Test-Path $cachePath) {
    Remove-Item -Path $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Cleared plugin cache: $cachePath" -ForegroundColor Green
} else {
    Write-Host "[INFO] Plugin cache already clean or not found." -ForegroundColor DarkGray
}

# Remove any lingering broken hooks
if (Test-Path $hooksPath) {
    Remove-Item -Path $hooksPath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Cleared local hooks: $hooksPath" -ForegroundColor Green
} else {
    Write-Host "[INFO] Hooks dir already clean or not found." -ForegroundColor DarkGray
}

Write-Host "`nFix applied successfully. You can now restart Claude Code." -ForegroundColor Cyan
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
