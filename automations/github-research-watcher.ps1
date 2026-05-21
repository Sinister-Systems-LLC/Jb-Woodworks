# Sinister Sanctum :: github-research-watcher (v1 :: 2026-05-21)
#
# Operator directive: "C:\Users\Zonia\Desktop\Github Research placing things
# here we talked about and more. everything i place things here i need you
# to auto review them and add to system if they fit or we can expand from
# therm".
#
# Watches C:\Users\Zonia\Desktop\Github Research\ for new folders (operator
# drops repo zips / clones there). On detect:
#   1. Append to _shared-memory/inbox/test/github-research-imports.json
#   2. Write a stub audit-request at _shared-memory/plans/sinister-forge-2026-05-21/desktop-imports-audit.md
#   3. Trigger a Claude session (via cross-agent inbox) to review the import + decide USE / EVALUATE / SKIP
#
# Fired by bootstrap-portability.ps1 on every session start (so the next
# spawn picks up any new drops since last session). 6h gate prevents
# over-scanning during a busy operator-research session.
#
# Author: Sinister Sanctum master agent (test, Claude) :: 2026-05-21

param(
    [string]$SanctumRoot = '',
    [string]$WatchDir = 'C:\Users\Zonia\Desktop\Github Research',
    [switch]$Force,
    [switch]$Quiet
)

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}
if (-not (Test-Path $WatchDir)) {
    if (-not $Quiet) { Write-Host "[github-research-watcher] watch dir not found: $WatchDir" -ForegroundColor DarkGray }
    exit 0
}

$sentinelDir = Join-Path $SanctumRoot '_shared-memory\github-research-watch'
$sentinelFile = Join-Path $sentinelDir 'last-scan.json'
New-Item -ItemType Directory -Force -Path $sentinelDir | Out-Null

# 6h gate
$prevState = @{}
if ((Test-Path $sentinelFile) -and -not $Force) {
    try {
        $raw = Get-Content $sentinelFile -Raw -ErrorAction SilentlyContinue
        $prev = $raw | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($prev) {
            foreach ($p in $prev.PSObject.Properties) { $prevState[$p.Name] = $p.Value }
            $lastUtc = [datetime]::Parse($prev.last_scan_utc)
            $ageH = (([datetime]::UtcNow) - $lastUtc).TotalHours
            if ($ageH -lt 6) {
                if (-not $Quiet) { Write-Host ("[github-research-watcher] skip (last scan {0:N1}h ago, < 6h gate)" -f $ageH) -ForegroundColor DarkGray }
                exit 0
            }
        }
    } catch { }
}

# Scan top-level dirs + zips
$items = Get-ChildItem -Path $WatchDir -ErrorAction SilentlyContinue | Where-Object {
    $_.PSIsContainer -or $_.Extension -in @('.zip','.tar.gz','.tgz','.7z')
} | Sort-Object Name

$newItems = @()
$state = @{ last_scan_utc = ([datetime]::UtcNow).ToString('o'); items = @{} }
foreach ($it in $items) {
    $key = $it.Name
    $stamp = $it.LastWriteTime.ToString('o')
    $state.items[$key] = $stamp
    if (-not $prevState.ContainsKey('items') -or -not $prevState.items.PSObject.Properties.Name -contains $key) {
        $newItems += $it
    } elseif ($prevState.items.$key -ne $stamp) {
        $newItems += $it
    }
}

if ($newItems.Count -eq 0) {
    if (-not $Quiet) { Write-Host "[github-research-watcher] OK (no new drops)" -ForegroundColor DarkGray }
    ($state | ConvertTo-Json -Depth 4) | Out-File $sentinelFile -Encoding utf8
    exit 0
}

if (-not $Quiet) { Write-Host ("[github-research-watcher] {0} new item(s) in {1}" -f $newItems.Count, $WatchDir) -ForegroundColor Cyan }

# Append to inbox + audit-request
$auditDir = Join-Path $SanctumRoot '_shared-memory\plans\sinister-forge-2026-05-21'
New-Item -ItemType Directory -Force -Path $auditDir | Out-Null
$auditFile = Join-Path $auditDir 'desktop-imports-audit.md'

$header = "`n## Scan at $([datetime]::UtcNow.ToString('o'))`n"
$header | Out-File $auditFile -Encoding utf8 -Append
foreach ($it in $newItems) {
    $line = "- **$($it.Name)** ($($it.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))) - pending audit"
    $line | Out-File $auditFile -Encoding utf8 -Append
    if (-not $Quiet) { Write-Host "  [new] $($it.Name)" -ForegroundColor Cyan }
}

# Drop an inbox ASK so the next agent picks it up
$inboxDir = Join-Path $SanctumRoot '_shared-memory\inbox\test'
New-Item -ItemType Directory -Force -Path $inboxDir | Out-Null
$ts = (Get-Date -Format 'yyyyMMdd-HHmmss')
$inboxFile = Join-Path $inboxDir "$ts-github-research-imports.json"
$ask = @{
    tag = '[ASK]'
    from = 'github-research-watcher'
    to = 'test'
    ts_utc = ([datetime]::UtcNow).ToString('o')
    subject = "$($newItems.Count) new Github Research drop(s) need audit"
    new_items = @($newItems | ForEach-Object { @{ name = $_.Name; path = $_.FullName; mtime = $_.LastWriteTime.ToString('o') } })
    action_required = "Read each new item's README/LICENSE. Decide USE/EVALUATE/SKIP. If USE: integrate into projects/sinister-forge/ or appropriate project. If EVALUATE: clone to D:\Research\ (NOT Sanctum tree). If SKIP: document why in desktop-imports-audit.md."
    reply_to = "_shared-memory/plans/sinister-forge-2026-05-21/desktop-imports-audit.md"
}
($ask | ConvertTo-Json -Depth 4) | Out-File $inboxFile -Encoding utf8

# Update sentinel
($state | ConvertTo-Json -Depth 4) | Out-File $sentinelFile -Encoding utf8

if (-not $Quiet) { Write-Host ("[github-research-watcher] inbox ASK dropped: $inboxFile") -ForegroundColor Green }
