# start-sinister-session.ps1 :: Sinister Sanctum session launcher (v6 :: concise)
# Author: RKOJ-ELENO :: 2026-05-23
#
# v6 rewrite (operator directive 2026-05-23):
#   - One screen. No matrix rain / glitch reveal / multi-step wizard.
#   - jcode-style banner header + numbered project list, full stop.
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
        ($obj | ConvertTo-Json -Depth 8) | Out-File $PrefsPath -Encoding utf8
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

function Persist-AgentPref($projectKey, $agentName, $accent, $prefs) {
    if (-not $prefs) {
        $prefs = [pscustomobject]@{
            version = 2
            default = [pscustomobject]@{ agent_name = ''; accent_color = 'purple' }
            per_project = [pscustomobject]@{}
            available_colors = @('purple','magenta','cyan','green','yellow','white','random')
        }
    }
    if (-not $prefs.per_project) {
        $prefs | Add-Member -MemberType NoteProperty -Name 'per_project' -Value ([pscustomobject]@{}) -Force
    }
    $existing = $prefs.per_project.$projectKey
    if ($existing) {
        $existing.agent_name = $agentName
        $existing.accent_color = $accent
    } else {
        $prefs.per_project | Add-Member -MemberType NoteProperty -Name $projectKey -Value ([pscustomobject]@{
            agent_name = $agentName
            accent_color = $accent
        }) -Force
    }
    WritePrefsJson $prefs
    return $prefs
}

# ============================================================
# BANNER (jcode-style)
# ============================================================

function Draw-Banner {
    Clear-Host
    Write-Host ''
    $logo = @(
        '   ____  _       _      _',
        '  / ___|(_)_ __ (_)___ | |_ ___ _ __',
        "  \___ \| | '_ \| / __|| __/ _ \ '__|",
        '   ___) | | | | | \__ \| ||  __/ |',
        '  |____/|_|_| |_|_|___/ \__\___|_|',
        '',
        '          S A N C T U M'
    )
    foreach ($line in $logo) { Center $line $C.LightP }
    Write-Host ''
    Center 'server: Sanctum   client: EVE' $C.Soft
    $verLine = 'v6.0  -  ' + (Get-Date).ToString('yyyy-MM-dd HH:mm')
    Center $verLine $C.Dim
    Write-Host ''
    Hr 76 $C.Purple
    Write-Host ''
}

# ============================================================
# PROJECT PICKER (one screen)
# ============================================================

