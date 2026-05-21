# Sinister Sanctum :: smoke-test-rkoj.ps1
# Author: RKOJ-ELENO :: 2026-05-21
# License: AGPL-3.0-or-later
#
# Post-build smoke test for RKOJ.exe.
# Validates imports, slash command dispatch, and basic boot before the
# operator ever clicks the .exe.

$ErrorActionPreference = "Stop"
$repo = "D:\Sinister Sanctum"
$results = @()

function Test-Step {
    param([string]$name, [scriptblock]$block)
    $start = Get-Date
    try {
        & $block | Out-Null
        $ms = ([math]::Round(((Get-Date) - $start).TotalMilliseconds))
        Write-Host "  [PASS] $name ($ms ms)" -ForegroundColor Green
        $script:results += [pscustomobject]@{ Name = $name; Status = "PASS"; Duration = $ms }
    } catch {
        Write-Host "  [FAIL] $name :: $_" -ForegroundColor Red
        $script:results += [pscustomobject]@{ Name = $name; Status = "FAIL"; Error = "$_" }
    }
}

Write-Host "RKOJ.exe smoke test :: $((Get-Date).ToString('HH:mm:ss'))" -ForegroundColor Cyan
Write-Host ""

# Phase 1: Python-side imports (these run BEFORE PyInstaller bundles)
Write-Host "Phase 1: Python imports" -ForegroundColor Yellow
$env:PYTHONPATH = "$repo\projects\sinister-forge\source;$repo\tools\sinister-login\src;$repo\tools\sinister-usage\src;$repo\tools\sinister-swarm\src;$repo\tools\sinister-model\src;$env:PYTHONPATH"
Test-Step "import forge.app" { python -c "from forge.app import ForgeApp" }
Test-Step "import forge.panes.sidebar" { python -c "from forge.panes.sidebar import Sidebar" }
Test-Step "import forge.panes.adb_panel" { python -c "from forge.panes.adb_panel import AdbPanel" }
Test-Step "import forge.commands" { python -c "from forge.commands import SLASH_COMMANDS, dispatch; print(len(SLASH_COMMANDS))" }
Test-Step "import forge.spawn.claude" { python -c "from forge.spawn.claude import ClaudeSubprocess" }
Test-Step "import sinister_login" { python -c "import sinister_login; print(sinister_login.__version__)" }
Test-Step "import sinister_usage" { python -c "import sinister_usage; print(sinister_usage.__version__)" }
Test-Step "import sinister_model (post-D)" { python -c "import sinister_model; print(sinister_model.__version__)" }
Test-Step "import anthropic SDK" { python -c "import anthropic; print(anthropic.__version__)" }

Write-Host ""
Write-Host "Phase 2: EXE artifact existence" -ForegroundColor Yellow
Test-Step "dist\RKOJ.exe exists" { if (-not (Test-Path "$repo\automations\build\forge-exe\dist\RKOJ.exe")) { throw "missing" } }
Test-Step "Desktop\RKOJ.exe exists" { if (-not (Test-Path "C:\Users\Zonia\Desktop\RKOJ.exe")) { throw "missing" } }

Write-Host ""
Write-Host "Phase 3: EXE --version no-hang test (5s timeout)" -ForegroundColor Yellow
Test-Step "RKOJ.exe --version returns" {
    $proc = Start-Process -FilePath "C:\Users\Zonia\Desktop\RKOJ.exe" -ArgumentList "--version" -PassThru -WindowStyle Hidden -RedirectStandardOutput "$env:TEMP\rkoj-ver.txt"
    if (-not $proc.WaitForExit(5000)) { $proc.Kill(); throw "hung past 5s" }
    if ($proc.ExitCode -ne 0) { throw "exit code $($proc.ExitCode)" }
}

Write-Host ""
$passes = ($results | Where-Object Status -eq "PASS").Count
$fails = ($results | Where-Object Status -eq "FAIL").Count
Write-Host "Summary: $passes pass / $fails fail" -ForegroundColor $(if ($fails -eq 0) { "Green" } else { "Red" })
if ($fails -gt 0) { exit 1 }
