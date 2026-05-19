# sync-from-github.ps1 - operator-triggered Sanctum pull from GitHub.
# Pulls Leo's latest into D:\Sinister Sanctum\ via `git pull --ff-only`.
# If working tree is dirty -> refuses + tells operator to commit/stash first.
# If clean + behind -> fast-forwards.
# Never force-pushes. Never overwrites. Always operator-triggered (no schedule).

[CmdletBinding()]
param(
    [string]$Root = 'D:\Sinister Sanctum',
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

. (Join-Path $PSScriptRoot 'hub-scripts\_runlog.ps1')
$log = Start-Runlog -Script 'sync-from-github'

if (-not (Test-Path $Root)) {
    Write-Host "FAIL: Sanctum root not found: $Root" -ForegroundColor Red
    Save-Runlog -Log $log -AutoClose $false | Out-Null
    exit 1
}

Push-Location $Root
try {
    if (-not (Test-Path '.git')) {
        Write-Host "[FAIL] $Root is not a git repository (no .git/). Initialize first with git init + remote add." -ForegroundColor Red
        Add-RunlogStep -Log $log -Name 'preflight' -Ok $false -Summary 'no .git'
        Save-Runlog -Log $log -AutoClose $false | Out-Null
        if (-not $Quiet) { Read-Host 'Press Enter to close' }
        exit 1
    }

    # Detect dirty working tree
    $dirty = & git status --porcelain 2>$null
    if ($dirty) {
        Write-Host "[ABORT] working tree has uncommitted changes:" -ForegroundColor Red
        $dirty | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" }
        Write-Host ""
        Write-Host "Commit or stash first, then re-run." -ForegroundColor Yellow
        Add-RunlogStep -Log $log -Name 'preflight' -Ok $false -Summary 'dirty working tree'
        Save-Runlog -Log $log -AutoClose $false | Out-Null
        if (-not $Quiet) { Read-Host 'Press Enter to close' }
        exit 1
    }
    Write-Host "[OK] working tree clean" -ForegroundColor Green

    # Fetch
    Write-Host "Fetching origin..." -ForegroundColor Cyan
    & git fetch origin 2>&1 | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[FAIL] fetch failed (no remote? offline? auth?)" -ForegroundColor Red
        Add-RunlogStep -Log $log -Name 'fetch' -Ok $false -Summary "exit $LASTEXITCODE"
        Save-Runlog -Log $log -AutoClose $false | Out-Null
        if (-not $Quiet) { Read-Host 'Press Enter to close' }
        exit 1
    }
    Add-RunlogStep -Log $log -Name 'fetch' -Ok $true -Summary 'origin fetched'

    # Determine branch + ahead/behind
    $branch = (& git rev-parse --abbrev-ref HEAD 2>$null).Trim()
    $ahead  = & cmd /c "git rev-list --count origin/$branch..HEAD 2>NUL"
    $behind = & cmd /c "git rev-list --count HEAD..origin/$branch 2>NUL"
    if (-not $ahead) { $ahead = '0' }
    if (-not $behind) { $behind = '0' }
    Write-Host ("Branch: {0}  ahead: {1}  behind: {2}" -f $branch, $ahead, $behind) -ForegroundColor Cyan

    Set-RunlogOutput -Log $log -Key 'branch' -Value $branch
    Set-RunlogOutput -Log $log -Key 'ahead' -Value ([int]$ahead)
    Set-RunlogOutput -Log $log -Key 'behind' -Value ([int]$behind)

    if ([int]$behind -eq 0) {
        Write-Host "[OK] already up to date" -ForegroundColor Green
        Add-RunlogStep -Log $log -Name 'pull' -Ok $true -Summary 'already up to date'
    } elseif ([int]$ahead -gt 0) {
        Write-Host "[WARN] local is BOTH ahead ($ahead) AND behind ($behind). Need to rebase / merge manually." -ForegroundColor Yellow
        Write-Host "       Refusing auto-pull to avoid silent merge." -ForegroundColor Yellow
        Add-RunlogStep -Log $log -Name 'pull' -Ok $false -Summary "ahead+behind; manual merge needed"
        Add-RunlogNextAction -Log $log -Action "Operator: cd '$Root'; git pull --rebase OR git merge origin/$branch (manual decision)."
    } else {
        if ($DryRun) {
            Write-Host "[DRY] would: git pull --ff-only ($behind commits behind)" -ForegroundColor DarkGray
            Add-RunlogStep -Log $log -Name 'pull' -Ok $true -Summary "dry-run: $behind commits"
        } else {
            Write-Host "Pulling $behind commits via fast-forward..." -ForegroundColor Green
            & git pull --ff-only 2>&1 | ForEach-Object { Write-Host "  $_" }
            $pullRc = $LASTEXITCODE
            Add-RunlogStep -Log $log -Name 'pull' -Ok ($pullRc -eq 0) -Summary "ff-pulled $behind commits"
        }
    }
} finally {
    Pop-Location
}

$allOk = ($log.errors.Count -eq 0)
$manifest = Save-Runlog -Log $log -AutoClose $allOk
Write-Host ""
Write-Host "Manifest: $manifest" -ForegroundColor DarkGray

if ($allOk) {
    if (-not $Quiet) { Write-Host "Auto-close in 8s..." -ForegroundColor Green; Start-Sleep -Seconds 8 }
    exit 0
}
if (-not $Quiet) { Read-Host "Some checks failed. Press Enter to close" }
exit 1
