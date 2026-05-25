# Author: RKOJ-ELENO :: 2026-05-25
# sinister-link-poller.ps1 — backwards-compat shim
#
# Per operator hard-canonical 2026-05-25 (NO .bat / NO .ps1 / EXECUTE
# EVERYTHING): NEW automations are Python. Existing .ps1 files stay
# in place; this one was 0 bytes and is now a minimal shim that
# delegates to the canonical Python poller
# `automations\sinister_link_poller.py` so any pre-existing references
# (TROUBLESHOOTING.md / GETTING-STARTED.md / install-sinister-link-poller.ps1 /
# SINISTER-LINK.md) keep working without surprise.
#
# Exit code mirrors the python process's exit code.

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum'
)

$ErrorActionPreference = 'Stop'
$env:SINISTER_SANCTUM_ROOT = $SanctumRoot
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) {
    Write-Error 'python.exe not on PATH; install Python 3.10+ via deploy/setup.py'
    exit 127
}
$script = Join-Path $SanctumRoot 'automations\sinister_link_poller.py'
if (-not (Test-Path $script)) {
    Write-Error "missing $script -- re-run deploy/setup.py to restore"
    exit 126
}
& $py.Path $script
exit $LASTEXITCODE
