# start-sinister-session.ps1 :: Sinister Sanctum session launcher (v6 :: concise)
# Author: RKOJ-ELENO :: 2026-05-23
#
# v6 rewrite (operator directive 2026-05-23):
#   - One screen. No matrix rain / glitch reveal / multi-step wizard.
#   - EVE-style banner header + numbered project list, full stop.
#   - 11 visible projects (Sanctum, Sinister Panel, Kernel APK, Sinister Emulator,
#     RKOJ unified, Snap Emulator API, TikTok Emulator API, Bumble Emulator API,
#     Sinister Freeze, JB Woodworks, Showmasters) + G) General + A) Auto-Resume
#     + N) New Project.
#   - Auto-set: accent=purple, agent_name from agent-prefs.json, host=claude,
#     mode=resume, speed=turbo, token=compact, count=1. NO prompts for those.
#   - "Today's focus" prompt: GONE.
#   - New project flow: name + one-line desc only. We derive slug, scaffold the
#     brief, register in projects.json, launch with "scaffold this" cold-start.
#   - Auto-resume: scans `_shared-memory/resume-points/` across all projects,
#     picks the most-recent for the chosen lane (or asks if ambiguous).
#   - Old v5 backed up to start-sinister-session-v5.ps1.bak.

[CmdletBinding()]
param(
    [string]$Project = '',
    [switch]$NoLaunch,
    [switch]$Fast,
    [switch]$Banner,
    [string]$AgentName = '',
    [string]$AccentColor = '',
    [string]$ProjectsFile = 'projects.json',
    [string]$PrefsFile = 'agent-prefs.json'
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Sinister Sanctum :: Session Online'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# ============================================================
# PATHS + CONSTANTS
# ============================================================

$SanctumRoot = if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }
if (-not (Test-Path $SanctumRoot)) {
    Write-Host "  [FAIL] Sanctum root not found: $SanctumRoot" -ForegroundColor Red
    Start-Sleep -Seconds 3
    exit 2
}
$AutomationsRoot = Join-Path $SanctumRoot 'automations'
$TemplatesRoot = Join-Path $AutomationsRoot 'session-templates'
$ProjectsPath = Join-Path $TemplatesRoot $ProjectsFile
$PrefsPath = Join-Path $TemplatesRoot $PrefsFile
$ResumePointsRoot = Join-Path $SanctumRoot '_shared-memory\resume-points'
$ScriptRunsDir = Join-Path $SanctumRoot '_shared-memory\script-runs'

# Color palette (purple-everything)
$C = @{
    Purple = 'DarkMagenta'
    LightP = 'Magenta'
    White  = 'White'
    Soft   = 'Gray'
    Dim    = 'DarkGray'
    OK     = 'Green'
    Warn   = 'Yellow'
    Fail   = 'Red'
    Accent = 'Magenta'
}

# ============================================================
# HELPERS
# ============================================================

function Hr([int]$Width = 76, [string]$Color = $C.Purple) {
    Write-Host ('  ' + ('-' * $Width)) -ForegroundColor $Color
}

function Center([string]$Text, [string]$Color = $C.White) {
    $w = try { [Console]::WindowWidth } catch { 100 }
    if ($w -lt 40) { $w = 100 }
    $pad = [Math]::Max(0, [int](($w - $Text.Length) / 2))
    Write-Host ((' ' * $pad) + $Text) -ForegroundColor $Color
}

function Pick-RandomArt {
    $artDir = Join-Path $AutomationsRoot 'session-art'
    if (-not (Test-Path $artDir)) { return $null }
    $arts = @(Get-ChildItem -Path $artDir -Filter '*.txt' -ErrorAction SilentlyContinue)
    if (-not $arts -or $arts.Count -eq 0) { return $null }
    $pick = $arts | Get-Random
    try {
        $lines = @(Get-Content -Path $pick.FullName -Encoding UTF8 -ErrorAction Stop)
        while ($lines.Count -gt 0 -and -not ($lines[$lines.Count - 1]).Trim()) {
            $lines = $lines[0..($lines.Count - 2)]
        }
        return @{ name = [System.IO.Path]::GetFileNameWithoutExtension($pick.Name); lines = $lines }
    } catch {
        return $null
    }
}

# Quick-win caches (operator 2026-05-23: "terminals keep getting held up and freeze; make
# sure we are as efficent as we can be like how jcode works"). Both counts re-read
# JSON / glob on every Draw-Banner call (~50-200ms each on warm cache, more on cold).
# Cache for 30s; banner redraws within a single picker loop pay zero re-read cost.
$script:_mcpCache = @{ ts = [DateTime]::MinValue; count = 0 }
$script:_botCache = @{ ts = [DateTime]::MinValue; count = 0 }

function Get-MCPCount {
    if (([DateTime]::UtcNow - $script:_mcpCache.ts).TotalSeconds -lt 30) {
        return $script:_mcpCache.count
    }
    # MCP servers live in ~/.claude/.mcp.json (read-only here; operator-owned).
    $mcpPaths = @(
        (Join-Path $env:USERPROFILE '.claude\.mcp.json'),
        (Join-Path $env:USERPROFILE '.claude.json')
    )
    $n = 0
    foreach ($p in $mcpPaths) {
        if (-not (Test-Path $p)) { continue }
        try {
            $c = Get-Content -Path $p -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($c.mcpServers) {
                $n = @($c.mcpServers.PSObject.Properties).Count
                if ($n -gt 0) { break }
            }
        } catch {}
    }
    $script:_mcpCache.ts = [DateTime]::UtcNow
    $script:_mcpCache.count = $n
    return $n
}

function Get-BotCount {
    if (([DateTime]::UtcNow - $script:_botCache.ts).TotalSeconds -lt 30) {
        return $script:_botCache.count
    }
    $botDir = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents'
    $n = 0
    if (Test-Path $botDir) {
        $n = @(Get-ChildItem -Path $botDir -Directory -ErrorAction SilentlyContinue).Count
    }
    $script:_botCache.ts = [DateTime]::UtcNow
    $script:_botCache.count = $n
    return $n
}

function ReadProjectsJson {
    if (-not (Test-Path $ProjectsPath)) {
        Write-Host "  [FAIL] projects.json not found at $ProjectsPath" -ForegroundColor Red
        exit 2
    }
    try {
        return Get-Content $ProjectsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Write-Host "  [FAIL] could not parse projects.json: $($_.Exception.Message)" -ForegroundColor Red
        exit 2
    }
}

function ReadPrefsJson {
    if (-not (Test-Path $PrefsPath)) {
        return $null
    }
    try {
        return Get-Content $PrefsPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        return $null
    }
}

