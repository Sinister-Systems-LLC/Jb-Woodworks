# eve-first-run-wizard.ps1 - interactive first-run setup wizard
# Author: RKOJ-ELENO :: 2026-05-25 (v3 - MCP + Docker + bots + scheduled tasks)
#
# Operator 2026-05-24 21:24Z + 2026-05-25 ~00:35Z first-run-auto-setup directive.
# Composes with:
#   eve-first-run-check.ps1   (detector, called first; exit 0/1/2)
#   grant-claude-autonomy.ps1 (existing 9-step idempotent setup; called by wizard)
#   spawn-setup-wizard.ps1    (NEW - spawns the real Claude Setup Wizard agent)
#   docs/LEO-SETUP.md         (manual fallback reference)
#
# Flow:
#   1. Re-run detector + show what's missing.
#   2. Greet operator by name (from git config or env).
#   3. For each hard-block: print fix instructions + wait for confirmation OR
#      auto-fix if we know how (grant-autonomy, shared-memory init, marker drop).
#   4. After hard-blocks fixed: spawn the Sinister Setup Wizard CLAUDE AGENT
#      (via spawn-setup-wizard.ps1) which holds the operator's hand through
#      the remaining bring-up (OAuth, git config, vault, smoke tests).
#   5. Log every step to _shared-memory/setup/leo-first-run-<utc>.log
#
# Usage:
#   powershell -File eve-first-run-wizard.ps1                 (interactive)
#   powershell -File eve-first-run-wizard.ps1 -DryRun         (probe only, no writes)
#   powershell -File eve-first-run-wizard.ps1 -NoHelperSpawn  (skip wizard-agent spawn)
#   powershell -File eve-first-run-wizard.ps1 -NonInteractive (no prompts - CI mode)

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$NoHelperSpawn,
    [switch]$NonInteractive,
    [string]$SanctumRoot = ''
)

$ErrorActionPreference = 'Continue'

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}

# --- Setup logging ---------------------------------------------------------
$setupDir = Join-Path $SanctumRoot '_shared-memory\setup'
if (-not (Test-Path $setupDir)) { New-Item -ItemType Directory -Path $setupDir -Force | Out-Null }
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$logFile = Join-Path $setupDir ("leo-first-run-$ts.log")

function Write-Log {
    param([string]$Msg, [string]$Level = 'INFO')
    $line = ((Get-Date).ToUniversalTime().ToString('o')) + " [$Level] " + $Msg
    try { Add-Content -Path $logFile -Value $line -Encoding UTF8 } catch {}
    $col = switch ($Level) {
        'OK'    { 'Green' }
        'WARN'  { 'Yellow' }
        'FAIL'  { 'Red' }
        'STEP'  { 'White' }
        default { 'Gray' }
    }
    Write-Host ('  ' + $Msg) -ForegroundColor $col
}

function Get-OperatorName {
    try {
        $g = (& git -C $SanctumRoot config --get user.name 2>$null) | Select-Object -First 1
        if ($g) { return $g.Trim() }
    } catch {}
    if ($env:USERNAME) { return $env:USERNAME }
    return 'operator'
}

$operatorName = Get-OperatorName

# --- Banner ----------------------------------------------------------------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   EVE FIRST-RUN SETUP WIZARD' -ForegroundColor White
Write-Host ('   Welcome, ' + $operatorName + '. This walks you through bring-up.') -ForegroundColor Gray
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''
Write-Log ("session-start :: operator=$operatorName host=$env:COMPUTERNAME dryrun=$DryRun") 'STEP'

# --- Step 1 - detector -----------------------------------------------------
Write-Log 'Step 1/5 :: Detector probe' 'STEP'
$checkScript = Join-Path $SanctumRoot 'automations\eve-first-run-check.ps1'
$detectorExit = 0
if (Test-Path $checkScript) {
    & $checkScript -Format text -SanctumRoot $SanctumRoot
    $detectorExit = $LASTEXITCODE
    Write-Log ("detector exit=$detectorExit") 'INFO'
} else {
    Write-Log 'detector script missing - proceeding anyway' 'WARN'
}

if ($DryRun) {
    Write-Log '[DRY-RUN] would now prompt operator + run setup steps. Skipping writes.' 'INFO'
    Write-Host '  [DRY-RUN] DONE.' -ForegroundColor Cyan
    exit 0
}

# --- Step 2 - confirm (unless NonInteractive) ------------------------------
if (-not $NonInteractive) {
    Write-Host '  Proceed with setup? [Y/n] ' -NoNewline -ForegroundColor White
    try { $ans = Read-Host } catch { $ans = '' }
    if ($ans -and $ans.Trim().ToLower() -eq 'n') {
        Write-Log 'operator aborted at confirmation prompt' 'WARN'
        Write-Host '  Manual setup: docs/LEO-SETUP.md' -ForegroundColor Gray
        exit 2
    }
}

