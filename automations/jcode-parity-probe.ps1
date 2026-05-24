# jcode-parity-probe.ps1 — empirical reachability test for jcode-equivalent features in our stack.
# Author: RKOJ-ELENO :: 2026-05-24
#
# Origin: counter-argument self-audit on jcode-eve-exe-parity-audit-2026-05-24.md picked alternative C:
# "build a probe that ACTUALLY tests each row's reachability rather than ship a static audit doc".
# This is v0.1 — covers 8 high-value rows; subsequent versions expand coverage.
#
# Exit 0 if all probes PASS; exit N if N probes FAIL.
# Prints one line per probe: [PASS|FAIL] R<row#> <description> :: <evidence>

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Json
)

$ErrorActionPreference = 'Continue'

$results = @()

function Add-Result {
    param([string]$Row, [string]$Desc, [bool]$Ok, [string]$Evidence)
    $script:results += [PSCustomObject]@{
        row = $Row
        desc = $Desc
        ok = $Ok
        evidence = $Evidence
    }
}

# R1b — sinister-login CLI reachable from PATH
$loginCli = & where.exe sinister-login.exe 2>$null | Select-Object -First 1
if (-not $loginCli) { $loginCli = & where.exe sinister-login 2>$null | Select-Object -First 1 }
$loginAlt = Join-Path $SanctumRoot 'tools\sinister-login\src\sinister_login\__main__.py'
Add-Result 'R1b' 'sinister-login CLI installed or src present' (($loginCli) -or (Test-Path $loginAlt)) $(if ($loginCli) { $loginCli } else { $loginAlt })

# R1c — sinister-usage CLI reachable from PATH
$usageCli = & where.exe sinister-usage.exe 2>$null | Select-Object -First 1
if (-not $usageCli) { $usageCli = & where.exe sinister-usage 2>$null | Select-Object -First 1 }
$usageAlt = Join-Path $SanctumRoot 'tools\sinister-usage\src\sinister_usage\__main__.py'
Add-Result 'R1c' 'sinister-usage CLI installed or src present' (($usageCli) -or (Test-Path $usageAlt)) $(if ($usageCli) { $usageCli } else { $usageAlt })

# R9-R10 — forge-memory-bridge auto-recall NOT in start-sinister-session.ps1 Build-Phrase (gap finding from audit)
$launcher = Join-Path $SanctumRoot 'automations\start-sinister-session.ps1'
if (Test-Path $launcher) {
    $launcherContent = Get-Content $launcher -Raw
    $hasBridge = $launcherContent -match 'forge-memory-bridge|memory_bridge|memory-bridge.*recall'
    Add-Result 'R9-R10' 'forge-memory-bridge invoked from launcher Build-Phrase (audit predicted GAP)' $hasBridge ("present=$hasBridge in $launcher")
} else {
    Add-Result 'R9-R10' 'forge-memory-bridge invoked from launcher Build-Phrase' $false "launcher script not found at $launcher"
}

# R13 — EVE.exe binary present (single-binary distribution)
$eveCandidates = @(
    'D:\Sinister Sanctum\automations\eve-launcher\dist\EVE\EVE.exe',
    'C:\Users\Zonia\Desktop\EVE\EVE.exe',
    "$env:LOCALAPPDATA\EVE\EVE.exe"
)
$eveFound = $eveCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
Add-Result 'R13' 'EVE.exe binary present (--onedir or --onefile)' ([bool]$eveFound) $(if ($eveFound) { $eveFound } else { "none of $($eveCandidates -join ' / ')" })

# R16 — sinister-swarm pip-installed
$swarmShow = & pip show sinister-swarm 2>$null | Select-String -Pattern 'Location|Version' | ForEach-Object { $_.Line } | Out-String
Add-Result 'R16' 'sinister-swarm pip-installed (editable)' ([bool]$swarmShow.Trim()) ($swarmShow.Trim() -replace "`r`n", ' | ')

# R21 — RKOJ Workstation daemon reachable at :5077
$rkojUp = $false
$rkojDetail = "tcp:5077 closed"
try {
    $tcp = New-Object System.Net.Sockets.TcpClient
    $task = $tcp.ConnectAsync('127.0.0.1', 5077)
    if ($task.Wait(500)) {
        $rkojUp = $tcp.Connected
        $rkojDetail = "tcp:5077 open"
    }
    $tcp.Close()
} catch { $rkojDetail = "tcp:5077 connect-error" }
Add-Result 'R21' 'RKOJ Workstation daemon :5077 reachable' $rkojUp $rkojDetail

# R29 — In-Qt EVE picker overlay source present
$pickerLib = Join-Path $SanctumRoot 'tools\eve-picker\eve_picker_lib.py'
$pickerQt = Join-Path $SanctumRoot 'projects\rkoj\source\sinister_rkoj_qt\picker_overlay.py'
$bothPresent = (Test-Path $pickerLib) -and (Test-Path $pickerQt)
Add-Result 'R29' 'EVE picker lib + Qt overlay source present' $bothPresent ("lib=$(Test-Path $pickerLib) qt=$(Test-Path $pickerQt)")

# P11 — UI-base hard-canonical block present in CLAUDE.md (composes with canonical-protections-check)
$claudeMd = Join-Path $SanctumRoot 'CLAUDE.md'
$uiBaseOk = $false
if (Test-Path $claudeMd) {
    $c = Get-Content $claudeMd -Raw
    $uiBaseOk = $c -match 'UI BASE.*dashboard-skeleton' -and $c -match 'sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24'
}
Add-Result 'P11' 'UI BASE hard-canonical block in CLAUDE.md' $uiBaseOk ("matched=$uiBaseOk")

# Report
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$passCount = ($results | Where-Object { $_.ok }).Count
$failCount = ($results | Where-Object { -not $_.ok }).Count

if ($Json) {
    [ordered]@{
        ts_utc = $ts
        pass = $passCount
        fail = $failCount
        results = $results
    } | ConvertTo-Json -Depth 5
} else {
    Write-Output "[$ts] jcode-parity-probe :: PASS=$passCount FAIL=$failCount"
    foreach ($r in $results) {
        $tag = $(if ($r.ok) { '[PASS]' } else { '[FAIL]' })
        Write-Output ("  $tag {0,-7} {1} :: {2}" -f $r.row, $r.desc, $r.evidence)
    }
}

exit $failCount
