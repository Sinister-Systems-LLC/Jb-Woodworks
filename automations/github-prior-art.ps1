# github-prior-art.ps1 :: search GitHub for pre-made code before building from scratch.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Wraps `gh search repos` with the fleet's github-first sourcing doctrine defaults:
#   - sort by stars (desc)
#   - filter to permissive licenses by default (MIT,Apache-2.0,BSD-3-Clause,BSD-2-Clause)
#   - filter to active repos (updated within the last 12 months)
#   - minimum 100 stars (drop toy repos)
#   - return top 5 candidates as a printable table
#
# Zero-burn: no Anthropic / LLM calls; just `gh` invocations. Honors GH_TOKEN env.
# Doctrine: _shared-memory/knowledge/github-first-sourcing-doctrine-2026-05-24.md
#
# Usage:
#   .\github-prior-art.ps1 -Topic "rate-limit watchdog python"
#   .\github-prior-art.ps1 -Topic "qpu cloud sdk" -License "MIT,Apache-2.0" -MinStars 50
#   .\github-prior-art.ps1 -Topic "websocket server" -Language go -Limit 10
#   .\github-prior-art.ps1 -Topic "auth token store" -Json   # for downstream piping
#
# Exit codes:
#   0  - 1+ candidates printed
#   2  - gh CLI not installed / not on PATH
#   3  - gh search returned non-JSON (auth or rate-limit failure)
#   4  - zero candidates matched (try broader topic / relax filters)

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Topic,

    # Permissive licenses by default. Comma-separated SPDX keys (lowercase).
    # `gh search repos --license` accepts: mit, apache-2.0, bsd-3-clause, bsd-2-clause, isc, unlicense, etc.
    [string]$License = 'mit,apache-2.0,bsd-3-clause,bsd-2-clause',

    [int]$MinStars = 100,

    [string]$Language = '',

    [int]$Limit = 5,

    # Months-back to filter "active". Default 12.
    [int]$ActiveMonths = 12,

    # Output JSON instead of table (for piping into operator-inbox / other automations).
    [switch]$Json,

    # Drop the active filter (return repos even if they haven't been touched in 12 months).
    [switch]$AllowStale
)

$ErrorActionPreference = 'Stop'

# --- 1. gh availability check ---
$gh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $gh) {
    Write-Host '[github-prior-art] gh CLI not on PATH.' -ForegroundColor Red
    Write-Host '  Install: https://cli.github.com/  (or `winget install GitHub.cli`)' -ForegroundColor Yellow
    exit 2
}

# --- 2. Build search args ---
# We over-fetch (limit * 3, capped at 30) so we can rank/trim post-query.
$fetchN = [Math]::Min(30, [Math]::Max(15, $Limit * 3))

# Compute the "updated since" date (ISO yyyy-MM-dd) for active filter.
$activeSince = (Get-Date).AddMonths(-1 * $ActiveMonths).ToString('yyyy-MM-dd')

$ghArgs = @(
    'search', 'repos', $Topic,
    '--sort', 'stars',
    '--order', 'desc',
    '--limit', "$fetchN",
    '--json', 'fullName,description,stargazersCount,updatedAt,license,url'
)

if ($License) {
    $licList = ($License -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }) -join ','
    if ($licList) {
        $ghArgs += @('--license', $licList)
    }
}
if ($Language) {
    $ghArgs += @('--language', $Language)
}
if (-not $AllowStale) {
    # gh accepts >YYYY-MM-DD for date qualifier
    $ghArgs += @('--updated', ">$activeSince")
}

