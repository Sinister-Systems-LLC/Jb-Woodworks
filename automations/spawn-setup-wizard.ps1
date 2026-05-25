# spawn-setup-wizard.ps1 - spawn the Sinister Setup Wizard Claude agent
# Author: RKOJ-ELENO :: 2026-05-25 (v2 - extended checklist for MCP/Docker/bots/tasks)
#
# Operator hard-canonical 2026-05-25 ~00:35Z (verbatim):
#   "i need the exe to auto setup when i place on leos computer and all you
#    need is the exe and the sinsiter sanctum folder. when its doing setup it
#    also needs to first thing spawn a Sinister Setup Wizard agent that is
#    prompted with the task of making sure leo gets setup."
#
# Spawns a real Claude agent in a mintty window with a primer prompt that
# turns it into the "Sinister Setup Wizard" -- holds Leo's hand through the
# Anthropic OAuth login, vault join, branch creation, env verification, and
# smoke test. Re-uses the same mintty + bash + claude --dangerously-skip-permissions
# spawn convention as start-sinister-session.ps1.
#
# Reuses primitives:
#   - eve-bulk-oauth-login.ps1 (for the isolated OAuth sandbox if needed)
#   - claude-oauth-accounts.ps1 (per-slot account management)
#   - eve-first-run-check.ps1 (the gating detector)
#
# Usage:
#   powershell -File spawn-setup-wizard.ps1               (spawn the wizard)
#   powershell -File spawn-setup-wizard.ps1 -DryRun       (print what we WOULD do)
#   powershell -File spawn-setup-wizard.ps1 -NoLogin      (skip OAuth pre-check)
#   powershell -File spawn-setup-wizard.ps1 -OperatorName Leo  (override greet)

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$NoLogin,
    [string]$OperatorName = '',
    [string]$SanctumRoot = ''
)

$ErrorActionPreference = 'Continue'

if (-not $SanctumRoot) {
    $SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
}
if (-not (Test-Path $SanctumRoot)) {
    Write-Host "  [FAIL] Sanctum root not found: $SanctumRoot" -ForegroundColor Red
    exit 2
}

# Resolve operator name from git or env
if (-not $OperatorName) {
    try {
        $g = (& git -C $SanctumRoot config --get user.name 2>$null) | Select-Object -First 1
        if ($g) { $OperatorName = $g.Trim() }
    } catch {}
    if (-not $OperatorName) { $OperatorName = $env:USERNAME }
    if (-not $OperatorName) { $OperatorName = 'operator' }
}

# --- Detect claude CLI -----------------------------------------------------

function Get-ClaudeCli {
    $c = Get-Command claude.exe -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $c = Get-Command claude -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    return $null
}

$claudeCli = Get-ClaudeCli
if (-not $claudeCli) {
    Write-Host '' -NoNewline
    Write-Host '  [HALT] claude CLI not on PATH.' -ForegroundColor Red
    Write-Host '  Install: 1) install Node.js (https://nodejs.org)' -ForegroundColor Yellow
    Write-Host '           2) npm i -g @anthropic-ai/claude-code' -ForegroundColor Yellow
    Write-Host '           3) re-run this script after re-opening PowerShell so PATH refreshes' -ForegroundColor Yellow
    if (-not $DryRun) { exit 3 }
    Write-Host '  [DRY-RUN] would HALT; continuing for dry-run report' -ForegroundColor DarkCyan
}

# --- Detect OAuth state ----------------------------------------------------

$credsPath = Join-Path $env:USERPROFILE '.claude\.credentials.json'
$claudeConfig = Join-Path $env:USERPROFILE '.claude.json'
$hasOAuth = (Test-Path $credsPath) -or (Test-Path $claudeConfig)
$hasApiKey = -not [string]::IsNullOrWhiteSpace($env:ANTHROPIC_API_KEY)

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   SINISTER SETUP WIZARD :: SPAWN' -ForegroundColor White
Write-Host ('   Operator: ' + $OperatorName + ' @ ' + $env:COMPUTERNAME) -ForegroundColor Gray
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''
Write-Host ('  claude CLI         : ' + ($(if ($claudeCli) { $claudeCli } else { 'MISSING' }))) -ForegroundColor Gray
Write-Host ('  OAuth credentials  : ' + ($(if ($hasOAuth) { 'present' } else { 'missing' }))) -ForegroundColor Gray
Write-Host ('  ANTHROPIC_API_KEY  : ' + ($(if ($hasApiKey) { 'set' } else { 'not set' }))) -ForegroundColor Gray
Write-Host ''