function WritePrefsJson($obj) {
    try {
        [System.IO.File]::WriteAllText($PrefsPath, ($obj | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
    } catch {}
}

function Get-VisibleProjects($projectsJson) {
    $allByKey = @{}
    foreach ($p in $projectsJson.projects) { $allByKey[$p.key] = $p }
    $keys = if ($projectsJson.picker -and $projectsJson.picker.visible_keys) {
        @($projectsJson.picker.visible_keys)
    } else {
        # Fallback: every entry without _subsumed_by, in order
        @($projectsJson.projects | Where-Object { -not $_._subsumed_by } | ForEach-Object { $_.key })
    }
    $rows = @()
    foreach ($k in $keys) {
        if ($allByKey.ContainsKey($k)) { $rows += $allByKey[$k] }
    }
    return $rows
}

function Get-ProjectAgentName($projectKey, $prefs) {
    if ($prefs -and $prefs.per_project -and $prefs.per_project.$projectKey -and $prefs.per_project.$projectKey.agent_name) {
        return $prefs.per_project.$projectKey.agent_name
    }
    return $projectKey
}

function Confirm-AgentPrefs($projectKey, $projDisplay, $prefs) {
    # Operator 2026-05-23: "name and color on the bat file agents need to set when its
    # opened and its not doing that or i think ever setting it". Inline confirm + override
    # right before spawn. Single Read-Host: Enter accepts existing, 'r' triggers full
    # Customize-Project, anything else = new agent_name (keeps current accent).
    $currentAgent = Get-ProjectAgentName $projectKey $prefs
    $currentAccent = 'purple'
    if ($prefs -and $prefs.per_project -and $prefs.per_project.$projectKey -and $prefs.per_project.$projectKey.accent_color) {
        $currentAccent = $prefs.per_project.$projectKey.accent_color
    }
    Write-Host ''
    Write-Host ('  Spawning ') -NoNewline -ForegroundColor $C.Soft
    Write-Host $projDisplay -NoNewline -ForegroundColor $C.White
    Write-Host (' :: agent="') -NoNewline -ForegroundColor $C.Soft
    Write-Host $currentAgent -NoNewline -ForegroundColor $C.LightP
    Write-Host ('"  accent=') -NoNewline -ForegroundColor $C.Soft
    Write-Host $currentAccent -ForegroundColor $C.LightP
    # 2026-05-23 operator: "the sinsiter start bat file isnt working." — clearer
    # call-to-action so the operator knows pressing Enter is the next step.
    Write-Host ('  Press [Enter] to launch now -or- r to rename/recolor -or- type a new agent name') -ForegroundColor $C.Dim
    Write-Host '  > ' -NoNewline -ForegroundColor $C.LightP
    $resp = Read-Host
    if (-not $resp -or -not $resp.Trim()) {
        # Accept current — make sure they're persisted so subsequent launches see them.
        $prefs = Persist-AgentPref $projectKey $currentAgent $currentAccent $prefs
        return @{ prefs = $prefs; agent = $currentAgent; accent = $currentAccent }
    }
    $resp = $resp.Trim()
    if ($resp.ToLower() -eq 'r' -or $resp.ToLower() -eq 'rename') {
        # Drop into full Customize-Project for THIS key only.
        $newAgent = $currentAgent
        $newAccent = $currentAccent
        Write-Host ('   New agent name (Enter = keep "' + $currentAgent + '")') -ForegroundColor $C.Soft
        Write-Host '   > ' -NoNewline -ForegroundColor $C.LightP
        $n = Read-Host
        if ($n -and $n.Trim()) { $newAgent = $n.Trim() }
        $palette = @('purple','magenta','cyan','green','yellow','white','random')
        Write-Host ('   Accent (Enter = keep "' + $currentAccent + '", options: ' + ($palette -join ', ') + ')') -ForegroundColor $C.Soft
        Write-Host '   > ' -NoNewline -ForegroundColor $C.LightP
        $a = Read-Host
        if ($a -and $a.Trim()) {
            $a = $a.Trim().ToLower()
            if ($a -eq 'random') { $a = ($palette | Where-Object { $_ -ne 'random' } | Get-Random) }
            if ($palette -contains $a) { $newAccent = $a } else {
                Write-Host ('   [warn] unknown accent "' + $a + '", keeping "' + $currentAccent + '"') -ForegroundColor $C.Warn
            }
        }
        $prefs = Persist-AgentPref $projectKey $newAgent $newAccent $prefs
        Write-Host ('   [OK] saved: agent="' + $newAgent + '" accent=' + $newAccent) -ForegroundColor $C.OK
        return @{ prefs = $prefs; agent = $newAgent; accent = $newAccent }
    }
    # Anything else = new agent_name override (keep accent).
    $prefs = Persist-AgentPref $projectKey $resp $currentAccent $prefs
    Write-Host ('   [OK] saved: agent="' + $resp + '" accent=' + $currentAccent + ' (use r to change accent)') -ForegroundColor $C.OK
    return @{ prefs = $prefs; agent = $resp; accent = $currentAccent }
}

function Persist-AgentPref($projectKey, $agentName, $accent, $prefs) {
    # Operator 2026-05-23 evening: "amke name setting and color setting work it does not wotk now".
    # Root cause: prior impl mutated $existing.agent_name on a PSCustomObject which silently no-ops
    # when the property doesn't already exist. Fix: always rebuild the per-project entry as a
    # fresh PSCustomObject and use Add-Member -Force so add OR update both work. Also surface
    # write errors instead of swallowing them.
    $obj = if ($prefs) { $prefs } else {
        [pscustomobject]@{
            version = 2
            default = [pscustomobject]@{ agent_name = ''; accent_color = 'purple' }
            per_project = [pscustomobject]@{}
            available_colors = @('purple','magenta','cyan','green','yellow','white','random')
        }
    }
    if (-not $obj.per_project) {
        $obj | Add-Member -MemberType NoteProperty -Name 'per_project' -Value ([pscustomobject]@{}) -Force
    }
    # Always rebuild the per-project entry as a fresh PSCustomObject so add OR update both work.
    $entry = [pscustomobject]@{
        agent_name   = $agentName
        accent_color = $accent
    }
    $obj.per_project | Add-Member -MemberType NoteProperty -Name $projectKey -Value $entry -Force
    # Explicit write with surfaced error if it fails (was silent try/catch before).
    try {
        $json = $obj | ConvertTo-Json -Depth 8
        [System.IO.File]::WriteAllText($PrefsPath, $json, [System.Text.UTF8Encoding]::new($false))
    } catch {
        Write-Host ('  [warn] could not persist agent-prefs: ' + $_.Exception.Message) -ForegroundColor Yellow
    }
    return $obj
}

# ============================================================
# BANNER (EVE-style)
# ============================================================

function Draw-Banner {
    # Operator directive 2026-05-23: "make sure startup sequence even is optimzed for
    # token use like how jcode is". Default = compact one-liner (no ASCII art, no
    # multi-line info block). Pass -Banner to restore the v6.1 full banner.
    Clear-Host
    Write-Host ''

    if ($Banner) {
        # Legacy full banner (ASCII art + multi-line info block).
        $art = Pick-RandomArt
        if ($art -and $art.lines) {
            foreach ($line in $art.lines) { Center $line $C.LightP }
        } else {
            Center '   .##############.' $C.LightP
            Center '  ##              ##' $C.LightP
            Center '  ##   SANCTUM    ##' $C.LightP
            Center '  ##              ##' $C.LightP
            Center '   ################' $C.LightP
        }
        Write-Host ''
        Center '~ sanctum ~' $C.Dim
        Write-Host ''

        $mcpCount = Get-MCPCount
        $botCount = Get-BotCount
        $now = (Get-Date).ToString('yyyy-MM-dd HH:mm')
        $cwd = $SanctumRoot -replace '^[A-Za-z]:', '~'

        Center 'server: Sanctum'                                  $C.Soft
        Center 'client: EVE'                                      $C.Soft
        Center 'claude-opus-4-7[1m]  *  turbo  *  compact phrase' $C.Dim
        Center ('v6.1  *  ' + $now)                               $C.Dim
        Center $cwd                                               $C.Dim
        Write-Host ''
        $statusLine = ('* mcp({0})   * bots({1})   * plugins(16)' -f $mcpCount, $botCount)
        Center $statusLine $C.Soft
        Write-Host ''
        Hr 76 $C.Purple
        Write-Host ''
        return
    }

    # Compact one-liner (default). Single grokkable line, no ASCII art, no padding.
    $mcpCount = Get-MCPCount
    $botCount = Get-BotCount
    $now = (Get-Date).ToString('yyyy-MM-dd HH:mm')
    $oneLiner = ('  Sinister Sanctum · v6.1 · mcp({0}) · bots({1}) · plugins(16) · {2}' -f $mcpCount, $botCount, $now)
    Write-Host $oneLiner -ForegroundColor $C.Soft
    Write-Host ''
}

# ============================================================
# PROJECT PICKER (one screen)
# ============================================================

function Render-Picker($rows, $defaultKey, $prefs) {
    Write-Host '  Pick a project' -ForegroundColor $C.White
    Hr 76 $C.Purple
    Write-Host ''
    $i = 1
    foreach ($p in $rows) {
        $marker = if ($p.key -eq $defaultKey) { '*' } else { ' ' }
        Write-Host ('   ' + $marker) -NoNewline -ForegroundColor $C.LightP
        Write-Host (' {0,2}) ' -f $i) -NoNewline -ForegroundColor $C.LightP
        Write-Host ('{0,-22}' -f $p.display) -NoNewline -ForegroundColor $C.White
        # Show per-project agent_name + accent inline if it diverges from the default.
        $tagText = if ($p.tag) { $p.tag } else { '' }
        $agentNameForRow = Get-ProjectAgentName $p.key $prefs
        $accentForRow = 'purple'
        if ($prefs -and $prefs.per_project -and $prefs.per_project.$($p.key) -and $prefs.per_project.$($p.key).accent_color) {
            $accentForRow = $prefs.per_project.$($p.key).accent_color
        }
        $isCustomized = ($agentNameForRow -ne $p.key) -or ($accentForRow -ne 'purple')
        if ($isCustomized) {
            $maxTag = 36
            if ($tagText.Length -gt $maxTag) { $tagText = $tagText.Substring(0, $maxTag - 1) + '...' }
            Write-Host ('{0,-38}' -f $tagText) -NoNewline -ForegroundColor $C.Soft
            Write-Host (' [' + $agentNameForRow + ' / ' + $accentForRow + ']') -ForegroundColor $C.Dim
        } else {
            if ($tagText) { Write-Host $tagText -ForegroundColor $C.Soft } else { Write-Host '' }
        }
        $i++
    }
    Write-Host ''
    Hr 76 $C.Purple
    Write-Host ''
    Write-Host '    G) ' -NoNewline -ForegroundColor $C.LightP
    Write-Host ('{0,-22}' -f 'General') -NoNewline -ForegroundColor $C.White
    Write-Host 'No project scope, full memory, ad-hoc' -ForegroundColor $C.Soft
    Write-Host '    A) ' -NoNewline -ForegroundColor $C.LightP
    Write-Host ('{0,-22}' -f 'Auto-Resume') -NoNewline -ForegroundColor $C.White
    Write-Host 'Continue most-recent session' -ForegroundColor $C.Soft
    Write-Host '    N) ' -NoNewline -ForegroundColor $C.LightP
    Write-Host ('{0,-22}' -f 'New Project') -NoNewline -ForegroundColor $C.White
    Write-Host 'Just name + desc, we scaffold the rest' -ForegroundColor $C.Soft
    Write-Host '    S) ' -NoNewline -ForegroundColor $C.LightP
    Write-Host ('{0,-22}' -f 'Autonomy Setup') -NoNewline -ForegroundColor $C.White
    Write-Host 'Run grant-claude-autonomy (new PC bootstrap)' -ForegroundColor $C.Soft
    Write-Host '    Q) ' -NoNewline -ForegroundColor $C.LightP
    Write-Host ('{0,-22}' -f 'Quit') -NoNewline -ForegroundColor $C.White
    Write-Host 'Close without spawning' -ForegroundColor $C.Soft
    Write-Host ''
    Hr 76 $C.Purple
    Write-Host ''
    Write-Host ('  Selection [1-{0} / G / A / N / S / Q, default={1}]  ' -f $rows.Count, $defaultKey) -NoNewline -ForegroundColor $C.White
    Write-Host '>' -NoNewline -ForegroundColor $C.LightP
    return (Read-Host ' ')
}

function Resolve-Pick($pick, $rows, $defaultKey) {
    # Operator 2026-05-23 evening picker screenshot: "only have here. general auto resume
    # (make sure it works) new project autonomy setup quit. all else is done for us."
    # Multi-selection + R (Rename+Color) + K (Clear context) removed per that directive.
    # Customize-Project and Clear-Context function bodies retained as dead code in case
    # operator restores them later.
    if (-not $pick) { return @{ kind = 'project'; key = $defaultKey } }
    $t = $pick.Trim().ToLower()
    if ($t -match '^\d+$') {
        $idx = [int]$t - 1
        if ($idx -ge 0 -and $idx -lt $rows.Count) { return @{ kind = 'project'; key = $rows[$idx].key } }
        return @{ kind = 'project'; key = $defaultKey }
    }
    if ($t -eq 'g') { return @{ kind = 'project'; key = 'general' } }
    if ($t -eq 'a') { return @{ kind = 'autoresume' } }
    if ($t -eq 'n') { return @{ kind = 'newproject' } }
    if ($t -eq 's' -or $t -eq 'setup' -or $t -eq 'autonomy') { return @{ kind = 'autonomy' } }
    if ($t -eq 'q' -or $t -eq 'quit' -or $t -eq 'exit') { return @{ kind = 'quit' } }
    return @{ kind = 'project'; key = $defaultKey }
}

# ============================================================
# AUTO-RESUME
# ============================================================

function Find-AllResumePoints {
    if (-not (Test-Path $ResumePointsRoot)) { return @() }
    # Cap to first 80 most-recent files — was 200 which caused multi-second scans
    # on busy fleets (operator perceived as freeze). 80 covers free-text recall well.
    $files = Get-ChildItem $ResumePointsRoot -Recurse -Filter '*.json' -ErrorAction SilentlyContinue |
             Sort-Object LastWriteTime -Descending | Select-Object -First 80
    if (-not $files -or $files.Count -eq 0) { return @() }
    $rows = @()
    foreach ($f in $files) {
        try {
            $j = Get-Content $f.FullName -Raw -Encoding UTF8 -ErrorAction Stop | ConvertFrom-Json
            $focus = ''
            $bag = New-Object System.Text.StringBuilder
            foreach ($field in 'focus_intent','last_ship','current_focus') {
                if ($j.$field) {
                    if (-not $focus) { $focus = "$($j.$field)" }
                    [void]$bag.Append(' ').Append("$($j.$field)")
                }
            }
            if ($j.progress_top3) {
                foreach ($p in $j.progress_top3) { [void]$bag.Append(' ').Append("$p") }
                if (-not $focus -and $j.progress_top3.Count -gt 0) { $focus = "$($j.progress_top3[0])" }
            }
            if ($j.latest_plan -and $j.latest_plan.artifact) {
                [void]$bag.Append(' ').Append([System.IO.Path]::GetFileNameWithoutExtension("$($j.latest_plan.artifact)"))
            }
            $rows += [pscustomobject]@{
                file    = $f.FullName
                when    = $f.LastWriteTime
                project = if ($j.project) { "$($j.project)" } elseif ($j.project_key) { "$($j.project_key)" } else { ($f.Directory.Name) }
                agent   = if ($j.agent_name) { "$($j.agent_name)" } else { '' }
                mode    = if ($j.mode) { "$($j.mode)" } else { 'resume' }
                focus   = if ($focus) { $focus } else { '(no focus recorded)' }
                bag     = $bag.ToString().ToLower()
            }
        } catch {}
    }
    return $rows
}

function Score-Row($row, $tokens) {
    if (-not $tokens -or $tokens.Count -eq 0) { return 0 }
    $score = 0
    foreach ($t in $tokens) {
        if (-not $t) { continue }
        $tl = $t.ToLower()
        if ($row.bag -match [Regex]::Escape($tl)) { $score += 10 }
        if ("$($row.project)".ToLower() -match [Regex]::Escape($tl)) { $score += 6 }
        if ("$($row.agent)".ToLower() -match [Regex]::Escape($tl)) { $score += 4 }
        if ("$($row.focus)".ToLower() -match [Regex]::Escape($tl)) { $score += 8 }
    }
    return $score
}

function Render-ResumeList($rows, $title) {
    Write-Host ''
    Write-Host ('  ' + $title) -ForegroundColor $C.White
    Hr 76 $C.Purple
    Write-Host ''
    $i = 1
    foreach ($r in $rows) {
        $ago = (Get-Date) - $r.when
        $agoStr = if ($ago.TotalMinutes -lt 60) { '{0,5:N0}m ago' -f $ago.TotalMinutes }
                  elseif ($ago.TotalHours -lt 48) { '{0,5:N1}h ago' -f $ago.TotalHours }
                  else { '{0,5:N0}d ago' -f $ago.TotalDays }
        Write-Host ('   {0,2}) ' -f $i) -NoNewline -ForegroundColor $C.LightP
        Write-Host ('{0,-22}' -f $r.project) -NoNewline -ForegroundColor $C.White
        Write-Host ($agoStr + '  ') -NoNewline -ForegroundColor $C.Dim
        $focusShort = $r.focus
        $maxFocus = 60
        if ($focusShort.Length -gt $maxFocus) { $focusShort = $focusShort.Substring(0, $maxFocus - 1) + '...' }
        Write-Host $focusShort -ForegroundColor $C.Soft
        $i++
    }
    Write-Host ''
}

function Pick-ResumeRow($visible, $defaultKey) {
    # Returns a hashtable describing what the caller should do:
    #   @{ kind = 'resume'; row = <row> }      -> resume from the picked resume-point
    #   @{ kind = 'fresh';  key = <project> }  -> spawn fresh on that project
    #   @{ kind = 'cancel' }                   -> operator cancelled; caller falls back
    #
    # Graceful no-match flow (operator directive 2026-05-23):
    #   - "most of tiume where i am auto resuming will not have resume point or things like that"
    #   - "i don want to see this in the auto resume" (the weak-score 'Best matches' list)
    # Behavior:
    #   - Threshold: if top score < $weakThreshold (20), DON'T render 'Best matches'.
    #     Instead try to match the query against $visible project keys/displays. If a
    #     project partial-matches, offer fresh-spawn. Otherwise fall through to picker.
    #   - Zero resume-points at all: show the project picker so operator can spawn fresh.
    $weakThreshold = 20

    Write-Host ''
    Write-Host '  Auto-Resume' -ForegroundColor $C.White
    Hr 76 $C.Purple
    Write-Host ''
    Write-Host '   scanning _shared-memory/resume-points/ ...' -NoNewline -ForegroundColor $C.Dim
    try { [Console]::Out.Flush() } catch {}
    $rows = Find-AllResumePoints
    Write-Host (' done (' + (@($rows).Count) + ' found)') -ForegroundColor $C.OK

    if (-not $rows -or $rows.Count -eq 0) {
        Write-Host '   [!] no resume-points anywhere. Pick a project to start fresh.' -ForegroundColor $C.Warn
        return (Pick-FreshProject $visible $defaultKey '')
    }

    Write-Host ''
    Write-Host '   Describe what you were working on (free text)' -ForegroundColor $C.Soft
    Write-Host '   or press Enter to list the most recent 10.' -ForegroundColor $C.Dim
    Write-Host '   > ' -NoNewline -ForegroundColor $C.LightP
    $query = Read-Host

    $candidates = @()
    $listTitle = 'Recent sessions'
    $topScore = 0

    if ($query -and $query.Trim()) {
        $tokens = @($query.Trim() -split '\s+' | Where-Object { $_.Length -ge 2 })
        $scored = $rows | ForEach-Object {
            [pscustomobject]@{ row = $_; score = (Score-Row $_ $tokens) }
        } | Where-Object { $_.score -gt 0 } | Sort-Object -Property @{ Expression='score'; Descending=$true }, @{ Expression={ $_.row.when }; Descending=$true }
        $scoredArr = @($scored)
        if ($scoredArr.Count -gt 0) { $topScore = [int]$scoredArr[0].score }

        if ($topScore -lt $weakThreshold) {
            # No row strongly matched. Do NOT show "Best matches" with weak rows.
            Write-Host ''
            Write-Host ('   no strong matches for "' + $query.Trim() + '"') -ForegroundColor $C.Dim
            return (Pick-FreshProject $visible $defaultKey $query.Trim())
        }

        $candidates = @($scoredArr | Select-Object -First 10 | ForEach-Object { $_.row })
        $listTitle = "Best matches for: $query"
    } else {
        $candidates = @($rows | Select-Object -First 10)
    }

    Render-ResumeList $candidates $listTitle
    Write-Host ('  Selection [1-{0}, default=1, or X to cancel]  ' -f $candidates.Count) -NoNewline -ForegroundColor $C.White
    Write-Host '>' -NoNewline -ForegroundColor $C.LightP
    $pick = Read-Host ' '
    if ($pick -and $pick.Trim().ToLower() -eq 'x') { return @{ kind = 'cancel' } }
    $idx = 0
    if ($pick -match '^\d+$') { $idx = [int]$pick - 1 }
    if ($idx -lt 0 -or $idx -ge $candidates.Count) { $idx = 0 }
    return @{ kind = 'resume'; row = $candidates[$idx] }
}

function Pick-FreshProject($visible, $defaultKey, $query) {
    # Helper used by Pick-ResumeRow when there are no strong matches (or no rows).
    # If $query partial-matches a project key or display, offer that one directly.
    # Otherwise render a compact inline project picker.
    if ($query) {
        $q = $query.ToLower()
        $matched = @()
        foreach ($p in $visible) {
            if ("$($p.key)".ToLower() -match [Regex]::Escape($q) -or "$($p.display)".ToLower() -match [Regex]::Escape($q)) {
                $matched += $p
            }
        }
        if ($matched.Count -eq 1) {
            $hit = $matched[0]
            Write-Host ''
            Write-Host ('   project match: ' + $hit.display) -ForegroundColor $C.OK
            Write-Host ('   Spawn fresh on "' + $hit.display + '"? [Y/n] > ') -NoNewline -ForegroundColor $C.LightP
            $ans = Read-Host
            if (-not $ans -or $ans.Trim().ToLower() -ne 'n') {
                return @{ kind = 'fresh'; key = $hit.key }
            }
        } elseif ($matched.Count -gt 1) {
            Write-Host ''
            Write-Host ('   ' + $matched.Count + ' project name matches:') -ForegroundColor $C.Soft
            $i = 1
            foreach ($p in $matched) {
                Write-Host ('   {0,2}) {1}' -f $i, $p.display) -ForegroundColor $C.White
                $i++
            }
            Write-Host ('   Pick [1-{0}, Enter to cancel] > ' -f $matched.Count) -NoNewline -ForegroundColor $C.LightP
            $pick = Read-Host
            if ($pick -match '^\d+$') {
                $idx = [int]$pick - 1
                if ($idx -ge 0 -and $idx -lt $matched.Count) {
                    return @{ kind = 'fresh'; key = $matched[$idx].key }
                }
            }
            return @{ kind = 'cancel' }
        }
    }

    # Compact inline picker — no project matched (or no query). Show numbered list.
    Write-Host ''
    Write-Host '   Pick a project to start fresh:' -ForegroundColor $C.White
    $i = 1
    foreach ($p in $visible) {
        $marker = if ($p.key -eq $defaultKey) { '*' } else { ' ' }
        Write-Host ('   ' + $marker + ' {0,2}) {1}' -f $i, $p.display) -ForegroundColor $C.White
        $i++
    }
    Write-Host ('   Selection [1-{0}, Enter=default ({1}), X to cancel] > ' -f $visible.Count, $defaultKey) -NoNewline -ForegroundColor $C.LightP
    $pick = Read-Host
    if (-not $pick) { return @{ kind = 'fresh'; key = $defaultKey } }
    $t = $pick.Trim().ToLower()
    if ($t -eq 'x' -or $t -eq 'cancel' -or $t -eq 'q') { return @{ kind = 'cancel' } }
    if ($t -match '^\d+$') {
        $idx = [int]$t - 1
        if ($idx -ge 0 -and $idx -lt $visible.Count) {
            return @{ kind = 'fresh'; key = $visible[$idx].key }
        }
    }
    return @{ kind = 'fresh'; key = $defaultKey }
}

# ============================================================
# NEW PROJECT (just name + desc)
# ============================================================

function Slugify([string]$s) {
    $s = $s.ToLower()
    $s = $s -replace '[^a-z0-9]+', '-'
    $s = $s -replace '^-+', '' -replace '-+$', ''
    return $s
}

function Create-NewProject {
    Write-Host ''
    Write-Host '  New project' -ForegroundColor $C.White
    Hr 76 $C.Purple
    Write-Host ''
    Write-Host '   Name        ' -NoNewline -ForegroundColor $C.LightP
    Write-Host '(human-friendly, e.g. "My Tool")' -ForegroundColor $C.Dim
    Write-Host '   > ' -NoNewline -ForegroundColor $C.LightP
    $display = Read-Host
    if (-not $display -or -not $display.Trim()) {
        Write-Host '   [FAIL] name required.' -ForegroundColor $C.Fail
        Start-Sleep -Seconds 2
        return $null
    }
    $display = $display.Trim()

    Write-Host ''
    Write-Host '   Description ' -NoNewline -ForegroundColor $C.LightP
    Write-Host '(one line)' -ForegroundColor $C.Dim
    Write-Host '   > ' -NoNewline -ForegroundColor $C.LightP
    $desc = Read-Host
    if (-not $desc) { $desc = 'a new Sinister project' }
    $desc = $desc.Trim()

    $slug = Slugify $display
    $root = Join-Path $SanctumRoot ("projects\$slug")
    if (-not (Test-Path $root)) { New-Item -ItemType Directory -Path $root -Force | Out-Null }

    $github = "Sinister-Systems-LLC/$(($display -replace '\s+', '-'))"
    $now = (Get-Date).ToString('yyyy-MM-dd HH:mm')

    $brief = @"
# $display - SCAFFOLD BRIEF

**Slug:** $slug
**Captured:** $now
**Origin:** Start-Sinister-Session.bat -> N) new project

## Goal

$desc

## Acceptance

- Folder under D:\Sinister Sanctum\projects\$slug\ has an initial source tree
- README.md, CLAUDE.md, SESSION-START.md, .gitignore present
- Source files compile / import cleanly (no runtime needed yet)
- A one-paragraph summary of what was created lives at the bottom of this file

## Out-of-scope

- Real implementation logic (this is just scaffolding)
- CI / Docker / cloud deploys (deferred)
- Tests beyond a smoke check (deferred)

## Status

idea
"@
    $briefPath = Join-Path $root '_SCAFFOLD-BRIEF.md'
    [System.IO.File]::WriteAllText($briefPath, $brief, [System.Text.UTF8Encoding]::new($false))

    # Register in projects.json (append + add to picker.visible_keys)
    try {
        $json = ReadProjectsJson
        $existing = $json.projects | Where-Object { $_.key -eq $slug } | Select-Object -First 1
        if (-not $existing) {
            $newEntry = [pscustomobject]@{
                key = $slug
                display = $display
                tag = $desc
                root = $root
                session_start = ''
                claude_md = (Join-Path $root 'CLAUDE.md')
                github = $github
            }
            $json.projects = @($json.projects) + $newEntry
            if ($json.picker -and $json.picker.visible_keys) {
                $vk = @($json.picker.visible_keys)
                if (-not ($vk -contains $slug)) { $vk += $slug }
                $json.picker.visible_keys = $vk
            }
            [System.IO.File]::WriteAllText($ProjectsPath, ($json | ConvertTo-Json -Depth 12), [System.Text.UTF8Encoding]::new($false))
        }
    } catch {
        Write-Host "   [WARN] could not update projects.json: $($_.Exception.Message)" -ForegroundColor $C.Warn
    }

    Write-Host ''
    Write-Host "   [OK] scaffolded $display at $root" -ForegroundColor $C.OK
    Write-Host ''
    Start-Sleep -Milliseconds 600
    return @{
        key = $slug
        display = $display
        root = $root
        github = $github
        scaffold = $true
        desc = $desc
    }
}

# ============================================================
# CUSTOMIZE (rename + accent) -- H directive 2026-05-23
# ============================================================

function Customize-Project($projectsJson, $visible, $prefs) {
    Write-Host ''
    Write-Host '  Rename + Color' -ForegroundColor $C.White
    Hr 76 $C.Purple
    Write-Host ''
    $i = 1
    foreach ($p in $visible) {
        $currentAgent = Get-ProjectAgentName $p.key $prefs
        $currentAccent = 'purple'
        if ($prefs -and $prefs.per_project -and $prefs.per_project.$($p.key) -and $prefs.per_project.$($p.key).accent_color) {
            $currentAccent = $prefs.per_project.$($p.key).accent_color
        }
        Write-Host ('   {0,2}) ' -f $i) -NoNewline -ForegroundColor $C.LightP
        Write-Host ('{0,-22}' -f $p.display) -NoNewline -ForegroundColor $C.White
        Write-Host ('agent="' + $currentAgent + '"  accent=' + $currentAccent) -ForegroundColor $C.Soft
        $i++
    }
    Write-Host ''
    Write-Host ('  Which project? [1-{0}, Enter to cancel] ' -f $visible.Count) -NoNewline -ForegroundColor $C.White
    Write-Host '>' -NoNewline -ForegroundColor $C.LightP
    $pick = Read-Host ' '
    if (-not $pick -or -not ($pick -match '^\d+$')) {
        Write-Host '   [skip] cancelled.' -ForegroundColor $C.Dim
        return $prefs
    }
    $idx = [int]$pick - 1
    if ($idx -lt 0 -or $idx -ge $visible.Count) {
        Write-Host '   [skip] out of range.' -ForegroundColor $C.Dim
        return $prefs
    }
    $target = $visible[$idx]
    $currentAgent = Get-ProjectAgentName $target.key $prefs
    $currentAccent = 'purple'
    if ($prefs -and $prefs.per_project -and $prefs.per_project.$($target.key) -and $prefs.per_project.$($target.key).accent_color) {
        $currentAccent = $prefs.per_project.$($target.key).accent_color
    }
    Write-Host ''
    Write-Host ('   New agent name (Enter = keep "' + $currentAgent + '")') -ForegroundColor $C.Soft
    Write-Host '   > ' -NoNewline -ForegroundColor $C.LightP
    $newName = Read-Host
    if (-not $newName -or -not $newName.Trim()) { $newName = $currentAgent } else { $newName = $newName.Trim() }

    $palette = @('purple','magenta','cyan','green','yellow','white','random')
    Write-Host ''
    Write-Host ('   Accent color (Enter = keep "' + $currentAccent + '")') -ForegroundColor $C.Soft
    Write-Host ('   options: ' + ($palette -join ', ')) -ForegroundColor $C.Dim
    Write-Host '   > ' -NoNewline -ForegroundColor $C.LightP
    $newAccent = Read-Host
    if (-not $newAccent -or -not $newAccent.Trim()) {
        $newAccent = $currentAccent
    } else {
        $newAccent = $newAccent.Trim().ToLower()
        if ($newAccent -eq 'random') { $newAccent = ($palette | Where-Object { $_ -ne 'random' } | Get-Random) }
        if (-not ($palette -contains $newAccent)) {
            Write-Host ('   [warn] unknown accent "' + $newAccent + '", keeping "' + $currentAccent + '".') -ForegroundColor $C.Warn
            $newAccent = $currentAccent
        }
    }
    $prefs = Persist-AgentPref $target.key $newName $newAccent $prefs
    Write-Host ''
    Write-Host ('   [OK] ' + $target.display + ' -> agent="' + $newName + '"  accent=' + $newAccent) -ForegroundColor $C.OK
    Write-Host ''
    Start-Sleep -Milliseconds 800
    return $prefs
}

# ============================================================
# CLEAR (context-pruner shortcut) -- K directive 2026-05-23
# ============================================================

function Clear-Context {
    Write-Host ''
    Write-Host '  Clear stale context' -ForegroundColor $C.White
    Hr 76 $C.Purple
    Write-Host ''
    Write-Host '   This rotates: inbox >7 days, plans status=shipped >14 days,' -ForegroundColor $C.Soft
    Write-Host '   cross-agent broadcasts >30 days, PROGRESS >2000 lines.' -ForegroundColor $C.Soft
    Write-Host '   Live state stays. _archive/ collects the pruned items.' -ForegroundColor $C.Dim
    Write-Host ''
    Write-Host '   Proceed? [Y/n] > ' -NoNewline -ForegroundColor $C.LightP
    $ans = Read-Host
    if ($ans -and $ans.Trim().ToLower() -eq 'n') {
        Write-Host '   [skip] cancelled.' -ForegroundColor $C.Dim
        return
    }
    $pruner = Join-Path $AutomationsRoot 'context-pruner.ps1'
    if (-not (Test-Path $pruner)) {
        Write-Host ('   [warn] context-pruner.ps1 not found at ' + $pruner) -ForegroundColor $C.Warn
        Start-Sleep -Seconds 1
        return
    }
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $pruner
        Write-Host '   [OK] context pruned.' -ForegroundColor $C.OK
    } catch {
        Write-Host ('   [warn] pruner errored: ' + $_.Exception.Message) -ForegroundColor $C.Warn
    }
    Write-Host ''
    Start-Sleep -Milliseconds 800
}

