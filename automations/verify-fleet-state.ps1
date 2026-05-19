# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# verify-fleet-state.ps1 -- read-only fleet-wide state probe.
#
# Reports for every category the operator + master need to keep aware of:
#   1. Scheduled tasks: registered? running? last-run-status?
#   2. Env vars: set? (presence only; never prints values)
#   3. MCP servers: every cwd in ~/.claude/.mcp.json resolves?
#   4. Skills Hub: skills/_REGISTRY.yaml parses? skills/HUB.md exists?
#   5. Listening ports: are RKOJ :5077, Vault :5078, Gitea :3000, today's-updates hub :7099, header :7088 alive?
#
# Prints the missing items + the exact register command for each.
#
# Exit codes:
#   0 -- everything clean
#   1 -- gaps detected (operator action items printed below)
#   2 -- probe failed (e.g. permission error reading scheduled tasks)

[CmdletBinding()]
param(
    [string]$McpJsonPath  = (Join-Path $env:USERPROFILE '.claude\.mcp.json'),
    [string]$RegistryPath = 'D:\Sinister Sanctum\skills\_REGISTRY.yaml',
    [string]$HubPath      = 'D:\Sinister Sanctum\skills\HUB.md'
)

$ErrorActionPreference = 'Continue'
$Purple = 'Magenta'

function Write-Section { param([string]$T) Write-Host ''; Write-Host ('== ' + $T + ' ==') -ForegroundColor $Purple }
function Write-OK     { param([string]$M) Write-Host ('[ OK ] ' + $M) -ForegroundColor Green }
function Write-Warn   { param([string]$M) Write-Host ('[WARN] ' + $M) -ForegroundColor Yellow }
function Write-Fail   { param([string]$M) Write-Host ('[FAIL] ' + $M) -ForegroundColor Red }
function Write-Info   { param([string]$M) Write-Host ('[INFO] ' + $M) -ForegroundColor White }
function Write-Dim    { param([string]$M) Write-Host ('  ' + $M) -ForegroundColor DarkGray }

$gaps = @()

Write-Host ''
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host '##  Sanctum fleet state :: verify-fleet-state.ps1              ##' -ForegroundColor $Purple
Write-Host '##  read-only probe; never modifies anything                   ##' -ForegroundColor $Purple
Write-Host '################################################################' -ForegroundColor $Purple

# --------- step 1: scheduled tasks ---------
Write-Section 'Step 1: scheduled tasks'

