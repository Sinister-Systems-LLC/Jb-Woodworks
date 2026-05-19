# migrate-projects.ps1 - junction the 8 Sinister-branded projects into D:\Sinister Sanctum\projects\
# Operator-run. Outside Claude's sandbox. Idempotent.

[CmdletBinding()]
param(
    [string]$LLCRoot = 'D:\Sinister Sanctum',
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'

# Load runlog helper
$RunlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $RunlogHelper) { . $RunlogHelper }
$log = if (Get-Command Start-Runlog -ErrorAction SilentlyContinue) { Start-Runlog -Script 'migrate-projects' } else { $null }

$projectsRoot = Join-Path $LLCRoot 'projects'
$botsRoot     = Join-Path $LLCRoot 'bots'
$null = New-Item -ItemType Directory -Force -Path $projectsRoot, $botsRoot

# 8 Sinister projects -> source path
$Projects = @(
    # Operator's NEW canonical layout (Phase 8w discovery): D:\Sinister\01_Projects\Sinister\
    # Per the master plan, other agents are robocopying source into these dirs.
    # We prefer 01_Projects paths; fall back to Desktop if 01_Projects entry doesn't exist yet.
    @{ name='snap-signer';          src='D:\Sinister\01_Projects\Sinister\Snap-Signer';              fallback='C:\Users\Zonia\Desktop\Snap Signer';                 needs_scrub=$false }
    @{ name='sinister-snap-emu';    src='D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU';        fallback='C:\Users\Zonia\Desktop\Sinister Snap EMU.API';       needs_scrub=$false }
    @{ name='sinister-tiktok-emu';  src='D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU';      fallback='C:\Users\Zonia\Desktop\Sinister Tiktok EMU.API';     needs_scrub=$true }
    @{ name='sinister-bumble-emu';  src='D:\Sinister\01_Projects\Sinister\Sinister-Bumble-EMU';      fallback='C:\Users\Zonia\Desktop\Sinister Bumble EMU.API';     needs_scrub=$true }
    @{ name='sinister-panel';       src='D:\Sinister\01_Projects\Sinister\Sinister-Panel';           fallback='C:\Users\Zonia\Desktop\Sinister-Panel';              needs_scrub=$false }
    @{ name='sinister-rka';         src='D:\Sinister\01_Projects\Sinister\Sinister-RKA';             fallback='C:\Users\Zonia\Desktop\Sinister RKA GOOD';           needs_scrub=$true }
    @{ name='sinister-apk';         src='D:\Sinister\01_Projects\Sinister\Sinister-APK';             fallback='C:\Users\Zonia\Desktop\Kernel-SU-Setup';             needs_scrub=$false }
    @{ name='kernel-su-setup';      src='D:\Sinister\01_Projects\Sinister\Kernel-SU-Setup';          fallback='C:\Users\Zonia\Desktop\Kernel-SU-Setup';             needs_scrub=$false }
    @{ name='library-of-alexandria';src='D:\Sinister\01_Projects\Sinister\Library-of-Alexandria';    fallback='C:\Users\Zonia\Desktop\Sinister Library Of Alexandria'; needs_scrub=$false }
    @{ name='sinister-emulator-bundle'; src='D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle'; fallback=''; needs_scrub=$false }
    @{ name='sinister-sandbox';     src='D:\Sinister\01_Projects\Sinister\Sinister-Sandbox';         fallback=''; needs_scrub=$false }
    @{ name='sinister-tg';          src='D:\Sinister\01_Projects\Sinister\Sinister-TG';              fallback=''; needs_scrub=$false }
    @{ name='sinister-imessage-bridge'; src='D:\Sinister\01_Projects\Sinister\Sinister-iMessage-Bridge'; fallback=''; needs_scrub=$false }
    @{ name='sinister-workstation-setup'; src='D:\Sinister\01_Projects\Sinister\Sinister-Workstation-Setup'; fallback=''; needs_scrub=$false }
)
# Resolve src -> use 01_Projects path if it exists, else fall back to Desktop
foreach ($p in $Projects) {
    if (-not (Test-Path $p.src) -and $p.fallback -and (Test-Path $p.fallback)) {
        $p.src = $p.fallback
    }
}