# ============================================================
# COLD-START PHRASE (one source of truth - delegates to session-contracts.md)
# ============================================================

function Build-Phrase($projRec, $agentName, $mode, $isGeneral, $isScaffold, $modes = $null) {
    # Operator 2026-05-23 evening (multiple screenshots): child Claude refused prior phrase
    # framing it as "long instruction block claiming pre-authorization for a list of activities,
    # embedded in a first turn / No verifiable provenance / hard-canonical / DO NOT REVERT /
    # binding language". Root cause: the inlined SANDBOX-DOCTRINE block + "operator hard-
    # canonical" + "DO NOT REVERT" reads like a jailbreak attempt to a fresh classifier.
    # Fix: short natural directive pointing at on-disk docs (CLAUDE.md, SESSION-START/, brain
    # entries) which have verifiable provenance via git history.
    $root = $projRec.root
    $display = $projRec.display
    $projKey = $projRec.key
    $base = "Working on $display at $root as the '$agentName' lane. Open $root\CLAUDE.md for the project's cold-start protocol. Log progress to _shared-memory\PROGRESS\$agentName.md and write a heartbeat to _shared-memory\heartbeats\<slug>.json each turn."
    if ($isScaffold) {
        $phrase = $base + " Mode: SCAFFOLD. Read _SCAFFOLD-BRIEF.md, then create the initial repo skeleton (README.md + CLAUDE.md + SESSION-START.md + .gitignore + source/). Keep it minimal but runnable. When done, append a Built summary to _SCAFFOLD-BRIEF.md."
    }
    elseif ($isGeneral) {
        $phrase = $base + " Mode: GENERAL. No fixed project scope; use _shared-memory/ for ad-hoc work and route lane-specific items via the cross-agent inbox."
    }
    else {
        $phrase = $base + " Mode: RESUME. Pick up from the latest resume-point in _shared-memory\resume-points\$display\ (highest-UTC json). After each meaningful deliverable, write a fresh resume-point via automations\resume-point-write.ps1 -ProjectKey $projKey -AgentName $agentName -Mode resume."
    }
    # Operator 2026-05-23 — jcode-parity autonomy. When swarm and/or loop are opted in at
    # the picker, instruct the child accordingly. Env vars (SINISTER_SWARM_MODE /
    # SINISTER_LOOP_MODE) are also exported so any tooling inside the spawn shell can
    # branch off them.
    if ($modes -and $modes.swarm) {
        $phrase += " SWARM MODE on: for non-trivial multi-file work, spawn 3-5 parallel sub-agents via the Agent tool and aggregate findings before acting. Use sinister-swarm CLI or sinister-bus orchestration when the work spans multiple lanes."
    }
    if ($modes -and $modes.loop) {
        $phrase += " LOOP MODE on: do not stop after the first solution; keep iterating and expanding on ideas until the task is verifiably complete or the operator interrupts. If a recurring cadence helps, invoke the /loop skill in dynamic mode."
    }
    # Operator 2026-05-23 — fleet-wide bot quick-ref pointer (B.6 ship). 30-60% input-token
    # reduction per session when local bots substitute for Opus on routine work.
    $phrase += " Before reaching for Opus on routine work (file search / classify / scrape / digest / heartbeat / inbox), check _shared-memory/knowledge/bot-fleet-quick-reference.md — 13 free local MCP bots cover most of it."
    return $phrase
}

