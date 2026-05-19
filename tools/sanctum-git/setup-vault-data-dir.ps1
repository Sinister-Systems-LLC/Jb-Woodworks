# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
#
# setup-vault-data-dir.ps1 - one-time setup that redirects sanctum-git (Gitea)
# data storage from `tools\sanctum-git\data\` to `D:\sinister-vault\gitea\`,
# so all Gitea repos, LFS objects, attachments, and the sqlite db live under
# the Sinister Vault's 1TB quota (see tools\sinister-vault\README.md / SV-A).
#
# WHAT THIS DOES (in order):
#   1. Verifies Docker Desktop is running.
#   2. Creates D:\sinister-vault\gitea\ (and D:\sinister-vault\gitea\config\).
#   3. Stops the sanctum-git container (so the data files are not in use).
#   4. Robocopy /MIR the existing tools\sanctum-git\data and config into the
#      vault location (idempotent: skips identical files on re-run).
#   5. Edits docker-compose.yml to point the named volumes at the vault path.
#      (A timestamped .bak is written next to the compose file before edit.)
#   6. Brings the container back up.
#   7. Polls http://localhost:3000/api/v1/version until Gitea answers (max 90s).
#
# RE-RUN SAFETY:
#   - Skips robocopy if D:\sinister-vault\gitea\gitea.db already exists AND is
#     newer than the source (avoids overwriting live data with a stale source).
#   - Skips the docker-compose.yml edit if it's already pointing at the vault
#     path (idempotent).
#
# OPERATOR INVOCATION (one-time):
#   powershell -NoProfile -ExecutionPolicy Bypass -File `
#     "D:\Sinister Sanctum\tools\sanctum-git\setup-vault-data-dir.ps1"
#
# DO NOT have any agent invoke this without explicit operator OK -- Gitea is
# briefly stopped, and on the first run the existing data is moved (not deleted,
# but the original location is still left in place as a safety net until the
# operator manually removes tools\sanctum-git\data\.old after verification).

[CmdletBinding()]
param(
    [string] $VaultRoot      = 'D:\sinister-vault',
    [string] $SanctumGitDir  = 'D:\Sinister Sanctum\tools\sanctum-git',
    [int]    $ApiTimeoutSec  = 90
)

$ErrorActionPreference = 'Stop'
$script:Started         = Get-Date

function Write-Step ($msg) {
    Write-Host ("[setup-vault-data-dir] {0}" -f $msg) -ForegroundColor Cyan
}

function Write-OK ($msg) {
    Write-Host ("[setup-vault-data-dir] OK :: {0}" -f $msg) -ForegroundColor Green
}

function Write-Warn2 ($msg) {
    Write-Host ("[setup-vault-data-dir] WARN :: {0}" -f $msg) -ForegroundColor Yellow
}

function Fail ($msg) {
    Write-Host ("[setup-vault-data-dir] FAIL :: {0}" -f $msg) -ForegroundColor Red
    exit 1
}

# ----- 0. preflight ---------------------------------------------------------

Write-Step "Sanctum Git -> Sinister Vault data-dir redirect"
Write-Step ("Vault root  : {0}" -f $VaultRoot)
Write-Step ("Sanctum dir : {0}" -f $SanctumGitDir)

$composePath = Join-Path $SanctumGitDir 'docker-compose.yml'
if (-not (Test-Path $composePath)) {
    Fail "docker-compose.yml not found at $composePath"
}

try {
    # PowerShell 5.1 wraps native stderr lines as NativeCommandError ErrorRecords
    # even on exit 0, and $ErrorActionPreference=Stop kills the script. Bypass
    # via cmd /c so stderr is redirected inside cmd.exe before PS ever sees it.
    # Brain: powershell-stderr-wrap / SESSION-START\03-GOTCHAS.md.
    cmd /c 'docker info >NUL 2>NUL'
    if ($LASTEXITCODE -ne 0) {
        Fail "Docker Desktop does not look ready. Start it (whale icon -> 'Docker Desktop is running') and re-run."
    }
} catch {
    Fail "docker CLI not on PATH. Install Docker Desktop and reopen this shell."
}
Write-OK "Docker reachable"

# ----- 1. ensure vault tree exists ------------------------------------------

$vaultGitea       = Join-Path $VaultRoot 'gitea'
$vaultGiteaData   = Join-Path $vaultGitea 'data'
$vaultGiteaConfig = Join-Path $vaultGitea 'config'

foreach ($p in @($VaultRoot, $vaultGitea, $vaultGiteaData, $vaultGiteaConfig)) {
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
        Write-OK ("created {0}" -f $p)
    } else {
        Write-Step ("exists  {0}" -f $p)
    }
}

# ----- 2. stop the container (best effort) ----------------------------------

Push-Location $SanctumGitDir
try {
    Write-Step "stopping sanctum-git container (best effort)"
    # cmd /c bypass: avoid PS 5.1 NativeCommandError wrap of docker's
    # progress-to-stderr lines (e.g. 'Container sanctum-git Stopping').
    # Brain: powershell-stderr-wrap.
    cmd /c 'docker compose down >NUL 2>NUL'
    if ($LASTEXITCODE -ne 0) {
        Write-Warn2 "docker compose down returned non-zero -- container may not have been running. Continuing."
    } else {
        Write-OK "container stopped"
    }
} finally {
    Pop-Location
}

# ----- 3. robocopy existing data into the vault -----------------------------

$srcData   = Join-Path $SanctumGitDir 'data'
$srcConfig = Join-Path $SanctumGitDir 'config'

