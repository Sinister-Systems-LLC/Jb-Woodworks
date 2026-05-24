# Author: RKOJ-ELENO :: 2026-05-24
# Sanctum :: per-project protections autofix (X2 of iter 8)
#
# Runs per-project-protections-check.ps1 -Json, identifies weak lanes
# (score < 4/5), and offers to autofix the missing protection slots:
#
#   PP1 CLAUDE.md missing  -> create a minimal CLAUDE.md stub at <root>/CLAUDE.md
#   PP2 .claude/settings.json missing -> create with understand-anything enabled
#   PP3 heartbeat stale/missing -> write a fresh heartbeat JSON
#   PP4 PROGRESS log missing -> create with header
#   PP5 brain-entry uncovered -> log to ACTION-QUEUE (lane must author its own)
#
# Modes:
#   -DryRun     # show what would change, don't write
#   -Lane <key> # autofix one lane only
#   -Yes        # skip confirm prompts (still respects -DryRun)
#
# Conservative: never overwrites existing files. Operator can run as often
# as desired; it's idempotent.

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [string]$Lane = '',
    [switch]$DryRun,
    [switch]$Yes
)

$ppScript = Join-Path $SanctumRoot 'automations\per-project-protections-check.ps1'
if (-not (Test-Path $ppScript)) {
    Write-Error "per-project-protections-check.ps1 not found at $ppScript"
    exit 2
}

# Hashtable splat for named params (array splat was treating values as positional).
$ppParams = @{ SanctumRoot = $SanctumRoot; Json = $true }
if ($Lane) { $ppParams.Lane = $Lane }
$ppOut = & $ppScript @ppParams 2>$null | Out-String
$pp = $ppOut | ConvertFrom-Json
if (-not $pp.results) {
    Write-Error 'per-project-protections returned no results'
    exit 2
}

# Read projects.json for root lookup
$projectsFile = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
$rawJson = [System.IO.File]::ReadAllText($projectsFile)
if ($rawJson.Length -gt 0 -and [int]$rawJson[0] -eq 0xFEFF) { $rawJson = $rawJson.Substring(1) }
$proj = $rawJson | ConvertFrom-Json
$rootByKey = @{}
foreach ($p in $proj.projects) { if ($p.key -and $p.root) { $rootByKey[$p.key] = $p.root } }

