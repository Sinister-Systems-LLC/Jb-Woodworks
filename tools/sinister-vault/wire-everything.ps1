# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# wire-everything.ps1 -- one-click bring-up for the Sinister Vault daemon.
#
# What this does (idempotent -- safe to re-run any time):
#   1. Sanity-check the venv at .venv\Scripts\python.exe (warn + continue if missing).
#   2. Call install-vault-task.ps1 to register the 'SinisterVault' scheduled task.
#   3. Start-ScheduledTask SinisterVault -- wait 5s for cold-start.
#   4. Verify health via GET http://127.0.0.1:5078/api/vault/health (5s timeout).
#   5. Stage a proposed MCP server entry at D:\Sinister Sanctum\_vault\mcp-vault-entry-PROPOSED.json
#      (operator must merge into ~/.claude/.mcp.json by hand -- lane discipline).
#   6. Print next-steps for the operator.
#
# Exit codes:
#   0  -- full success (task registered + healthy + proposal staged)
#   1  -- fatal error (missing files, install-task script failed hard)
#   2  -- task registered but health check failed (still staged the proposal)
#
# UTF-8 with BOM. No em-dashes (use -- instead). No `Read-Host ""`.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File wire-everything.ps1

[CmdletBinding()]
param(
    [string]$TaskName = 'SinisterVault',
    [int]$Port = 5078,
    [int]$StartupWaitSeconds = 5
)

$ErrorActionPreference = 'Continue'

# Purple accent palette -- standing rule for Sinister Sanctum agent output.
$Purple = 'Magenta'
$ScriptDir = $PSScriptRoot
if (-not $ScriptDir) { $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path }
$VaultRoot   = Split-Path -Parent (Split-Path -Parent $ScriptDir)  # D:\Sinister Sanctum
$VenvPython  = Join-Path $ScriptDir '.venv\Scripts\python.exe'
$InstallPs1  = Join-Path $ScriptDir 'install-vault-task.ps1'
$DaemonLogs  = Join-Path $ScriptDir '_daemon-logs'
$VaultDir    = Join-Path $VaultRoot '_vault'
$ProposalOut = Join-Path $VaultDir 'mcp-vault-entry-PROPOSED.json'
$McpVaultPy  = Join-Path $VaultRoot 'bots\agents\vault\server.py'

function Write-Section {
    param([string]$Title)
    Write-Host ''
    Write-Host ('== ' + $Title + ' ==') -ForegroundColor $Purple
}

function Write-OK {
    param([string]$Msg)
    Write-Host ('[ OK ] ' + $Msg) -ForegroundColor Green
}

function Write-Warn {
    param([string]$Msg)
    Write-Host ('[WARN] ' + $Msg) -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Msg)
    Write-Host ('[FAIL] ' + $Msg) -ForegroundColor Red
}

Write-Host ''
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host '##  Sinister Vault -- wire-everything.ps1                      ##' -ForegroundColor $Purple
Write-Host '##  one-click bring-up: register task, start, verify, stage   ##' -ForegroundColor $Purple
Write-Host '################################################################' -ForegroundColor $Purple

# ---------------------------------------------------------------- prereqs ---
Write-Section 'Step 1: prereq sanity check'

$venvOk = $true
if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Warn ('venv python missing at: ' + $VenvPython)
    Write-Host '       The scheduled task will be registered, but the bat will FATAL on launch.'
    Write-Host '       To fix later:'
    Write-Host ('         cd "' + $ScriptDir + '"')
    Write-Host '         python -m venv .venv'
    Write-Host '         .venv\Scripts\pip install -r requirements.txt'
    $venvOk = $false
} else {
    Write-OK ('venv python present: ' + $VenvPython)
}

if (-not (Test-Path -LiteralPath $InstallPs1)) {
    Write-Fail ('install-vault-task.ps1 not found at: ' + $InstallPs1)
    Write-Fail 'Cannot continue -- bail.'
    exit 1
}
Write-OK ('install-vault-task.ps1 present: ' + $InstallPs1)

