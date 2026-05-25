# eve-first-run-check.ps1 - first-run detection for EVE.exe
# Author: RKOJ-ELENO :: 2026-05-25 (v3 - MCP + Docker + bots + scheduled tasks)
#
# Operator 2026-05-24 21:24Z: "make sure the first time eve runs on a pc it auto
# sets it self up and has a general agent that it spawns that can aid in setup.
# make sure this happens and we have a way to do this so there is perfect setup
# for leo. test it and make sure it works"
#
# Operator 2026-05-25 ~00:35Z: "i need the exe to auto setup when i place on
# leos computer and all you need is the exe and the sinsiter sanctum folder.
# when its doing setup it also needs to first thing spawn a Sinister Setup
# Wizard agent that is prompted with the task of making sure leo gets setup"
#
# Detects fresh-PC signals + returns JSON / text status + structured exit code.
# EVE.exe calls this on startup; if first-run, it invokes eve-first-run-wizard
# which (a) fixes what it can + (b) spawns the Sinister Setup Wizard agent.
#
# Exit codes:
#   0 = ready (no action)
#   1 = hard-block first-run (wizard MUST fire)
#   2 = soft-warn (wizard recommended; non-blocking)
#
# Usage:
#   powershell -File eve-first-run-check.ps1 [-Format json|text] [-Force]
#                                            [-Verbose] [-SimulateFreshMachine]
#                                            [-SanctumRoot <path>]

[CmdletBinding()]
param(
    [ValidateSet('json','text')] [string]$Format = 'json',
    [switch]$Force,
    [switch]$SimulateFreshMachine,
    [string]$SanctumRoot = ''
)

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}

$markerFile = Join-Path $env:USERPROFILE '.sanctum-autonomy-granted'

# --- Probe helpers ---------------------------------------------------------

function Test-CommandPresent { param([string]$Name)
    return ((Get-Command $Name -ErrorAction SilentlyContinue) -ne $null)
}

function Test-GitForWindows {
    return (Test-Path 'C:\Program Files\Git\usr\bin\mintty.exe') -or
           (Test-Path 'C:\Program Files\Git\git-bash.exe') -or
           (Test-Path 'C:\Program Files\Git\bin\bash.exe')
}

function Test-NetworkReachable { param([string]$RemoteHost = 'api.anthropic.com')
    if ($SimulateFreshMachine) { return $false }
    try {
        $r = Test-Connection -ComputerName $RemoteHost -Count 1 -Quiet -ErrorAction SilentlyContinue -TimeoutSeconds 3
        return [bool]$r
    } catch {
        return $false
    }
}

function Test-SanctumStructure {
    if (-not (Test-Path $SanctumRoot)) { return $false }
    $req = @('automations', '_shared-memory', 'tools', 'docs', 'CLAUDE.md')
    foreach ($r in $req) {
        if (-not (Test-Path (Join-Path $SanctumRoot $r))) { return $false }
    }
    return $true
}

function Get-OperatorName {
    try {
        $n = (& git config --get user.name 2>$null) | Select-Object -First 1
        if ($n) { return $n.Trim() }
    } catch {}
    return $env:USERNAME
}

function Test-DockerDaemon {
    if ($SimulateFreshMachine) { return $false }
    if (-not (Test-CommandPresent 'docker')) { return $false }
    try {
        $out = & docker info --format '{{.ServerVersion}}' 2>$null
        return ($LASTEXITCODE -eq 0 -and $out)
    } catch { return $false }
}

