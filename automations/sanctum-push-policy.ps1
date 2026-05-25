# sanctum-push-policy.ps1 :: pre-push policy enforcement helper
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator hard-canonical 2026-05-25 ~00:50Z: every project pushes to
# Sinister-Sanctum origin EXCEPT 3 carved-out projects (LetsText,
# Showmasters, JB Woodworks) which keep their own remote.
#
# Modes:
#   -Action Check          -- check the current dir's origin URL against
#                             policy. Exit 0 = OK, 1 = violation.
#   -Action Audit          -- emit full audit table for all projects in
#                             projects.json. Exit 0 always (informational).
#   -Action CheckPath -Path -- check a specific dir's origin URL
#                              (used by sanctum-auto-push.ps1 pre-push).
#
# Policy source-of-truth = automations/session-templates/projects.json
# field per project = `github` (e.g. "Sinister-Systems-LLC/Sinister-Panel").
#
# Carve-outs (per-project allow-list for non-Sanctum remotes):
#   - jb-woodworks   -> Sinister-Systems-LLC/Jb-Woodworks
#   - showmasters    -> Sinister-Systems-LLC/Showmasters
#   - letstext       -> operator-private external_root, no enforcement
#
# Composes with: docs/BRANCH-CONVENTION.md +
# _shared-memory/knowledge/single-repo-push-policy-2026-05-25.md.