if (-not (Test-Path -LiteralPath $DaemonLogs)) {
    try {
        New-Item -ItemType Directory -Path $DaemonLogs -Force | Out-Null
        Write-OK ('created _daemon-logs dir: ' + $DaemonLogs)
    } catch {
        Write-Warn ('could not create _daemon-logs dir: ' + $_.Exception.Message)
    }
}

# --------------------------------------------------------------- register ---
Write-Section 'Step 2: register scheduled task via install-vault-task.ps1'

$registerExit = 0
try {
    & $InstallPs1
    $registerExit = $LASTEXITCODE
    if ($null -eq $registerExit) { $registerExit = 0 }
} catch {
    Write-Fail ('install-vault-task.ps1 threw: ' + $_.Exception.Message)
    $registerExit = 1
}

if ($registerExit -ne 0) {
    Write-Fail ('install-vault-task.ps1 exited rc=' + $registerExit)
    Write-Host '       Most likely cause: insufficient privileges (try Run as Administrator).'
    Write-Host '       Will still attempt to start an existing task and verify health.'
} else {
    Write-OK ('task registered (rc=' + $registerExit + ')')
}

# ------------------------------------------------------------------- start ---
Write-Section ('Step 3: Start-ScheduledTask ' + $TaskName)

$startedOk = $false
try {
    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    if ($null -ne $existing) {
        Start-ScheduledTask -TaskName $TaskName -ErrorAction Stop
        Write-OK ('Start-ScheduledTask issued for ' + $TaskName)
        $startedOk = $true
    }
} catch {
    Write-Fail ('Start-ScheduledTask failed: ' + $_.Exception.Message)
}

if ($startedOk) {
    Write-Host ('       waiting ' + $StartupWaitSeconds + 's for cold-start...') -ForegroundColor DarkGray
    Start-Sleep -Seconds $StartupWaitSeconds
}

# -------------------------------------------------------------- verify  ---
Write-Section ('Step 4: verify health on http://127.0.0.1:' + $Port + '/api/vault/health')

$healthOk = $false
$healthPayload = $null
try {
    $healthUri = 'http://127.0.0.1:' + $Port + '/api/vault/health'
    $healthPayload = Invoke-RestMethod -Uri $healthUri -TimeoutSec 5 -ErrorAction Stop
    if ($healthPayload -and $healthPayload.ok -eq $true) {
        Write-Host ('[ OK ] Vault daemon healthy on :' + $Port) -ForegroundColor $Purple
        Write-Host ('       version=' + $healthPayload.version + '  uptime_s=' + $healthPayload.uptime_s) -ForegroundColor DarkGray
        Write-Host ('       used_human=' + $healthPayload.used_human + '  vault_root=' + $healthPayload.vault_root) -ForegroundColor DarkGray
        $healthOk = $true
    } else {
        Write-Fail 'health endpoint replied but ok != true'
    }
} catch {
    Write-Fail ('health check failed: ' + $_.Exception.Message)
    Write-Host '       check the daemon logs at:'
    Write-Host ('         ' + $DaemonLogs + '\vault-<stamp>.log')
    Write-Host ('         ' + $DaemonLogs + '\daemon.log')
}

# Also probe the new /api/vault/heartbeat endpoint -- informational, never fatal.
try {
    $hbUri = 'http://127.0.0.1:' + $Port + '/api/vault/heartbeat'
    $hb = Invoke-RestMethod -Uri $hbUri -TimeoutSec 5 -ErrorAction Stop
    if ($hb) {
        $aliveTxt = if ($hb.alive) { 'alive=true' } else { 'alive=false' }
        $ageTxt = if ($null -ne $hb.age_s) { ('age_s=' + $hb.age_s) } else { 'age_s=null' }
        Write-Host ('       heartbeat: ' + $aliveTxt + '  ' + $ageTxt) -ForegroundColor DarkGray
        if ($hb.last_line) {
            Write-Host ('       last_line: ' + $hb.last_line) -ForegroundColor DarkGray
        }
    }
} catch {
    Write-Host '       heartbeat probe skipped (endpoint not reachable yet)' -ForegroundColor DarkGray
}

# --------------------------------------------------------------- stage mcp ---
Write-Section 'Step 5: stage proposed MCP entry (operator merges manually)'