function Render-Picker($rows, $defaultKey) {
    Write-Host '  Pick a project' -ForegroundColor $C.White
    Hr 76 $C.Purple
    Write-Host ''
    $i = 1
    foreach ($p in $rows) {
        $marker = if ($p.key -eq $defaultKey) { '*' } else { ' ' }
        Write-Host ('   ' + $marker) -NoNewline -ForegroundColor $C.LightP
        Write-Host (' {0,2}) ' -f $i) -NoNewline -ForegroundColor $C.LightP
        Write-Host ('{0,-22}' -f $p.display) -NoNewline -ForegroundColor $C.White
        if ($p.tag) { Write-Host $p.tag -ForegroundColor $C.Soft } else { Write-Host '' }
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
    Write-Host ''
    Hr 76 $C.Purple
    Write-Host ''
    Write-Host ('  Selection [1-{0} / G / A / N, default={1}]  ' -f $rows.Count, $defaultKey) -NoNewline -ForegroundColor $C.White
    Write-Host '>' -NoNewline -ForegroundColor $C.LightP
    return (Read-Host ' ')
}

function Resolve-Pick($pick, $rows, $defaultKey) {
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
    return @{ kind = 'project'; key = $defaultKey }
}

# ============================================================
# AUTO-RESUME
# ============================================================

function Find-LatestResumePoint {
    if (-not (Test-Path $ResumePointsRoot)) { return $null }
    $files = Get-ChildItem $ResumePointsRoot -Recurse -Filter '*.json' -ErrorAction SilentlyContinue |
             Sort-Object LastWriteTime -Descending | Select-Object -First 10
    if (-not $files -or $files.Count -eq 0) { return $null }
    $rows = @()
    foreach ($f in $files) {
        try {
            $j = Get-Content $f.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            $rows += [pscustomobject]@{
                file = $f.FullName
                when = $f.LastWriteTime
                project = if ($j.project) { "$($j.project)" } elseif ($j.project_key) { "$($j.project_key)" } else { ($f.Directory.Name) }
                agent = if ($j.agent_name) { "$($j.agent_name)" } else { '' }
                mode = if ($j.mode) { "$($j.mode)" } else { 'resume' }
            }
        } catch {}
    }
    return $rows
}

function Pick-ResumeRow {
    $rows = Find-LatestResumePoint
    if (-not $rows -or $rows.Count -eq 0) {
        Write-Host '  [!] no resume-points found; falling back to default project.' -ForegroundColor $C.Warn
        return $null
    }
    Write-Host ''
    Write-Host '  Recent sessions' -ForegroundColor $C.White
    Hr 76 $C.Purple
    Write-Host ''
    $i = 1
    foreach ($r in $rows) {
        $ago = (Get-Date) - $r.when
        $agoStr = if ($ago.TotalMinutes -lt 60) { '{0:N0}m ago' -f $ago.TotalMinutes }
                  elseif ($ago.TotalHours -lt 48) { '{0:N1}h ago' -f $ago.TotalHours }
                  else { '{0:N0}d ago' -f $ago.TotalDays }
        Write-Host ('   {0,2}) ' -f $i) -NoNewline -ForegroundColor $C.LightP
        Write-Host ('{0,-20}' -f $r.project) -NoNewline -ForegroundColor $C.White
        Write-Host ('{0,-9}' -f $r.mode) -NoNewline -ForegroundColor $C.Soft
        Write-Host $agoStr -ForegroundColor $C.Dim
        $i++
    }
    Write-Host ''
    Write-Host ('  Selection [1-{0}, default=1]  ' -f $rows.Count) -NoNewline -ForegroundColor $C.White
    Write-Host '>' -NoNewline -ForegroundColor $C.LightP
    $pick = Read-Host ' '
    $idx = 0
    if ($pick -match '^\d+$') { $idx = [int]$pick - 1 }
    if ($idx -lt 0 -or $idx -ge $rows.Count) { $idx = 0 }
    return $rows[$idx]
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
            ($json | ConvertTo-Json -Depth 12) | Out-File $ProjectsPath -Encoding utf8
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
# COLD-START PHRASE (one source of truth - delegates to session-contracts.md)
# ============================================================

function Build-Phrase($projRec, $agentName, $mode, $isGeneral, $isScaffold) {
    $root = $projRec.root
    $display = $projRec.display
    $github = if ($projRec.github) { "https://github.com/$($projRec.github)" } else { '' }

    $coldStart = "Cold-start protocol: (1) read D:\Sinister Sanctum\SESSION-START\ in order; (2) read D:\Sinister\Sinister Skills\01_MEMORY\master\OPERATOR-DIRECTIVES.md; (3) read D:\Sinister Sanctum\PARALLEL-AGENT-COORDINATION.md; (4) read D:\Sinister Sanctum\_shared-memory\WORKSTATION.md + DIRECTIVES.md + WORK-TOWARD.md; (5) check D:\Sinister Sanctum\_shared-memory\knowledge\_INDEX.md for any relevant topic; (6) log progress to D:\Sinister Sanctum\_shared-memory\PROGRESS\<your-agent-name>.md; (7) work on a per-agent branch agent/<your-slug>/<short-topic>; (8) add `Author: RKOJ-ELENO :: <date>` to every new .bat/.md/.ps1."

    $contracts = " READ-CONTRACTS: D:\Sinister Sanctum\automations\session-contracts.md (6 binding contracts; Speed = turbo). Honor for the session."

    $identity = " You are the '$agentName' agent. Heartbeat each turn via sinister-bus.heartbeat my_agent=`"$agentName`" + sinister-bus.inbox_poll my_agent=`"$agentName`". Use purple accents in your output."

    if ($isScaffold) {
        $desc = if ($projRec.desc) { $projRec.desc } else { 'a new Sinister project' }
        return "$coldStart Then: SCAFFOLD MODE for $display at $root. Read _SCAFFOLD-BRIEF.md, then create initial source tree + README.md + CLAUDE.md + SESSION-START.md + .gitignore. Keep it minimal but runnable. When done, append a one-paragraph 'Built' summary to _SCAFFOLD-BRIEF.md.$contracts$identity"
    }

    if ($isGeneral) {
        return "$coldStart Then: GENERAL MODE - no fixed project scope. You have full memory access (D:\Sinister Sanctum\_shared-memory, knowledge/, PROGRESS/, plans/, inbox/, MASTER-PLAN.md, OPERATOR-ACTION-QUEUE.md). Respond to ad-hoc operator queries; route lane-specific work to the right agent via cross-agent inbox if needed.$contracts$identity"
    }

    # Default: resume mode for the project
    $projKey = $projRec.key
    return "$coldStart Then: RESUME MODE for $display (root: $root). Continue exactly where last session left off. FIRST action: read the LATEST resume-point at D:\Sinister Sanctum\_shared-memory\resume-points\<project-display-or-key>\<HIGHEST-UTC>.json. If none exists, fall back to: top entry of PROGRESS/<your-agent-name>.md + most-recent plans/$projKey-*/ artifact + inbox/<your-slug>/*.json. Re-establish context surgically; claim any in_progress TaskList row; BEGIN. At end of every meaningful deliverable: write a NEW resume-point via powershell -File D:\Sinister Sanctum\automations\resume-point-write.ps1 -SanctumRoot 'D:\Sinister Sanctum' -ProjectKey $projKey -AgentName $agentName -Mode resume.$contracts$identity"
}

# ============================================================
# LAUNCH (git-bash + claude --dangerously-skip-permissions)
# ============================================================

function Launch-Session($projRec, $agentName, $accent, $phrase) {
    $gitBash = 'C:\Program Files\Git\git-bash.exe'
    $bashExe = 'C:\Program Files\Git\bin\bash.exe'
    $minttyExe = 'C:\Program Files\Git\usr\bin\mintty.exe'
    if (-not (Test-Path $gitBash) -and -not (Test-Path $bashExe)) {
        Write-Host '  [FAIL] git-bash not found. Install Git for Windows.' -ForegroundColor $C.Fail
        return
    }

    # Pre-trust the folder in .claude.json so Claude doesn't show first-run dialog
    $claudeCfg = Join-Path $env:USERPROFILE '.claude.json'
    if (Test-Path $claudeCfg) {
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
            } else {
                $cfg.projects.$rootKey.hasTrustDialogAccepted = $true
                $cfg.projects.$rootKey.hasClaudeMdExternalIncludesApproved = $true
                $cfg.projects.$rootKey.hasClaudeMdExternalIncludesWarningShown = $true
                $cfg.projects.$rootKey.hasCompletedProjectOnboarding = $true
            }
            ($cfg | ConvertTo-Json -Depth 12) | Out-File $claudeCfg -Encoding utf8
        } catch {}
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
    $bashPhrase = $phrase -replace "'", "'\''"
    $bashAgentName = $agentName -replace "'", "'\''"
    $windowTitle = "Sinister :: $agentName :: $($projRec.display)"

    $launchSh = Join-Path $env:TEMP "sinister-launch-$([guid]::NewGuid().ToString().Substring(0,8)).sh"
    $shContent = @"
#!/bin/bash
printf '\033]0;$windowTitle\007'
printf '\033]10;$($cm.fg)\007'
printf '\033]11;$($cm.bg)\007'
printf '\033]12;$($cm.cur)\007'
export SINISTER_AGENT_NAME='$bashAgentName'
export SINISTER_ACCENT_COLOR='$accent'
export SINISTER_PROJECT_KEY='$($projRec.key)'
export SINISTER_MODE='resume'
clear 2>/dev/null || printf '\033c'
echo ''
echo '  =============================================='
echo '   SINISTER SANCTUM :: launching Claude'
echo '  =============================================='
echo "   Agent:   $agentName"
echo "   Project: $($projRec.display)"
echo "   Root:    $bashPath"
echo ''
cd "$bashPath" || { echo '[FAIL] could not cd to project root'; exec bash; }
claude --dangerously-skip-permissions '$bashPhrase'
echo ''
echo '  Claude exited. Dropping to bash. Type exit to close.'
exec bash
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

    $spawned = $false
    $spawnedProcess = $null
    try {
        if (Test-Path $minttyExe) {
            $spawnedProcess = Start-Process -FilePath $minttyExe -ArgumentList @(
                '-o', "ForegroundColour=$fgRgb",
                '-o', "BackgroundColour=$bgRgb",
                '-o', "CursorColour=$curRgb",
                '-o', 'FontSize=11',
                '-o', 'Term=xterm-256color',
                '--',
                '/bin/bash', $launchShBash
            ) -PassThru -ErrorAction Stop
            $spawned = $true
        } elseif (Test-Path $gitBash) {
            $spawnedProcess = Start-Process -FilePath $gitBash -ArgumentList @($launchShBash) -PassThru -ErrorAction Stop
            $spawned = $true
        } elseif (Test-Path $bashExe) {
            $spawnedProcess = Start-Process -FilePath $bashExe -ArgumentList @('-l', '-i', $launchShBash) -PassThru -ErrorAction Stop
            $spawned = $true
        }
    } catch {
        Write-Host "  [FAIL] could not spawn bash: $($_.Exception.Message)" -ForegroundColor $C.Fail
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

    Write-Host "  [OK] window up. Close this launcher when ready." -ForegroundColor $C.OK
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
        ($rec | ConvertTo-Json -Depth 6) | Out-File $path -Encoding utf8
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
    $phrase = Build-Phrase $projRec $resolvedAgent 'resume' $isGeneral $false
    if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $resolvedAccent $phrase }
    Write-RunLog $Project $resolvedAgent $resolvedAccent 'headless'
    exit 0
}

Draw-Banner
$pick = Render-Picker $visible $defaultKey
$resolved = Resolve-Pick $pick $visible $defaultKey

switch ($resolved.kind) {
    'autoresume' {
        $row = Pick-ResumeRow
        if (-not $row) {
            $targetKey = $defaultKey
        } else {
            # Map project display/key to projects.json entry
            $hit = $projectsJson.projects | Where-Object { $_.key -eq $row.project -or $_.display -eq $row.project } | Select-Object -First 1
            $targetKey = if ($hit) { $hit.key } else { $defaultKey }
        }
        $projRec = $projectsJson.projects | Where-Object { $_.key -eq $targetKey } | Select-Object -First 1
        $resolvedAgent = Get-ProjectAgentName $targetKey $prefs
        $prefs = Persist-AgentPref $targetKey $resolvedAgent 'purple' $prefs
        $phrase = Build-Phrase $projRec $resolvedAgent 'resume' ($targetKey -eq 'general') $false
        if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent 'purple' $phrase }
        Write-RunLog $targetKey $resolvedAgent 'purple' 'autoresume'
    }
    'newproject' {
        $new = Create-NewProject
        if (-not $new) { exit 1 }
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
        $phrase = Build-Phrase $projRec $resolvedAgent 'scaffold' $false $true
        if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent 'purple' $phrase }
        Write-RunLog $new.key $resolvedAgent 'purple' 'newproject'
    }
    'project' {
        $targetKey = $resolved.key
        $projRec = $projectsJson.projects | Where-Object { $_.key -eq $targetKey } | Select-Object -First 1
        if (-not $projRec) {
            Write-Host "  [FAIL] project not found: $targetKey" -ForegroundColor $C.Fail
            exit 2
        }
        $resolvedAgent = Get-ProjectAgentName $targetKey $prefs
        $prefs = Persist-AgentPref $targetKey $resolvedAgent 'purple' $prefs
        $isGeneral = ($targetKey -eq 'general')
        $phrase = Build-Phrase $projRec $resolvedAgent 'resume' $isGeneral $false
        if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent 'purple' $phrase }
        Write-RunLog $targetKey $resolvedAgent 'purple' 'project'
    }
}

exit 0
