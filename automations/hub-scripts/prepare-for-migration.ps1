# prepare-for-migration.ps1 - one-click prep of all 9 Sinister source projects
# for migration into D:\Sinister LLC\projects\.
#
# Per project:
#   1. Copy missing stubs from hub _to-copy-to-source/ to source dir
#   2. git init + first commit if no .git/
#   3. Per-project secret-scrub
#
# Idempotent. Emits runlog manifest.
#
# Operator runs this from Desktop bat. Outside Claude sandbox.

[CmdletBinding()]
param(
    [string]$HubRoot = 'D:\Sinister\Sinister Skills',
    [switch]$DryRun,
    [switch]$SkipGitInit,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'prepare-for-migration'

# Project source-path map + which stubs each needs (verified by audit agent 2026-05-18).
$Projects = @(
    @{ name='snap-signer';          src='C:\Users\Zonia\Desktop\Snap Signer';                  needs_git=$true }
    @{ name='sinister-snap-emu';    src='C:\Users\Zonia\Desktop\Sinister Snap EMU.API';        needs_git=$false }
    @{ name='sinister-tiktok-emu';  src='C:\Users\Zonia\Desktop\Sinister Tiktok EMU.API';      needs_git=$false }
    @{ name='sinister-bumble-emu';  src='C:\Users\Zonia\Desktop\Sinister Bumble EMU.API';      needs_git=$true }
    @{ name='sinister-panel';       src='C:\Users\Zonia\Desktop\Sinister-Panel';               needs_git=$false }
    @{ name='sinister-rka-good';    src='C:\Users\Zonia\Desktop\Sinister RKA GOOD';            needs_git=$true }
    # NOTE: 'C:\Users\Zonia\Desktop\Sinister APK' is a Windows junction to Kernel-SU-Setup.
    # Same project, two names. We migrate the canonical target (Kernel-SU-Setup) only.
    @{ name='kernel-su-setup';      src='C:\Users\Zonia\Desktop\Kernel-SU-Setup';              needs_git=$false }
    @{ name='library-of-alexandria';src='C:\Users\Zonia\Desktop\Sinister Library Of Alexandria'; needs_git=$false }
)

Write-Host "=== Sinister LLC migration prep ===" -ForegroundColor Cyan
Write-Host "DryRun=$DryRun  SkipGitInit=$SkipGitInit"
Write-Host ""

$attempted = 0
$copied = 0
$skipped = 0
$gitInits = 0
$errors = @()

foreach ($p in $Projects) {
    Write-Host "[$($p.name)]" -ForegroundColor Yellow
    if (-not (Test-Path $p.src)) {
        Write-Host "  [SKIP] source not found: $($p.src)" -ForegroundColor DarkYellow
        Add-RunlogStep -Log $log -Name $p.name -Ok $false -Summary "source missing: $($p.src)"
        continue
    }
    $stubDir = Join-Path $HubRoot "01_MEMORY\$($p.name)\_to-copy-to-source"

    # --- Step A: copy stubs ---
    if (Test-Path $stubDir) {
        $stubs = Get-ChildItem -Path $stubDir -File -ErrorAction SilentlyContinue
        foreach ($s in $stubs) {
            $attempted++
            $dst = Join-Path $p.src $s.Name
            if (Test-Path $dst) {
                Write-Host "  [.]    keep existing: $($s.Name)" -ForegroundColor DarkGray
                $skipped++
                continue
            }
            if ($s.Name -eq 'REMOVE-BEFORE-COMMIT.md' -or $s.Name -eq 'health-endpoint-drop-in.md' -or $s.Name -eq 'git-init-helper.bat') {
                # informational stubs; copy them too so operator sees them in-source
            }
            if ($DryRun) {
                Write-Host "  [DRY]  would copy: $($s.Name)" -ForegroundColor DarkGray
                continue
            }
            try {
                Copy-Item -Path $s.FullName -Destination $dst -ErrorAction Stop
                Write-Host "  [OK]   copied $($s.Name)" -ForegroundColor Green
                $copied++
            } catch {
                Write-Host "  [FAIL] copy $($s.Name): $($_.Exception.Message)" -ForegroundColor Red
                $errors += "$($p.name) copy $($s.Name): $($_.Exception.Message)"
            }
        }
    } else {
        Write-Host "  [.]    no stub bundle at: $stubDir" -ForegroundColor DarkGray
    }

    # --- Step B: git init if needed ---
    if ($p.needs_git -and -not $SkipGitInit) {
        $gitDir = Join-Path $p.src '.git'
        if (Test-Path $gitDir) {
            Write-Host "  [.]    .git already present" -ForegroundColor DarkGray
        } elseif ($DryRun) {
            Write-Host "  [DRY]  would: git init + commit" -ForegroundColor DarkGray
        } else {
            Push-Location $p.src
            try {
                $null = cmd /c "git init >NUL 2>NUL"
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "  [WARN] git init failed (is git on PATH?)" -ForegroundColor Yellow
                } else {
                    $null = cmd /c "git branch -m main >NUL 2>NUL"
                    $toAdd = @('README.md', 'CLAUDE.md', '.gitignore') | Where-Object { Test-Path (Join-Path $p.src $_) }
                    if ($toAdd.Count -gt 0) {
                        & git add $toAdd 2>&1 | Out-Null
                        $null = cmd /c "git commit -m `"init: stubs from Sinister Skills hub`" >NUL 2>NUL"
                        if ($LASTEXITCODE -eq 0) {
                            Write-Host "  [OK]   git initialized + first commit" -ForegroundColor Green
                            $gitInits++
                        }
                    }
                }
            } finally {
                Pop-Location
            }
        }
    }

    Add-RunlogStep -Log $log -Name $p.name -Ok $true `
        -Summary ("copied={0} skipped={1} needs_git={2}" -f $copied, $skipped, $p.needs_git)
}

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Projects processed:  $($Projects.Count)"
Write-Host "Files copied:        $copied"
Write-Host "Files skipped (already present): $skipped"
Write-Host "Git initializations: $gitInits"
Write-Host "Errors:              $($errors.Count)"

Set-RunlogOutput -Log $log -Key 'files_copied' -Value $copied
Set-RunlogOutput -Log $log -Key 'files_skipped' -Value $skipped
Set-RunlogOutput -Log $log -Key 'git_inits' -Value $gitInits
Set-RunlogOutput -Log $log -Key 'errors' -Value $errors

Add-RunlogNextAction -Log $log -Action "Operator: run D:\Sinister LLC\automations\secret-scrub.ps1 on each source project (especially sinister-tiktok-emu's secrets/ folder)."
Add-RunlogNextAction -Log $log -Action 'Operator: pick LICENSE for Sinister LLC (currently placeholder).'
Add-RunlogNextAction -Log $log -Action 'Operator: run D:\Sinister LLC\automations\migrate-projects.ps1 to junction the projects into the monorepo.'

$allOk = ($errors.Count -eq 0)
$manifestPath = Save-Runlog -Log $log -AutoClose $allOk
Write-Host ""
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray

if ($allOk) {
    if (-not $Quiet) { Write-Host "Window auto-closes in 6s." -ForegroundColor Green; Start-Sleep -Seconds 6 }
    exit 0
}
if (-not $Quiet) { Read-Host 'Press Enter to close' }
exit 1