if (-not (Test-Path -LiteralPath $VaultDir)) {
    try {
        New-Item -ItemType Directory -Path $VaultDir -Force | Out-Null
    } catch {
        Write-Warn ('could not create _vault dir: ' + $_.Exception.Message)
    }
}

# Sanity-check the python + server.py paths we are about to bake into the proposal.
$pythonForProposal = $VenvPython
if (-not (Test-Path -LiteralPath $pythonForProposal)) {
    Write-Warn ('venv python missing -- proposal still references: ' + $pythonForProposal)
    Write-Warn '       operator: create the venv before merging, or edit the proposal first.'
}
if (-not (Test-Path -LiteralPath $McpVaultPy)) {
    Write-Warn ('MCP server.py missing -- proposal still references: ' + $McpVaultPy)
}

# Build proposal -- emit JSON via ConvertTo-Json so escaping stays correct on
# Windows paths (forward-slash form picked deliberately for cross-tool sanity).
$proposal = [ordered]@{
    comment = "Proposed entry for ~/.claude/.mcp.json -- operator must merge manually (lane discipline)"
    generated_by = "wire-everything.ps1 :: Sinister Sanctum master agent :: 2026-05-19"
    vault = [ordered]@{
        command = ($pythonForProposal -replace '\\', '/')
        args = @(($McpVaultPy -replace '\\', '/'))
        env = [ordered]@{
            SINISTER_HUB_ROOT = "D:/Sinister/Sinister Skills"
            VAULT_DAEMON_URL  = ('http://127.0.0.1:' + $Port)
        }
    }
}

try {
    $json = $proposal | ConvertTo-Json -Depth 6
    # Write UTF-8 (no BOM) -- this is data, not a script.
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($ProposalOut, $json, $utf8NoBom)
    Write-OK ('staged: ' + $ProposalOut)
} catch {
    Write-Fail ('could not stage proposal: ' + $_.Exception.Message)
}

# ----------------------------------------------------------- next steps ---
Write-Section 'Step 6: operator next-steps'

Write-Host '  (a) Review + merge the proposed MCP entry:'
Write-Host ('      file: ' + $ProposalOut) -ForegroundColor $Purple
Write-Host '      target: ~/.claude/.mcp.json   (add the "vault" key under "mcpServers")'
Write-Host '      then re-run: install-fleet.ps1   (if your fleet uses it)'
Write-Host ''
Write-Host '  (b) Restart Claude Code so the vault MCP server loads.'
Write-Host ''
Write-Host '  (c) Verify from any agent:'
Write-Host '      vault.health                    (MCP tool, once server is wired)'
Write-Host ('      curl http://127.0.0.1:' + $Port + '/api/vault/health      (HTTP, available now)')
Write-Host ('      curl http://127.0.0.1:' + $Port + '/api/vault/heartbeat   (liveness signal)')
Write-Host ''
Write-Host '  Heartbeat file (fleet-monitor reads mtime; stale if > 120s):'
Write-Host ('      ' + (Join-Path $VaultRoot '_shared-memory\heartbeats\sinister-vault.beat'))
Write-Host ''

# ----------------------------------------------------------------- exit ---
if ($healthOk) {
    Write-Host ''
    Write-Host '################################################################' -ForegroundColor Green
    Write-Host '##  wire-everything.ps1 -- ALL GREEN                          ##' -ForegroundColor Green
    Write-Host '################################################################' -ForegroundColor Green
    exit 0
}

if ($registerExit -eq 0 -and -not $healthOk) {
    Write-Host ''
    Write-Host '################################################################' -ForegroundColor Yellow
    Write-Host '##  wire-everything.ps1 -- task installed, health degraded   ##' -ForegroundColor Yellow
    Write-Host '##  see _daemon-logs and retry: Start-ScheduledTask SinisterVault' -ForegroundColor Yellow
    Write-Host '################################################################' -ForegroundColor Yellow
    exit 2
}

Write-Host ''
Write-Host '################################################################' -ForegroundColor Red
Write-Host '##  wire-everything.ps1 -- FAILED                            ##' -ForegroundColor Red
Write-Host '################################################################' -ForegroundColor Red
exit 1
