# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# sanctum-skills-hub.ps1 -- one-click operator menu for the Sanctum Skills Hub.
#
# Invoked from C:\Users\Zonia\Desktop\Sanctum-Skills-Hub.bat. Lets the operator:
#   1) view fleet state (read-only)
#   2) regenerate skills/HUB.md from the registry
#   3) install Image 2 MCP set (Playwright + Context7 + Sequential-thinking + KG-memory)
#   4) register RKOJ + SinisterVault scheduled tasks via UAC self-elevation
#   5) open skills/HUB.md in notepad
#   6) open skills/ folder in Explorer
#   7) print env-var set commands for the operator to copy
#   8) open the 5 Phase-C Ruflo skill case-studies for thumb review
#   q) quit
#
# Read-only by default; every write action is gated behind explicit menu pick.

[CmdletBinding()]
param(
    [string]$Action,        # internal: used by self-elevation to skip menu and run a specific action
    [switch]$Elevated       # internal: set true after self-elevation completes
)

$ErrorActionPreference = 'Continue'
$Purple   = 'Magenta'
$Sanctum  = 'D:\Sinister Sanctum'

function Write-PurpleBar { Write-Host '################################################################' -ForegroundColor $Purple }
function Write-Section   { param([string]$T) Write-Host ''; Write-Host ('== ' + $T + ' ==') -ForegroundColor $Purple }
function Write-OK        { param([string]$M) Write-Host ('[ OK ] ' + $M) -ForegroundColor Green }
function Write-Warn      { param([string]$M) Write-Host ('[WARN] ' + $M) -ForegroundColor Yellow }
function Write-Info      { param([string]$M) Write-Host ('[INFO] ' + $M) -ForegroundColor White }
function Write-Dim       { param([string]$M) Write-Host ('  ' + $M) -ForegroundColor DarkGray }
function Write-Prompt    { param([string]$M) Write-Host $M -ForegroundColor Cyan -NoNewline }

function Show-Banner {
    Clear-Host
    Write-Host ''
    Write-PurpleBar
    Write-Host '##                                                            ##' -ForegroundColor $Purple
    Write-Host '##   S A N C T U M    S K I L L S    H U B                    ##' -ForegroundColor $Purple
    Write-Host '##   one place every Sanctum agent reads on cold-start        ##' -ForegroundColor $Purple
    Write-Host '##                                                            ##' -ForegroundColor $Purple
    Write-PurpleBar
    Write-Host ''
    Write-Dim ('source-of-truth: ' + (Join-Path $Sanctum 'skills\_REGISTRY.yaml'))
    Write-Dim ('hub doc        : ' + (Join-Path $Sanctum 'skills\HUB.md'))
    Write-Dim ('security doc   : ' + (Join-Path $Sanctum 'skills\SECURITY.md'))
    Write-Host ''
}

function Show-Menu {
    Write-Section 'Menu (pick a number, then ENTER)'
    Write-Host '  [1] Status      -- run verify-fleet-state + sync-fleet dry-run (read-only)' -ForegroundColor White
    Write-Host '  [2] Regen HUB   -- sync-fleet.ps1 -Apply  (regenerates skills\HUB.md from registry)' -ForegroundColor White
    Write-Host '  [3] Install MCPs-- Image 2 set: Playwright + Context7 + Sequential-thinking + KG-memory' -ForegroundColor White
    Write-Host '  [4] Reg tasks   -- register RKOJ + SinisterVault scheduled tasks (UAC self-elevate)' -ForegroundColor White
    Write-Host '  [5] Open HUB    -- notepad skills\HUB.md' -ForegroundColor White
    Write-Host '  [6] Open folder -- explorer skills\' -ForegroundColor White
    Write-Host '  [7] Env vars    -- print exact SetEnvironmentVariable commands to copy' -ForegroundColor White
    Write-Host '  [8] Case studies-- open the 5 Phase-C Ruflo skill verdicts for your thumb' -ForegroundColor White
    Write-Host '  [q] Quit' -ForegroundColor White
    Write-Host ''
}

function Run-Status {
    Write-Section 'Status :: verify-fleet-state.ps1'
    & powershell -ExecutionPolicy Bypass -File (Join-Path $Sanctum 'automations\verify-fleet-state.ps1')

    Write-Section 'Status :: sync-fleet.ps1 (dry-run)'
    & powershell -ExecutionPolicy Bypass -File (Join-Path $Sanctum 'automations\sync-fleet.ps1')
}