Write-Host "=== Migrate Sinister projects into $projectsRoot ===" -ForegroundColor Cyan
Write-Host ""

$successCount = 0
$failCount = 0
$scrubFlagged = @()

foreach ($p in $Projects) {
    $name = $p.name
    $src = $p.src
    $dst = Join-Path $projectsRoot $name
    Write-Host "[$name]" -ForegroundColor Yellow
    if (-not (Test-Path $src)) {
        Write-Host "  [SKIP] source not found: $src" -ForegroundColor DarkYellow
        if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $false -Summary "source missing: $src" }
        $failCount++
        continue
    }
    if (Test-Path $dst) {
        Write-Host "  [OK] junction already exists: $dst" -ForegroundColor Green
        if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $true -Summary 'already junctioned' }
        $successCount++
        if ($p.needs_scrub) { $scrubFlagged += $name }
        continue
    }
    if ($DryRun) {
        Write-Host "  [DRY] would: mklink /J `"$dst`" `"$src`"" -ForegroundColor DarkGray
        continue
    }
    $null = cmd /c "mklink /J `"$dst`" `"$src`" >NUL 2>NUL"
    if ($LASTEXITCODE -eq 0 -and (Test-Path $dst)) {
        Write-Host "  [OK] junctioned -> $src" -ForegroundColor Green
        if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $true -Summary "junction created" }
        $successCount++
        if ($p.needs_scrub) { $scrubFlagged += $name }
    } else {
        Write-Host "  [FAIL] mklink returned $LASTEXITCODE" -ForegroundColor Red
        if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $false -Summary "mklink fail: exit $LASTEXITCODE" }
        $failCount++
    }
}

# Mirror the 12 bots as junctions too
Write-Host ""
Write-Host "[bots] junction agents/" -ForegroundColor Yellow
$botsSrc = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents'
$botsDst = Join-Path $LLCRoot 'bots\agents'
if (Test-Path $botsDst) {
    Write-Host "  [OK] already junctioned: $botsDst" -ForegroundColor Green
} elseif ($DryRun) {
    Write-Host "  [DRY] would: mklink /J `"$botsDst`" `"$botsSrc`"" -ForegroundColor DarkGray
} else {
    $null = cmd /c "mklink /J `"$botsDst`" `"$botsSrc`" >NUL 2>NUL"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] bots junctioned" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] bots mklink returned $LASTEXITCODE" -ForegroundColor Red
    }
}

# Summary + scrub flag
Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Junctioned OK: $successCount / $($Projects.Count)"
Write-Host "Failed:        $failCount"
if ($scrubFlagged.Count -gt 0) {
    Write-Host ""
    Write-Host "REQUIRED BEFORE GIT COMMIT:" -ForegroundColor Red
    foreach ($n in $scrubFlagged) {
        Write-Host "  - $n  ->  .\automations\secret-scrub.ps1 -Path projects\$n" -ForegroundColor Red
    }
}

if ($log) {
    Set-RunlogOutput -Log $log -Key 'success' -Value $successCount
    Set-RunlogOutput -Log $log -Key 'fail' -Value $failCount
    if ($scrubFlagged.Count -gt 0) {
        foreach ($n in $scrubFlagged) {
            Add-RunlogNextAction -Log $log -Action "Operator: run .\automations\secret-scrub.ps1 -Path projects\$n before any git push."
        }
    }
    Add-RunlogNextAction -Log $log -Action "Operator: review LICENSE (currently placeholder); pick MIT / Apache / Proprietary."
    Add-RunlogNextAction -Log $log -Action "Operator: cd to D:\Sinister Sanctum; git init (when ready); add remote; git add -A; git commit."
    $manifestPath = Save-Runlog -Log $log -AutoClose $true
    Write-Host ""
    Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray
}

exit ($failCount -eq 0 ? 0 : 1)