function Test-ScheduledTask { param([string]$Name)
    if ($SimulateFreshMachine) { return $false }
    try {
        & schtasks /Query /TN $Name 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Test-McpConfigPresent {
    if ($SimulateFreshMachine) { return $false }
    return (Test-Path (Join-Path $env:USERPROFILE '.claude\.mcp.json'))
}

function Test-ClaudeMcpList {
    if ($SimulateFreshMachine) { return @{ ok = $false; count = 0; raw = '' } }
    if (-not (Test-CommandPresent 'claude')) { return @{ ok = $false; count = 0; raw = 'no-claude-cli' } }
    try {
        $out = & claude mcp list 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) { return @{ ok = $false; count = 0; raw = $out } }
        $lines = ($out -split "`n") | Where-Object { $_ -match '^\s*\S+:.*Connected' }
        return @{ ok = $true; count = ($lines | Measure-Object).Count; raw = $out }
    } catch { return @{ ok = $false; count = 0; raw = $_.Exception.Message } }
}

function Test-BypassPermissions {
    if ($SimulateFreshMachine) { return $false }
    $sp = Join-Path $env:USERPROFILE '.claude\settings.json'
    if (-not (Test-Path $sp)) { return $false }
    try {
        $cfg = Get-Content $sp -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($cfg.bypassPermissions -ne $true) { return $false }
        if (-not $cfg.permissions) { return $false }
        if ($cfg.permissions.defaultMode -ne 'bypassPermissions') { return $false }
        $allow = @($cfg.permissions.allow)
        return ($allow -match 'dangerously-skip-permissions').Count -gt 0
    } catch { return $false }
}

function Test-UnderstandAnythingEnabled {
    if ($SimulateFreshMachine) { return $false }
    $sp = Join-Path $env:USERPROFILE '.claude\settings.json'
    if (-not (Test-Path $sp)) { return $false }
    try {
        $cfg = Get-Content $sp -Raw -Encoding UTF8 | ConvertFrom-Json
        return ($cfg.enabledPlugins.'understand-anything@understand-anything' -eq $true)
    } catch { return $false }
}

function Test-EveExeMirror {
    if ($SimulateFreshMachine) { return $false }
    return (Test-Path (Join-Path $env:USERPROFILE '.eve\EVE.exe'))
}

function Test-GitConfigured {
    if ($SimulateFreshMachine) { return $false }
    try {
        $n = (& git config --global --get user.name 2>$null)
        $e = (& git config --global --get user.email 2>$null)
        return (-not [string]::IsNullOrWhiteSpace($n)) -and (-not [string]::IsNullOrWhiteSpace($e))
    } catch { return $false }
}

function Test-VaultDaemonReachable {
    if ($SimulateFreshMachine) { return $false }
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect('127.0.0.1', 5078, $null, $null)
        $ok = $async.AsyncWaitHandle.WaitOne(700, $false)
        if ($ok -and $client.Connected) {
            $client.Close()
            return $true
        }
        $client.Close()
        return $false
    } catch { return $false }
}

# --- Probe each signal -----------------------------------------------------

# SimulateFreshMachine flips key checks to FAIL so wizard would fire on a real fresh PC
$simFresh = [bool]$SimulateFreshMachine

$mcpListProbe = Test-ClaudeMcpList

$checks = [ordered]@{
    sanctum_root_exists       = (-not $simFresh) -and (Test-SanctumStructure)
    marker_present            = (-not $simFresh) -and (Test-Path $markerFile)
    git_bash_present          = (-not $simFresh) -and (Test-GitForWindows)
    claude_cli_present        = (-not $simFresh) -and ((Test-CommandPresent 'claude.exe') -or (Test-CommandPresent 'claude'))
    node_present              = (-not $simFresh) -and ((Test-CommandPresent 'node.exe') -or (Test-CommandPresent 'node'))
    python_present            = (-not $simFresh) -and ((Test-CommandPresent 'python.exe') -or (Test-CommandPresent 'python'))
    anthropic_api_key_present = (-not $simFresh) -and (-not [string]::IsNullOrWhiteSpace($env:ANTHROPIC_API_KEY))
    shared_memory_initialized = (-not $simFresh) -and (Test-Path (Join-Path $SanctumRoot '_shared-memory'))
    projects_json_present     = (-not $simFresh) -and (Test-Path (Join-Path $SanctumRoot 'automations\session-templates\projects.json'))
    prefs_json_present        = (-not $simFresh) -and (Test-Path (Join-Path $SanctumRoot 'automations\session-templates\agent-prefs.json'))
    vault_setup               = (-not $simFresh) -and (Test-Path (Join-Path $SanctumRoot '_vault'))
    claude_creds_present      = (-not $simFresh) -and ((Test-Path (Join-Path $env:USERPROFILE '.claude\.credentials.json')) -or (Test-Path (Join-Path $env:USERPROFILE '.claude.json')))
    network_reachable         = Test-NetworkReachable -RemoteHost 'api.anthropic.com'
    # NEW v3 -- expanded surface for Leo fresh-machine auto-setup
    docker_cli_present        = (-not $simFresh) -and (Test-CommandPresent 'docker')
    docker_daemon_reachable   = Test-DockerDaemon
    mcp_config_present        = Test-McpConfigPresent
    mcp_servers_connected     = ($mcpListProbe.ok -and $mcpListProbe.count -gt 0)
    mcp_servers_connected_n   = $mcpListProbe.count
    task_auto_push            = Test-ScheduledTask 'SinisterSanctumAutoPush'
    task_oauth_health         = Test-ScheduledTask 'SinisterOAuthHealthPoll'
    task_link_poll            = Test-ScheduledTask 'SinisterLinkPoll'
    task_account_watchdog     = Test-ScheduledTask 'SinisterAccountWatchdog'
    bypass_permissions_on     = Test-BypassPermissions
    understand_anything_on    = Test-UnderstandAnythingEnabled
    eve_exe_mirrored          = Test-EveExeMirror
    git_user_configured       = Test-GitConfigured
    vault_daemon_reachable    = Test-VaultDaemonReachable
    operator_name             = (Get-OperatorName)
}

