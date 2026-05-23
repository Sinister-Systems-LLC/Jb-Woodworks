# check-hetzner-state.ps1 - operator-run; emits a runlog manifest describing
# which Hetzner-deployed services are alive + which local projects are ahead
# of what's deployed.
#
# Bots read via sinister-bus.runlog_latest check-hetzner-state.

[CmdletBinding()]
param(
    [string]$HubRoot = 'D:\Sinister\Sinister Skills',
    [int]$TimeoutSec = 5,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'

. (Join-Path $PSScriptRoot '_runlog.ps1')
$log = Start-Runlog -Script 'check-hetzner-state'

# Service map mirrors 09_REFERENCE/HETZNER-DEPLOYS.md
$Services = @(
    @{ name='sinister-panel'; url='https://snap.sinijkr.com/'; healthUrl='https://snap.sinijkr.com/api/health'; source='C:\Users\Zonia\Desktop\Sinister-Panel' }
    @{ name='sinister-rka';   url=$null; healthUrl=$null; source='C:\Users\Zonia\Desktop\Sinister RKA GOOD' }
)

Write-Host "=== Hetzner state check ===" -ForegroundColor Cyan
Write-Host "Time: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))"
Write-Host ""

$summary = @{}
$pendingDeploys = @()

foreach ($svc in $Services) {
    Write-Host "[$($svc.name)]" -ForegroundColor Yellow
    $stepStart = Get-Date
    $status = @{
        name = $svc.name
        url = $svc.url
        http_ok = $null
        http_status = $null
        version_text = $null
        commits_ahead = $null
        source_exists = (Test-Path $svc.source)
    }

    # HTTP probe. 401/403 = service IS up but auth-gated -> treat as up.
    $probeUrl = if ($svc.healthUrl) { $svc.healthUrl } else { $svc.url }
    if ($probeUrl) {
        $code = $null
        $up = $false
        $note = ''
        $ver = $null
        try {
            $resp = Invoke-WebRequest -Uri $probeUrl -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
            $code = $resp.StatusCode
            $up = ($code -ge 200 -and $code -lt 500)
            $body = $resp.Content
            if ($body -and $body.Length -gt 0) {
                try {
                    $j = $body | ConvertFrom-Json -ErrorAction Stop
                    if ($j.version) { $ver = "$($j.version)" } elseif ($j.commit) { $ver = "$($j.commit)" }
                } catch {}
            }
        } catch {
            $errResp = $_.Exception.Response
            if ($errResp) {
                $code = [int]$errResp.StatusCode
                if ($code -eq 401 -or $code -eq 403) {
                    $up = $true
                    $note = 'auth-gated; service IS up'
                } else {
                    $up = $false
                    $note = "HTTP $code"
                }
            } else {
                $code = 'unreachable'
                $up = $false
                $note = $_.Exception.Message
            }
        }
        $status.http_ok = $up
        $status.http_status = $code
        $status.version_text = $ver
        $marker = if ($up) { '[OK]  ' } else { '[FAIL]' }
        $color = if ($up) { 'Green' } else { 'Red' }
        $msg = "  $marker HTTP $code"
        if ($ver)  { $msg += "  version=$ver" }
        if ($note) { $msg += "  ($note)" }
        Write-Host $msg -ForegroundColor $color
    } else {
        Write-Host "  [.]    no public URL configured (internal-only service)" -ForegroundColor DarkGray
    }

    # Commits-ahead check (where source is a git repo)
    if ($status.source_exists -and (Test-Path (Join-Path $svc.source '.git'))) {
        Push-Location $svc.source
        try {
            $branch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
            if ($branch -and $branch -ne 'HEAD') {
                # Use cmd /c to isolate stderr from PS native-stderr quirk
                $ahead = & cmd /c "git rev-list --count origin/$branch..HEAD 2>NUL"
                if ($LASTEXITCODE -eq 0 -and $ahead) {
                    $status.commits_ahead = [int]$ahead
                    if ($status.commits_ahead -gt 0) {
                        Write-Host ("  [WARN] {0} commits ahead of origin/{1}" -f $status.commits_ahead, $branch) -ForegroundColor Yellow
                        $pendingDeploys += $svc.name
                    } else {
                        Write-Host ("  [OK]   in sync with origin/{0}" -f $branch) -ForegroundColor Green
                    }
                }
            }
        } catch {
            Write-Host "  [.]    git ahead check skipped: $($_.Exception.Message)" -ForegroundColor DarkGray
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "  [.]    no .git at source ($($svc.source))" -ForegroundColor DarkGray
    }

    $summary[$svc.name] = $status
    $stepMs = [int]((Get-Date) - $stepStart).TotalMilliseconds
    $stepOk = ($status.http_ok -ne $false)
    $stepSummary = if ($status.http_ok -eq $true) { "HTTP $($status.http_status)" } elseif ($status.http_ok -eq $false) { "unreachable" } else { "no URL probe" }
    if ($status.commits_ahead -and $status.commits_ahead -gt 0) { $stepSummary += "; $($status.commits_ahead) commits ahead" }
    Add-RunlogStep -Log $log -Name $svc.name -Ok $stepOk -Ms $stepMs -Summary $stepSummary
}

Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
foreach ($k in $summary.Keys) {
    $s = $summary[$k]
    $codeStr = if ($null -eq $s.http_status) { 'n/a' } else { "$($s.http_status)" }
    $aheadStr = if ($null -eq $s.commits_ahead) { 'n/a' } else { "$($s.commits_ahead)" }
    $upStr = if ($s.http_ok -eq $true) { 'UP' } elseif ($s.http_ok -eq $false) { 'DOWN' } else { '?' }
    Write-Host (" {0,-20}  {1,-4}  http={2,-12}  ahead={3}" -f $k, $upStr, $codeStr, $aheadStr)
}

Set-RunlogOutput -Log $log -Key 'services' -Value $summary
Set-RunlogOutput -Log $log -Key 'pending_deploys' -Value $pendingDeploys

if ($pendingDeploys.Count -gt 0) {
    Add-RunlogNextAction -Log $log -Action ('Operator: run Deploy-Hetzner.bat from Desktop to push: ' + ($pendingDeploys -join ', '))
}
foreach ($k in $summary.Keys) {
    if ($summary[$k].http_ok -eq $false) {
        Add-RunlogNextAction -Log $log -Action ("Operator: $k is DOWN ($($summary[$k].http_status)). SSH in + restart its docker compose.")
    }
}

$allOk = ($pendingDeploys.Count -eq 0) -and -not ($summary.Values | Where-Object { $_.http_ok -eq $false })
$manifestPath = Save-Runlog -Log $log -AutoClose $allOk

Write-Host ""
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray

if ($allOk) {
    if (-not $Quiet) { Write-Host "All services healthy + in sync. Window will auto-close in 4s." -ForegroundColor Green; Start-Sleep -Seconds 4 }
    exit 0
}
if (-not $Quiet) { Read-Host 'Press Enter to close' }
exit 1
