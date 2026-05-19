# show-memory-garden.ps1 - one-shot operator dashboard: per-bot aliveness
# (facts, calls, last absorbed, smart-retrieval status) + summary.
# Read-only. Auto-closes.

[CmdletBinding()]
param(
    [string]$HubRoot = 'D:\Sinister\Sinister Skills',
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'

. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'show-memory-garden'

Write-Host "=== Sinister Bots - Memory Garden ===" -ForegroundColor Cyan
Write-Host "Time: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host ""

# Use system python; load _shared/bot_memory directly
$pyCode = @'
import sys, os, json
os.environ['SINISTER_HUB_ROOT'] = r'D:\Sinister\Sinister Skills'
sys.path.insert(0, r'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents')
from _shared import bot_memory as bm
bots = ['sentinel','translator','librarian','watcher','auditor','sinister-bus',
        'triage','scribe','curator','custodian','stealth-browser','researcher']
rows = []
for n in bots:
    try:
        s = bm.memory_stats(n)
        rows.append({'bot': n, 'facts': s.get('fact_count',0), 'embedded': s.get('embedded_fact_count',0),
                     'calls': s.get('lifetime_calls',0), 'last_called': s.get('last_called') or '',
                     'last_absorbed': s.get('last_absorbed') or '', 'smart': s.get('smart_retrieval_active', False)})
    except Exception as e:
        rows.append({'bot': n, 'error': str(e)[:80]})
rows.sort(key=lambda r: -(r.get('facts') or 0))
print(json.dumps(rows))
'@

$pyTmp = [IO.Path]::GetTempFileName() + '.py'
Set-Content -Path $pyTmp -Value $pyCode -Encoding utf8
$json = python $pyTmp 2>&1 | Select-Object -Last 1
Remove-Item $pyTmp -Force -ErrorAction SilentlyContinue

try {
    $rows = $json | ConvertFrom-Json
} catch {
    Write-Host "[FAIL] couldn't parse garden output: $json" -ForegroundColor Red
    Add-RunlogStep -Log $log -Name 'parse' -Ok $false -Summary "parse failed"
    Save-Runlog -Log $log -AutoClose $false | Out-Null
    if (-not $Quiet) { Read-Host 'Press Enter to close' }
    exit 1
}

# Print table
$totalFacts = 0
$totalCalls = 0
Write-Host ("{0,-18}  {1,5}  {2,8}  {3,5}  {4,5}  {5}" -f 'BOT','FACTS','EMBEDDED','CALLS','SMART','LAST ABSORBED') -ForegroundColor Yellow
Write-Host ('-' * 80)
foreach ($r in $rows) {
    if ($r.error) {
        Write-Host ("{0,-18}  ERROR: {1}" -f $r.bot, $r.error) -ForegroundColor Red
        continue
    }
    $facts = [int]$r.facts
    $totalFacts += $facts
    $totalCalls += [int]$r.calls
    $smartStr = if ($r.smart) { 'YES' } else { '-' }
    $lastStr = if ($r.last_absorbed) { $r.last_absorbed.Substring(0, [Math]::Min(20, $r.last_absorbed.Length)) } else { '-' }
    $color = if ($facts -gt 0) { 'Green' } elseif ($r.calls -gt 0) { 'White' } else { 'DarkGray' }
    Write-Host ("{0,-18}  {1,5}  {2,8}  {3,5}  {4,5}  {5}" -f $r.bot, $facts, $r.embedded, $r.calls, $smartStr, $lastStr) -ForegroundColor $color
}

Write-Host ""
Write-Host ("TOTAL  facts={0}  calls={1}  bots_with_facts={2}" -f $totalFacts, $totalCalls, (($rows | Where-Object { $_.facts -gt 0 }).Count)) -ForegroundColor Cyan

Set-RunlogOutput -Log $log -Key 'total_facts' -Value $totalFacts
Set-RunlogOutput -Log $log -Key 'total_calls' -Value $totalCalls
Set-RunlogOutput -Log $log -Key 'garden' -Value $rows
Add-RunlogStep -Log $log -Name 'render' -Ok $true -Summary "$totalFacts facts across $(($rows | Where-Object { $_.facts -gt 0 }).Count) bots"
$manifestPath = Save-Runlog -Log $log -AutoClose $true
Write-Host ""
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray

if (-not $Quiet) { Write-Host "Window will auto-close in 5s..." -ForegroundColor Green; Start-Sleep -Seconds 5 }
exit 0