# --- Decide first-run / hard-block / soft-warn -----------------------------

$hardBlocks = @()    # exit 1 if any
$softWarns  = @()    # exit 2 if any (and no hardBlocks)

if ($Force) { $hardBlocks += 'force-flag-set' }
if (-not $checks.sanctum_root_exists) { $hardBlocks += "sanctum-root-missing-or-incomplete ($SanctumRoot)" }
if (-not $checks.git_bash_present)    { $hardBlocks += 'git-for-windows-missing (install: https://gitforwindows.org)' }
if (-not $checks.claude_cli_present)  { $hardBlocks += 'claude-cli-missing (install Node + npm i -g @anthropic-ai/claude-code)' }
if (-not $checks.shared_memory_initialized) { $hardBlocks += 'shared-memory-uninitialized (_shared-memory/ tree missing)' }
if (-not $checks.claude_creds_present -and -not $checks.anthropic_api_key_present) {
    $hardBlocks += 'no-auth (neither ~/.claude credentials nor ANTHROPIC_API_KEY env)'
}

# marker missing alone is soft-warn (first-run wizard hasn't been run yet on this PC)
if (-not $checks.marker_present -and $hardBlocks.Count -eq 0) {
    $softWarns += 'autonomy-marker-missing (~/.sanctum-autonomy-granted) - wizard will create'
}
if (-not $checks.node_present)              { $softWarns += 'node-missing (needed to install claude CLI if missing)' }
if (-not $checks.python_present)            { $softWarns += 'python-missing (only needed to rebuild EVE.exe)' }
if (-not $checks.network_reachable)         { $softWarns += 'network-unreachable (api.anthropic.com unreachable - check internet)' }
if (-not $checks.anthropic_api_key_present) { $softWarns += 'ANTHROPIC_API_KEY env not set (claude CLI OAuth still works)' }
if (-not $checks.vault_setup)               { $softWarns += 'vault not initialized (collaborative sync inactive; ok for solo bring-up)' }
if (-not $checks.prefs_json_present)        { $softWarns += 'agent-prefs.json missing (first spawn will create defaults)' }
# NEW v3 soft-warns -- wizard auto-fixes each
if (-not $checks.docker_cli_present)        { $softWarns += 'docker-cli-missing (Docker Desktop not installed; bot Tier-2 LLM stack offline. winget install Docker.DockerDesktop)' }
if ($checks.docker_cli_present -and -not $checks.docker_daemon_reachable) { $softWarns += 'docker-daemon-not-reachable (Docker Desktop installed but not running; start it from Start menu)' }
if (-not $checks.mcp_config_present)        { $softWarns += 'mcp-config-missing (~/.claude/.mcp.json absent; wizard will copy template from automations/templates/leo-mcp-config.json)' }
if ($checks.claude_cli_present -and -not $checks.mcp_servers_connected) { $softWarns += "mcp-servers-not-connected ($($checks.mcp_servers_connected_n) connected per `claude mcp list`; expect 15+ on fully-set-up machine)" }
if (-not $checks.task_auto_push)            { $softWarns += 'task-auto-push-missing (SinisterSanctumAutoPush not registered; wizard will install)' }
if (-not $checks.task_oauth_health)         { $softWarns += 'task-oauth-health-missing (SinisterOAuthHealthPoll not registered; wizard will install)' }
if (-not $checks.task_link_poll)            { $softWarns += 'task-link-poll-missing (SinisterLinkPoll not registered; wizard will install)' }
if (-not $checks.task_account_watchdog)     { $softWarns += 'task-account-watchdog-missing (SinisterAccountWatchdog not registered; wizard will install)' }
if (-not $checks.bypass_permissions_on)     { $softWarns += 'bypass-permissions-off (~/.claude/settings.json missing bypassPermissions=true OR dangerously-skip in allow-list; wizard will fix via grant-claude-autonomy.ps1)' }
if (-not $checks.understand_anything_on)    { $softWarns += 'understand-anything-plugin-disabled (cold-start step 0 requires it; wizard will enable via grant-claude-autonomy.ps1)' }
if (-not $checks.eve_exe_mirrored)          { $softWarns += 'eve-exe-mirror-missing (~/.eve/EVE.exe not present; non-blocking - run verify-eve-features.ps1 -SyncMirror)' }
if (-not $checks.git_user_configured)       { $softWarns += 'git-user-not-configured (set with: git config --global user.name + user.email; wizard agent will prompt)' }
if (-not $checks.vault_daemon_reachable)    { $softWarns += 'vault-daemon-unreachable (port :5078 not listening; optional - skip unless you want vault sync)' }

