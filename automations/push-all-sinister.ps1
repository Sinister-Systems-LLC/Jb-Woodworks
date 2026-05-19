# push-all-sinister.ps1 â€” loops Sanctum + 4 product repos and reports status.
#
# Default mode = DRY-RUN (just reports per-repo status â€” branch, ahead/behind,
# dirty, scrub-status, remote). Operator passes -Live to actually push.
#
# Each repo gated by secret-scrub via git-toolkit.ps1 safe-push (which already
# refuses on any scrub hit). Never force-pushes. Refuses on detached HEAD.
#
# Operator runs via C:\Users\Zonia\Desktop\Push-All-Sinister.bat.

[CmdletBinding()]
param(
    [switch]$Live,
    [string[]]$Only = @(),
    [string[]]$Skip = @()
)

$ErrorActionPreference = 'Continue'

# Load runlog helper
$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) { . $runlogHelper }
$log = if (Get-Command Start-Runlog -ErrorAction SilentlyContinue) { Start-Runlog -Script 'push-all-sinister' } else { $null }

# Repo registry (in push order)
$Repos = @(
    @{ name='sanctum';            path='D:\Sinister Sanctum';                                                  remote='git@github.com:Sinister-Systems-LLC/Sinister-Sanctum.git';        needs_init=$true  }
    @{ name='snap-emu';           path='D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source';        remote='git@github.com:Sinister-Systems-LLC/Sinister-Snap-API-EMU.git';   needs_init=$false }
    @{ name='tiktok-emu';         path='D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU\source';      remote='git@github.com:Sinister-Systems-LLC/Sinister-TikTok-API-EMU.git'; needs_init=$true  }
    @{ name='panel';              path='D:\Sinister\01_Projects\Sinister\Sinister-Panel\source';           remote='git@github.com:Sinister-Systems-LLC/Sinister-Panel.git';          needs_init=$false }
    @{ name='kernel-apk';         path='D:\Sinister\01_Projects\Sinister\Sinister-APK';                    remote='git@github.com:Sinister-Systems-LLC/Sinister-Kernel-APK.git';     needs_init=$true  }
)

# Apply -Only / -Skip filters
if ($Only.Count -gt 0)  { $Repos = $Repos | Where-Object { $Only -contains $_.name } }
if ($Skip.Count -gt 0)  { $Repos = $Repos | Where-Object { $Skip -notcontains $_.name } }

$mode = if ($Live) { 'LIVE PUSH' } else { 'DRY-RUN (status report only)' }
Write-Host '==============================================' -ForegroundColor Cyan
Write-Host "  Push-All-Sinister :: $mode" -ForegroundColor Cyan
Write-Host '==============================================' -ForegroundColor Cyan
Write-Host ''

$report = @()