# --- Pre-run OAuth login if no auth at all (unless -NoLogin) ---------------

if (-not $hasOAuth -and -not $hasApiKey -and -not $NoLogin -and $claudeCli) {
    # RKOJ-ELENO :: 2026-05-25 :: P0 fix -- `claude login` was renamed to
    # `claude auth login`. Probe which subcommand the installed claude binary
    # supports, then call the right form. Operator screenshot 2026-05-25
    # ~01:50Z: "login didnt work fix this shits".
    $useAuthLogin = $false
    try {
        & $claudeCli auth --help *> $null
        $useAuthLogin = ($LASTEXITCODE -eq 0)
    } catch { $useAuthLogin = $false }
    $loginVerb = if ($useAuthLogin) { 'auth login' } else { 'login' }
    Write-Host ('  [pre-step] No auth detected. Running `claude ' + $loginVerb + '` interactively.') -ForegroundColor Yellow
    Write-Host '  (a browser tab will open for Anthropic OAuth; complete it then return here)' -ForegroundColor Gray
    Write-Host ''
    if ($DryRun) {
        Write-Host ('  [DRY-RUN] would run: claude ' + $loginVerb) -ForegroundColor DarkCyan
    } else {
        try {
            if ($useAuthLogin) { & $claudeCli auth login } else { & $claudeCli login }
            $hasOAuth = (Test-Path $credsPath) -or (Test-Path $claudeConfig)
        } catch {
            Write-Host ('  [warn] claude ' + $loginVerb + ' threw: ' + $_.Exception.Message) -ForegroundColor Yellow
        }
    }
}

# --- Construct the Wizard primer prompt ------------------------------------
# Keep this short + natural; long binding language trips Claude's first-turn
# classifier (same lesson as start-sinister-session.ps1 Build-Phrase comment).

$wizardPrompt = @"
You are the Sinister Setup Wizard. Your task is to onboard $OperatorName to the Sinister Sanctum fleet. Read $SanctumRoot\docs\LEO-SETUP.md and $SanctumRoot\docs\LEO-VAULT-SETUP.md first so you know the full bring-up surface. Then walk $OperatorName through this checklist one item per turn, asking confirmation at each gate:

  1) Verify Anthropic OAuth login is working (claude CLI logged in). If not, run `claude login`.
  2) Run automations\eve-first-run-check.ps1 -Format text and surface every remaining FAIL/WARN.
  3) Set git config --global user.name='$OperatorName' and ask for their git user.email, set it globally.
  4) Create their working branch agent/$($OperatorName.ToLower())/onboard-bring-up.
  5) Confirm Docker Desktop is installed AND running (whale icon in tray). If installed but not running, offer to start it via `Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'`. If not installed, point at `winget install Docker.DockerDesktop`.
  6) Pull operator-standard Docker images by running `automations\install-leo-bots.ps1` (NO -DryRun for the real install). Verify with `docker ps -a` and `docker images | grep ollama`.
  7) Seed MCP config: if ~/.claude/.mcp.json missing, copy automations\templates\leo-mcp-config.json there (substituting `${SINISTER_SANCTUM_ROOT}` with $SanctumRoot). Then run `claude mcp list` and confirm 10+ servers Connected. Tell $OperatorName: restart Claude Code to load new MCP servers.
  8) Install all scheduled tasks via `automations\install-leo-scheduled-tasks.ps1` (operator-confirm each). Then verify with `schtasks /Query /TN SinisterSanctumAutoPush` etc.
  9) Confirm autonomy grant active: run `automations\grant-claude-autonomy.ps1 -ReadOnly` and confirm Step 6/7/8 all OK + bypassPermissions=true in ~/.claude/settings.json.
 10) Offer Tailscale install + vault join (point at docs\LEO-VAULT-SETUP.md). Optional; ok to defer.
 11) Smoke test: spawn a tiny shell command (e.g. printf 'hello') and verify it runs.
 12) Create $OperatorName's first heartbeat at _shared-memory\heartbeats\$($OperatorName.ToLower()).json with agent='$OperatorName' + ts_utc + status='onboarding'.
 13) Append a 5-line onboarding report to _shared-memory\setup\$($OperatorName.ToLower())-onboarding-report-<utc>.md (create if missing) summarising what worked + what is pending.