$isFirstRun = ($hardBlocks.Count -gt 0)
$exitCode = if ($isFirstRun) { 1 } elseif ($softWarns.Count -gt 0) { 2 } else { 0 }

# --- Build payload ---------------------------------------------------------

$payload = [ordered]@{
    is_first_run  = $isFirstRun
    exit_code     = $exitCode
    operator_name = $checks.operator_name
    hard_blocks   = $hardBlocks
    soft_warns    = $softWarns
    reasons       = $hardBlocks                # backward-compat name
    warnings      = $softWarns                 # backward-compat name
    checks        = $checks
    sanctum_root  = $SanctumRoot
    marker_file   = $markerFile
    ts_utc        = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    sim_fresh     = $simFresh
}

# --- Render ----------------------------------------------------------------

if ($Format -eq 'json') {
    $payload | ConvertTo-Json -Depth 4 -Compress
} else {
    Write-Host ''
    Write-Host ('  EVE First-Run Check :: ' + $checks.operator_name + ' @ ' + $env:COMPUTERNAME) -ForegroundColor White
    if ($simFresh) { Write-Host '  [SIMULATING FRESH MACHINE]' -ForegroundColor Magenta }
    Write-Host ''
    if ($isFirstRun) {
        Write-Host '  [FIRST-RUN DETECTED - wizard MUST fire]' -ForegroundColor Yellow
        Write-Host '  Hard blocks:' -ForegroundColor Gray
        foreach ($r in $hardBlocks) { Write-Host ('    - ' + $r) -ForegroundColor Red }
    } elseif ($exitCode -eq 2) {
        Write-Host '  [SOFT WARNS - wizard recommended but not required]' -ForegroundColor DarkYellow
    } else {
        Write-Host '  [SETUP COMPLETE - no first-run needed]' -ForegroundColor Green
    }
    if ($softWarns.Count -gt 0) {
        Write-Host '  Warnings (non-blocking):' -ForegroundColor Gray
        foreach ($w in $softWarns) { Write-Host ('    - ' + $w) -ForegroundColor DarkYellow }
    }
    Write-Host ''
    Write-Host '  Checks:' -ForegroundColor Gray
    foreach ($k in $checks.Keys) {
        if ($k -eq 'operator_name') { continue }
        if ($k -eq 'mcp_servers_connected_n') { continue }
        $v = $checks[$k]
        $tag = if ($v) { '[OK]  ' } else { '[FAIL]' }
        $col = if ($v) { 'Green' } else { 'Red' }
        $detail = ''
        if ($k -eq 'mcp_servers_connected' -and $v) { $detail = " ($($checks.mcp_servers_connected_n) connected)" }
        Write-Host ('    ' + $tag + '  ' + $k + $detail) -ForegroundColor $col
    }
    Write-Host ''
}

exit $exitCode
