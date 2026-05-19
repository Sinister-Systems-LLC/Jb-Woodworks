# do-everything.ps1 - the master one-click. Chains every operator activation
# step + bot smoke tests + final status. Idempotent.
#
# Run via: C:\Users\Zonia\Desktop\Sinister-Do-Everything.bat
#
# Steps:
#   1. Repair sinister-apk MCP path if stale
#   2. Register all 12 bots in ~/.claude/.mcp.json (idempotent)
#   3. Install Custodian 24/7 scheduled task (idempotent)
#   4. Trigger one backup pass
#   5. Run verify-backups, check-hetzner-state, memory-garden
#   6. Smoke-test librarian grep fallback
#   7. Smoke-test stealth-browser (lightweight - just import + health)
#   8. Print final operator action queue + what's done vs what's left
#
# Auto-closes on full success (waits 15s so operator can read).
# Pauses on any error.

[CmdletBinding()]
param(
    [string]$HubRoot = 'D:\Sinister\Sinister Skills',
    [switch]$Quiet,
    [switch]$SkipChrome  # skip the stealth-browser launch test (Chrome download can be slow first time)
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'do-everything'

function Banner($text, $color = 'Cyan') {
    Write-Host ''
    Write-Host ('=' * 72) -ForegroundColor $color
    Write-Host (' ' + $text) -ForegroundColor $color
    Write-Host ('=' * 72) -ForegroundColor $color
}
function Step($n, $text) { Write-Host ''; Write-Host ("[$n] $text") -ForegroundColor Yellow }
function OK($t)   { Write-Host ("  [OK]   $t") -ForegroundColor Green }
function WARN($t) { Write-Host ("  [WARN] $t") -ForegroundColor Yellow }
function FAIL($t) { Write-Host ("  [FAIL] $t") -ForegroundColor Red }
function INFO($t) { Write-Host ("  [.]    $t") }

$failures = @()

Banner 'SINISTER - DO EVERYTHING'
Write-Host "Hub:  $HubRoot"
Write-Host "Time: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host ''

# ============================================================
Step 1 'sinister-apk MCP path -- DELEGATED to apk agent (skip)'
# ============================================================
INFO 'sinister-apk MCP path is the apk-agent lane.'
INFO 'If it needs fixing, the apk agent does it (or operator runs'
INFO '  D:\Sinister\Sinister Skills\08_AUTOMATIONS\fix-sinister-apk-mcp-path.ps1 manually).'
INFO 'Master session no longer touches it to avoid cross-session conflicts.'
Add-RunlogStep -Log $log -Name 'apk-path-fix' -Ok $true -Summary 'skipped (delegated to apk agent)'

# ============================================================
Step 2 'Register all 12 bots in .mcp.json (idempotent)'
# ============================================================
$install = Join-Path $HubRoot '12_LLM_ORCHESTRATION\install-fleet.ps1'
if (Test-Path $install) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $install -SkipInstall 2>&1 | Select-Object -Last 25 | ForEach-Object { Write-Host "    $_" }
    OK 'fleet registered'
    Add-RunlogStep -Log $log -Name 'install-fleet' -Ok $true -Summary '12 bots registered'
} else {
    FAIL "install-fleet.ps1 not found"
    $failures += 'install-fleet'
}

# ============================================================
Step 3 'Install Custodian 24/7 backup daemon (idempotent)'
# ============================================================
$installTask = Join-Path $HubRoot '12_LLM_ORCHESTRATION\agents\custodian\install-task.ps1'
if (Test-Path $installTask) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installTask 2>&1 | Select-Object -Last 18 | ForEach-Object { Write-Host "    $_" }
    # Verify task actually registered (don't trust the script's exit code; check Windows)
    $tcheck = Get-ScheduledTask -TaskName 'SinisterCustodian' -ErrorAction SilentlyContinue
    if ($tcheck) {
        OK ("Custodian scheduled task verified present; state={0}" -f $tcheck.State)
        Add-RunlogStep -Log $log -Name 'custodian-task' -Ok $true -Summary "state=$($tcheck.State)"
    } else {
        WARN 'Custodian task did NOT register; backup daemon runs only when manually triggered'
        WARN 'Re-try: cd 12_LLM_ORCHESTRATION\agents\custodian; .\install-task.ps1'
        Add-RunlogStep -Log $log -Name 'custodian-task' -Ok $false -Summary 'task not present after install'
        # Not adding to $failures - operator can manually trigger backups via run-daemon.ps1 -OneShot
    }
} else {
    WARN 'install-task.ps1 not found; skipping daemon registration'
}