[CmdletBinding()]
param(
    [ValidateSet('Check','Audit','CheckPath')]
    [string]$Action = 'Audit',
    [string]$Path = '',
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Continue'

# Carve-outs: project keys whose canonical push target is NOT Sanctum.
$CarveOuts = @{
    'jb-woodworks'  = 'Sinister-Systems-LLC/Jb-Woodworks'
    'showmasters'   = 'Sinister-Systems-LLC/Showmasters'
    'letstext'      = $null  # operator-private; no enforcement
}

# Canonical Sanctum repo (the everything-else target).
$SanctumRepo = 'Sinister-Systems-LLC/Sinister-Sanctum'

function Get-Projects {
    $registry = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
    if (-not (Test-Path $registry)) {
        Write-Host "FAIL: projects.json not found at $registry" -ForegroundColor Red
        exit 2
    }
    return (Get-Content -LiteralPath $registry -Raw | ConvertFrom-Json).projects
}

function Get-OriginUrl {
    param([string]$RepoPath)
    if (-not (Test-Path (Join-Path $RepoPath '.git'))) { return $null }
    $url = & git -C $RepoPath remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return $url.Trim()
}

function Match-PolicyRepo {
    # Accept any URL containing the canonical "owner/repo" substring,
    # whether https://github.com/owner/repo.git, git@github.com:owner/repo.git,
    # or local Gitea mirrors. Case-insensitive.
    param([string]$Url, [string]$OwnerRepo)
    if (-not $Url -or -not $OwnerRepo) { return $false }
    return ($Url -match [regex]::Escape($OwnerRepo))
}

function Resolve-PolicyForPath {
    # Map a working dir to its expected canonical push target.
    # Returns @{ key=...; expected=...; carve_out=$bool }.
    param([string]$WorkingDir)
    $abs = (Resolve-Path -LiteralPath $WorkingDir -ErrorAction SilentlyContinue).Path
    if (-not $abs) { return $null }
    $projects = Get-Projects
    # Find the LONGEST matching root (so projects/sinister-panel/source matches
    # the sinister-panel key, not the sanctum root key which is a prefix of everything).
    $best = $null
    $bestLen = -1
    foreach ($p in $projects) {
        if (-not $p.root) { continue }
        $root = $p.root.TrimEnd('\','/')
        if ($abs.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)) {
            if ($root.Length -gt $bestLen) {
                $best = $p
                $bestLen = $root.Length
            }
        }
    }
    if ($best) {
        $key = $best.key
        if ($CarveOuts.ContainsKey($key)) {
            return @{ key=$key; expected=$CarveOuts[$key]; carve_out=$true }
        }
        return @{ key=$key; expected=$SanctumRepo; carve_out=$false }
    }
    # Default: Sanctum
    return @{ key='sanctum'; expected=$SanctumRepo; carve_out=$false }
}

function Action-Check {
    param([string]$WorkingDir = (Get-Location).Path)
    $policy = Resolve-PolicyForPath -WorkingDir $WorkingDir
    if (-not $policy) {
        Write-Host "FAIL: cannot resolve project policy for $WorkingDir" -ForegroundColor Red
        exit 2
    }
    if (-not $policy.expected) {
        # LetsText-class: external_root, no enforcement
        Write-Host "OK: $($policy.key) is operator-private (no policy enforcement)" -ForegroundColor DarkGray
        exit 0
    }
    $url = Get-OriginUrl -RepoPath $WorkingDir
    if (-not $url) {
        # No .git here = nothing to enforce; whatever parent .git handles it.
        Write-Host "OK: no embedded .git at $WorkingDir (commits route to parent)" -ForegroundColor DarkGray
        exit 0
    }
    if (Match-PolicyRepo -Url $url -OwnerRepo $policy.expected) {
        Write-Host "OK: $($policy.key) origin matches policy ($($policy.expected))" -ForegroundColor Green
        exit 0
    }
    Write-Host "FAIL: $($policy.key) origin=$url violates policy (expected $($policy.expected))" -ForegroundColor Red
    Write-Host "      Consolidate via: remove $WorkingDir\.git\ so files commit to Sanctum root, OR add the carve-out exception." -ForegroundColor Yellow
    exit 1
}

function Action-Audit {
    Write-Host ""
    Write-Host "Sanctum push-policy audit -- $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" -ForegroundColor Magenta
    Write-Host ("-" * 90)
    $rowFmt = "{0,-32} {1,-12} {2,-44}"
    Write-Host ($rowFmt -f 'project', 'verdict', 'detail')
    Write-Host ("-" * 90)

    # 1. Root
    $rootUrl = Get-OriginUrl -RepoPath $SanctumRoot
    $rootOk = Match-PolicyRepo -Url $rootUrl -OwnerRepo $SanctumRepo
    $verdict = if ($rootOk) { 'OK' } else { 'VIOLATION' }
    $rootColor = if ($rootOk) { 'Green' } else { 'Red' }
    Write-Host ($rowFmt -f 'sanctum (root)', $verdict, $rootUrl) -ForegroundColor $rootColor

    # 2. Each projects/* subdir
    $projectsDir = Join-Path $SanctumRoot 'projects'
    if (-not (Test-Path $projectsDir)) {
        Write-Host "WARN: projects dir not found at $projectsDir" -ForegroundColor Yellow
        return
    }
    foreach ($d in (Get-ChildItem -Path $projectsDir -Directory)) {
        $name = $d.Name
        $candidates = @($d.FullName, (Join-Path $d.FullName 'source'), (Join-Path $d.FullName 'site'))
        foreach ($c in $candidates) {
            if (Test-Path (Join-Path $c '.git')) {
                $url = Get-OriginUrl -RepoPath $c
                # Resolve policy by walking projects.json
                $policy = Resolve-PolicyForPath -WorkingDir $c
                $expected = if ($policy -and $policy.expected) { $policy.expected } else { $SanctumRepo }
                $ok = Match-PolicyRepo -Url $url -OwnerRepo $expected
                $verdict = if ($ok) { 'OK' } elseif (-not $url) { 'NO-REMOTE' } else { 'VIOLATION' }
                $disp = "$name" + $(if ($c -ne $d.FullName) { '/' + (Split-Path -Leaf $c) } else { '' })
                $detail = if ($url) { $url } else { '(no remote configured)' }
                $color = if ($verdict -eq 'OK') { 'Green' } elseif ($verdict -eq 'NO-REMOTE') { 'Yellow' } else { 'Red' }
                Write-Host ($rowFmt -f $disp, $verdict, $detail) -ForegroundColor $color
            }
        }
    }
    Write-Host ("-" * 90)
    Write-Host "Legend: OK = matches policy; VIOLATION = origin URL diverges; NO-REMOTE = embedded .git with no origin." -ForegroundColor DarkGray
    exit 0
}

switch ($Action) {
    'Check'     { Action-Check -WorkingDir (Get-Location).Path }
    'CheckPath' {
        if (-not $Path) { Write-Host "FAIL: -Path required for CheckPath" -ForegroundColor Red; exit 2 }
        Action-Check -WorkingDir $Path
    }
    'Audit'     { Action-Audit }
}