foreach ($r in $Repos) {
    $name = $r.name
    $path = $r.path
    Write-Host "[$name] $path" -ForegroundColor Yellow

    if (-not (Test-Path $path)) {
        Write-Host "  [SKIP] path does not exist" -ForegroundColor DarkYellow
        $report += [pscustomobject]@{ name=$name; status='missing'; branch=''; ahead=''; behind=''; dirty=''; pushed=$false }
        if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $false -Summary 'path missing' }
        continue
    }

    Push-Location $path
    try {
        # Init check (presence of .git is not enough; must be a real repo)
        $hasGit = Test-Path '.git'
        $isRealRepo = $false
        if ($hasGit) {
            $null = cmd /c 'git rev-parse --is-inside-work-tree >NUL 2>NUL'
            $isRealRepo = ($LASTEXITCODE -eq 0)
        }
        if (-not $isRealRepo) {
            $gitMsg = if ($hasGit) { '.git/ exists but is corrupted/empty' } elseif ($r.needs_init) { 'needs init before push' } else { 'skipping' }
            Write-Host "  [INFO] no usable repo - $gitMsg" -ForegroundColor DarkGray
            $report += [pscustomobject]@{ name=$name; status='no-git'; branch=''; ahead=''; behind=''; dirty=''; pushed=$false }
            if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $true -Summary "no usable git repo: $gitMsg" }
            continue
        }

        # Branch + ahead/behind
        $branchRaw = & git rev-parse --abbrev-ref HEAD 2>$null
        $branch = if ($branchRaw) { ($branchRaw | Out-String).Trim() } else { '' }
        $ahead = 0; $behind = 0
        if ($branch -and $branch -ne 'HEAD') {
            $abRaw = (& git rev-list --left-right --count "origin/$branch...HEAD" 2>$null)
            if ($abRaw) {
                $parts = $abRaw.Trim() -split '\s+'
                if ($parts.Count -eq 2) { $behind = [int]$parts[0]; $ahead = [int]$parts[1] }
            }
        }
        $dirtyRaw = (& git status --porcelain 2>$null)
        $dirtyLines = if ($dirtyRaw) { ($dirtyRaw -split "`n").Count } else { 0 }

        Write-Host ("  branch={0,-12} ahead={1,3} behind={2,3} dirty={3,4} lines" -f $branch, $ahead, $behind, $dirtyLines) -ForegroundColor DarkGray

        if (-not $Live) {
            $report += [pscustomobject]@{ name=$name; status='ready'; branch=$branch; ahead=$ahead; behind=$behind; dirty=$dirtyLines; pushed=$false }
            if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $true -Summary "dry: branch=$branch ahead=$ahead dirty=$dirtyLines" }
            continue
        }

        # LIVE mode: delegate to git-toolkit.ps1 safe-push (does secret-scrub + push)
        $toolkit = 'D:\Sinister Sanctum\automations\git-toolkit.ps1'
        if (-not (Test-Path $toolkit)) {
            Write-Host "  [FAIL] git-toolkit.ps1 not found" -ForegroundColor Red
            $report += [pscustomobject]@{ name=$name; status='no-toolkit'; branch=$branch; ahead=$ahead; behind=$behind; dirty=$dirtyLines; pushed=$false }
            if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $false -Summary 'git-toolkit missing' }
            continue
        }

        # For sanctum (needs init + initial commit), use the dedicated orchestrator
        if ($name -eq 'sanctum') {
            $sanctumPs1 = 'D:\Sinister Sanctum\automations\sanctum-to-github.ps1'
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $sanctumPs1 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
            $rc = $LASTEXITCODE
            $pushed = ($rc -eq 0)
            $statusStr = if ($pushed) { 'pushed' } else { "failed-$rc" }
            $report += [pscustomobject]@{ name=$name; status=$statusStr; branch=$branch; ahead=$ahead; behind=$behind; dirty=$dirtyLines; pushed=$pushed }
            if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $pushed -Summary "sanctum-to-github exit=$rc" }
            continue
        }

        # Other repos: safe-push (secret-scrub first, then push)
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $toolkit safe-push $path 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        $rc = $LASTEXITCODE
        $pushed = ($rc -eq 0)
        $statusStr = if ($pushed) { 'pushed' } else { "failed-$rc" }
        $report += [pscustomobject]@{ name=$name; status=$statusStr; branch=$branch; ahead=$ahead; behind=$behind; dirty=$dirtyLines; pushed=$pushed }
        if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $pushed -Summary "safe-push exit=$rc" }
    }
    finally { Pop-Location }

    Write-Host ''
}

Write-Host '==============================================' -ForegroundColor Cyan
Write-Host '  SUMMARY' -ForegroundColor Cyan
Write-Host '==============================================' -ForegroundColor Cyan
$report | Format-Table -AutoSize | Out-String | Write-Host

if (-not $Live) {
    Write-Host ''
    Write-Host 'This was a DRY-RUN. To actually push, re-run with -Live:' -ForegroundColor Yellow
    Write-Host '  powershell -File "D:\Sinister Sanctum\automations\push-all-sinister.ps1" -Live' -ForegroundColor Yellow
    Write-Host '  (or use the bat that prompts: C:\Users\Zonia\Desktop\Push-All-Sinister.bat)' -ForegroundColor Yellow
    if ($log) { Add-RunlogNextAction -Log $log -Action 'Operator: review dry-run report; re-run with -Live to push' }
}

if ($log) { Save-Runlog -Log $log -AutoClose ($Live -eq $false) | Out-Null }
exit 0
