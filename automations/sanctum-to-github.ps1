# sanctum-to-github.ps1 â€” one-click push of Sanctum to GitHub.
#
# Idempotent:
#   - If no .git/ -> git init + branch main + add remote + initial commit + push
#   - If .git/ exists -> stage changes + commit (if any) + push
#   - Secret-scrub gate FIRST every time; abort on any hit
#   - Refuses on detached HEAD or if origin URL doesn't match expected
#   - Never force-pushes
#
# Operator runs via C:\Users\Zonia\Desktop\Push-Sanctum-To-GitHub.bat.

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$ExpectedRemote = 'git@github.com:Sinister-Systems-LLC/Sinister-Sanctum.git',
    [string]$ExpectedRemoteHttps = 'https://github.com/Sinister-Systems-LLC/Sinister-Sanctum.git',
    [string]$CommitMessage = '',
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'

# Load runlog helper
$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) { . $runlogHelper }
$log = if (Get-Command Start-Runlog -ErrorAction SilentlyContinue) { Start-Runlog -Script 'sanctum-to-github' } else { $null }

function Out-Step($name, $ok, $summary='') {
    $color = if ($ok) { 'Green' } else { 'Red' }
    $marker = if ($ok) { '[OK]' } else { '[FAIL]' }
    Write-Host ("  {0} {1}  {2}" -f $marker, $name, $summary) -ForegroundColor $color
    if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $ok -Summary $summary }
}

Write-Host '=== Sanctum -> GitHub ===' -ForegroundColor Cyan
Write-Host "  root: $SanctumRoot"
Write-Host "  remote: $ExpectedRemote"
Write-Host ''

if (-not (Test-Path $SanctumRoot)) {
    Out-Step 'resolve' $false "Sanctum root not found: $SanctumRoot"
    if ($log) { Save-Runlog -Log $log -AutoClose $false | Out-Null }
    exit 1
}