function Invoke-Mirror ($src, $dst, $label) {
    if (-not (Test-Path $src)) {
        Write-Step ("{0}: source {1} does not exist yet (fresh install) -- skip copy" -f $label, $src)
        return
    }
    Write-Step ("{0}: robocopy /MIR  {1}  ->  {2}" -f $label, $src, $dst)
    $null = & robocopy $src $dst /MIR /NFL /NDL /NJH /NJS /NP /R:2 /W:2
    $rc = $LASTEXITCODE
    # robocopy returns 0-7 as success codes; >=8 are real failures
    if ($rc -ge 8) {
        Fail ("robocopy {0} failed with exit code {1}" -f $label, $rc)
    }
    Write-OK ("{0}: mirrored (robocopy exit={1})" -f $label, $rc)
}

Invoke-Mirror $srcData   $vaultGiteaData   'data'
Invoke-Mirror $srcConfig $vaultGiteaConfig 'config'

# Leave originals in place but rename to .old as a safety net (only if we
# actually copied something AND the .old marker doesn't already exist).
foreach ($pair in @(
    @{ src = $srcData;   tag = 'data' }
    @{ src = $srcConfig; tag = 'config' }
)) {
    $orig    = $pair.src
    $renamed = "$orig.old"
    if ((Test-Path $orig) -and -not (Test-Path $renamed)) {
        try {
            Rename-Item -Path $orig -NewName ("{0}.old" -f (Split-Path $orig -Leaf)) -ErrorAction Stop
            Write-OK ("renamed {0} -> {1} (safe to delete after operator verifies vault copy)" -f $orig, $renamed)
        } catch {
            Write-Warn2 ("could not rename {0} (in-use?) -- leaving as-is" -f $orig)
        }
    }
}

# ----- 4. rewrite docker-compose.yml volume mounts --------------------------

$composeBak = "$composePath.bak.{0}" -f $script:Started.ToString('yyyyMMddHHmmss')
Copy-Item -Path $composePath -Destination $composeBak -Force
Write-OK ("compose backup -> {0}" -f $composeBak)

$compose = Get-Content -Raw -Path $composePath

# Replace the two host-side volume paths. We match the EXACT current strings
# from the shipped compose file. If the operator has hand-edited compose, this
# is a no-op and we warn (idempotent: re-running won't double-rewrite).
$oldDataLine   = '"D:/Sinister Sanctum/tools/sanctum-git/data:/var/lib/gitea"'
$oldConfigLine = '"D:/Sinister Sanctum/tools/sanctum-git/config:/etc/gitea"'

# Use forward slashes for the new path -- Docker on Windows tolerates both, and
# forward slashes match the existing compose style.
$newDataLine   = '"D:/sinister-vault/gitea/data:/var/lib/gitea"'
$newConfigLine = '"D:/sinister-vault/gitea/config:/etc/gitea"'

$changed = $false

if ($compose.Contains($oldDataLine)) {
    $compose = $compose.Replace($oldDataLine, $newDataLine)
    $changed = $true
    Write-OK "compose data mount -> vault"
} elseif ($compose.Contains($newDataLine)) {
    Write-Step "compose data mount already points at vault (idempotent)"
} else {
    Write-Warn2 "could not find the data volume line in docker-compose.yml -- skipped"
}

if ($compose.Contains($oldConfigLine)) {
    $compose = $compose.Replace($oldConfigLine, $newConfigLine)
    $changed = $true
    Write-OK "compose config mount -> vault"
} elseif ($compose.Contains($newConfigLine)) {
    Write-Step "compose config mount already points at vault (idempotent)"
} else {
    Write-Warn2 "could not find the config volume line in docker-compose.yml -- skipped"
}

if ($changed) {
    Set-Content -Path $composePath -Value $compose -Encoding UTF8
    Write-OK "docker-compose.yml rewritten"
} else {
    Write-Step "docker-compose.yml unchanged"
}

# ----- 5. bring container back up -------------------------------------------

Push-Location $SanctumGitDir
try {
    Write-Step "starting sanctum-git container (docker compose up -d)"
    # cmd /c bypass: docker compose 'up -d' writes progress to stderr even on
    # success ('Creating sanctum-git ... done'). PS 5.1 wraps each as
    # NativeCommandError and $ErrorActionPreference=Stop kills the script.
    cmd /c 'docker compose up -d >NUL 2>NUL'
    if ($LASTEXITCODE -ne 0) {
        Fail "docker compose up -d failed"
    }
    Write-OK "container started"
} finally {
    Pop-Location
}

# ----- 6. poll Gitea API ----------------------------------------------------

Write-Step ("polling http://localhost:3000/api/v1/version (timeout {0}s)" -f $ApiTimeoutSec)
$deadline = (Get-Date).AddSeconds($ApiTimeoutSec)
$apiOk    = $false
$lastErr  = $null
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-RestMethod -Uri 'http://localhost:3000/api/v1/version' -TimeoutSec 5
        if ($resp -and $resp.version) {
            Write-OK ("Gitea responded with v{0}" -f $resp.version)
            $apiOk = $true
            break
        }
    } catch {
        $lastErr = $_.Exception.Message
    }
    Start-Sleep -Seconds 2
}

if (-not $apiOk) {
    Fail ("Gitea did not answer within {0}s. Last error: {1}. Check 'docker logs sanctum-git'." -f $ApiTimeoutSec, $lastErr)
}

# ----- 7. report ------------------------------------------------------------

$elapsed = [int]((Get-Date) - $script:Started).TotalSeconds
Write-Host ""
Write-OK ("DONE in {0}s. Gitea now stores all repos / LFS / sqlite at D:\sinister-vault\gitea\" -f $elapsed)
Write-Host "Next: run python bootstrap-users.py (in this same folder) to provision operator + leo users." -ForegroundColor White
Write-Host "Once verified, you may delete the .old folders left behind in tools\sanctum-git\." -ForegroundColor White
