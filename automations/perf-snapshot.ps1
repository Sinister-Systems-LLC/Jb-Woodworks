# perf-snapshot.ps1
# Author: RKOJ-ELENO :: 2026-05-24
# On-demand diagnostic capture for the freeze triad
# (agents freezing, PC slow, EVE.exe won't close).
# Composes with: perf-freeze-root-cause-2026-05-24.md.
# Writes a timestamped snapshot to _shared-memory/perf-snapshots/.

[CmdletBinding()]
param(
    [string]$Tag = 'manual',
    [switch]$Quiet
)

$ErrorActionPreference = 'SilentlyContinue'
$sanctum = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
$outDir = Join-Path $sanctum '_shared-memory\perf-snapshots'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$outFile = Join-Path $outDir "$ts-$Tag.txt"

$lines = New-Object System.Collections.Generic.List[string]
function Add-Section { param($title, $body) $lines.Add(''); $lines.Add('=== ' + $title + ' ==='); $lines.Add($body) }

# Memory
$os = Get-CimInstance Win32_OperatingSystem
$totalMB = [math]::Round($os.TotalVisibleMemorySize / 1KB, 0)
$freeMB = [math]::Round($os.FreePhysicalMemory / 1KB, 0)
$usedPct = [math]::Round((($totalMB - $freeMB) / $totalMB) * 100, 1)
Add-Section 'MEMORY' "Total: $totalMB MB | Free: $freeMB MB | Used: $usedPct%"

# Process counts
$pc = @{}
foreach ($n in @('claude', 'node', 'bun', 'mintty', 'EVE', 'python', 'pythonw', 'powershell', 'pwsh')) {
    $procs = Get-Process -Name $n -ErrorAction SilentlyContinue
    if ($procs) {
        $mb = [math]::Round(($procs | Measure-Object WS -Sum).Sum / 1MB, 0)
        $pc[$n] = "$($procs.Count) procs / $mb MB"
    }
}
Add-Section 'PROCESS COUNTS' (($pc.GetEnumerator() | ForEach-Object { "$($_.Key): $($_.Value)" }) -join "`n")

# Top 20 by working set
$top = Get-Process | Sort-Object WS -Descending | Select-Object -First 20 |
    ForEach-Object { "{0,-22} pid={1,-6} ws={2,6:N1}MB" -f $_.Name, $_.Id, ($_.WS / 1MB) }
Add-Section 'TOP 20 PROCESSES (working set)' ($top -join "`n")

# Stale .tmp files in shared-memory
$tmp = Get-ChildItem -Path (Join-Path $sanctum '_shared-memory') -Recurse -File -Filter '*.tmp.*' -ErrorAction SilentlyContinue
Add-Section 'STALE .tmp.PID.TS FILES' ($(if ($tmp) { ($tmp | ForEach-Object { "$($_.FullName) (age $([math]::Round(((Get-Date)-$_.LastWriteTime).TotalMinutes,1))min)" }) -join "`n" } else { 'none' }))

# Stale .lock files (>30min)
$locks = Get-ChildItem -Path (Join-Path $sanctum '_shared-memory') -Recurse -File -Filter '*.lock' -ErrorAction SilentlyContinue |
    Where-Object { ((Get-Date) - $_.LastWriteTime).TotalMinutes -gt 30 }
Add-Section 'STALE .lock FILES (>30min)' ($(if ($locks) { ($locks | ForEach-Object { "$($_.FullName) (age $([math]::Round(((Get-Date)-$_.LastWriteTime).TotalMinutes,1))min)" }) -join "`n" } else { 'none' }))

# Disk queue (single quick sample, no parallel hang)
try {
    $sample = Get-Counter '\PhysicalDisk(_total)\Avg. Disk Queue Length' -SampleInterval 1 -MaxSamples 1 -ErrorAction Stop
    $q = [math]::Round($sample.CounterSamples[0].CookedValue, 2)
    Add-Section 'DISK QUEUE LENGTH' "current: $q (>1.0 = saturated, >2.0 = thrashing)"
} catch { Add-Section 'DISK QUEUE LENGTH' 'sample-failed' }

# Scheduled task next-run windows (cluster detection)
$tasks = schtasks /Query /FO CSV 2>$null | ConvertFrom-Csv | Where-Object { $_.TaskName -match 'Sinister' } |
    Select-Object TaskName, 'Next Run Time', Status |
    Sort-Object 'Next Run Time'
Add-Section 'SINISTER SCHEDULED TASKS' (($tasks | ForEach-Object { "$($_.TaskName) | next: $($_.'Next Run Time') | $($_.Status)" }) -join "`n")

[System.IO.File]::WriteAllText($outFile, ($lines -join "`n"), [System.Text.Encoding]::UTF8)
if (-not $Quiet) {
    Write-Host "perf-snapshot written: $outFile" -ForegroundColor Cyan
    Write-Host "memory: $usedPct% used | claude: $($pc['claude']) | EVE: $($pc['EVE']) | stale .tmp: $($tmp.Count) | stale locks: $($locks.Count)" -ForegroundColor Yellow
}