Push-Location $SanctumRoot
try {
    # === 1. Secret-scrub gate ===
    $scrubPs1 = Join-Path $SanctumRoot 'automations\secret-scrub.ps1'
    if (Test-Path $scrubPs1) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scrubPs1 -LLCRoot $SanctumRoot -Quiet 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        $scrubRc = $LASTEXITCODE
        if ($scrubRc -ne 0) {
            Out-Step 'secret-scrub' $false "exit $scrubRc -- ABORTING push"
            if ($log) {
                Add-RunlogNextAction -Log $log -Action 'Review secret-scrub findings + fix BEFORE re-running push bat'
                Save-Runlog -Log $log -AutoClose $false | Out-Null
            }
            Pop-Location
            Write-Host ''
            Write-Host '[ABORT] secret-scrub found something. Fix it, then re-run.' -ForegroundColor Red
            exit 2
        }
        Out-Step 'secret-scrub' $true 'clean'
    } else {
        Out-Step 'secret-scrub' $false 'scrub script missing - REFUSING to push without scrub'
        if ($log) { Save-Runlog -Log $log -AutoClose $false | Out-Null }
        Pop-Location
        exit 3
    }

    # === 2. Ensure git initialized ===
    $isNew = $false
    if (-not (Test-Path '.git')) {
        if ($DryRun) {
            Out-Step 'git-init' $true 'DRY: would init + add remote + initial commit'
        } else {
            $null = cmd /c 'git init >NUL 2>NUL'
            $null = cmd /c 'git branch -m main >NUL 2>NUL'
            Out-Step 'git-init' ($LASTEXITCODE -eq 0) 'init + branch main'
            $isNew = $true
        }
    } else {
        Out-Step 'git-init' $true 'repo already initialized'
    }

    # === 3. Ensure remote ===
    if (-not $DryRun) {
        $existingRemote = (& git remote get-url origin 2>$null)
        if (-not $existingRemote) {
            & git remote add origin $ExpectedRemote 2>&1 | Out-Null
            Out-Step 'remote-add' ($LASTEXITCODE -eq 0) "origin = $ExpectedRemote"
        } elseif ($existingRemote -ne $ExpectedRemote -and $existingRemote -ne $ExpectedRemoteHttps) {
            Out-Step 'remote-check' $false "origin mismatch: have='$existingRemote' want='$ExpectedRemote'. NOT changing automatically -- fix manually if intentional."
            if ($log) { Save-Runlog -Log $log -AutoClose $false | Out-Null }
            Pop-Location
            exit 4
        } else {
            Out-Step 'remote-check' $true "origin OK ($existingRemote)"
        }
    }

    # === 4. Status + stage ===
    $statusRaw = if ($DryRun -or $isNew) { '' } else { (& git status --porcelain 2>&1 | Out-String).Trim() }
    if ($isNew -and -not $DryRun) { $statusRaw = '(initial commit pending)' }
    Write-Host "    status: $($statusRaw -split "`n" | Measure-Object).Count line(s) of change" -ForegroundColor DarkGray

    if (-not $DryRun) {
        & git add -A 2>&1 | Out-Null
        Out-Step 'git-add' ($LASTEXITCODE -eq 0) 'staged all'
    }

    # === 5. Commit (only if there are staged changes) ===
    if (-not $DryRun) {
        $null = cmd /c 'git diff --cached --quiet'
        $hasStaged = ($LASTEXITCODE -ne 0)
        if ($hasStaged) {
            if (-not $CommitMessage) {
                $stamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm UTC')
                $CommitMessage = if ($isNew) { 'init: initial Sinister Sanctum shipment' } else { "sync: Sanctum auto-push @ $stamp" }
            }
            $tmp = New-TemporaryFile
            [System.IO.File]::WriteAllText($tmp.FullName, $CommitMessage, [System.Text.UTF8Encoding]::new($false))
            & git commit -F $tmp.FullName 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
            Remove-Item $tmp.FullName -Force -ErrorAction SilentlyContinue
            Out-Step 'commit' ($LASTEXITCODE -eq 0) "msg: $CommitMessage"
        } else {
            Out-Step 'commit' $true 'nothing to commit'
        }
    } else {
        Out-Step 'commit' $true 'DRY: would commit if changes'
    }

    # === 6. Branch sanity ===
    if (-not $DryRun) {
        $branchRaw = & git rev-parse --abbrev-ref HEAD 2>$null
        $branch = if ($branchRaw) { ($branchRaw | Out-String).Trim() } else { '' }
        if (-not $branch -or $branch -eq 'HEAD') {
            Out-Step 'branch-check' $false 'detached HEAD - refusing to push'
            if ($log) { Save-Runlog -Log $log -AutoClose $false | Out-Null }
            Pop-Location
            exit 5
        }
        Out-Step 'branch-check' $true "branch=$branch"
    }

    # === 7. Push ===
    if ($DryRun) {
        Out-Step 'push' $true 'DRY: would git push -u origin main'
    } else {
        $branchRaw = & git rev-parse --abbrev-ref HEAD 2>$null
        $branch = if ($branchRaw) { ($branchRaw | Out-String).Trim() } else { '' }
        & git push -u origin $branch 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
        $pushRc = $LASTEXITCODE
        if ($pushRc -eq 0) {
            Out-Step 'push' $true "pushed branch=$branch to origin"
        } else {
            Out-Step 'push' $false "exit $pushRc -- check auth + remote"
            if ($log) {
                Add-RunlogNextAction -Log $log -Action "git push failed (exit $pushRc). Check that you've authenticated with GitHub (gh auth login, or SSH key)."
                Save-Runlog -Log $log -AutoClose $false | Out-Null
            }
            Pop-Location
            exit 6
        }
    }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host '=== DONE ===' -ForegroundColor Cyan
Write-Host "  Sanctum is now in sync with $ExpectedRemote" -ForegroundColor Green
Write-Host ''

if ($log) {
    if ($isNew) {
        Add-RunlogNextAction -Log $log -Action 'Check https://github.com/Sinister-Systems-LLC/Sinister-Sanctum to confirm initial commit landed.'
    }
    Save-Runlog -Log $log -AutoClose $true | Out-Null
}
exit 0