# ============================================================
# AGENT MODES PROMPT (operator 2026-05-23 — jcode-parity autonomy)
# ============================================================
# "when making agents add option to be asked if i want to turn on swarm and or loop
#  (make system so agents dont stop working or expanding on ideas, jcode has that
#  use what they do)"
#
# Compact single-line prompt before each spawn. Default = both OFF. Returns a
# hashtable @{swarm=$bool; loop=$bool}.
# Operator can preset via env: SINISTER_DEFAULT_SWARM=1 / SINISTER_DEFAULT_LOOP=1
# Operator can skip-this-prompt via env: SINISTER_SKIP_MODES_PROMPT=1 (uses defaults).
# ============================================================

function Prompt-AgentModes {
    $defSwarm = ($env:SINISTER_DEFAULT_SWARM -eq '1')
    $defLoop  = ($env:SINISTER_DEFAULT_LOOP -eq '1')
    if ($env:SINISTER_SKIP_MODES_PROMPT -eq '1') {
        return @{ swarm = $defSwarm; loop = $defLoop }
    }
    $defLabel = if ($defSwarm -and $defLoop) { 'both' } elseif ($defSwarm) { 'swarm' } elseif ($defLoop) { 'loop' } else { 'neither' }
    # RKOJ-ELENO :: 2026-05-23 :: SPEED FIX — $C.Header / $C.Prompt were never defined
    # in the $C palette (lines ~54-64), so each spawn emitted two silent Write-Host
    # parameter errors that polluted stderr and could stall buffered output. Use
    # existing palette entries (White / LightP).
    Write-Host ''
    Write-Host '  Modes (jcode-parity autonomy):' -ForegroundColor $C.White
    Write-Host '    s = swarm  (spawn parallel sub-agents for multi-file work)' -ForegroundColor $C.Dim
    Write-Host '    l = loop   (keep iterating + expanding; do not stop on first solution)' -ForegroundColor $C.Dim
    Write-Host '    b = both   |   Enter = none   |   ! = remember default (this session)' -ForegroundColor $C.Dim
    Write-Host -NoNewline ('  Choose [default: ' + $defLabel + ']: ') -ForegroundColor $C.LightP
    $ans = Read-Host
    $modes = @{ swarm = $defSwarm; loop = $defLoop }
    if (-not $ans) { return $modes }
    $a = $ans.ToLower().Trim()
    # Strip optional '!' suffix used to lock-in this session default.
    $lockDefault = $false
    if ($a.EndsWith('!')) { $lockDefault = $true; $a = $a.TrimEnd('!') }
    switch -Regex ($a) {
        '^(s|swarm)$'        { $modes.swarm = $true;  $modes.loop = $false }
        '^(l|loop)$'         { $modes.swarm = $false; $modes.loop = $true }
        '^(b|both|sl|ls)$'   { $modes.swarm = $true;  $modes.loop = $true }
        '^(n|no|off|none)$'  { $modes.swarm = $false; $modes.loop = $false }
        default              { Write-Host ('  (unrecognized: "' + $ans + '") -> using default: ' + $defLabel) -ForegroundColor $C.Dim }
    }
    if ($lockDefault) {
        $env:SINISTER_DEFAULT_SWARM = if ($modes.swarm) { '1' } else { '0' }
        $env:SINISTER_DEFAULT_LOOP  = if ($modes.loop)  { '1' } else { '0' }
        $env:SINISTER_SKIP_MODES_PROMPT = '1'
        Write-Host '  [locked] modes saved for this session; clear with $env:SINISTER_SKIP_MODES_PROMPT=$null' -ForegroundColor $C.Dim
    }
    return $modes
}