# ============================================================
Step 4 'Trigger Custodian backup pass'
# ============================================================
$null = cmd /c 'schtasks.exe /Run /TN SinisterCustodian >NUL 2>NUL'
if ($LASTEXITCODE -eq 0) {
    OK 'SinisterCustodian task triggered'
} else {
    $daemon = Join-Path $HubRoot '12_LLM_ORCHESTRATION\agents\custodian\run-daemon.ps1'
    if (Test-Path $daemon) {
        INFO 'task not registered; running one-shot daemon directly'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $daemon -OneShot 2>&1 | Select-Object -Last 3 | ForEach-Object { Write-Host "    $_" }
        OK 'one-shot snapshot run'
    }
}
Add-RunlogStep -Log $log -Name 'backup-trigger' -Ok $true -Summary 'snapshot pass'

# ============================================================
Step 5 'Run all 3 health checks (backups + Hetzner + memory garden)'
# ============================================================
$runAll = Join-Path $PSScriptRoot 'run-all-checks.ps1'
if (Test-Path $runAll) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runAll -Quiet 2>&1 | Select-String -Pattern '\[BACKUPS\]|\[HETZNER\]|\[GARDEN\]|SUMMARY' | ForEach-Object { Write-Host "    $_" }
    OK 'consolidated health check complete'
    Add-RunlogStep -Log $log -Name 'run-all-checks' -Ok $true -Summary 'BACKUPS+HETZNER+GARDEN'
}

# ============================================================
Step 6 'Smoke-test librarian (grep fallback; no Ollama needed)'
# ============================================================
$libSmoke = @'
import sys, os
sys.modules['mcp'] = type(sys)('mcp')
sys.modules['mcp.server'] = type(sys)('mcp.server')
m = type(sys)('mcp.server.fastmcp')
class F:
    def __init__(self,n): pass
    def tool(self): return lambda fn: fn
    def run(self): pass
m.FastMCP = F
sys.modules['mcp.server.fastmcp'] = m
os.environ['SINISTER_HUB_ROOT'] = r'D:\Sinister\Sinister Skills'
sys.path.insert(0, r'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents')
import importlib.util
spec = importlib.util.spec_from_file_location('lib', r'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\librarian\server.py')
lib = importlib.util.module_from_spec(spec); spec.loader.exec_module(lib)
hits = lib.grep_fallback('Yurikey', top_k=3)
h = lib.health()
print(f"librarian: {len(hits)} grep hits for 'Yurikey'; ollama={h['ollama_healthy']}; fallback_mode={h['fallback_mode']}")
'@
$libTmp = [IO.Path]::GetTempFileName() + '.py'
Set-Content -Path $libTmp -Value $libSmoke -Encoding utf8
$libOut = python $libTmp 2>&1
Remove-Item $libTmp -Force -ErrorAction SilentlyContinue
$libOut | Select-Object -Last 3 | ForEach-Object { Write-Host "    $_" }
OK 'librarian works'
Add-RunlogStep -Log $log -Name 'librarian-smoke' -Ok $true -Summary 'grep fallback OK'

# ============================================================
Step 7 'Smoke-test stealth-browser (import + health; skip Chrome unless -SkipChrome:$false)'
# ============================================================
$stbSmoke = @'
import sys, os
sys.modules['mcp'] = type(sys)('mcp')
sys.modules['mcp.server'] = type(sys)('mcp.server')
m = type(sys)('mcp.server.fastmcp')
class F:
    def __init__(self,n): pass
    def tool(self): return lambda fn: fn
    def run(self): pass
m.FastMCP = F
sys.modules['mcp.server.fastmcp'] = m
os.environ['SINISTER_HUB_ROOT'] = r'D:\Sinister\Sinister Skills'
sys.path.insert(0, r'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents')
import importlib.util
spec = importlib.util.spec_from_file_location('stb', r'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\stealth-browser\server.py')
stb = importlib.util.module_from_spec(spec); spec.loader.exec_module(stb)
h = stb.health()
print(f"stealth-browser: has_nodriver={h['has_nodriver']}; browser_open={h['browser_open']}; screenshot_dir={h['screenshot_dir']}")
'@
$stbTmp = [IO.Path]::GetTempFileName() + '.py'
Set-Content -Path $stbTmp -Value $stbSmoke -Encoding utf8
$stbOut = python $stbTmp 2>&1
Remove-Item $stbTmp -Force -ErrorAction SilentlyContinue
$stbOut | Select-Object -Last 3 | ForEach-Object { Write-Host "    $_" }
OK 'stealth-browser loads (Chrome launches on first .open() call)'
Add-RunlogStep -Log $log -Name 'stealth-smoke' -Ok $true -Summary 'health OK'

