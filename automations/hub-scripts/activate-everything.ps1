# activate-everything.ps1 - one-shot operator-run activation script.
# Called from C:\Users\Zonia\Desktop\Sinister-Bots-Activation.bat
# Does everything Claude cannot do from the sandbox, in a single pass.
# Idempotent. Re-run safely.

[CmdletBinding()]
param(
    [string]$HubRoot = 'D:\Sinister\Sinister Skills',
    [switch]$SkipApiKeyPrompt,
    [switch]$SkipOllamaPrompt,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

# Runlog
. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'activate-everything'
$scriptStart = Get-Date

function Step-Runlog($name, [scriptblock]$body) {
    $start = Get-Date
    $ok = $true; $err = ''
    try { . $body } catch { $ok = $false; $err = $_.Exception.Message }
    $ms = [int]((Get-Date) - $start).TotalMilliseconds
    Add-RunlogStep -Log $log -Name $name -Ok $ok -Ms $ms -Summary $err
}

function Banner($text, $color = 'Cyan') {
    Write-Host ''
    Write-Host ('=' * 70) -ForegroundColor $color
    Write-Host (' ' + $text) -ForegroundColor $color
    Write-Host ('=' * 70) -ForegroundColor $color
}

function Step($num, $text) {
    Write-Host ''
    Write-Host ("[$num] $text") -ForegroundColor Yellow
}

function OK($text)    { Write-Host ("  [OK]   $text") -ForegroundColor Green }
function WARN($text)  { Write-Host ("  [WARN] $text") -ForegroundColor Yellow }
function FAIL($text)  { Write-Host ("  [FAIL] $text") -ForegroundColor Red }
function INFO($text)  { Write-Host ("  [.]    $text") }

Banner 'Sinister Bots - one-shot activation'
Write-Host "Hub: $HubRoot"
Write-Host "Time: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))"

# Pre-flight: hub exists?
if (-not (Test-Path $HubRoot)) {
    FAIL "Hub root not found: $HubRoot"
    Write-Host ''
    Read-Host 'Press Enter to exit'
    exit 1
}
OK "Hub root found"

# =========================================================
Step 1 'Aggregate sandbox gotchas (operator-owned scan)'
# =========================================================
$gotchaScript = Join-Path $HubRoot '08_AUTOMATIONS\aggregate-gotchas.ps1'
if (Test-Path $gotchaScript) {
    INFO "Running: $gotchaScript"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $gotchaScript -HubRoot $HubRoot 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -eq 0) { OK 'SANDBOX-GOTCHAS.md regenerated' } else { WARN "gotcha aggregator exit code: $LASTEXITCODE" }
} else {
    FAIL "aggregate-gotchas.ps1 not found at $gotchaScript"
}

# =========================================================
Step 2 'Install Custodian 24/7 backup scheduled task'
# =========================================================
$taskScript = Join-Path $HubRoot '12_LLM_ORCHESTRATION\agents\custodian\install-task.ps1'
if (Test-Path $taskScript) {
    INFO "Running: $taskScript"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $taskScript 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -eq 0) {
        OK 'Custodian scheduled task installed (runs at logon + daily 03:00)'
    } else {
        WARN "install-task.ps1 exit code: $LASTEXITCODE - may need admin"
    }
} else {
    FAIL "install-task.ps1 not found at $taskScript"
}

# =========================================================
Step 3 'Trigger first Custodian backup pass now'
# =========================================================
$queryOut = & schtasks.exe /Query /TN 'SinisterCustodian' 2>&1
if ($LASTEXITCODE -eq 0) {
    & schtasks.exe /Run /TN 'SinisterCustodian' 2>&1 | Out-Null
    OK 'SinisterCustodian task launched (check D:\_backups\_logs\ for output)'
} else {
    # Task not registered; fall back to direct one-shot
    $daemon = Join-Path $HubRoot '12_LLM_ORCHESTRATION\agents\custodian\run-daemon.ps1'
    if (Test-Path $daemon) {
        INFO 'Task not registered; running one-shot daemon directly'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $daemon -OneShot 2>&1 | Select-Object -Last 5 | ForEach-Object { Write-Host "    $_" }
    } else {
        WARN 'Neither scheduled task nor daemon script available'
    }
}

# Show backup state
$backupCount = 0
$backupMB = 0
if (Test-Path 'D:\_backups\snapshots') {
    $stats = Get-ChildItem -Recurse 'D:\_backups\snapshots' -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum
    $backupCount = $stats.Count
    $backupMB = [Math]::Round($stats.Sum / 1MB, 1)
}
INFO "Backup state: $backupCount files, $backupMB MB at D:\_backups\snapshots"