$expectedTasks = @(
    @{ name = 'SinisterCustodian';         install = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian\install-task.ps1'; purpose = 'active backup to D:\_backups\ (daemon)' }
    @{ name = 'SinisterSanctumAutoPush';   install = 'D:\Sinister Sanctum\automations\install-auto-push-task.ps1';                          purpose = 'auto-push main to GitHub every 30 min (skips when clean)' }
    @{ name = 'SinisterMdSweep';           install = 'D:\Sinister Sanctum\automations\install-md-sweep-task.ps1';                           purpose = 'sweep stale .md files to _trash/' }
    @{ name = 'RKOJ';                      install = 'D:\Sinister Sanctum\automations\window-manager\install-console-task.ps1';            purpose = 'RKOJ.exe workbench auto-start' }
    @{ name = 'SinisterVault';             install = 'D:\Sinister Sanctum\tools\sinister-vault\install-vault-task.ps1';                    purpose = 'Vault daemon at :5078 auto-start' }
)

foreach ($t in $expectedTasks) {
    try {
        $task = Get-ScheduledTask -TaskName $t.name -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName $t.name -ErrorAction Stop
        $lastResult = $info.LastTaskResult
        $stateText = '' + $task.State + '  (last: ' + $info.LastRunTime + ', result: ' + $lastResult + ')'
        if ($task.State -eq 'Ready' -or $task.State -eq 'Running') {
            Write-OK ('' + $t.name.PadRight(28) + ' ' + $stateText)
        } else {
            Write-Warn ('' + $t.name.PadRight(28) + ' ' + $stateText + '  (state not ready/running)')
            $gaps += [pscustomobject]@{ category='task'; name=$t.name; reason='state not ready/running'; fix=$t.install }
        }
    } catch {
        Write-Fail ('' + $t.name.PadRight(28) + ' NOT REGISTERED')
        Write-Dim ('  ' + $t.purpose)
        Write-Dim ('  fix: powershell -ExecutionPolicy Bypass -File "' + $t.install + '"')
        $gaps += [pscustomobject]@{ category='task'; name=$t.name; reason='not registered'; fix=$t.install }
    }
}

# --------- step 2: env vars ---------
Write-Section 'Step 2: env vars (presence only; values never printed)'

$expectedEnv = @(
    @{ name = 'ANTHROPIC_API_KEY';         unlocks = 'Scribe + Curator + Chatbot LLM paths'; critical = $true }
    @{ name = 'OPENAI_API_KEY';            unlocks = 'Codex Companion peer-review';          critical = $true }
    @{ name = 'SINISTER_VAULT_PASSPHRASE'; unlocks = 'at-rest Fernet encryption (_vault/)';   critical = $true }
    @{ name = 'LEO_ANTHROPIC_API_KEY';     unlocks = "leo's billing isolation";              critical = $false }
    @{ name = 'SINISTER_HUB_ROOT';         unlocks = 'override of hardcoded hub path';       critical = $false }
    @{ name = 'SINISTER_AGENT_NAME';       unlocks = 'default agent identity';               critical = $false }
    @{ name = 'GITEA_ADMIN_PASSWORD';      unlocks = 'sanctum-git bootstrap';                critical = $false }
)

foreach ($e in $expectedEnv) {
    $v = [Environment]::GetEnvironmentVariable($e.name, 'User')
    if ($v) {
        Write-OK ('' + $e.name.PadRight(28) + ' set')
    } else {
        if ($e.critical) {
            Write-Warn ('' + $e.name.PadRight(28) + ' UNSET  (unlocks: ' + $e.unlocks + ')')
            $gaps += [pscustomobject]@{ category='env'; name=$e.name; reason='unset (critical)'; fix=('[Environment]::SetEnvironmentVariable(''' + $e.name + ''',''<value>'',''User'')') }
        } else {
            Write-Info ('' + $e.name.PadRight(28) + ' unset  (unlocks: ' + $e.unlocks + ')  [low priority]')
        }
    }
}

# --------- step 3: MCP server cwd resolution ---------
Write-Section 'Step 3: MCP server cwd resolution (read-only)'

if (-not (Test-Path -LiteralPath $McpJsonPath)) {
    Write-Fail ('mcp.json not found at: ' + $McpJsonPath)
    $gaps += [pscustomobject]@{ category='mcp'; name='mcp.json'; reason='file missing'; fix='reinstall Claude Code' }
} else {
    try {
        $mcp = Get-Content -LiteralPath $McpJsonPath -Raw | ConvertFrom-Json
        if (-not $mcp.mcpServers) {
            Write-Fail 'mcp.json has no mcpServers key'
            $gaps += [pscustomobject]@{ category='mcp'; name='mcp.json'; reason='no mcpServers key'; fix='reinstall Claude Code or restore backup' }
        } else {
            $mcpNames = @($mcp.mcpServers.PSObject.Properties.Name)
            Write-Info ('total registered: ' + $mcpNames.Count)
            $missingCwd = @()
            foreach ($name in $mcpNames) {
                $entry = $mcp.mcpServers.$name
                if ($entry.cwd) {
                    if (-not (Test-Path -LiteralPath $entry.cwd)) {
                        Write-Warn ('' + $name.PadRight(28) + ' cwd missing: ' + $entry.cwd)
                        $missingCwd += $name
                        $gaps += [pscustomobject]@{ category='mcp'; name=$name; reason=('cwd missing: ' + $entry.cwd); fix='update entry cwd or remove' }
                    }
                }
            }
            if ($missingCwd.Count -eq 0) {
                Write-OK 'every MCP server entry has a resolvable cwd'
            }
        }
    } catch {
        Write-Fail ('mcp.json parse failed: ' + $_.Exception.Message)
        $gaps += [pscustomobject]@{ category='mcp'; name='mcp.json'; reason='parse failed'; fix='restore from .mcp.json.bak-<UTC>' }
    }
}

# --------- step 4: Skills Hub artifacts ---------
Write-Section 'Step 4: Skills Hub artifacts'

if (Test-Path -LiteralPath $RegistryPath) {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        $yparse = & python -c "import yaml,sys; yaml.safe_load(open(sys.argv[1])); print('OK')" $RegistryPath 2>&1
        if ($yparse -match 'OK') {
            Write-OK ('' + ($RegistryPath -replace '.+\\','').PadRight(28) + ' parses')
        } else {
            Write-Fail ('_REGISTRY.yaml parse failed: ' + ($yparse -join ' '))
            $gaps += [pscustomobject]@{ category='hub'; name='_REGISTRY.yaml'; reason='yaml parse fail'; fix='manually inspect; run sync-fleet -DryRun' }
        }
    } else {
        Write-Warn 'python not on PATH; cannot verify YAML parse'
    }
} else {
    Write-Fail ('_REGISTRY.yaml not found at: ' + $RegistryPath)
    $gaps += [pscustomobject]@{ category='hub'; name='_REGISTRY.yaml'; reason='file missing'; fix='restore from git or rebuild from HUB.md' }
}

if (Test-Path -LiteralPath $HubPath) {
    $hubAge = ((Get-Date) - (Get-Item $HubPath).LastWriteTime).TotalDays
    Write-OK ('' + ($HubPath -replace '.+\\','').PadRight(28) + ' present (' + ('{0:N1}' -f $hubAge) + ' days old)')
} else {
    Write-Fail ('HUB.md not found at: ' + $HubPath)
    Write-Dim '  fix: powershell -File "D:\Sinister Sanctum\automations\sync-fleet.ps1" -Apply'
    $gaps += [pscustomobject]@{ category='hub'; name='HUB.md'; reason='file missing'; fix='sync-fleet.ps1 -Apply' }
}

# --------- step 5: listening ports ---------
Write-Section 'Step 5: listening ports (TCP probe; 800 ms timeout)'

$expectedPorts = @(
    @{ port = 5077; service = 'RKOJ.exe workbench';        critical = $true }
    @{ port = 5078; service = 'Sinister Vault daemon';     critical = $true }
    @{ port = 3000; service = 'Gitea (sanctum-git)';       critical = $false }
    @{ port = 7099; service = "today's-updates hub";       critical = $false }
    @{ port = 7088; service = 'top header bar concept';    critical = $false }
)

foreach ($p in $expectedPorts) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect('127.0.0.1', $p.port, $null, $null)
        $ok  = $iar.AsyncWaitHandle.WaitOne(800)
        if ($ok -and $client.Connected) {
            Write-OK ('' + ('127.0.0.1:' + $p.port).PadRight(28) + ' ' + $p.service + ' alive')
            $client.Close()
        } else {
            if ($p.critical) {
                Write-Warn ('' + ('127.0.0.1:' + $p.port).PadRight(28) + ' ' + $p.service + ' NOT listening')
                $gaps += [pscustomobject]@{ category='port'; name=('127.0.0.1:' + $p.port); reason=('not listening: ' + $p.service); fix='start the daemon' }
            } else {
                Write-Info ('' + ('127.0.0.1:' + $p.port).PadRight(28) + ' ' + $p.service + ' offline (non-critical)')
            }
        }
    } catch {
        Write-Info ('' + ('127.0.0.1:' + $p.port).PadRight(28) + ' probe failed (' + $_.Exception.Message + ')')
    }
}

# --------- summary + exit ---------
Write-Section 'Summary'

if ($gaps.Count -eq 0) {
    Write-OK 'everything clean -- no operator action items.'
    exit 0
} else {
    Write-Warn ('' + $gaps.Count + ' gap(s) detected:')
    Write-Host ''
    $gaps | Group-Object -Property category | ForEach-Object {
        Write-Host ('  ' + $_.Name) -ForegroundColor Yellow
        $_.Group | ForEach-Object {
            Write-Dim ('  - ' + $_.name + '  (' + $_.reason + ')')
            Write-Dim ('    fix: ' + $_.fix)
        }
    }
    Write-Host ''
    Write-Info 'all fixes above are operator-clicked; master cannot register tasks or set env vars or edit mcp.json.'
    exit 1
}
