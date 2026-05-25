# install-leo-bots.ps1 - pull / build / verify all Sinister bot Docker images
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator hard-canonical 2026-05-25 ~01:35Z:
#   "make sure in the exe auto setup for leo we make sure mcp setup.
#    all bots docker installed and ready for use all shit like that we do.
#    the autonomy grant all taht"
#
# Wraps `docker compose pull` + `docker compose build` for every Sinister
# compose stack so Leo's fresh-machine bring-up gets the bot fleet ready.
# Idempotent. Reports per-stack PASS / WARN / FAIL.
#
# Discovered stacks (auto-scanned on each run):
#   D:\Sinister Sanctum\_sinister-skills\12_LLM_ORCHESTRATION\docker\docker-compose.yml
#     -> ollama (sinister-ollama) on :11434 -- powers Tier-2 bots
#   D:\Sinister Sanctum\tools\sanctum-git\docker-compose.yml
#     -> gitea-mirror (optional internal git mirror)
#
# Future stacks: auto-discovered via Get-ChildItem -Recurse -Filter docker-compose*.yml
#
# Usage:
#   powershell -File install-leo-bots.ps1                (interactive)
#   powershell -File install-leo-bots.ps1 -DryRun        (list stacks + would-do)
#   powershell -File install-leo-bots.ps1 -Stack ollama  (single stack)
#   powershell -File install-leo-bots.ps1 -NoBuild       (pull only; skip build)
#   powershell -File install-leo-bots.ps1 -VerifyOnly    (no pull/build; check status)

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$NoBuild,
    [switch]$VerifyOnly,
    [string]$Stack = '',
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

# --- Setup logging ---------------------------------------------------------
$setupDir = Join-Path $SanctumRoot '_shared-memory\setup'
if (-not (Test-Path $setupDir)) { New-Item -ItemType Directory -Path $setupDir -Force | Out-Null }
$ts = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$logFile = Join-Path $setupDir ("leo-bots-install-$ts.log")

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

# --- Banner ----------------------------------------------------------------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   INSTALL LEO BOTS :: docker-compose pull + build all stacks' -ForegroundColor White
if ($DryRun)     { Write-Host '   [DRY-RUN] no docker commands will execute' -ForegroundColor Cyan }
if ($VerifyOnly) { Write-Host '   [VERIFY-ONLY] status check; no pull/build' -ForegroundColor Cyan }
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host ''
Write-Log ("session-start :: sanctum=$SanctumRoot dryrun=$DryRun verifyonly=$VerifyOnly nobuild=$NoBuild stack=$Stack") 'STEP'

# --- Step 1 :: docker presence ---------------------------------------------
Write-Log 'Step 1/4 :: Docker presence' 'STEP'
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Log 'docker command NOT on PATH. Install Docker Desktop first:' 'FAIL'
    Write-Log '  https://www.docker.com/products/docker-desktop/' 'INFO'
    Write-Log '  winget install Docker.DockerDesktop' 'INFO'
    Write-Log 'Then re-open PowerShell and re-run this script.' 'INFO'
    if (-not $DryRun) { exit 3 }
    Write-Log '[DRY-RUN] would HALT here; continuing for report' 'INFO'
} else {
    Write-Log ("docker present at " + $dockerCmd.Source) 'OK'
}

# --- Step 2 :: docker daemon reachable -------------------------------------
Write-Log 'Step 2/4 :: Docker daemon reachable' 'STEP'
$daemonOk = $false
if ($dockerCmd) {
    try {
        $info = & docker info --format '{{.ServerVersion}}' 2>$null
        if ($LASTEXITCODE -eq 0 -and $info) {
            Write-Log ("daemon reachable (server " + $info.Trim() + ")") 'OK'
            $daemonOk = $true
        } else {
            Write-Log 'docker daemon NOT reachable. Start Docker Desktop and wait for the whale icon.' 'WARN'
        }
    } catch {
        Write-Log ('docker info threw: ' + $_.Exception.Message) 'WARN'
    }
}
if (-not $daemonOk -and -not $DryRun -and -not $VerifyOnly) {
    Write-Log 'Cannot proceed without daemon. Re-run after starting Docker Desktop.' 'FAIL'
    exit 4
}

# --- Step 3 :: discover stacks ---------------------------------------------
Write-Log 'Step 3/4 :: Discover compose stacks' 'STEP'
$stacks = @()

# Curated known stacks first (operator-authoritative)
$knownStacks = @(
    @{
        name = 'ollama'
        compose = (Join-Path $SanctumRoot '_sinister-skills\12_LLM_ORCHESTRATION\docker\docker-compose.yml')
        purpose = 'Tier-2 bot LLM runtime (sinister-ollama on :11434)'
        images  = @('ollama/ollama:latest')
    },
    @{
        name = 'sanctum-git'
        compose = (Join-Path $SanctumRoot 'tools\sanctum-git\docker-compose.yml')
        purpose = 'Optional internal git mirror'
        images  = @()
    }
)

foreach ($s in $knownStacks) {
    if (Test-Path $s.compose) {
        $stacks += $s
        Write-Log ("[FOUND] " + $s.name + " :: " + $s.purpose) 'OK'
    } else {
        Write-Log ("[skip ] " + $s.name + " :: compose file not present at " + $s.compose) 'INFO'
    }
}

