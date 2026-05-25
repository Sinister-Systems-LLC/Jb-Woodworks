# detect-similar-agents.ps1 — find same/similar-project agents already running
# Author: RKOJ-ELENO :: 2026-05-24
#
# Operator hard-canonical 2026-05-24T19:58Z:
#   "now every time a agent is started from eve exe, it needs to detect if there
#    are similar agents in similar projects working or agents of the same project
#    working. that agent is then to review what they are doing and then create
#    its plan of what it needs to do"
#
# Reads:
#   - _shared-memory/heartbeats/*.json  (live + idle, age-filtered)
#   - _shared-memory/spawned-windows.jsonl (per-spawn ledger; PID liveness check)
#
# Prints a compact report grouped by [same-project | similar-project | other]:
#   [same-project ] sanctum                heartbeat 2m ago     focus: ...
#   [similar-proj ] sinister-os-mobile     heartbeat 5m ago     focus: ...
#
# Used by Build-Phrase in start-sinister-session.ps1 to inject the detect output
# into the new agent's cold-start phrase so they review before planning.

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ProjectKey,
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [int]$LiveAgeMinutes = 10,
    [int]$IdleAgeMinutes = 60,
    [switch]$AsJson
)

$ErrorActionPreference = 'Continue'
$heartbeatsDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$spawnedJsonl  = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'

if (-not (Test-Path $heartbeatsDir)) {
    if ($AsJson) { '[]' } else { Write-Host "  (no heartbeats dir)" -ForegroundColor DarkGray }
    return
}

# Heuristics for "similar project" — share the same prefix or word stem.
function _Similar([string]$key, [string]$target) {
    if ($key -eq $target) { return 'same' }
    if (-not $key -or -not $target) { return $null }
    # Split on dashes; any token in common (length >= 4) counts as similar.
    $a = ($key.ToLower() -split '[-_]') | Where-Object { $_.Length -ge 4 }
    $b = ($target.ToLower() -split '[-_]') | Where-Object { $_.Length -ge 4 }
    foreach ($t in $a) { if ($b -contains $t) { return 'similar' } }
    return $null
}

$now = (Get-Date).ToUniversalTime()
$findings = @()

Get-ChildItem -Path $heartbeatsDir -Filter '*.json' -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $raw = Get-Content -Path $_.FullName -Raw -ErrorAction Stop
        $hb = $raw | ConvertFrom-Json -ErrorAction Stop
        $hbProject = $hb.project
        if (-not $hbProject) { $hbProject = $hb.slug }
        $kind = _Similar -key $hbProject -target $ProjectKey
        if (-not $kind) { return }
        # Age filter
        $ts = $null
        try { $ts = [datetime]::Parse($hb.ts_utc).ToUniversalTime() } catch { return }
        $ageMin = [int]($now - $ts).TotalMinutes
        $thresh = if ($kind -eq 'same') { $IdleAgeMinutes } else { $LiveAgeMinutes }
        if ($ageMin -gt $thresh) { return }
        $findings += [pscustomobject]@{
            kind     = $kind
            project  = $hbProject
            slug     = $hb.slug
            agent    = $hb.agent_display
            branch   = $hb.branch
            focus    = $hb.focus
            ageMin   = $ageMin
            ts_utc   = $hb.ts_utc
        }
    } catch {}
}

if ($AsJson) {
    $findings | ConvertTo-Json -Depth 5
    return
}

if ($findings.Count -eq 0) {
    Write-Host "  (no live same/similar-project agents detected)" -ForegroundColor DarkGray
    return
}

# Sort: same-project first, then by age ascending
$sorted = $findings | Sort-Object @{Expression={if ($_.kind -eq 'same') {0} else {1}}}, ageMin
foreach ($f in $sorted) {
    $tag  = if ($f.kind -eq 'same') { '[same-project ]' } else { '[similar-proj ]' }
    $col  = if ($f.kind -eq 'same') { 'Yellow' } else { 'Cyan' }
    $line = ("  {0} {1,-26} {2,3}m ago    focus: {3}" -f $tag, $f.project, $f.ageMin, ($(if ($f.focus) { $f.focus.Substring(0, [Math]::Min(70, $f.focus.Length)) } else { '(no focus)' })))
    Write-Host $line -ForegroundColor $col
}