function Run-RegenHub {
    Write-Section 'Regen :: sync-fleet.ps1 -Apply'
    Write-Warn 'this OVERWRITES skills\HUB.md with the auto-generated version from _REGISTRY.yaml.'
    Write-Prompt 'continue? (y/N): '
    $ans = Read-Host
    if ($ans -match '^[yY]') {
        & powershell -ExecutionPolicy Bypass -File (Join-Path $Sanctum 'automations\sync-fleet.ps1') -Apply
    } else {
        Write-Info 'cancelled.'
    }
}

function Run-InstallMcps {
    Write-Section 'Install :: install-mcp-servers.ps1'
    Write-Warn 'this adds 4 vendor MCP servers to ~/.claude/.mcp.json (backs up first):'
    Write-Dim '  - playwright           (@playwright/mcp@latest)'
    Write-Dim '  - context7             (@upstash/context7-mcp@latest)'
    Write-Dim '  - sequential-thinking  (@modelcontextprotocol/server-sequential-thinking)'
    Write-Dim '  - memory               (@modelcontextprotocol/server-memory)'
    Write-Dim 'on first use, npx will fetch each package (Playwright ~150 MB Chromium).'
    Write-Dim 'YOU MUST RESTART CLAUDE CODE after this so the new servers load.'
    Write-Host ''
    Write-Prompt 'continue? (y/N): '
    $ans = Read-Host
    if ($ans -match '^[yY]') {
        & powershell -ExecutionPolicy Bypass -File (Join-Path $Sanctum 'automations\install-mcp-servers.ps1')
        Write-Host ''
        Write-Warn '>>> RESTART CLAUDE CODE NOW so the new MCP servers load. <<<'
    } else {
        Write-Info 'cancelled.'
    }
}

function Run-RegTasks {
    Write-Section 'Register :: RKOJ + SinisterVault scheduled tasks'

    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Warn 'this requires UAC (RunLevel Highest tasks). Self-elevating in a new window...'
        Start-Sleep -Milliseconds 600
        try {
            $self = $MyInvocation.MyCommand.Path
            Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", "`"$self`"", "-Elevated", "-Action", "regtasks"
            Write-Info 'elevated window launched. Watch the UAC prompt + the new window.'
        } catch {
            Write-Warn ('UAC denied or cancelled: ' + $_.Exception.Message)
        }
        return
    }

    # Elevated path -- actually register the tasks
    Write-Info 'running install-console-task.ps1 (RKOJ auto-start)...'
    $rkoj = Join-Path $Sanctum 'automations\window-manager\install-console-task.ps1'
    if (Test-Path -LiteralPath $rkoj) {
        & powershell -ExecutionPolicy Bypass -File $rkoj
    } else {
        Write-Warn ('not found: ' + $rkoj)
    }

    Write-Info 'running install-vault-task.ps1 (SinisterVault daemon)...'
    $vault = Join-Path $Sanctum 'tools\sinister-vault\install-vault-task.ps1'
    if (Test-Path -LiteralPath $vault) {
        & powershell -ExecutionPolicy Bypass -File $vault
    } else {
        Write-Warn ('not found: ' + $vault)
    }

    Write-Host ''
    Write-Info 'verifying registration...'
    foreach ($n in @('RKOJ','SinisterVault')) {
        try {
            $t = Get-ScheduledTask -TaskName $n -ErrorAction Stop
            Write-OK ('' + $n.PadRight(20) + ' state=' + $t.State)
        } catch {
            Write-Warn ('' + $n.PadRight(20) + ' NOT registered')
        }
    }
}

function Run-OpenHub {
    $hub = Join-Path $Sanctum 'skills\HUB.md'
    if (Test-Path -LiteralPath $hub) {
        Write-Info ('opening: ' + $hub)
        Start-Process notepad.exe $hub
    } else {
        Write-Warn ('not found: ' + $hub)
    }
}

function Run-OpenFolder {
    $skills = Join-Path $Sanctum 'skills'
    Write-Info ('opening: ' + $skills)
    Start-Process explorer.exe $skills
}