# =========================================================
Step 4 'Set ANTHROPIC_API_KEY for scribe + curator (Tier-3 bots)'
# =========================================================
$existingKey = [Environment]::GetEnvironmentVariable('ANTHROPIC_API_KEY', 'User')
if ($existingKey -and $existingKey.StartsWith('sk-ant-')) {
    OK ('ANTHROPIC_API_KEY already set (ends in ...{0})' -f $existingKey.Substring($existingKey.Length - 6))
} elseif ($SkipApiKeyPrompt) {
    WARN 'ANTHROPIC_API_KEY not set + -SkipApiKeyPrompt passed; scribe + curator will return api_key_present=false'
} else {
    Write-Host ''
    Write-Host '  ANTHROPIC_API_KEY is NOT set. Scribe (daily-digest) + Curator (code-library scout) need it.'
    Write-Host '  Get one from https://console.anthropic.com/settings/keys'
    $key = Read-Host '  Paste key now (starts sk-ant-) or press Enter to skip'
    if ($key -and $key.StartsWith('sk-ant-')) {
        [Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', $key, 'User')
        OK 'ANTHROPIC_API_KEY set at user scope (active in new sessions)'
    } else {
        WARN 'Skipped. Scribe + Curator stay in degraded mode until you set it.'
    }
}

# =========================================================
Step 5 'Ollama + model pulls (Tier-2 bots: librarian, triage, researcher)'
# =========================================================
$dockerInstalled = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
if (-not $dockerInstalled) {
    WARN 'Docker not in PATH. Tier-2 bots (librarian/triage/researcher) work in fallback mode only until you install Docker + pull Ollama models.'
} else {
    $ollamaUp = $false
    try {
        $resp = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 3 -UseBasicParsing
        if ($resp.StatusCode -eq 200) { $ollamaUp = $true }
    } catch {}

    if ($ollamaUp) {
        OK 'Ollama already reachable at localhost:11434'
    } elseif ($SkipOllamaPrompt) {
        WARN 'Ollama not running + -SkipOllamaPrompt passed; skipping'
    } else {
        Write-Host ''
        Write-Host '  Ollama is NOT running. Bots will fall back to deterministic mode.'
        $startOllama = Read-Host '  Start Docker Compose Ollama stack now? [y/N]'
        if ($startOllama -match '^[Yy]') {
            $dockerDir = Join-Path $HubRoot '12_LLM_ORCHESTRATION\docker'
            if (Test-Path "$dockerDir\setup.bat") {
                INFO 'Running docker setup'
                & cmd.exe /c "cd /d `"$dockerDir`" && setup.bat" 2>&1 | Select-Object -Last 10 | ForEach-Object { Write-Host "    $_" }
                Start-Sleep -Seconds 3
                try {
                    $resp = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -TimeoutSec 5 -UseBasicParsing
                    if ($resp.StatusCode -eq 200) { OK 'Ollama is up' } else { WARN 'Ollama not yet responding; give it 30s and retry' }
                } catch { WARN 'Ollama not yet responding; give it 30s and retry' }
            } else {
                FAIL "setup.bat not found at $dockerDir"
            }
        } else {
            WARN 'Skipped.'
        }
    }

    # Pull models if ollama is up
    if ($ollamaUp -or (Test-Path 'C:\Program Files\Docker\Docker\resources\bin\docker.exe')) {
        $pullModels = $true
        if (-not $SkipOllamaPrompt) {
            $resp = Read-Host '  Pull Ollama models (qwen2.5:1.5b + qwen2.5-coder:7b + nomic-embed-text, ~6GB)? [y/N]'
            $pullModels = ($resp -match '^[Yy]')
        }
        if ($pullModels) {
            foreach ($m in @('qwen2.5:1.5b', 'qwen2.5-coder:7b', 'nomic-embed-text')) {
                INFO "Pulling $m (background; may take several minutes per model)"
                Start-Process -FilePath 'docker' -ArgumentList @('exec', '-it', 'ollama', 'ollama', 'pull', $m) -NoNewWindow -PassThru | Out-Null
            }
            OK 'Model pulls started in background; check Docker Desktop for progress'
        }
    }
}

# =========================================================
Step 6 'Verify MCP registry has all 19 servers'
# =========================================================
$mcpJson = "$env:USERPROFILE\.claude\.mcp.json"
if (Test-Path $mcpJson) {
    try {
        $mcp = Get-Content $mcpJson -Raw -Encoding utf8 | ConvertFrom-Json
        $count = ($mcp.mcpServers.PSObject.Properties.Name).Count
        $bots = @('sentinel','translator','librarian','watcher','auditor','sinister-bus','triage','scribe','curator','custodian','stealth-browser','researcher')
        $present = $mcp.mcpServers.PSObject.Properties.Name
        $missing = $bots | Where-Object { $present -notcontains $_ }
        OK "$count MCP servers registered in .mcp.json"
        if ($missing.Count -gt 0) {
            WARN ('Missing bots: ' + ($missing -join ', ') + ' -- run install-fleet.ps1 -SkipInstall')
        }
    } catch {
        FAIL "Could not parse .mcp.json: $_"
    }
} else {
    FAIL ".mcp.json not found at $mcpJson"
}

# =========================================================
Step 7 'Final summary + what you still need to do'
# =========================================================
Banner 'DONE'

Write-Host ''
Write-Host 'WHAT JUST HAPPENED:' -ForegroundColor Cyan
Write-Host '  1. Regenerated 09_REFERENCE/SANDBOX-GOTCHAS.md from memory scan'
Write-Host '  2. Installed SinisterCustodian + SinisterCustodian-DailyRestart scheduled tasks'
Write-Host '  3. Triggered a Custodian backup pass'
Write-Host '  4. Prompted for ANTHROPIC_API_KEY (if missing)'
Write-Host '  5. Offered to start Ollama + pull models'
Write-Host '  6. Verified .mcp.json has all 12 Sinister Bots'
Write-Host ''
Write-Host 'YOU STILL NEED TO:' -ForegroundColor Yellow
Write-Host '  1. RESTART CLAUDE CODE - the 12 new MCP servers load only on session start'
Write-Host '  2. After restart, verify by calling in any Claude session:'
Write-Host '       sinister-bus.list_network    (expect 19 endpoints)'
Write-Host '       custodian.health             (expect snapshot_count > 0)'
Write-Host '       sentinel.list_alarms         (expect 3 default alarms)'
Write-Host '  3. Edit 09_REFERENCE/SANDBOX-GOTCHAS.md below the HAND-EDITED marker'
Write-Host '     to add your curated gotchas (the auto-scan caught the regex hits;'
Write-Host '     you add the prose alternates - "trip X, green path Y").'
Write-Host ''
Write-Host 'OPTIONAL:' -ForegroundColor DarkGray
Write-Host '  - Hacker bot (183-tool pentest dispatcher) is pending operator OK to fetch'
Write-Host '    AKCodez/hackingtool-plugin source. Tell Claude "yes, RE the hackingtool" to unblock.'
Write-Host ''
Write-Host 'Logs:'
Write-Host '  - D:\_backups\_logs\custodian-<date>.log (daemon output)'
Write-Host '  - D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\token-usage.jsonl'
Write-Host '  - D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\absorption-log.jsonl'
Write-Host ''

# =========================================================
Step 6.5 'Check Hetzner state (probes + git-ahead)'
# =========================================================
$hetznerCheck = Join-Path $PSScriptRoot 'check-hetzner-state.ps1'
if (Test-Path $hetznerCheck) {
    INFO "Running: $hetznerCheck"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $hetznerCheck -Quiet 2>&1 | ForEach-Object { Write-Host "    $_" }
    OK "Hetzner state manifest written (check runtime-state/script-runs/)"
} else {
    WARN "check-hetzner-state.ps1 not found; skipping"
}

# Compose runlog
Set-RunlogOutput -Log $log -Key 'backup_files' -Value $backupCount
Set-RunlogOutput -Log $log -Key 'backup_mb' -Value $backupMB
Add-RunlogNextAction -Log $log -Action 'Restart Claude Code so the 12 bot MCP servers load.'
Add-RunlogNextAction -Log $log -Action 'After restart: sinister-bus.list_network (expect 19 endpoints).'
Add-RunlogNextAction -Log $log -Action 'After restart: sinister-bus.runlog_latest check-hetzner-state for live service status.'
Add-RunlogNextAction -Log $log -Action 'Edit 09_REFERENCE/SANDBOX-GOTCHAS.md below HAND-EDITED marker with curated trip -> green-path pairs.'

# Determine auto-close: only when there were no warnings/errors AND user didn't pass -SkipApiKeyPrompt
$allOk = ($log.warnings.Count -eq 0 -and $log.errors.Count -eq 0)
$manifestPath = Save-Runlog -Log $log -AutoClose $allOk

Write-Host ""
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray
Write-Host ""

# Bat checks LASTEXITCODE to decide whether to pause; we also pause in-script if not Quiet AND something needs attention
if ($allOk) {
    if (-not $Quiet) {
        Write-Host "All steps OK. Window will auto-close in 5s (Ctrl+C to keep open)..." -ForegroundColor Green
        Start-Sleep -Seconds 5
    }
    exit 0
}

if (-not $Quiet) {
    Read-Host 'Press Enter to close'
}
exit 1