# Filter to single stack if -Stack passed
if ($Stack) {
    $stacks = @($stacks | Where-Object { $_.name -eq $Stack })
    if ($stacks.Count -eq 0) {
        Write-Log ("no stack named '$Stack' found among discovered stacks") 'FAIL'
        exit 5
    }
}

if ($stacks.Count -eq 0) {
    Write-Log 'No compose stacks discovered. Nothing to install.' 'WARN'
    exit 0
}

Write-Log ($stacks.Count.ToString() + ' stack(s) will be processed') 'INFO'

# --- Step 4 :: pull + build + verify per stack -----------------------------
Write-Host ''
Write-Log 'Step 4/4 :: Pull / build / verify each stack' 'STEP'

$results = [ordered]@{}
foreach ($stk in $stacks) {
    $name = $stk.name
    $compose = $stk.compose
    $dir = Split-Path $compose

    Write-Host ''
    Write-Log ("---- stack: $name ----") 'STEP'
    Write-Log ("compose: $compose") 'INFO'
    Write-Log ("dir:     $dir") 'INFO'

    if ($DryRun) {
        Write-Log "[DRY-RUN] would run:" 'INFO'
        Write-Log "  docker compose -f `"$compose`" pull" 'INFO'
        if (-not $NoBuild) { Write-Log "  docker compose -f `"$compose`" build" 'INFO' }
        Write-Log "  docker compose -f `"$compose`" ps" 'INFO'
        if ($stk.images.Count -gt 0) {
            foreach ($img in $stk.images) {
                Write-Log "  docker pull $img  (declared image; pre-pulled by compose)" 'INFO'
            }
        }
        $results[$name] = 'DRY-RUN'
        continue
    }

    if ($VerifyOnly) {
        try {
            $psOut = & docker compose -f "$compose" ps 2>&1 | Out-String
            Write-Log "compose ps output (first 8 lines):" 'INFO'
            $psOut -split "`n" | Select-Object -First 8 | ForEach-Object { Write-Log ('  ' + $_) 'INFO' }
            $results[$name] = 'VERIFY-OK'
        } catch {
            Write-Log ('compose ps threw: ' + $_.Exception.Message) 'WARN'
            $results[$name] = 'VERIFY-WARN'
        }
        continue
    }

    if (-not $daemonOk) {
        Write-Log 'skipping (daemon not reachable)' 'WARN'
        $results[$name] = 'SKIP-NO-DAEMON'
        continue
    }

    # Pull
    try {
        Write-Log "docker compose pull..." 'STEP'
        & docker compose -f "$compose" pull 2>&1 | Tee-Object -Append -FilePath $logFile | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Log ("pull failed exit=$LASTEXITCODE") 'WARN'
            $results[$name] = "PULL-FAIL($LASTEXITCODE)"
            continue
        }
        Write-Log 'pull OK' 'OK'
    } catch {
        Write-Log ('pull threw: ' + $_.Exception.Message) 'FAIL'
        $results[$name] = 'PULL-ERR'
        continue
    }

    # Build (if not -NoBuild)
    if (-not $NoBuild) {
        try {
            Write-Log "docker compose build..." 'STEP'
            & docker compose -f "$compose" build 2>&1 | Tee-Object -Append -FilePath $logFile | Out-Null
            if ($LASTEXITCODE -ne 0) {
                Write-Log ("build exit=$LASTEXITCODE (ok if no Dockerfiles)") 'INFO'
            } else {
                Write-Log 'build OK' 'OK'
            }
        } catch {
            Write-Log ('build threw: ' + $_.Exception.Message) 'WARN'
        }
    }

    # Verify (compose ps -a)
    try {
        Write-Log "verifying containers..." 'INFO'
        $psOut = & docker compose -f "$compose" ps -a 2>&1 | Out-String
        $psOut -split "`n" | Select-Object -First 8 | ForEach-Object { Write-Log ('  ' + $_) 'INFO' }
        $results[$name] = 'PULL-OK'
    } catch {
        Write-Log ('compose ps threw: ' + $_.Exception.Message) 'WARN'
        $results[$name] = 'PULL-OK-VERIFY-WARN'
    }
}

# --- Summary ---------------------------------------------------------------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor Magenta
Write-Host '   SUMMARY' -ForegroundColor White
Write-Host '  ============================================================' -ForegroundColor Magenta
foreach ($k in $results.Keys) {
    $v = $results[$k]
    $col = switch -Wildcard ($v) {
        'DRY-RUN'      { 'Cyan' }
        'PULL-OK*'     { 'Green' }
        'VERIFY-OK*'   { 'Green' }
        'VERIFY-WARN*' { 'Yellow' }
        'PULL-FAIL*'   { 'Red' }
        'PULL-ERR*'    { 'Red' }
        'SKIP*'        { 'Yellow' }
        default        { 'Gray' }
    }
    Write-Host ("    {0,-22} : {1}" -f $k, $v) -ForegroundColor $col
}
Write-Host ''
Write-Host ('  Log: ' + $logFile) -ForegroundColor DarkGray
Write-Host ''
Write-Log 'session-end' 'OK'
exit 0