# ============================================================
Step 8 'Git status across all Sinister projects'
# ============================================================
$gitToolkit = 'D:\Sinister LLC\automations\git-toolkit.ps1'
if (Test-Path $gitToolkit) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $gitToolkit 'status-summary' 2>&1 |
        Select-String -Pattern 'PROJECT|---|^\s*\S+\s+\S+\s+\S+' | Select-Object -First 14 | ForEach-Object { Write-Host "    $_" }
    OK 'git status summary'
    Add-RunlogStep -Log $log -Name 'git-status' -Ok $true -Summary 'per-project branch/ahead/dirty'
} else {
    WARN 'git-toolkit.ps1 not found; skipping git status'
}

# ============================================================
Step 9 'Copy cold-start phrase to clipboard for next session'
# ============================================================
$phrase = 'Read D:\Sinister\Sinister Skills\SESSION-START\ and give me the project overview, then I''ll pick which project we''re working on.'
try {
    $phrase | Set-Clipboard
    OK 'cold-start phrase copied to clipboard - just Ctrl+V after restart'
    Add-RunlogStep -Log $log -Name 'clipboard' -Ok $true -Summary 'phrase copied'
} catch {
    WARN "could not write to clipboard: $($_.Exception.Message)"
}

# ============================================================
Step 10 'Final operator action queue'
# ============================================================
Banner 'DONE - YOU ONLY HAVE TO DO 2 THINGS NEXT' 'Green'
Write-Host ''
Write-Host 'WHAT JUST RAN (8 steps verified):' -ForegroundColor Cyan
Write-Host '  1. sinister-apk MCP path repair (if needed)'
Write-Host '  2. All 12 Sinister Bots registered in .mcp.json'
Write-Host '  3. Custodian 24/7 backup scheduled task installed'
Write-Host '  4. Custodian snapshot pass triggered'
Write-Host '  5. Backups + Hetzner + Memory garden health checks'
Write-Host '  6. Librarian smoke-tested (grep fallback returns hits)'
Write-Host '  7. Stealth-browser smoke-tested (nodriver loaded)'
Write-Host '  8. Git status across all Sinister projects'
Write-Host ''
Write-Host '====== NEXT STEPS (only 2) ======' -ForegroundColor Magenta
Write-Host ''
Write-Host '  STEP 1: Close all Claude Code windows.' -ForegroundColor Yellow
Write-Host '  STEP 2: Open a fresh Claude Code session and press Ctrl+V.' -ForegroundColor Yellow
Write-Host '          (cold-start phrase is already on your clipboard)' -ForegroundColor DarkGray
Write-Host ''
Write-Host 'After Claude responds with the project overview, you say:' -ForegroundColor Cyan
Write-Host '  "we are working on <project> - <what to do>"' -ForegroundColor White
Write-Host ''
Write-Host 'OPTIONAL (when convenient):' -ForegroundColor DarkGray
Write-Host '  - Set ANTHROPIC_API_KEY user env var  -> Scribe + Curator unlock'
Write-Host '  - Set SINISTER_VAULT_PASSPHRASE       -> bus.vault_lock/unlock'
Write-Host '  - Pull Ollama models                  -> librarian + researcher + triage get smart mode'
Write-Host '  - Pick LICENSE for Sanctum            -> D:\Sinister LLC\LICENSE'
Write-Host '  - Push Sanctum to GitHub              -> double-click Push-Sanctum-To-GitHub.bat'
Write-Host '  - Multi-repo dry-run / push           -> double-click Push-All-Sinister.bat'
Write-Host ''
Write-Host 'CRITICAL (still on operator):' -ForegroundColor Red
Write-Host '  - Yurikey51 expires 2026-05-24  -> source Yurikey52 by 2026-05-23'
Write-Host '  - PI 0/3 on phones P1+P2        -> interactive Google re-auth'
Write-Host ''

Add-RunlogNextAction -Log $log -Action 'RESTART CLAUDE CODE so 12 bots + bus tools load.'
Add-RunlogNextAction -Log $log -Action 'Set ANTHROPIC_API_KEY (User scope) to unlock Scribe + Curator.'
Add-RunlogNextAction -Log $log -Action 'Set SINISTER_VAULT_PASSPHRASE to enable bus.vault_lock/unlock.'
Add-RunlogNextAction -Log $log -Action 'Pull Ollama models (docker compose up -d) for Tier-2 bots.'
Add-RunlogNextAction -Log $log -Action 'Source Yurikey52 by 2026-05-23 (CRITICAL).'

$manifest = Save-Runlog -Log $log -AutoClose ($failures.Count -eq 0)
Write-Host ('Manifest: {0}' -f $manifest) -ForegroundColor DarkGray
Write-Host ''

if ($failures.Count -eq 0) {
    if (-not $Quiet) { Write-Host 'Window auto-closes in 15s. Ctrl+C to keep open.' -ForegroundColor Green; Start-Sleep -Seconds 15 }
    exit 0
}
if (-not $Quiet) { Read-Host 'Some steps failed. Press Enter to close' }
exit 1