Loop policy: loop=on. Ship one checklist item per turn; do not delete or kill anything without explicit '$OperatorName' confirmation; ask for permission before any write outside _shared-memory\setup\ and _shared-memory\heartbeats\. When all items are DONE, write a final 'BRING-UP COMPLETE' summary and end the turn cleanly. If $OperatorName asks to abort at any point, write whatever was completed to the onboarding report and exit gracefully.
"@

$wizardPrompt = $wizardPrompt -replace "`r`n", ' '
$wizardPrompt = $wizardPrompt -replace "  +", ' '

# --- Construct the launch script -------------------------------------------

# Convert Windows path D:\foo\bar to bash /d/foo/bar (PS 5.1 doesn't support scriptblock substitution in -replace, so use manual concat).
$bashSanctumRoot = if ($SanctumRoot -match '^([A-Za-z]):(.*)$') {
    '/' + $Matches[1].ToLower() + ($Matches[2] -replace '\\', '/')
} else {
    $SanctumRoot -replace '\\', '/'
}
$launchDir = Join-Path $SanctumRoot '_shared-memory\setup'
if (-not (Test-Path $launchDir)) { New-Item -ItemType Directory -Path $launchDir -Force | Out-Null }
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$launchSh = Join-Path $launchDir ("wizard-spawn-$ts.sh")

# Escape single quotes in prompt for bash single-quoted heredoc
$bashPrompt = $wizardPrompt -replace "'", "'\''"

$launchContent = @"
#!/usr/bin/env bash
export PATH="/usr/bin:/bin:/usr/local/bin:`$PATH"
cd "$bashSanctumRoot" || { echo '[FAIL] could not cd to sanctum root'; read _; exit 1; }
printf '\n'
printf '  ============================================================\n'
printf '  Sinister Setup Wizard -- onboarding %s\n' "$OperatorName"
printf '  ============================================================\n'
printf '\n'
printf '  Spawning Claude with --dangerously-skip-permissions...\n'
printf '\n'
claude --dangerously-skip-permissions '$bashPrompt'
ec=`$?
printf '\n'
if [ `$ec -eq 0 ]; then
    printf '[OK] wizard session ended cleanly.\n'
else
    printf '[INFO] wizard exited with code %s.\n' "`$ec"
fi
printf 'Press Enter to close this window.\n'
read _
"@

$launchContent = $launchContent -replace "`r`n", "`n"

if ($DryRun) {
    Write-Host '  [DRY-RUN] Wizard primer prompt (first 240 chars):' -ForegroundColor DarkCyan
    Write-Host ('    ' + $wizardPrompt.Substring(0, [Math]::Min(240, $wizardPrompt.Length)) + '...') -ForegroundColor Gray
    Write-Host ''
    Write-Host '  [DRY-RUN] Would write launch script to:' -ForegroundColor DarkCyan
    Write-Host ('    ' + $launchSh) -ForegroundColor Gray
    Write-Host '  [DRY-RUN] Would spawn mintty with:' -ForegroundColor DarkCyan
    Write-Host ('    mintty --hold error -t "Sinister Setup Wizard -- ' + $OperatorName + '" -- /bin/bash <launch.sh>') -ForegroundColor Gray
    Write-Host ''
    Write-Host '  [DRY-RUN] Skipping actual spawn.' -ForegroundColor DarkCyan
    exit 0
}

[System.IO.File]::WriteAllText($launchSh, $launchContent, [System.Text.UTF8Encoding]::new($false))
$launchShBash = if ($launchSh -match '^([A-Za-z]):(.*)$') {
    '/' + $Matches[1].ToLower() + ($Matches[2] -replace '\\', '/')
} else {
    $launchSh -replace '\\', '/'
}

# --- Spawn the mintty window ----------------------------------------------

$minttyExe = 'C:\Program Files\Git\usr\bin\mintty.exe'
$gitBash   = 'C:\Program Files\Git\git-bash.exe'
$bashExe   = 'C:\Program Files\Git\bin\bash.exe'

