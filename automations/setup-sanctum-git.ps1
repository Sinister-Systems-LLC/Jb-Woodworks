# setup-sanctum-git.ps1 - first-run bootstrap for the sanctum-git Gitea stack
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
#
# Flow:
#   1. Verify Docker Desktop is running (docker info).
#   2. cd into D:\Sinister Sanctum\tools\sanctum-git\.
#   3. docker compose up -d.
#   4. Poll http://localhost:3000/api/v1/version until it answers (max 90 s).
#   5. Print next-steps (open the wizard, complete install, then git-mirror init).
#   6. Auto-close in 6 s on success; pause on failure so operator can read errors.

[CmdletBinding()]
param(
    [switch]$NoAutoClose
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Sanctum Git :: Setup'

# Purple-branded header (matches launcher / capture-invention palette).
$Purple = 'DarkMagenta'
$LightP = 'Magenta'
$White  = 'White'
$Glow   = 'Green'
$Warn   = 'Yellow'
$Red    = 'Red'
$Dim    = 'DarkGray'

function Say($text, $color = $White) { Write-Host $text -ForegroundColor $color }

Write-Host ''
Write-Host '  ============================================================' -ForegroundColor $Purple
Write-Host '   S A N C T U M   G I T   ::   S E T U P' -ForegroundColor $LightP
Write-Host '   Self-hosted Gitea on localhost:3000' -ForegroundColor $White
Write-Host '  ============================================================' -ForegroundColor $Purple
Write-Host ''

$ToolDir = 'D:\Sinister Sanctum\tools\sanctum-git'
$ComposeFile = Join-Path $ToolDir 'docker-compose.yml'

# -------- Step 1: verify tool dir + compose file --------
Write-Host '[SETUP] Verifying tool directory...' -ForegroundColor $LightP
if (-not (Test-Path $ToolDir)) {
    Write-Host "[FAIL] tool dir missing: $ToolDir" -ForegroundColor $Red
    Read-Host 'Press Enter to close'
    exit 1
}
if (-not (Test-Path $ComposeFile)) {
    Write-Host "[FAIL] docker-compose.yml missing: $ComposeFile" -ForegroundColor $Red
    Read-Host 'Press Enter to close'
    exit 2
}
Write-Host "[OK]    $ToolDir" -ForegroundColor $Glow

# -------- Step 2: verify Docker Desktop --------
Write-Host ''
Write-Host '[SETUP] Verifying Docker Desktop is running...' -ForegroundColor $LightP
$null = & docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host '[FAIL] docker info returned non-zero — is Docker Desktop running?' -ForegroundColor $Red
    Write-Host '       Open Docker Desktop (whale icon in tray) and wait for' -ForegroundColor $Dim
    Write-Host '       "Docker Desktop is running" before re-running this script.' -ForegroundColor $Dim
    Read-Host 'Press Enter to close'
    exit 3
}
Write-Host '[OK]    Docker Desktop is running' -ForegroundColor $Glow

# -------- Step 3: docker compose up -d --------
Write-Host ''
Write-Host '[SETUP] Starting the Gitea container (docker compose up -d)...' -ForegroundColor $LightP
Push-Location $ToolDir
try {
    & docker compose up -d 2>&1 | ForEach-Object { Write-Host "        $_" -ForegroundColor $Dim }
    if ($LASTEXITCODE -ne 0) {
        Write-Host '[FAIL] docker compose up -d returned non-zero' -ForegroundColor $Red
        Pop-Location
        Read-Host 'Press Enter to close'
        exit 4
    }
}
finally {
    Pop-Location
}
Write-Host '[OK]    container started' -ForegroundColor $Glow

# -------- Step 4: poll the API until ready (max 90 s) --------
Write-Host ''
Write-Host '[SETUP] Waiting for Gitea API at http://localhost:3000/api/v1/version ...' -ForegroundColor $LightP
$deadline = (Get-Date).AddSeconds(90)
$ready = $false
$lastErr = ''
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri 'http://localhost:3000/api/v1/version' -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($resp.StatusCode -eq 200) {
            $ready = $true
            Write-Host "[OK]    Gitea responded: $($resp.Content)" -ForegroundColor $Glow
            break
        }
    }
    catch {
        $lastErr = $_.Exception.Message
        Start-Sleep -Seconds 2
        Write-Host '        ... still waiting' -ForegroundColor $Dim
    }
}
if (-not $ready) {
    Write-Host "[FAIL] Gitea did not answer within 90 s. Last error: $lastErr" -ForegroundColor $Red
    Write-Host '       Check `docker compose logs gitea` from the tool folder.' -ForegroundColor $Dim
    Read-Host 'Press Enter to close'
    exit 5
}

# -------- Step 5: next steps --------
Write-Host ''
Write-Host '  ============================================================' -ForegroundColor $Purple
Write-Host '   N E X T   S T E P S' -ForegroundColor $LightP
Write-Host '  ============================================================' -ForegroundColor $Purple
Say '   1. Open http://localhost:3000 in your browser.' $White
Say '   2. Complete the install wizard. Defaults are fine —' $White
Say '      SQLite, domain localhost, port 3000.' $Dim
Say '   3. Create your first user — CHECK "Set as administrator".' $White
Say '      Username: operator     Email: andrew.viperrr@gmail.com' $Dim
Say '   4. Copy tools\sanctum-git\.env.example to .env and fill in' $White
Say '      GITEA_ADMIN_PASSWORD (and GITEA_SECRET_KEY if shown).' $Dim
Say '   5. Mirror existing projects:' $White
Say '         Mirror-To-Sanctum-Git.bat   (interactive)' $LightP
Say '      or  git-mirror.ps1 -Cmd push-all' $LightP
Write-Host ''

if ($NoAutoClose) {
    Read-Host 'Press Enter to close'
} else {
    Write-Host '  Window auto-closes in 6 seconds.' -ForegroundColor $Dim
    Start-Sleep -Seconds 6
}
exit 0