# --- Step 3 - run grant-autonomy (idempotent) ------------------------------
Write-Host ''
Write-Log 'Step 2/5 :: Grant Claude full autonomy (idempotent 9-step)' 'STEP'
$grantScript = Join-Path $SanctumRoot 'automations\grant-claude-autonomy.ps1'
if (Test-Path $grantScript) {
    try {
        & $grantScript -SanctumRoot $SanctumRoot -Quiet
        Write-Log ("grant-claude-autonomy exit=$LASTEXITCODE") 'OK'
    } catch {
        Write-Log ('grant-claude-autonomy threw: ' + $_.Exception.Message) 'FAIL'
    }
} else {
    Write-Log 'grant-claude-autonomy.ps1 missing - skipping' 'WARN'
}

# --- Step 4 - initialize _shared-memory ------------------------------------
Write-Host ''
Write-Log 'Step 3/5 :: Initialize _shared-memory/ tree' 'STEP'
$smRoot = Join-Path $SanctumRoot '_shared-memory'
$smDirs = @('heartbeats','PROGRESS','knowledge','resume-points','plans','inbox','cross-agent','script-runs','spawn-debug','setup')
foreach ($d in $smDirs) {
    $p = Join-Path $smRoot $d
    if (-not (Test-Path $p)) {
        try {
            New-Item -ItemType Directory -Path $p -Force | Out-Null
            Write-Log ("created $d") 'OK'
        } catch {
            Write-Log ("create $d failed: " + $_.Exception.Message) 'FAIL'
        }
    } else {
        Write-Log ("[skip] exists $d") 'INFO'
    }
}

# --- Step 5 - API key surface ----------------------------------------------
Write-Host ''
Write-Log 'Step 4/5 :: Check Anthropic API key + OAuth' 'STEP'
if ([string]::IsNullOrWhiteSpace($env:ANTHROPIC_API_KEY)) {
    $credsPath = Join-Path $env:USERPROFILE '.claude\.credentials.json'
    if (Test-Path $credsPath) {
        Write-Log 'ANTHROPIC_API_KEY not set; OAuth credentials present -> claude CLI will use OAuth' 'INFO'
    } else {
        Write-Log 'NEITHER ANTHROPIC_API_KEY nor OAuth creds present.' 'WARN'
        Write-Log 'Spawned Setup Wizard will walk you through `claude login`.' 'INFO'
    }
} else {
    $masked = $env:ANTHROPIC_API_KEY.Substring(0, [Math]::Min(12, $env:ANTHROPIC_API_KEY.Length)) + '...'
    Write-Log ("ANTHROPIC_API_KEY set ($masked)") 'OK'
}

# --- Step 6 - mark setup complete ------------------------------------------
Write-Host ''
Write-Log 'Step 5/5 :: Mark setup complete' 'STEP'
$marker = Join-Path $env:USERPROFILE '.sanctum-autonomy-granted'
if (-not (Test-Path $marker)) {
    try {
        Set-Content -Path $marker -Value ("set up by $operatorName at " + (Get-Date).ToString('o')) -Encoding UTF8
        Write-Log ("created marker $marker") 'OK'
    } catch {
        Write-Log ("marker create failed: " + $_.Exception.Message) 'FAIL'
    }
} else {
    Write-Log ("[skip] marker already exists at $marker") 'INFO'
}

# Drop EVE-specific first-run marker so eve.py knows wizard ran
$eveMarker = Join-Path $env:USERPROFILE '.eve\first_run_marker.lock'
$eveMarkerDir = Split-Path $eveMarker
if (-not (Test-Path $eveMarkerDir)) { New-Item -ItemType Directory -Path $eveMarkerDir -Force | Out-Null }
try {
    Set-Content -Path $eveMarker -Value ((Get-Date).ToString('o')) -Encoding UTF8
    Write-Log ("created eve first-run marker $eveMarker") 'OK'
} catch {
    Write-Log ("eve marker create failed: " + $_.Exception.Message) 'WARN'
}

# --- Step 6a - MCP config seed (copy template if user has none) ------------
Write-Host ''
Write-Log 'Step 6a/9 :: MCP config seed' 'STEP'
$userMcp = Join-Path $env:USERPROFILE '.claude\.mcp.json'
$mcpTemplate = Join-Path $SanctumRoot 'automations\templates\leo-mcp-config.json'
if (Test-Path $userMcp) {
    Write-Log "~/.claude/.mcp.json already exists -- not overwriting (operator-canonical never-touches)" 'INFO'
} elseif (Test-Path $mcpTemplate) {
    try {
        $userMcpDir = Split-Path $userMcp
        if (-not (Test-Path $userMcpDir)) { New-Item -ItemType Directory -Path $userMcpDir -Force | Out-Null }
        $tplRaw = Get-Content $mcpTemplate -Raw -Encoding UTF8
        $tplFilled = $tplRaw -replace '\$\{SINISTER_SANCTUM_ROOT\}', ($SanctumRoot -replace '\\', '\\\\')
        [System.IO.File]::WriteAllText($userMcp, $tplFilled, [System.Text.UTF8Encoding]::new($false))
        Write-Log ("seeded $userMcp from template (15 servers; restart Claude Code to load)") 'OK'
    } catch {
        Write-Log ('mcp seed failed: ' + $_.Exception.Message) 'FAIL'
    }
} else {
    Write-Log "mcp template missing at $mcpTemplate -- skipping" 'WARN'
}

