# Author: Claude (Opus 4.7) - Sinister Sanctum Vault-Sync Agent
# Purpose: One-shot installer for Syncthing + NSSM as a Windows service.
# Run: powershell -ExecutionPolicy Bypass -File install.ps1
# Pre-req: Run as Administrator (NSSM service registration + firewall rules require it).

#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'

# ---------- Config ----------
$SyncthingDir    = 'C:\Program Files\Syncthing'
$NssmDir         = 'C:\Program Files\NSSM'
$SyncthingExe    = Join-Path $SyncthingDir 'syncthing.exe'
$NssmExe         = Join-Path $NssmDir 'nssm.exe'
$ServiceName     = 'Syncthing'
$VaultSyncRoot   = 'D:\sinister-vault\sync'
$ConfigDir       = Join-Path $env:LOCALAPPDATA 'Syncthing'
$ConfigTemplate  = Join-Path $PSScriptRoot 'config-template.xml'

# Syncthing release URLs (Windows x64) - resolve "latest" via GitHub API
$ReleasesApi     = 'https://api.github.com/repos/syncthing/syncthing/releases/latest'
$NssmDownload    = 'https://nssm.cc/release/nssm-2.24.zip'

function Write-Step($msg) { Write-Host "[+] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[OK] $msg"  -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[!] $msg"  -ForegroundColor Yellow }

# ---------- 1. Ensure vault sync root exists ----------
Write-Step "Ensuring vault sync root: $VaultSyncRoot"
if (-not (Test-Path $VaultSyncRoot)) {
    New-Item -ItemType Directory -Path $VaultSyncRoot -Force | Out-Null
}
Write-Ok "Vault sync root ready."

# ---------- 2. Download + extract Syncthing ----------
Write-Step "Resolving latest Syncthing release from GitHub API"
$headers = @{ 'User-Agent' = 'sinister-vault-installer'; 'Accept' = 'application/vnd.github+json' }
$release = Invoke-RestMethod -Uri $ReleasesApi -Headers $headers
$asset = $release.assets | Where-Object { $_.name -match 'syncthing-windows-amd64-.*\.zip$' } | Select-Object -First 1
if (-not $asset) { throw "Could not find Windows amd64 zip asset in latest release." }
$SyncthingZip = Join-Path $env:TEMP $asset.name
Write-Step "Downloading $($asset.name) -> $SyncthingZip"
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $SyncthingZip -Headers $headers

Write-Step "Extracting to $SyncthingDir"
if (Test-Path $SyncthingDir) { Remove-Item -Path $SyncthingDir -Recurse -Force }
$tmpExtract = Join-Path $env:TEMP 'syncthing-extract'
if (Test-Path $tmpExtract) { Remove-Item -Path $tmpExtract -Recurse -Force }
Expand-Archive -Path $SyncthingZip -DestinationPath $tmpExtract -Force
$inner = Get-ChildItem -Path $tmpExtract -Directory | Select-Object -First 1
New-Item -ItemType Directory -Path $SyncthingDir -Force | Out-Null
Copy-Item -Path (Join-Path $inner.FullName '*') -Destination $SyncthingDir -Recurse -Force
Write-Ok "Syncthing installed at $SyncthingDir"

# ---------- 3. NSSM (Windows service wrapper) ----------
if (-not (Test-Path $NssmExe)) {
    Write-Step "NSSM not found, downloading $NssmDownload"
    $NssmZip = Join-Path $env:TEMP 'nssm.zip'
    Invoke-WebRequest -Uri $NssmDownload -OutFile $NssmZip
    $tmpNssm = Join-Path $env:TEMP 'nssm-extract'
    if (Test-Path $tmpNssm) { Remove-Item -Path $tmpNssm -Recurse -Force }
    Expand-Archive -Path $NssmZip -DestinationPath $tmpNssm -Force
    $nssmInner = Get-ChildItem -Path $tmpNssm -Directory | Select-Object -First 1
    $nssmBin = Join-Path $nssmInner.FullName 'win64\nssm.exe'
    New-Item -ItemType Directory -Path $NssmDir -Force | Out-Null
    Copy-Item -Path $nssmBin -Destination $NssmExe -Force
    Write-Ok "NSSM installed at $NssmExe"
} else {
    Write-Ok "NSSM already present at $NssmExe"
}

# ---------- 4. Seed config template ----------
Write-Step "Seeding Syncthing config dir: $ConfigDir"
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}
$LiveConfig = Join-Path $ConfigDir 'config.xml'
if (-not (Test-Path $LiveConfig) -and (Test-Path $ConfigTemplate)) {
    Copy-Item -Path $ConfigTemplate -Destination $LiveConfig -Force
    Write-Ok "Seeded config.xml from template (operator must add device IDs in UI)."
} elseif (Test-Path $LiveConfig) {
    Write-Warn "config.xml already exists - leaving it alone."
} else {
    Write-Warn "Template not found; Syncthing will generate its own default on first run."
}