$spawned = $null
$windowTitle = "Sinister Setup Wizard -- $OperatorName"

try {
    if (Test-Path $minttyExe) {
        $minttyArgs = @(
            '--hold', 'error',
            '-t', $windowTitle,
            '-o', 'ForegroundColour=200,132,252',   # Sinister purple foreground
            '-o', 'BackgroundColour=14,12,20',      # dark background
            '-o', 'CursorColour=200,132,252',
            '-o', 'FontSize=12',
            '-o', 'Term=xterm-256color',
            '-o', 'Transparency=off',
            '-o', 'OpaqueWhenFocused=yes',
            '--', '/bin/bash', $launchShBash
        )
        $spawned = Start-Process -FilePath $minttyExe -ArgumentList $minttyArgs -PassThru -ErrorAction Stop
    } elseif (Test-Path $gitBash) {
        $spawned = Start-Process -FilePath $gitBash -ArgumentList @($launchShBash) -PassThru -ErrorAction Stop
    } elseif (Test-Path $bashExe) {
        $spawned = Start-Process -FilePath $bashExe -ArgumentList @('-l', '-i', $launchShBash) -PassThru -ErrorAction Stop
    } else {
        Write-Host '  [FAIL] No mintty / git-bash / bash found. Install Git for Windows.' -ForegroundColor Red
        exit 4
    }
} catch {
    Write-Host ('  [FAIL] mintty spawn threw: ' + $_.Exception.Message) -ForegroundColor Red
    exit 5
}

Write-Host ('  [OK] Sinister Setup Wizard spawned (pid=' + $spawned.Id + ')') -ForegroundColor Green
Write-Host ('  Window title: ' + $windowTitle) -ForegroundColor Gray
Write-Host ('  Launch script: ' + $launchSh) -ForegroundColor DarkGray
Write-Host ''

# --- Log the spawn to spawned-windows.jsonl (same convention as launcher) --

try {
    $swPath = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'
    $swDir = Split-Path $swPath
    if (-not (Test-Path $swDir)) { New-Item -ItemType Directory -Path $swDir -Force | Out-Null }
    $swRec = [pscustomobject]@{
        pid             = $spawned.Id
        agent           = 'Sinister Setup Wizard'
        project         = 'general'
        project_display = 'Setup Wizard (Leo bring-up)'
        mode            = 'setup-wizard'
        accent          = 'purple'
        started         = (Get-Date).ToString('o')
        launcher_pid    = $PID
        operator_name   = $OperatorName
    }
    $swLockFile = Join-Path $swDir '.spawned-windows.lock'
    $swLockLine = ($swRec | ConvertTo-Json -Compress)
    $swLocked = $false
    for ($t = 0; $t -lt 40; $t++) {
        try {
            $swFs = [System.IO.File]::Open($swLockFile, 'CreateNew', 'Write', 'None')
            $swFs.Close()
            $swLocked = $true
            break
        } catch {
            try {
                if (Test-Path $swLockFile) {
                    $age = ((Get-Date) - (Get-Item $swLockFile).LastWriteTime).TotalSeconds
                    if ($age -gt 10) { Remove-Item $swLockFile -Force -ErrorAction SilentlyContinue }
                }
            } catch {}
            Start-Sleep -Milliseconds 100
        }
    }
    try {
        Add-Content -Path $swPath -Value $swLockLine -Encoding UTF8
    } finally {
        if ($swLocked) { try { Remove-Item $swLockFile -Force -ErrorAction SilentlyContinue } catch {} }
    }
} catch {
    Write-Host ('  [warn] spawned-windows.jsonl log failed: ' + $_.Exception.Message) -ForegroundColor DarkYellow
}

# --- Log to setup log too --------------------------------------------------

try {
    $setupLog = Join-Path $launchDir ('wizard-spawns-' + (Get-Date).ToUniversalTime().ToString('yyyyMMdd') + '.log')
    $logLine = ((Get-Date).ToString('o') + ' :: spawn :: pid=' + $spawned.Id + ' operator=' + $OperatorName + ' launch=' + $launchSh)
    Add-Content -Path $setupLog -Value $logLine -Encoding UTF8
} catch {}

exit 0