# --- 3. Invoke gh ---
$invocationLine = 'gh ' + ($ghArgs | ForEach-Object { if ($_ -match '\s') { "`"$_`"" } else { $_ } }) -join ' '
if (-not $Json) {
    Write-Host ''
    Write-Host '[github-prior-art] invocation:' -ForegroundColor DarkMagenta
    Write-Host "  $invocationLine" -ForegroundColor DarkGray
    Write-Host ''
}

$raw = ''
try {
    $raw = & gh @ghArgs 2>&1 | Out-String
} catch {
    Write-Host "[github-prior-art] gh invocation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 3
}

if (-not $raw -or -not ($raw.Trim().StartsWith('['))) {
    Write-Host '[github-prior-art] gh returned non-JSON (check auth / GH_TOKEN / rate-limit):' -ForegroundColor Red
    Write-Host $raw -ForegroundColor DarkGray
    exit 3
}

try {
    $rows = $raw | ConvertFrom-Json
} catch {
    Write-Host "[github-prior-art] JSON parse failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 3
}

if (-not $rows -or $rows.Count -eq 0) {
    Write-Host '[github-prior-art] zero candidates. Try broader keywords or relax filters.' -ForegroundColor Yellow
    Write-Host "  Suggestion: .\\github-prior-art.ps1 -Topic '$Topic' -MinStars 10 -AllowStale" -ForegroundColor DarkGray
    exit 4
}

# --- 4. Post-filter on MinStars + shape ---
$candidates = @()
foreach ($r in $rows) {
    if ($r.stargazersCount -lt $MinStars) { continue }
    $licName = if ($r.license -and $r.license.key) { $r.license.key } else { '(none)' }
    $upd = if ($r.updatedAt) { ([datetime]$r.updatedAt).ToString('yyyy-MM-dd') } else { '?' }
    $desc = if ($r.description) {
        $d = "$($r.description)" -replace '\s+', ' '
        if ($d.Length -gt 80) { $d.Substring(0, 77) + '...' } else { $d }
    } else { '(no description)' }
    $candidates += [PSCustomObject]@{
        rank = 0
        name = $r.fullName
        stars = $r.stargazersCount
        last_commit = $upd
        license = $licName
        description = $desc
        url = $r.url
    }
}

if ($candidates.Count -eq 0) {
    Write-Host "[github-prior-art] zero candidates passed MinStars=$MinStars filter." -ForegroundColor Yellow
    Write-Host "  Suggestion: lower -MinStars (e.g. 10) or broaden -Topic." -ForegroundColor DarkGray
    exit 4
}

# Trim to requested Limit and assign rank
$candidates = $candidates | Select-Object -First $Limit
$i = 1
foreach ($c in $candidates) { $c.rank = $i; $i++ }

# --- 5. Emit ---
if ($Json) {
    $out = [PSCustomObject]@{
        topic = $Topic
        invocation = $invocationLine
        searched_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        license_filter = $License
        min_stars = $MinStars
        active_since = $(if ($AllowStale) { 'any' } else { $activeSince })
        language = $Language
        candidate_count = $candidates.Count
        candidates = $candidates
    }
    $out | ConvertTo-Json -Depth 5
    exit 0
}

Write-Host '[github-prior-art] candidates (sorted by stars, desc):' -ForegroundColor Cyan
Write-Host ''
$candidates | Format-Table -AutoSize -Wrap -Property rank, stars, last_commit, license, name, description

Write-Host ''
Write-Host '[github-prior-art] URLs (for README/license/contributor review per doctrine step 3):' -ForegroundColor DarkMagenta
foreach ($c in $candidates) {
    Write-Host ("  [{0}] {1}" -f $c.rank, $c.url) -ForegroundColor DarkGray
}

Write-Host ''
Write-Host '[github-prior-art] next step per doctrine:' -ForegroundColor DarkMagenta
Write-Host '  1. Read README + LICENSE on top 3.' -ForegroundColor DarkGray
Write-Host '  2. Surface candidates to operator inbox (per-project lanes) OR inline (Sanctum master).' -ForegroundColor DarkGray
Write-Host '  3. Fork or vendor with NOTICE-RKOJ-ELENO.md attribution.' -ForegroundColor DarkGray
Write-Host '  Doctrine: _shared-memory/knowledge/github-first-sourcing-doctrine-2026-05-24.md' -ForegroundColor DarkGray
Write-Host ''

exit 0