# ---------- 5. Register Syncthing as a Windows service via NSSM ----------
$existing = & sc.exe query $ServiceName 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Warn "Service '$ServiceName' already exists - stopping + removing first."
    & $NssmExe stop $ServiceName confirm | Out-Null
    & $NssmExe remove $ServiceName confirm | Out-Null
}
Write-Step "Registering '$ServiceName' service via NSSM"
& $NssmExe install $ServiceName $SyncthingExe '-no-browser' '-no-restart' '-home' $ConfigDir
& $NssmExe set $ServiceName Start SERVICE_AUTO_START
& $NssmExe set $ServiceName AppStdout (Join-Path $SyncthingDir 'syncthing.log')
& $NssmExe set $ServiceName AppStderr (Join-Path $SyncthingDir 'syncthing.err.log')
& $NssmExe set $ServiceName Description 'Syncthing - Sinister Vault P2P file sync'
Write-Ok "Service registered, auto-start enabled."

# ---------- 6. Firewall ----------
Write-Step "Opening Windows Firewall: TCP 22000 (sync), UDP 21027 (discovery), TCP 22000 (QUIC out)"
$rules = @(
    @{ Name = 'Syncthing-Sync-TCP-22000';      Protocol = 'TCP'; Port = 22000; Dir = 'Inbound' },
    @{ Name = 'Syncthing-Sync-UDP-22000';      Protocol = 'UDP'; Port = 22000; Dir = 'Inbound' },
    @{ Name = 'Syncthing-Discovery-UDP-21027'; Protocol = 'UDP'; Port = 21027; Dir = 'Inbound' }
)
foreach ($r in $rules) {
    Get-NetFirewallRule -DisplayName $r.Name -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $r.Name -Direction $r.Dir -Protocol $r.Protocol -LocalPort $r.Port -Action Allow -Profile Any | Out-Null
}
Write-Ok "Firewall rules in place."

# ---------- 7. Start service ----------
Write-Step "Starting '$ServiceName' service"
& $NssmExe start $ServiceName | Out-Null
Start-Sleep -Seconds 3
$status = (Get-Service -Name $ServiceName).Status
Write-Ok "Service status: $status"

# ---------- 8. Open web UI ----------
Write-Step "Opening Syncthing web UI: http://localhost:8384/"
Start-Process 'http://localhost:8384/'

# ---------- Report ----------
Write-Host ''
Write-Host '========================================================' -ForegroundColor Magenta
Write-Host ' Syncthing install complete.' -ForegroundColor Magenta
Write-Host "  - Binary:    $SyncthingExe"
Write-Host "  - Service:   $ServiceName (auto-start)"
Write-Host "  - Config:    $LiveConfig"
Write-Host "  - Sync root: $VaultSyncRoot"
Write-Host "  - Web UI:    http://localhost:8384/"
Write-Host '  - Next: see onboard-leo.md to pair Leo machine.'
Write-Host '========================================================' -ForegroundColor Magenta