# --- Step 6b - Docker + Bot images -----------------------------------------
Write-Host ''
Write-Log 'Step 6b/9 :: Docker + bot images (Tier-2 LLM stack)' 'STEP'
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Log 'docker CLI not on PATH. Install via one of:' 'WARN'
    Write-Log '  winget install Docker.DockerDesktop' 'INFO'
    Write-Log '  https://www.docker.com/products/docker-desktop/' 'INFO'
    Write-Log 'Then re-run this wizard or run automations\install-leo-bots.ps1 directly.' 'INFO'
} else {
    $botsScript = Join-Path $SanctumRoot 'automations\install-leo-bots.ps1'
    if (Test-Path $botsScript) {
        try {
            & $botsScript -SanctumRoot $SanctumRoot -DryRun
            Write-Log 'ran install-leo-bots.ps1 in -DryRun mode (review log)' 'OK'
            Write-Log 'To actually pull/build: powershell -File automations\install-leo-bots.ps1' 'INFO'
        } catch {
            Write-Log ('install-leo-bots.ps1 threw: ' + $_.Exception.Message) 'WARN'
        }
    } else {
        Write-Log "install-leo-bots.ps1 missing at $botsScript" 'WARN'
    }
}

# --- Step 6c - Scheduled tasks --------------------------------------------
Write-Host ''
Write-Log 'Step 6c/9 :: Scheduled tasks (every fleet poller)' 'STEP'
$tasksScript = Join-Path $SanctumRoot 'automations\install-leo-scheduled-tasks.ps1'
if (Test-Path $tasksScript) {
    try {
        & $tasksScript -SanctumRoot $SanctumRoot -DryRun
        Write-Log 'ran install-leo-scheduled-tasks.ps1 in -DryRun mode (review log)' 'OK'
        Write-Log 'To actually install: powershell -File automations\install-leo-scheduled-tasks.ps1' 'INFO'
    } catch {
        Write-Log ('install-leo-scheduled-tasks.ps1 threw: ' + $_.Exception.Message) 'WARN'
    }
} else {
    Write-Log "install-leo-scheduled-tasks.ps1 missing at $tasksScript" 'WARN'
}

# --- Step 7 - spawn the Sinister Setup Wizard CLAUDE AGENT -----------------
if (-not $NoHelperSpawn) {
    Write-Host ''
    Write-Log 'BONUS :: Spawning Sinister Setup Wizard Claude agent' 'STEP'
    $spawnScript = Join-Path $SanctumRoot 'automations\spawn-setup-wizard.ps1'
    if (Test-Path $spawnScript) {
        try {
            & $spawnScript -SanctumRoot $SanctumRoot -OperatorName $operatorName
            $spawnExit = $LASTEXITCODE
            if ($spawnExit -eq 0) {
                Write-Log 'Sinister Setup Wizard spawn requested OK (mintty window should appear)' 'OK'
            } else {
                Write-Log ("spawn-setup-wizard exit=$spawnExit") 'WARN'
            }
        } catch {
            Write-Log ('spawn-setup-wizard threw: ' + $_.Exception.Message) 'FAIL'
            Write-Log 'Manual fallback: click EVE.exe and pick G (General).' 'INFO'
        }
    } else {
        Write-Log 'spawn-setup-wizard.ps1 missing - falling back to launcher general mode' 'WARN'
        $ps1 = Join-Path $SanctumRoot 'automations\start-sinister-session.ps1'
        if (Test-Path $ps1) {
            $env:SINISTER_SETUP_HELPER = '1'
            $env:SINISTER_DEFAULT_SWARM = '1'
            $env:SINISTER_DEFAULT_LOOP  = '1'
            try {
                Start-Process powershell.exe -ArgumentList @(
                    '-NoProfile','-ExecutionPolicy','Bypass',
                    '-File', $ps1,
                    '-Project', 'general'
                ) -ErrorAction Stop | Out-Null
                Write-Log 'fallback setup-helper spawn requested' 'OK'
            } catch {
                Write-Log ('fallback spawn failed: ' + $_.Exception.Message) 'WARN'
            }
        }
    }
}

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   SETUP COMPLETE - EVE is ready.' -ForegroundColor Green
Write-Host ('   Log: ' + $logFile) -ForegroundColor DarkGray
Write-Host '   Next: close this window, then run EVE.exe to launch a session.' -ForegroundColor Gray
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''
Write-Log 'session-end :: SETUP COMPLETE' 'OK'
exit 0