# ============================================================
# WINDOW-POSITION RESTORE (operator 2026-05-23 evening:
# "i also want the resume of the projkect to place it in the same place the terminal
#  was in when it was closed. if something is already in that position then just
#  open without position set")
# ============================================================

function Get-SavedWindowPosition($projectKey, $sanctumRoot) {
    $path = Join-Path $sanctumRoot ('_shared-memory\window-positions\' + $projectKey + '.json')
    if (-not (Test-Path $path)) { return $null }
    try {
        $j = Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($null -eq $j.x -or $null -eq $j.y -or $null -eq $j.w -or $null -eq $j.h) { return $null }
        return $j
    } catch { return $null }
}

function Test-WindowPositionOccupied($x, $y, $w, $h) {
    # RKOJ-ELENO :: 2026-05-23 :: SPEED FIX — operator opt-out + lazy Add-Type.
    # Setting SINISTER_SKIP_POSITION_CHECK=1 skips the Win32 EnumWindows scan
    # entirely (eliminates 50-500ms cold-path latency on the spawn hot path).
    if ($env:SINISTER_SKIP_POSITION_CHECK -eq '1') { return $false }
    try {
        if (-not ('WinPosCheck' -as [type])) {
            Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Collections.Generic;
public class WinPosCheck {
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    public static List<RECT> rects = new List<RECT>();
    public static bool Collect(IntPtr hWnd, IntPtr lParam) {
        if (!IsWindowVisible(hWnd)) return true;
        RECT r;
        if (GetWindowRect(hWnd, out r)) {
            int w = r.Right - r.Left; int h = r.Bottom - r.Top;
            if (w > 100 && h > 100) rects.Add(r);
        }
        return true;
    }
}
"@ -ErrorAction SilentlyContinue
        }
        [WinPosCheck]::rects = New-Object 'System.Collections.Generic.List[WinPosCheck+RECT]'
        [WinPosCheck]::EnumWindows([WinPosCheck+EnumWindowsProc][WinPosCheck]::Collect, [IntPtr]::Zero) | Out-Null
        $savedArea = $w * $h
        foreach ($r in [WinPosCheck]::rects) {
            $ix = [Math]::Max($x, $r.Left)
            $iy = [Math]::Max($y, $r.Top)
            $ax = [Math]::Min($x + $w, $r.Right)
            $ay = [Math]::Min($y + $h, $r.Bottom)
            if ($ax -gt $ix -and $ay -gt $iy) {
                $overlap = ($ax - $ix) * ($ay - $iy)
                if ($savedArea -gt 0 -and ($overlap / [double]$savedArea) -gt 0.5) { return $true }
            }
        }
        return $false
    } catch { return $false }
}

# ============================================================
# LAUNCH (git-bash + claude --dangerously-skip-permissions)
# ============================================================

# RKOJ-ELENO :: 2026-05-23 :: auto-clone the upstream GitHub repo into
# $projRec.root on first-spawn-if-missing. Operator's local Sanctum stores
# four project sources as NTFS junctions to D:\Sinister\... that don't exist
# on Leo's machine. This function makes a fresh-clone Sanctum self-bootstrapping
# for any public Sinister-Systems-LLC repo. Idempotent: only clones if the
# target is missing or empty. Private repos rely on pre-existing gh auth or
# GH_TOKEN env (HTTPS clone surface).
function Ensure-ProjectSource($projRec) {
    if (-not $projRec) { return }
    $github = [string]$projRec.github
    if ([string]::IsNullOrWhiteSpace($github)) { return }
    $root = [string]$projRec.root
    if ([string]::IsNullOrWhiteSpace($root)) { return }
    $needsClone = $false
    if (-not (Test-Path $root)) {
        $needsClone = $true
    } else {
        try {
            $hasAny = @(Get-ChildItem -LiteralPath $root -Force -ErrorAction Stop | Select-Object -First 1).Count -gt 0
            if (-not $hasAny) { $needsClone = $true }
        } catch { $needsClone = $true }
    }
    if (-not $needsClone) { return }
    $repo = "https://github.com/$github.git"
    $key = $projRec.key
    Write-Host "  > cloning $repo into projects/$key/source/..." -ForegroundColor $C.Accent
    try {
        $parent = Split-Path -Parent $root
        if ($parent -and -not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        if (Test-Path $root) { Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue }
        & git clone $repo $root 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor $C.Dim }
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [WARN] git clone exited $LASTEXITCODE for $repo (private repo? auth issue?) — spawn will likely fail" -ForegroundColor $C.Warn
        }
    } catch {
        Write-Host "  [WARN] clone error: $_" -ForegroundColor $C.Warn
    }
}

