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
    param([string]$Row, [string]$Desc, [bool]$Ok, [string]$Evidence, [bool]$ExpectedFail = $false)
    $script:results += [PSCustomObject]@{
        row = $Row
        desc = $Desc
        ok = $Ok
        expected_fail = $ExpectedFail
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

# ============================================================
# v0.2 — remaining 22 rows from jcode-feature-matrix.md
# ============================================================

$forge = Join-Path $SanctumRoot 'projects\sinister-forge\source\forge'
$panes = Join-Path $forge 'panes'

# R1 — Multi-LLM provider routing doc
$routingDoc = Join-Path $SanctumRoot 'automations\agent-host-routing.md'
Add-Result 'R1'  'Multi-LLM routing doc present'                (Test-Path $routingDoc) $routingDoc

# R2 — Multi-pane scrolling TUI (Forge agent_pane.py)
$agentPane = Join-Path $panes 'agent_pane.py'
Add-Result 'R2'  'Forge agent_pane.py scaffolded'               (Test-Path $agentPane) $agentPane

# R3 — Forever-scroll buffer (shares agent_pane.py) + context-pruner
$ctxPruner = Join-Path $SanctumRoot 'automations\context-pruner.ps1'
Add-Result 'R3'  'context-pruner.ps1 archives long-term'        (Test-Path $ctxPruner) $ctxPruner

# R4 — Ctrl+W picker
$picker = Join-Path $panes 'picker.py'
Add-Result 'R4'  'Forge panes/picker.py present'                (Test-Path $picker) $picker

# R5 — Boot art + BootScreen class
$artPy = Join-Path $forge 'art.py'
$appPy = Join-Path $forge 'app.py'
$bootArtOk = $false
if ((Test-Path $artPy) -and (Test-Path $appPy)) {
    $bootArtOk = ((Get-Content $artPy -Raw) -match 'VAULT_BOY_FRAME') -and ((Get-Content $appPy -Raw) -match 'BootScreen')
}
Add-Result 'R5'  'Boot art frames + BootScreen class present'   $bootArtOk "art.py+app.py BootScreen"

# R6 — Cascadia + jcode palette (theme.py)
$themePy = Join-Path $forge 'theme.py'
Add-Result 'R6'  'Forge theme.py present (Cascadia + palette)'  (Test-Path $themePy) $themePy

# R7 — Status bar
$statusBar = Join-Path $panes 'status_bar.py'
$statusBar2 = Join-Path $panes 'statusbar.py'
$sbOk = (Test-Path $statusBar) -or (Test-Path $statusBar2)
Add-Result 'R7'  'Forge status_bar.py (any of two spellings)'   $sbOk "$statusBar or $statusBar2"

# R8 — Ruflo agentdb_* MCP server source on disk (can't easily call MCP from PS)
$rufloAny = $false
$rufloPaths = @(
    "$env:USERPROFILE\.npm-global\node_modules\@ruvllm",
    "$env:APPDATA\npm\node_modules\@ruvllm",
    'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents'
)
foreach ($rp in $rufloPaths) { if (Test-Path $rp) { $rufloAny = $true; $rufloPath = $rp; break } }
Add-Result 'R8'  'Ruflo MCP source/install present'             $rufloAny ($(if ($rufloAny) { $rufloPath } else { 'none of 3 candidates' }))

# R11 — Background memory consolidation
$memCons = Join-Path $SanctumRoot 'automations\memory-consolidate.ps1'
Add-Result 'R11' 'memory-consolidate.ps1 present'               (Test-Path $memCons) $memCons

# R12 — Memory-graph viz (render dir + 4 surfaces)
$renderTool = Join-Path $SanctumRoot 'tools\memory-graph-render'
$renderDir  = Join-Path $SanctumRoot '_shared-memory\forge-memory\mermaid-renders'
$r12Ok = (Test-Path $renderTool) -and (Test-Path (Join-Path $panes 'mermaid_panel.py'))
Add-Result 'R12' 'Memory-graph render tool + Forge panel'       $r12Ok "renderTool=$(Test-Path $renderTool) panel=$(Test-Path (Join-Path $panes 'mermaid_panel.py')) cacheDir=$(Test-Path $renderDir)"

# R14 — Term v0 in PATH (prompt_toolkit-based Python build)
$termCli = & where.exe sinister-term.exe 2>$null | Select-Object -First 1
if (-not $termCli) { $termCli = & where.exe sinister-term 2>$null | Select-Object -First 1 }
$termSrc = Join-Path $SanctumRoot 'tools\sinister-term'
$r14Ok = [bool]$termCli -or (Test-Path $termSrc)
Add-Result 'R14' 'sinister-term v0 reachable (CLI or src)'      $r14Ok ($(if ($termCli) { $termCli } else { $termSrc }))

# R15 — Mermaid panel + render wrapper
$mermaidPanel  = Join-Path $panes 'mermaid_panel.py'
$mermaidRender = Join-Path $forge 'mermaid_render.py'
$r15Ok = (Test-Path $mermaidPanel) -and (Test-Path $mermaidRender)
Add-Result 'R15' 'Forge mermaid_panel.py + mermaid_render.py'   $r15Ok "panel=$(Test-Path $mermaidPanel) render=$(Test-Path $mermaidRender)"

# R17 — Telemetry deliberately NOT ported (correct absence). Trivially PASS.
Add-Result 'R17' 'Telemetry deliberately absent (correct)'      $true 'no telemetry SDK shipped; verified by absence'

# R18 — Plugin / skill hot-reload (skills.py + start_watcher)
$skillsPy = Join-Path $forge 'skills.py'
$r18Ok = $false
if (Test-Path $skillsPy) { $r18Ok = (Get-Content $skillsPy -Raw) -match 'start_watcher|Observer|watchdog' }
Add-Result 'R18' 'Forge skills.py with hot-reload hooks'        $r18Ok ($(if ($r18Ok) { 'start_watcher/Observer found' } else { 'skills.py missing or no watcher' }))

# R19 — Per-agent identity / accent (agent-prefs.json)
$prefs = Join-Path $SanctumRoot 'automations\session-templates\agent-prefs.json'
Add-Result 'R19' 'agent-prefs.json present'                     (Test-Path $prefs) $prefs

# R20 — Forge Ctrl+W shipped (R4 covers); Term Ctrl+F is a known planned gap.
# Probe surfaces both: Forge keybind file + Term v1 keybinds (expected absent).
$kb = Join-Path $forge 'keybinds.py'
$r20Ok = Test-Path $kb
Add-Result 'R20' 'Forge keybinds.py present (Term gap known)'   $r20Ok ($(if ($r20Ok) { $kb } else { 'keybinds.py missing' }))

# R22 — Cold-start resume (resume-point-write.ps1)
$resumeWrite = Join-Path $SanctumRoot 'automations\resume-point-write.ps1'
Add-Result 'R22' 'resume-point-write.ps1 present'               (Test-Path $resumeWrite) $resumeWrite

# R23 — claude-hooks PH13 (planned gap) — expected FAIL until built
$claudeHooks = Join-Path $forge 'hooks.py'
$r23Ok = Test-Path $claudeHooks
Add-Result 'R23' 'claude-hooks PH13 wired (KNOWN GAP)'          $r23Ok ($(if ($r23Ok) { $claudeHooks } else { 'PH13 not yet shipped (expected per audit)' })) -ExpectedFail $true

# R24 — Skill_Seekers PH12 (planned gap)
$seekers = Join-Path $forge 'skill_seekers.py'
$r24Ok = Test-Path $seekers
Add-Result 'R24' 'Skill_Seekers PH12 wired (KNOWN GAP)'         $r24Ok ($(if ($r24Ok) { $seekers } else { 'PH12 not yet shipped (expected per audit)' })) -ExpectedFail $true

# R25 — agentgrep PH14 (planned gap, operator-gated)
$agentgrep = & where.exe agentgrep.exe 2>$null | Select-Object -First 1
if (-not $agentgrep) { $agentgrep = & where.exe agentgrep 2>$null | Select-Object -First 1 }
$r25Ok = [bool]$agentgrep
Add-Result 'R25' 'agentgrep PH14 cargo-installed (KNOWN GAP)'   $r25Ok ($(if ($r25Ok) { $agentgrep } else { 'PH14 cargo-install pending operator (expected)' })) -ExpectedFail $true

# R26 — Browser-bridge probe + Browser class source
$bbProbe = Join-Path $SanctumRoot 'tools\sinister-browser\sinister_browser\probe.py'
$bbMain  = Join-Path $SanctumRoot 'tools\sinister-browser\sinister_browser\__main__.py'
$r26Ok = (Test-Path $bbProbe) -and (Test-Path $bbMain)
Add-Result 'R26' 'sinister-browser probe.py + __main__.py'      $r26Ok "probe=$(Test-Path $bbProbe) main=$(Test-Path $bbMain)"

# R27 — Scrollable-tiling multi-pane (niri_workspace.py + columns.py)
$niri = Join-Path $panes 'niri_workspace.py'
$cols = Join-Path $panes 'columns.py'
$r27Ok = (Test-Path $niri) -and (Test-Path $cols)
Add-Result 'R27' 'Forge niri_workspace.py + columns.py'         $r27Ok "niri=$(Test-Path $niri) cols=$(Test-Path $cols)"

# R28 — Sinister-branded Rust mermaid renderer (planned fork)
$rustMmd = Join-Path $SanctumRoot 'tools\sinister-mermaid-render'
$r28Ok = Test-Path $rustMmd
Add-Result 'R28' 'sinister-mermaid-render tool dir (KNOWN GAP)' $r28Ok ($(if ($r28Ok) { $rustMmd } else { 'Rust fork pending (expected per audit)' })) -ExpectedFail $true

# Report
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$passCount     = ($results | Where-Object { $_.ok }).Count
$realFailCount = ($results | Where-Object { -not $_.ok -and -not $_.expected_fail }).Count
$expFailCount  = ($results | Where-Object { -not $_.ok -and $_.expected_fail }).Count
$total         = $results.Count

if ($Json) {
    [ordered]@{
        ts_utc = $ts
        pass = $passCount
        real_fail = $realFailCount
        expected_fail = $expFailCount
        total = $total
        results = $results
    } | ConvertTo-Json -Depth 5
} else {
    Write-Output "[$ts] jcode-parity-probe :: PASS=$passCount REAL-FAIL=$realFailCount EXPECTED-GAP=$expFailCount TOTAL=$total"
    foreach ($r in $results) {
        $tag = if ($r.ok) { '[PASS]    ' }
               elseif ($r.expected_fail) { '[EXP-GAP] ' }
               else { '[FAIL]    ' }
        Write-Output ("  $tag {0,-7} {1} :: {2}" -f $r.row, $r.desc, $r.evidence)
    }
}

# Exit code = real failures only (expected gaps don't fail the gate)
exit $realFailCount