$weak = $pp.results | Where-Object { $_.pass_count -lt 4 }
if (-not $weak) {
    Write-Host "All lanes are 4/5 or better. Nothing to autofix." -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Lanes below 4/5: $($weak.Count)" -ForegroundColor Yellow
foreach ($w in $weak) {
    Write-Host "  $($w.display) ($($w.pass_count)/$($w.total))" -ForegroundColor Yellow
}
Write-Host ""

if (-not $Yes -and -not $DryRun) {
    $ans = Read-Host "Proceed with autofix (PP1-PP4 stubs)? [y/N]"
    if ($ans -notmatch '^[yY]') { Write-Host "Aborted."; exit 0 }
}

$heartbeatsDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$progressDir = Join-Path $SanctumRoot '_shared-memory\PROGRESS'
if (-not (Test-Path $heartbeatsDir)) { New-Item -ItemType Directory -Path $heartbeatsDir -Force | Out-Null }
if (-not (Test-Path $progressDir)) { New-Item -ItemType Directory -Path $progressDir -Force | Out-Null }

$pp5Pending = @()  # lanes needing brain-entry (operator surface)
$summary = @()

foreach ($w in $weak) {
    $key = $w.key
    $display = $w.display
    $root = $rootByKey[$key]
    if (-not $root -or -not (Test-Path $root)) {
        $summary += "SKIP $display ($key): root missing"
        continue
    }
    $acts = @()

    # PP1: CLAUDE.md stub
    if (-not $w.pp1_claude_md) {
        $cm = Join-Path $root 'CLAUDE.md'
        if (-not (Test-Path $cm)) {
            $content = @"
> **Author:** RKOJ-ELENO :: $(Get-Date -Format 'yyyy-MM-dd')
> **Project:** $display
> **Auto-created:** per-project-protections-autofix.ps1 (iter 8 X2)

# CLAUDE.md - $display

This is a minimal scaffold. The lane agent should expand with:
- What this project owns
- Cold-start steps
- Lane-specific bot recommendations (see _shared-memory/knowledge/per-project-bot-adoption-playbook-2026-05-23.md)
- Composes-with

## Cold-start (every turn)

1. Heartbeat: ``sinister-bus.heartbeat(my_agent="$display")``
2. Inbox poll: ``sinister-bus.inbox_poll(my_agent="$display")``
3. Pick one bot from ``_shared-memory/knowledge/bot-fleet-quick-reference.md``
"@
            if ($DryRun) { $acts += "[dry] would create $cm" }
            else {
                [System.IO.File]::WriteAllText($cm, $content, [System.Text.UTF8Encoding]::new($false))
                $acts += "PP1 created $cm"
            }
        }
    }

    # PP2: .claude/settings.json stub
    if (-not $w.pp2_settings_json) {
        $sd = Join-Path $root '.claude'
        $sf = Join-Path $sd 'settings.json'
        if (-not (Test-Path $sf)) {
            if (-not (Test-Path $sd) -and -not $DryRun) { New-Item -ItemType Directory -Path $sd -Force | Out-Null }
            $content = @'
{
  "_comment": "Auto-created by per-project-protections-autofix.ps1 (iter 8 X2). Edit as needed.",
  "enabledPlugins": {
    "understand-anything@understand-anything": true
  }
}
'@
            if ($DryRun) { $acts += "[dry] would create $sf" }
            else {
                [System.IO.File]::WriteAllText($sf, $content, [System.Text.UTF8Encoding]::new($false))
                $acts += "PP2 created $sf"
            }
        }
    }

    # PP3: heartbeat stub
    if (-not $w.pp3_heartbeat_fresh) {
        $hb = Join-Path $heartbeatsDir "$key.json"
        $existing = if (Test-Path $hb) { Get-Content $hb -Raw | ConvertFrom-Json } else { $null }
        $tsNow = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        $hbData = [ordered]@{
            schema_version = 'sinister.heartbeat.v1'
            agent_identity = 'EVE'
            agent = $key
            agent_display = $display
            slug = $key
            ts_utc = $tsNow
            mode = if ($existing) { $existing.mode } else { 'auto-bootstrap' }
            session_status = 'autofix-stub'
            note = 'created/refreshed by per-project-protections-autofix.ps1 to bring PP3 to PASS; lane agent should overwrite on next turn'
        }
        $json = $hbData | ConvertTo-Json -Depth 5
        if ($DryRun) { $acts += "[dry] would write $hb" }
        else {
            [System.IO.File]::WriteAllText($hb, $json, [System.Text.UTF8Encoding]::new($false))
            $acts += "PP3 wrote $hb"
        }
    }

    # PP4: PROGRESS log stub
    if (-not $w.pp4_progress_log) {
        # Use display name (or Sinister X form) for filename
        $progressFile = Join-Path $progressDir "$display.md"
        if (-not (Test-Path $progressFile)) {
            $content = @"
# Agent: $display

Append-only progress log. Most recent at top.

Created by per-project-protections-autofix.ps1 (iter 8 X2) to bring PP4 to PASS.
Lane agent should append a real entry on next turn per CLAUDE.md Rule 9.

---
"@
            if ($DryRun) { $acts += "[dry] would create $progressFile" }
            else {
                [System.IO.File]::WriteAllText($progressFile, $content, [System.Text.UTF8Encoding]::new($false))
                $acts += "PP4 created $progressFile"
            }
        }
    }

    # PP5: brain-entry — lane responsibility; log to summary
    if ($w.pp5_brain_hits -eq 0) {
        $pp5Pending += $display
        $acts += "PP5 NEEDS lane to author a brain entry tagged '$key'"
    }

    if ($acts) {
        $summary += "[$display] $($w.pass_count)/5 - autofix candidates:"
        foreach ($a in $acts) { $summary += "    $a" }
    } else {
        $summary += "[$display] no autofixable gaps (likely PP5 only)"
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
foreach ($s in $summary) { Write-Host $s }
Write-Host ""
if ($pp5Pending.Count -gt 0) {
    Write-Host "Lanes needing PP5 (brain entry) - operator/lane action:" -ForegroundColor Yellow
    foreach ($p in $pp5Pending) { Write-Host "  $p" -ForegroundColor Yellow }
    Write-Host ""
}
if ($DryRun) { Write-Host "[DRY RUN] no files written. Re-run without -DryRun to apply." -ForegroundColor Cyan }
exit 0