function Launch-Session($projRec, $agentName, $accent, $phrase, $modes = $null) {
    $swarmEnv = if ($modes -and $modes.swarm) { '1' } else { '' }
    $loopEnv  = if ($modes -and $modes.loop)  { '1' } else { '' }
    $gitBash = 'C:\Program Files\Git\git-bash.exe'
    $bashExe = 'C:\Program Files\Git\bin\bash.exe'
    $minttyExe = 'C:\Program Files\Git\usr\bin\mintty.exe'
    if (-not (Test-Path $gitBash) -and -not (Test-Path $bashExe)) {
        Write-Host '  [FAIL] git-bash not found. Install Git for Windows.' -ForegroundColor $C.Fail
        return
    }

    # Pre-trust the folder in .claude.json so Claude doesn't show first-run dialog
    # RKOJ-ELENO :: 2026-05-23 :: env-gated full skip for power users (skip ~80ms serialize)
    if ($env:SINISTER_SKIP_TRUST_BLOCK -ne '1') {
    $claudeCfg = Join-Path $env:USERPROFILE '.claude.json'
    if (Test-Path $claudeCfg) {
        # RKOJ-ELENO :: 2026-05-23 :: silent-catch intentional — .claude.json corruption must not block claude launch (claude rebuilds it on next run)
        try {
            $cfg = Get-Content $claudeCfg -Raw | ConvertFrom-Json
            $rootKey = $projRec.root -replace '\\', '/'
            if (-not $cfg.projects) { $cfg | Add-Member -MemberType NoteProperty -Name 'projects' -Value ([pscustomobject]@{}) }
            if (-not $cfg.projects.$rootKey) {
                $cfg.projects | Add-Member -MemberType NoteProperty -Name $rootKey -Value ([pscustomobject]@{
                    allowedTools = @()
                    mcpContextUris = @()
                    mcpServers = [pscustomobject]@{}
                    enabledMcpjsonServers = @()
                    disabledMcpjsonServers = @()
                    hasTrustDialogAccepted = $true
                    projectOnboardingSeenCount = 1
                    hasClaudeMdExternalIncludesApproved = $true
                    hasClaudeMdExternalIncludesWarningShown = $true
                    hasCompletedProjectOnboarding = $true
                }) -Force
                [System.IO.File]::WriteAllText($claudeCfg, ($cfg | ConvertTo-Json -Depth 12), [System.Text.UTF8Encoding]::new($false))
            } else {
                # RKOJ-ELENO :: 2026-05-23 :: skip-if-already-set short-circuit — avoid 49 KB JSON rewrite when all 4 trust flags already $true (most spawns)
                $p = $cfg.projects.$rootKey
                if ($p.hasTrustDialogAccepted -eq $true -and $p.hasClaudeMdExternalIncludesApproved -eq $true -and $p.hasClaudeMdExternalIncludesWarningShown -eq $true -and $p.hasCompletedProjectOnboarding -eq $true) {
                    # already trusted — no-op
                } else {
                    $p.hasTrustDialogAccepted = $true
                    $p.hasClaudeMdExternalIncludesApproved = $true
                    $p.hasClaudeMdExternalIncludesWarningShown = $true
                    $p.hasCompletedProjectOnboarding = $true
                    [System.IO.File]::WriteAllText($claudeCfg, ($cfg | ConvertTo-Json -Depth 12), [System.Text.UTF8Encoding]::new($false))
                }
            }
        } catch {}
    }
    }

    # RKOJ-ELENO :: 2026-05-23 :: auto-clone the upstream repo into $projRec.root
    # if the source dir is missing/empty (fresh-clone Sanctum bootstrap).
    Ensure-ProjectSource $projRec

    # RKOJ-ELENO :: 2026-05-23 :: multi-Claude account rotation (Phase 1).
    # Pick an available account from claude-accounts.json; bail if all rate-limited.
    # Library is dot-sourced lazily so a missing file does not break the launcher.
    $selectedAccountName = $null
    $selectedApiKey      = $null
    try {
        $acctLib = Join-Path $SanctumRoot 'automations\claude-accounts.ps1'
        if (Test-Path $acctLib) {
            . $acctLib
            $next = Get-NextAvailableAccount
            if (-not $next) {
                $waitUntil = Get-WaitUntilAnyAvailable
                Write-Host "  [WAIT] all Claude accounts rate-limited until $waitUntil; bat will retry." -ForegroundColor $C.Warn
                Write-Host '  [press Enter to return to picker]' -ForegroundColor $C.Dim
                Read-Host | Out-Null
                return
            }
            $selectedAccountName = $next.name
            $selectedApiKey = Get-AccountCredentials -Name $selectedAccountName
            if (-not $selectedApiKey) {
                Write-Host "  [info] account '$selectedAccountName' selected (no credentials_file yet - using claude-cli default login)" -ForegroundColor $C.Dim
            } else {
                Write-Host "  [info] account '$selectedAccountName' selected (api_key injected via ANTHROPIC_API_KEY)" -ForegroundColor $C.Dim
            }
            # Lease the slot BEFORE we spawn so concurrent picker calls do not double-book.
            $null = Mark-AccountSpawned -Name $selectedAccountName
        }
    } catch {
        Write-Host "  [warn] account rotation init failed ($($_.Exception.Message)); continuing without rotation" -ForegroundColor $C.Dim
    }

    # Color map for terminal (always purple unless overridden)
    $colorMap = @{
        purple  = @{ fg = '#E8D6FF'; bg = '#15131A'; cur = '#A06EFF' }
        magenta = @{ fg = '#FFD6F0'; bg = '#1A1318'; cur = '#FF6EE8' }
        cyan    = @{ fg = '#D6F4FF'; bg = '#0E1A1F'; cur = '#6EE8FF' }
        green   = @{ fg = '#D6FFE0'; bg = '#0E1A14'; cur = '#6EFFA0' }
        yellow  = @{ fg = '#FFF4D6'; bg = '#1A1810'; cur = '#FFD66E' }
        white   = @{ fg = '#EEEEEE'; bg = '#0A0A0F'; cur = '#FFFFFF' }
    }
    $cm = if ($colorMap.ContainsKey($accent)) { $colorMap[$accent] } else { $colorMap['purple'] }
    function _hex2rgb([string]$h) {
        $h = $h.TrimStart('#')
        return ("$([Convert]::ToInt32($h.Substring(0,2),16)),$([Convert]::ToInt32($h.Substring(2,2),16)),$([Convert]::ToInt32($h.Substring(4,2),16))")
    }
    $fgRgb = _hex2rgb $cm.fg; $bgRgb = _hex2rgb $cm.bg; $curRgb = _hex2rgb $cm.cur

    $drive = $projRec.root.Substring(0,1).ToLower()
    $rest = $projRec.root.Substring(2) -replace '\\', '/'
    $bashPath = "/$drive$rest"
    # Convert SanctumRoot to bash form too so the banner script can be located on
    # any operator's clone (e.g. Leo's machine on a different drive letter).
    $sanctumDrive = $SanctumRoot.Substring(0,1).ToLower()
    $sanctumRest = $SanctumRoot.Substring(2) -replace '\\', '/'
    $bashSanctumRoot = "/$sanctumDrive$sanctumRest"
    $bashPhrase = $phrase -replace "'", "'\''"
    $bashAgentName = $agentName -replace "'", "'\''"
    $windowTitle = "Sinister :: $agentName :: $($projRec.display)"

    # RKOJ-ELENO :: 2026-05-23 :: Phase 1/2 — account name resolved earlier (above
    # the colormap block). $selectedAccountName + $selectedApiKey already set there.
    # This block just normalizes the name + sets the bash-escaped form.
    $accountName = if ($selectedAccountName) { $selectedAccountName } elseif ($env:SINISTER_ACCOUNT) { $env:SINISTER_ACCOUNT } else { 'operator' }
    $bashAccountName = $accountName -replace "'", "'\''"
    # bash-escape the api_key (may be $null/empty if no credentials file on disk).
    $bashApiKey = if ($selectedApiKey) { ($selectedApiKey -replace "'", "'\''") } else { '' }

    $launchSh = Join-Path $env:TEMP "sinister-launch-$([guid]::NewGuid().ToString().Substring(0,8)).sh"

    # I) EVE-style status pills (256-color bg + white fg). bash printf interprets the \033 escapes.
    $mcpCnt = Get-MCPCount
    $botCnt = Get-BotCount
    $pillA = '\033[48;5;91;38;5;15;1m'
    $pillM = '\033[48;5;30;38;5;15;1m'
    $pillD = '\033[48;5;94;38;5;15;1m'
    $pillG = '\033[48;5;22;38;5;15;1m'
    $pillB = '\033[48;5;19;38;5;15;1m'
    $pillR = '\033[48;5;52;38;5;15;1m'
    $pillZ = '\033[0m'
    $projDisplay = $projRec.display
    $projKey = $projRec.key

    $shContent = @"
#!/bin/bash
printf '\033]0;$windowTitle\007'
printf '\033]10;$($cm.fg)\007'
printf '\033]11;$($cm.bg)\007'
printf '\033]12;$($cm.cur)\007'
export SINISTER_AGENT_NAME='$bashAgentName'
export SINISTER_ACCENT_COLOR='$accent'
export SINISTER_PROJECT_KEY='$projKey'
export SINISTER_PROJECT_DISPLAY='$projDisplay'
export SINISTER_MODE='resume'
export SINISTER_SWARM_MODE='$swarmEnv'
export SINISTER_LOOP_MODE='$loopEnv'
# RKOJ-ELENO :: 2026-05-23 :: Phase 1/2 — multi-account rotation. PS1 resolved the
# next available account; the .sh uses this name to mark rate-limits + release.
_account_name='$bashAccountName'
export SINISTER_ACCOUNT="`$_account_name"
# Phase 1: inject ANTHROPIC_API_KEY from the account's credentials_file (if present).
# Empty string means no per-account key on disk - claude-cli falls back to its own login.
if [ -n '$bashApiKey' ]; then
    export ANTHROPIC_API_KEY='$bashApiKey'
fi
clear 2>/dev/null || printf '\033c'
printf '\n'
# Animated jcode-style ASCII C banner (operator 2026-05-23 image #3).
# RKOJ-ELENO :: 2026-05-23 :: SPEED FIX — was blocking ~0.56s before claude
# (worst-case 8s if `sleep` fallback triggered). Now backgrounded so claude
# starts immediately and the banner animates in parallel. Skip entirely via
# SINISTER_SKIP_BANNER=1.
_sanctum_banner='$bashSanctumRoot/automations/sinister-banner.sh'
if [ -f "`$_sanctum_banner" ] && [ "`${SINISTER_SKIP_BANNER:-0}" != "1" ]; then
    ( bash "`$_sanctum_banner" 8 0.07 2>/dev/null & ) >/dev/null 2>&1
fi
printf '\n'
printf '  $pillA $agentName $pillZ  $pillM resume $pillZ  $pillD claude-opus-4-7[1m] $pillZ  $pillG mcp:$mcpCnt $pillZ  $pillB bots:$botCnt $pillZ  $pillR --skip-perms $pillZ\n'
printf '\n'
printf '  project: $projDisplay\n'
printf '  root:    $bashPath\n'
printf '\n'
cd "$bashPath" || { echo '[FAIL] could not cd to project root'; exec bash; }
claude --dangerously-skip-permissions '$bashPhrase'
# RKOJ-ELENO :: 2026-05-23 :: detect rate-limit + mark account
# Claude doesn't always exit non-zero on 429, but writes telltale text to its run log.
# We grep the recent ~/.claude session log for 429 markers + call back into PS1 library.
_session_log_dir="`$HOME/.claude/projects"
if [ -d "`$_session_log_dir" ]; then
    _recent_log=`$(find "`$_session_log_dir" -name "*.jsonl" -mmin -10 -type f 2>/dev/null | head -1)
    if [ -n "`$_recent_log" ] && grep -qE 'rate.?limit|429|too many requests|retry.?after' "`$_recent_log" 2>/dev/null; then
        printf '\n  > [WARN] rate-limit signal detected in session log - marking account "%s" throttled\n' "`$_account_name"
        # Default 60s retry-after if not parseable. Watchdog handles recovery.
        powershell -NoProfile -ExecutionPolicy Bypass -File '$SanctumRoot\automations\claude-accounts.ps1' -Action RateLimited -Name "`$_account_name" -RetryAfterSeconds 60 2>/dev/null
    fi
fi
printf '\n  > Claude exited. Writing close-time resume-point...\n'
powershell -NoProfile -ExecutionPolicy Bypass -File '$SanctumRoot\automations\resume-point-write.ps1' -SanctumRoot '$SanctumRoot' -ProjectKey '$projKey' -AgentName '$bashAgentName' -Mode resume >/dev/null 2>&1
# RKOJ-ELENO :: 2026-05-23 — auto-push on session end (operator: "every time it
# updates it pushes to github ... thats the only github repo we push to ...
# connects with leo so we can work as one"). Backgrounded so the session-end
# UX stays snappy; auto-push.log captures the result.
( powershell -NoProfile -ExecutionPolicy Bypass -File '$SanctumRoot\automations\sanctum-auto-push.ps1' >/dev/null 2>&1 & ) >/dev/null 2>&1
# RKOJ-ELENO :: 2026-05-23 :: Phase 2 — release the account slot so current_sessions decrements
powershell -NoProfile -ExecutionPolicy Bypass -File '$SanctumRoot\automations\claude-accounts.ps1' -Action Release -Name "`$_account_name" >/dev/null 2>&1
printf '  > resume-point written + auto-push fired. Dropping into sinister-term (our own shell)...\n\n'
# M) operator directive 2026-05-23: use OUR own terminal (sinister-term) where possible.
# sterm = sinister-term entry-point installed via projects/sinister-term/source pip install -e
# Falls back to bash if sterm is not on PATH (graceful per the AGPL-quarantine-friendly path).
if command -v sterm >/dev/null 2>&1; then
  exec sterm
elif command -v sinister-term >/dev/null 2>&1; then
  exec sinister-term
else
  printf '  > sterm not on PATH; falling back to bash. Install with: pip install -e $bashSanctumRoot/projects/sinister-term/source\n'
  exec bash
fi
"@
    $shContent = $shContent -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($launchSh, $shContent, [System.Text.UTF8Encoding]::new($false))
    $launchShBash = '/' + $launchSh.Substring(0,1).ToLower() + ($launchSh.Substring(2) -replace '\\', '/')

    Write-Host ''
    Write-Host "  > spawning '$agentName' :: $($projRec.display)..." -ForegroundColor $C.Accent
    Write-Host ''

    # Fire resume-point-write in background so next session has a snapshot baseline
    try {
        $rpWriter = Join-Path $SanctumRoot 'automations\resume-point-write.ps1'
        if (Test-Path $rpWriter) {
            Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
                '-NoProfile', '-ExecutionPolicy', 'Bypass',
                '-File', $rpWriter,
                '-SanctumRoot', "`"$SanctumRoot`"",
                '-ProjectKey', $projRec.key,
                '-AgentName', $agentName,
                '-Mode', 'resume'
            ) -ErrorAction SilentlyContinue | Out-Null
        }
    } catch {}

    # Operator 2026-05-23 evening: "i also want the resume of the projkect to place it in
    # the same place the terminal was in when it was closed. if something is already in
    # that position then just open without position set". Look up the saved x/y from the
    # window-position-monitor sidecar; only apply if the slot isn't already covered.
    $minttyExtraArgs = @()
    $savedPos = Get-SavedWindowPosition $projRec.key $SanctumRoot
    if ($savedPos) {
        $occupied = Test-WindowPositionOccupied $savedPos.x $savedPos.y $savedPos.w $savedPos.h
        if (-not $occupied) {
            $minttyExtraArgs = @('-p', ($savedPos.x.ToString() + ',' + $savedPos.y.ToString()))
        }
    }

    $spawned = $false
    $spawnedProcess = $null
    $spawnAttemptLog = @()
    try {
        if (Test-Path $minttyExe) {
            # E) operator directive 2026-05-23: transparent look on the spawn window.
            $minttyArgs = @(
                '-o', "ForegroundColour=$fgRgb",
                '-o', "BackgroundColour=$bgRgb",
                '-o', "CursorColour=$curRgb",
                '-o', 'FontSize=11',
                '-o', 'Term=xterm-256color',
                '-o', 'Transparency=medium',
                '-o', 'OpaqueWhenFocused=no'
            ) + $minttyExtraArgs + @('--', '/bin/bash', $launchShBash)
            $spawnAttemptLog += "mintty.exe : $minttyExe"
            $spawnedProcess = Start-Process -FilePath $minttyExe -ArgumentList $minttyArgs -PassThru -ErrorAction Stop
            $spawned = $true
        } elseif (Test-Path $gitBash) {
            $spawnAttemptLog += "git-bash.exe (no mintty) : $gitBash"
            $spawnedProcess = Start-Process -FilePath $gitBash -ArgumentList @($launchShBash) -PassThru -ErrorAction Stop
            $spawned = $true
        } elseif (Test-Path $bashExe) {
            $spawnAttemptLog += "bash.exe (no mintty + no git-bash) : $bashExe"
            $spawnedProcess = Start-Process -FilePath $bashExe -ArgumentList @('-l', '-i', $launchShBash) -PassThru -ErrorAction Stop
            $spawned = $true
        } else {
            # 2026-05-23: per operator "the sinister start bat file isnt working" — none of
            # the three shells found means we cannot spawn. Surface FAIL loudly instead of
            # silently falling through to a misleading "[OK] window up".
            Write-Host "  [FAIL] no spawn-capable shell found." -ForegroundColor $C.Fail
            Write-Host "         tried mintty.exe   : $minttyExe" -ForegroundColor $C.Dim
            Write-Host "         tried git-bash.exe : $gitBash" -ForegroundColor $C.Dim
            Write-Host "         tried bash.exe     : $bashExe" -ForegroundColor $C.Dim
            Write-Host "         install Git for Windows from https://gitforwindows.org" -ForegroundColor $C.Dim
            Write-Host '  [press Enter to return to picker]' -ForegroundColor $C.Warn
            Read-Host | Out-Null
            return
        }
    } catch {
        Write-Host "  [FAIL] could not spawn bash: $($_.Exception.Message)" -ForegroundColor $C.Fail
        Write-Host ('         attempted: ' + ($spawnAttemptLog -join ' ; ')) -ForegroundColor $C.Dim
        Write-Host '  [press Enter to return to picker]' -ForegroundColor $C.Warn
        Read-Host | Out-Null
        return
    }

    # Track the spawn so the Console / Close-All button can see it
    if ($spawned -and $spawnedProcess) {
        try {
            $swPath = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'
            $swDir = Split-Path $swPath
            if (-not (Test-Path $swDir)) { New-Item -ItemType Directory -Path $swDir -Force | Out-Null }
            $swRec = [pscustomobject]@{
                pid = $spawnedProcess.Id
                agent = $agentName
                project = $projRec.key
                project_display = $projRec.display
                mode = 'resume'
                accent = $accent
                started = (Get-Date).ToString('o')
                launcher_pid = $PID
            }
            Add-Content -Path $swPath -Value ($swRec | ConvertTo-Json -Compress) -Encoding UTF8
        } catch {}
    }

    # Fire window-position monitor in background so when the spawned window closes,
    # its final x/y/w/h is persisted to _shared-memory/window-positions/<key>.json
    # for next-resume restore.
    if ($spawnedProcess -and $spawnedProcess.Id) {
        $monitorScript = Join-Path $SanctumRoot 'automations\window-position-monitor.ps1'
        if (Test-Path $monitorScript) {
            try {
                Start-Process powershell.exe -WindowStyle Hidden -ArgumentList @(
                    '-NoProfile','-ExecutionPolicy','Bypass',
                    '-File', $monitorScript,
                    '-TargetPid', $spawnedProcess.Id.ToString(),
                    '-ProjectKey', $projRec.key,
                    '-SanctumRoot', "$SanctumRoot"
                ) -ErrorAction SilentlyContinue | Out-Null
            } catch {}
        }
    }

    # Operator 2026-05-23: prior message printed unconditionally even when
    # $spawned was false — misleading "OK" with no window. Gate on actual
    # spawn outcome + surface the spawned PID so the operator can find the
    # window in tasklist if it's offscreen.
    if ($spawned -and $spawnedProcess) {
        Write-Host ("  [OK] window up. PID=" + $spawnedProcess.Id + " (spawned via " +
                    ($spawnAttemptLog[-1]) + ")") -ForegroundColor $C.OK
        Write-Host '       if the window is offscreen: tasklist | findstr mintty  -or-  Get-Process mintty' -ForegroundColor $C.Dim
    } elseif ($spawned) {
        Write-Host "  [OK] spawn attempt returned without process handle (mintty quirk?)." -ForegroundColor $C.Warn
    } else {
        Write-Host "  [WARN] spawn did not complete — see [FAIL] message above." -ForegroundColor $C.Warn
    }
    Write-Host ''
}

# ============================================================
# RUNLOG
# ============================================================

function Write-RunLog($projectKey, $agentName, $accent, $kind) {
    try {
        if (-not (Test-Path $ScriptRunsDir)) { New-Item -ItemType Directory -Path $ScriptRunsDir -Force | Out-Null }
        $rec = [pscustomobject]@{
            ts = (Get-Date).ToString('o')
            project = $projectKey
            agent = $agentName
            accent = $accent
            kind = $kind
            launcher_version = 'v6'
            outputs = [pscustomobject]@{ project = $projectKey; mode = 'resume' }
        }
        $path = Join-Path $ScriptRunsDir ("start-sinister-session-{0}-{1}.json" -f (Get-Date).ToString('yyyyMMdd-HHmmss'), [guid]::NewGuid().ToString().Substring(0,4))
        [System.IO.File]::WriteAllText($path, ($rec | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))
    } catch {}
}

# ============================================================
# MAIN
# ============================================================

$projectsJson = ReadProjectsJson
$prefs = ReadPrefsJson
$defaultKey = if ($projectsJson.default) { $projectsJson.default } else { 'sanctum' }
$visible = Get-VisibleProjects $projectsJson

# If -Project was passed headlessly, skip the picker
if ($Project) {
    $projRec = $projectsJson.projects | Where-Object { $_.key -eq $Project } | Select-Object -First 1
    if (-not $projRec) {
        Write-Host "  [FAIL] unknown -Project: $Project" -ForegroundColor $C.Fail
        exit 2
    }
    $resolvedAgent = if ($AgentName) { $AgentName } else { Get-ProjectAgentName $Project $prefs }
    $resolvedAccent = if ($AccentColor) { $AccentColor } else { 'purple' }
    $prefs = Persist-AgentPref $Project $resolvedAgent $resolvedAccent $prefs
    $isGeneral = ($Project -eq 'general')
    # Headless: don't prompt, use env defaults (SINISTER_DEFAULT_SWARM / SINISTER_DEFAULT_LOOP).
    $modes = @{ swarm = ($env:SINISTER_DEFAULT_SWARM -eq '1'); loop = ($env:SINISTER_DEFAULT_LOOP -eq '1') }
    $phrase = Build-Phrase $projRec $resolvedAgent 'resume' $isGeneral $false $modes
    if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $resolvedAccent $phrase $modes }
    Write-RunLog $Project $resolvedAgent $resolvedAccent 'headless'
    exit 0
}

# B) operator directive 2026-05-23: loop back to picker after each spawn so operator
# can launch more agents in a row. Q ends the loop.
$quit = $false
do {
    $prefs = ReadPrefsJson
    Draw-Banner
    $pick = Render-Picker $visible $defaultKey $prefs
    $resolved = Resolve-Pick $pick $visible $defaultKey

    switch ($resolved.kind) {
        'quit' {
            Write-Host ''
            Write-Host '  bye.' -ForegroundColor $C.Soft
            Write-Host ''
            $quit = $true
        }
        'autonomy' {
            # Operator directive 2026-05-23 evening: add Grant-Claude-Autonomy as menu option
            # for new-PC bootstrap (operator's "complete autonomous setup on new PCs" ask).
            $grantScript = Join-Path $AutomationsRoot 'grant-claude-autonomy.ps1'
            Write-Host ''
            Write-Host '  Autonomy setup' -ForegroundColor $C.White
            Hr 76 $C.Purple
            Write-Host ''
            if (Test-Path $grantScript) {
                Write-Host '   Running grant-claude-autonomy.ps1...' -ForegroundColor $C.Soft
                try {
                    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $grantScript
                    Write-Host '   [OK] autonomy setup complete.' -ForegroundColor $C.OK
                } catch {
                    Write-Host ('   [warn] grant-claude-autonomy errored: ' + $_.Exception.Message) -ForegroundColor $C.Warn
                }
            } else {
                Write-Host ('   [warn] grant-claude-autonomy.ps1 not found at ' + $grantScript) -ForegroundColor $C.Warn
                Write-Host '   peer sanctum lane is expanding this script per operator 2026-05-23 evening' -ForegroundColor $C.Dim
            }
            Write-Host ''
            Start-Sleep -Milliseconds 800
        }
        'autoresume' {
            # Updated 2026-05-23: Pick-ResumeRow now returns a hashtable with kind:
            #   'resume'  -> resume from row
            #   'fresh'   -> spawn fresh on the picked project key
            #   'cancel'  -> bail; loop back to picker
            $arOutcome = Pick-ResumeRow $visible $defaultKey
            $arKind = if ($arOutcome -and $arOutcome.kind) { $arOutcome.kind } else { 'cancel' }
            if ($arKind -eq 'cancel') {
                Write-Host '   [cancelled auto-resume]' -ForegroundColor $C.Dim
                Start-Sleep -Milliseconds 400
            } elseif ($arKind -eq 'fresh') {
                $targetKey = $arOutcome.key
                $projRec = $projectsJson.projects | Where-Object { $_.key -eq $targetKey } | Select-Object -First 1
                if ($projRec) {
                    $confirmed = Confirm-AgentPrefs $targetKey $projRec.display $prefs
                    $prefs = $confirmed.prefs
                    $resolvedAgent = $confirmed.agent
                    $accentVal = $confirmed.accent
                    $isGeneral = ($targetKey -eq 'general')
                    $modes = Prompt-AgentModes
                    $phrase = Build-Phrase $projRec $resolvedAgent 'resume' $isGeneral $false $modes
                    if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $accentVal $phrase $modes }
                    Write-RunLog $targetKey $resolvedAgent $accentVal 'autoresume-fresh'
                } else {
                    Write-Host "  [FAIL] project not found: $targetKey" -ForegroundColor $C.Fail
                    Start-Sleep -Seconds 2
                }
            } else {
                # kind = 'resume'
                $row = $arOutcome.row
                $hit = $projectsJson.projects | Where-Object { $_.key -eq $row.project -or $_.display -eq $row.project } | Select-Object -First 1
                $targetKey = if ($hit) { $hit.key } else { $defaultKey }
                $projRec = $projectsJson.projects | Where-Object { $_.key -eq $targetKey } | Select-Object -First 1
                $confirmed = Confirm-AgentPrefs $targetKey $projRec.display $prefs
                $prefs = $confirmed.prefs
                $resolvedAgent = $confirmed.agent
                $accentVal = $confirmed.accent
                $modes = Prompt-AgentModes
                $phrase = Build-Phrase $projRec $resolvedAgent 'resume' ($targetKey -eq 'general') $false $modes
                if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $accentVal $phrase $modes }
                Write-RunLog $targetKey $resolvedAgent $accentVal 'autoresume'
            }
        }
        'newproject' {
            $new = Create-NewProject
            if ($new) {
                $projRec = [pscustomobject]@{
                    key = $new.key
                    display = $new.display
                    root = $new.root
                    github = $new.github
                    session_start = ''
                    claude_md = (Join-Path $new.root 'CLAUDE.md')
                    desc = $new.desc
                }
                $resolvedAgent = $new.key
                $prefs = Persist-AgentPref $new.key $resolvedAgent 'purple' $prefs
                $modes = Prompt-AgentModes
                $phrase = Build-Phrase $projRec $resolvedAgent 'scaffold' $false $true $modes
                if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent 'purple' $phrase $modes }
                Write-RunLog $new.key $resolvedAgent 'purple' 'newproject'
                $projectsJson = ReadProjectsJson
                $visible = Get-VisibleProjects $projectsJson
            }
        }
        'project' {
            $targetKey = $resolved.key
            $projRec = $projectsJson.projects | Where-Object { $_.key -eq $targetKey } | Select-Object -First 1
            if ($projRec) {
                $confirmed = Confirm-AgentPrefs $targetKey $projRec.display $prefs
                $prefs = $confirmed.prefs
                $resolvedAgent = $confirmed.agent
                $accentVal = $confirmed.accent
                $isGeneral = ($targetKey -eq 'general')
                $modes = Prompt-AgentModes
                $phrase = Build-Phrase $projRec $resolvedAgent 'resume' $isGeneral $false $modes
                if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $accentVal $phrase $modes }
                Write-RunLog $targetKey $resolvedAgent $accentVal 'project'
            } else {
                Write-Host "  [FAIL] project not found: $targetKey" -ForegroundColor $C.Fail
                Start-Sleep -Seconds 2
            }
        }
    }

    if (-not $quit) {
        Write-Host ''
        Write-Host '  > picker will re-open. Press Enter to continue, or Q to quit.' -ForegroundColor $C.Dim
        Write-Host '  > ' -NoNewline -ForegroundColor $C.LightP
        $more = Read-Host
        if ($more) {
            $more2 = $more.Trim().ToLower()
            if ($more2 -eq 'q' -or $more2 -eq 'quit' -or $more2 -eq 'exit') { $quit = $true }
        }
    }
} until ($quit)

exit 0