function Run-EnvVars {
    Write-Section 'Env vars to set (copy + paste into any PowerShell window)'

    $envs = @(
        @{ name='ANTHROPIC_API_KEY';         value='sk-ant-api03-<your-key>'; unlocks='Scribe + Curator + Chatbot LLM paths' }
        @{ name='SINISTER_VAULT_PASSPHRASE'; value='<a-strong-passphrase>';   unlocks='at-rest Fernet encryption (_vault/)' }
        @{ name='OPENAI_API_KEY';            value='sk-<your-openai-key>';    unlocks='Codex Companion peer-review' }
        @{ name='LEO_ANTHROPIC_API_KEY';     value='sk-ant-api03-<leo-key>';  unlocks='leo billing isolation (low pri)' }
    )

    foreach ($e in $envs) {
        $current = [Environment]::GetEnvironmentVariable($e.name, 'User')
        $marker = if ($current) { 'SET' } else { 'unset' }
        $color = if ($current) { 'Green' } else { 'Yellow' }
        Write-Host ('  ' + $e.name.PadRight(28) + '[' + $marker + ']') -ForegroundColor $color
        Write-Dim ('  unlocks: ' + $e.unlocks)
        Write-Host ('  [Environment]::SetEnvironmentVariable(''' + $e.name + ''',''' + $e.value + ''',''User'')') -ForegroundColor DarkGray
        Write-Host ''
    }
    Write-Info 'after setting, RESTART any open PowerShell + Claude Code so new values are picked up.'
    Write-Info 'see also: D:\Sinister Sanctum\docs\ENV-VARIABLES.md for the full reference.'
}

function Run-CaseStudies {
    Write-Section 'Phase-C case-studies (thumb up = KEEP-WITH-CHANGES, thumb down = ARCHIVE)'

    $caseDir = Join-Path $Sanctum '_shared-memory\case-studies'
    $files = @(
        '2026-05-19-sk-swarm-coord.md'
        '2026-05-19-sk-vector-memory.md'
        '2026-05-19-sk-federation.md'
        '2026-05-19-sk-observability.md'
        '2026-05-19-sk-aidefence.md'
    )

    foreach ($f in $files) {
        $path = Join-Path $caseDir $f
        if (Test-Path -LiteralPath $path) {
            Write-OK $f
        } else {
            Write-Warn ('NOT FOUND: ' + $f)
        }
    }
    Write-Host ''
    Write-Prompt 'open all 5 in notepad now? (y/N): '
    $ans = Read-Host
    if ($ans -match '^[yY]') {
        foreach ($f in $files) {
            $path = Join-Path $caseDir $f
            if (Test-Path -LiteralPath $path) {
                Start-Process notepad.exe $path
                Start-Sleep -Milliseconds 200
            }
        }
        Write-Info '5 notepad windows opened. After reading each, append your thumb to the matching skills/_INDEX.md row (candidate -> fixed or archived).'
    }
}

# ============================================================================
# main
# ============================================================================

if ($Elevated -and $Action -eq 'regtasks') {
    # we are the self-elevated child window
    Show-Banner
    Write-Host '  (elevated mode -- registering scheduled tasks)' -ForegroundColor Yellow
    Run-RegTasks
    Write-Host ''
    Write-Info 'press ENTER to close this elevated window.'
    Read-Host | Out-Null
    exit 0
}

while ($true) {
    Show-Banner
    Show-Menu
    Write-Prompt 'choice: '
    $pick = Read-Host
    $pick = $pick.Trim().ToLower()
    if ($pick -eq 'q' -or $pick -eq 'quit' -or $pick -eq 'exit') {
        Write-Info 'goodbye.'
        break
    }
    switch ($pick) {
        '1' { Run-Status }
        '2' { Run-RegenHub }
        '3' { Run-InstallMcps }
        '4' { Run-RegTasks }
        '5' { Run-OpenHub }
        '6' { Run-OpenFolder }
        '7' { Run-EnvVars }
        '8' { Run-CaseStudies }
        default { Write-Warn ('unknown choice: ' + $pick) }
    }
    Write-Host ''
    Write-Prompt 'press ENTER to return to the menu...'
    Read-Host | Out-Null
}

Write-Host ''
Write-Info 'session ended. Re-run via C:\Users\Zonia\Desktop\Sanctum-Skills-Hub.bat any time.'
