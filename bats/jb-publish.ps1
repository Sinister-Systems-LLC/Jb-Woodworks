# Author: RKOJ-ELENO :: 2026-05-24
# JB Woodworks — one-shot publish pipeline.
#
# Runs when content changes need to ship to production:
#   1. Mirror the LIVE folder (D:\Sinister Sanctum\projects\jb-woodworks) into
#      the side-WT branch worktree (D:\jbw-wt\projects\jb-woodworks) and the
#      Railway deploy staging clone (D:\jbw-deploy).
#   2. Stage everything that changed under projects/jb-woodworks/ in the
#      side-WT and commit + push to the Sanctum monorepo's
#      agent/jb-woodworks/v0.3.0-scaffold branch.
#   3. Subtree-split that commit into a clean root-level history and
#      force-push to the standalone Sinister-Systems-LLC/Jb-Woodworks main.
#   4. `railway up --service web -d` from /d/jbw-deploy (the only path with
#      a wired Railway project link).
#   5. Force-redeploy the Vercel proxy (`vercel deploy --prod --force`) to
#      bust the year-long edge cache so visitors see the new content on
#      the very next request.
#
# Usage:
#   .\bats\jb-publish.ps1 -Message "fix: tweak hero copy"
#
# If -Message is omitted, falls back to a stamped default.

[CmdletBinding()]
param(
  [string]$Message = "content(jb-woodworks): publish $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
)

$ErrorActionPreference = "Stop"

$LIVE   = "D:\Sinister Sanctum\projects\jb-woodworks"
$WT     = "D:\jbw-wt\projects\jb-woodworks"
$DEPLOY = "D:\jbw-deploy"

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "  JB Woodworks publish pipeline" -ForegroundColor Cyan
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ssZ')" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# -------- 1. Mirror LIVE → side-WT + deploy --------
Write-Host "`n[1/5] Mirroring LIVE -> side-WT + deploy..." -ForegroundColor Yellow
$exclude = @("node_modules", ".next", "public\img\_sorted_2026", ".claude")
foreach ($dst in @($WT, $DEPLOY)) {
  $rcArgs = @($LIVE, $dst, "/E", "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:1", "/W:1")
  foreach ($d in $exclude) { $rcArgs += "/XD"; $rcArgs += (Join-Path $LIVE $d) }
  & robocopy @rcArgs | Out-Null
}
Write-Host "    mirrored to both targets" -ForegroundColor Green

# -------- 2. Commit + push side-WT --------
Write-Host "`n[2/5] Commit + push agent/jb-woodworks/v0.3.0-scaffold..." -ForegroundColor Yellow
$wtRoot = "D:\jbw-wt"
& git -C $wtRoot add "projects/jb-woodworks" | Out-Null
$status = & git -C $wtRoot status --porcelain "projects/jb-woodworks"
if ([string]::IsNullOrWhiteSpace($status)) {
  Write-Host "    nothing to commit on agent branch" -ForegroundColor DarkYellow
} else {
  & git -C $wtRoot commit -m $Message | Out-Null
  & git -C $wtRoot push origin agent/jb-woodworks/v0.3.0-scaffold | Out-Null
  Write-Host "    pushed Sanctum branch" -ForegroundColor Green
}

# -------- 3. Subtree split + push standalone --------
Write-Host "`n[3/5] Subtree-split + force-push Sinister-Systems-LLC/Jb-Woodworks main..." -ForegroundColor Yellow
& git -C $wtRoot branch -D jbw-standalone-main 2>$null | Out-Null
& git -C $wtRoot subtree split --prefix=projects/jb-woodworks/ HEAD -b jbw-standalone-main | Out-Null
& git -C $wtRoot push jbw-deploy +jbw-standalone-main:main | Out-Null
Write-Host "    standalone repo synced" -ForegroundColor Green

# -------- 4. Railway up --------
Write-Host "`n[4/5] railway up --service web -d (Railway deploy)..." -ForegroundColor Yellow
Push-Location $DEPLOY
try {
  $env:RAILWAY_TOKEN = "db0fd599-85f8-4da6-8aa2-5809ae6ad580"
  # Up to 3 attempts on the upload (cold network sometimes times out).
  $deployId = $null
  for ($attempt = 1; $attempt -le 3; $attempt++) {
    $output = & railway up --service web -d 2>&1
    $deployId = ($output | Select-String -Pattern 'id=([a-f0-9-]+)').Matches |
                ForEach-Object { $_.Groups[1].Value } | Select-Object -First 1
    if ($deployId) { break }
    Write-Host "    attempt $attempt timed out, retrying..." -ForegroundColor DarkYellow
    Start-Sleep -Seconds 3
  }
  if (-not $deployId) { throw "railway up never returned a deploy id" }
  Write-Host "    deploy id: $deployId" -ForegroundColor Green
} finally {
  Pop-Location
}

# -------- 5. Force-redeploy Vercel proxy (edge cache bust) --------
Write-Host "`n[5/5] Vercel proxy force-redeploy (bust edge cache)..." -ForegroundColor Yellow
$vercelToken = (Get-Content "$env:APPDATA\com.vercel.cli\Data\auth.json" | ConvertFrom-Json).token
$env:VERCEL_TOKEN      = $vercelToken
$env:VERCEL_ORG_ID     = "team_1xCq6PZEgK4TyXV1rvLUyuEq"
$env:VERCEL_PROJECT_ID = "prj_st9imaVyeJ443qppOQMCzyZ1Jw7v"
Push-Location "D:\jbw-proxy"
try {
  & vercel deploy --yes --prod --force | Out-Null
  Write-Host "    Vercel proxy redeployed" -ForegroundColor Green
} finally {
  Pop-Location
}

Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host "  Done. Site updates at https://jbwoodworks.co/ within ~30s." -ForegroundColor Cyan
Write-Host "  Hard-refresh in your browser (Ctrl+Shift+R) if needed." -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan
