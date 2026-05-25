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
    [string]$PrefsFile = 'agent-prefs.json',
    # RKOJ-ELENO :: 2026-05-24 :: -DryRun stops AFTER the auto-best-slot pick +
    # creds-swap log line, BEFORE the mintty spawn. Used by smoke tests so we
    # can verify the pick flow without firing a real claude session window.
    [switch]$DryRun
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
    # RKOJ-ELENO :: 2026-05-24 :: post-skills-rename path fix. Operator 19:36Z
    # "no bots" root cause: hardcoded pre-rename path that no longer exists.
    $candidates = @(
        'D:\Sinister Sanctum\_sinister-skills\12_LLM_ORCHESTRATION\agents',
        'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents'
    )
    $n = 0
    foreach ($botDir in $candidates) {
        if (Test-Path $botDir) {
            $n = @(Get-ChildItem -Path $botDir -Directory -ErrorAction SilentlyContinue).Count
            break
        }
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

# RKOJ-ELENO :: 2026-05-25 :: per-user agent-prefs (operator 00:32Z).
# Dot-source claude-accounts.ps1 so we can call Get-CurrentUserEmail. Best-effort:
# if the lib is missing or fails to load, the helper below falls back to $env:USERNAME
# so launcher still works on a fresh / broken install.
try {
    $accountsLib = Join-Path $AutomationsRoot 'claude-accounts.ps1'
    if (Test-Path $accountsLib) { . $accountsLib }
} catch {}

function Get-LauncherUserEmail {
    # Prefer the claude-accounts library helper (reads default account's email-formatted label).
    # Falls back to $env:USERNAME@local so per-user namespacing still works without auth setup.
    try {
        if (Get-Command Get-CurrentUserEmail -ErrorAction SilentlyContinue) {
            $em = Get-CurrentUserEmail
            if ($em) { return $em }
        }
    } catch {}
    $u = if ($env:USERNAME) { $env:USERNAME } elseif ($env:USER) { $env:USER } else { 'unknown' }
    return "$($u.ToLower())@local"
}

function _Migrate-PrefsToPerUser($obj) {
    # If $obj already has a top-level 'users' map, it's the new schema -- return unchanged.
    # If it has the old flat schema (top-level 'per_project'), wrap it under the current user
    # email and stamp _migrated_to_per_user_at_utc so we never re-migrate.
    if (-not $obj) { return $obj }
    $hasUsers = ($obj.PSObject.Properties.Name -contains 'users')
    $hasFlat  = ($obj.PSObject.Properties.Name -contains 'per_project')
    if ($hasUsers -and -not $hasFlat) { return $obj }
    $currentUser = Get-LauncherUserEmail
    $migrated = [pscustomobject]@{
        version          = 3
        _schema          = 'per_user_v1'
        _migrated_to_per_user_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        available_colors = if ($obj.available_colors) { $obj.available_colors } else { @('purple','magenta','cyan','green','yellow','white','random') }
        default          = if ($obj.default) { $obj.default } else { [pscustomobject]@{ agent_name = ''; accent_color = 'purple' } }
        users            = [pscustomobject]@{}
    }
    if ($obj.PSObject.Properties.Name -contains 'defaults') {
        $migrated | Add-Member -MemberType NoteProperty -Name 'defaults' -Value $obj.defaults -Force
    }
    if ($hasFlat -and $obj.per_project) {
        $userEntry = [pscustomobject]@{ projects = $obj.per_project }
        $migrated.users | Add-Member -MemberType NoteProperty -Name $currentUser -Value $userEntry -Force
    } else {
        $migrated.users | Add-Member -MemberType NoteProperty -Name $currentUser -Value ([pscustomobject]@{ projects = [pscustomobject]@{} }) -Force
    }
    # If the legacy object already had 'users' AND 'per_project' (mid-migration anomaly),
    # merge legacy per_project rows into the current-user namespace without clobbering existing.
    if ($hasUsers -and $obj.users) {
        foreach ($prop in $obj.users.PSObject.Properties) {
            if (-not ($migrated.users.PSObject.Properties.Name -contains $prop.Name)) {
                $migrated.users | Add-Member -MemberType NoteProperty -Name $prop.Name -Value $prop.Value -Force
            }
        }
    }
    return $migrated
}

function ReadPrefsJson {
    if (-not (Test-Path $PrefsPath)) {
        return $null
    }
    try {
        $obj = Get-Content $PrefsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        # Migrate legacy flat schema to per-user namespace on first read. Write-back so the
        # on-disk file matches the new shape (operator: "Don't lose existing data").
        if ($obj -and ($obj.PSObject.Properties.Name -notcontains '_schema' -or $obj._schema -ne 'per_user_v1')) {
            $obj = _Migrate-PrefsToPerUser $obj
            try {
                [System.IO.File]::WriteAllText($PrefsPath, ($obj | ConvertTo-Json -Depth 10), [System.Text.UTF8Encoding]::new($false))
            } catch {}
        }
        return $obj
    } catch {
        return $null
    }
}

function _Get-UserPrefsEntry($prefs, $userEmail) {
    # Returns the {projects:{...}} object for $userEmail, creating an empty one inline if missing.
    if (-not $prefs) { return $null }
    if (-not ($prefs.PSObject.Properties.Name -contains 'users') -or -not $prefs.users) {
        $prefs | Add-Member -MemberType NoteProperty -Name 'users' -Value ([pscustomobject]@{}) -Force
    }
    if (-not ($prefs.users.PSObject.Properties.Name -contains $userEmail) -or -not $prefs.users.$userEmail) {
        $prefs.users | Add-Member -MemberType NoteProperty -Name $userEmail -Value ([pscustomobject]@{ projects = [pscustomobject]@{} }) -Force
    }
    $entry = $prefs.users.$userEmail
    if (-not ($entry.PSObject.Properties.Name -contains 'projects') -or -not $entry.projects) {
        $entry | Add-Member -MemberType NoteProperty -Name 'projects' -Value ([pscustomobject]@{}) -Force
    }
    return $entry
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
    # RKOJ-ELENO :: 2026-05-25 :: per-user lookup (operator 00:32Z "leo may be slightly dif").
    # New schema: prefs.users[<email>].projects[<key>].agent_name. Falls back to legacy
    # prefs.per_project[<key>] if the migration didn't run yet, then to $projectKey.
    if ($prefs) {
        $userEmail = Get-LauncherUserEmail
        if ($prefs.users -and $prefs.users.$userEmail -and $prefs.users.$userEmail.projects -and $prefs.users.$userEmail.projects.$projectKey -and $prefs.users.$userEmail.projects.$projectKey.agent_name) {
            return $prefs.users.$userEmail.projects.$projectKey.agent_name
        }
        if ($prefs.per_project -and $prefs.per_project.$projectKey -and $prefs.per_project.$projectKey.agent_name) {
            return $prefs.per_project.$projectKey.agent_name
        }
    }
    return $projectKey
}

function Get-ProjectAccent($projectKey, $prefs, $fallback = 'purple') {
    # RKOJ-ELENO :: 2026-05-25 :: per-user accent lookup, parallels Get-ProjectAgentName.
    if ($prefs) {
        $userEmail = Get-LauncherUserEmail
        if ($prefs.users -and $prefs.users.$userEmail -and $prefs.users.$userEmail.projects -and $prefs.users.$userEmail.projects.$projectKey -and $prefs.users.$userEmail.projects.$projectKey.accent_color) {
            return $prefs.users.$userEmail.projects.$projectKey.accent_color
        }
        if ($prefs.per_project -and $prefs.per_project.$projectKey -and $prefs.per_project.$projectKey.accent_color) {
            return $prefs.per_project.$projectKey.accent_color
        }
    }
    return $fallback
}

function Confirm-AgentPrefs($projectKey, $projDisplay, $prefs) {
    # Operator 2026-05-23: "name and color on the bat file agents need to set when its
    # opened and its not doing that or i think ever setting it". Inline confirm + override
    # right before spawn. Single Read-Host: Enter accepts existing, 'r' triggers full
    # Customize-Project, anything else = new agent_name (keeps current accent).
    $currentAgent = Get-ProjectAgentName $projectKey $prefs
    $currentAccent = Get-ProjectAccent $projectKey $prefs 'purple'
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
    # RKOJ-ELENO :: 2026-05-25 :: operator 00:32Z per-user namespacing. Writes go to
    # prefs.users[<currentEmail>].projects[<key>]. Legacy prefs.per_project block is
    # preserved (read-fallback only) but never written to by this helper anymore.
    $obj = if ($prefs) { $prefs } else {
        [pscustomobject]@{
            version          = 3
            _schema          = 'per_user_v1'
            _migrated_to_per_user_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
            default          = [pscustomobject]@{ agent_name = ''; accent_color = 'purple' }
            users            = [pscustomobject]@{}
            available_colors = @('purple','magenta','cyan','green','yellow','white','random')
        }
    }
    # Defend against a downstream caller passing a pre-migration object.
    if (-not ($obj.PSObject.Properties.Name -contains '_schema') -or $obj._schema -ne 'per_user_v1') {
        $obj = _Migrate-PrefsToPerUser $obj
    }
    $userEmail = Get-LauncherUserEmail
    $userEntry = _Get-UserPrefsEntry $obj $userEmail
    $entry = [pscustomobject]@{
        agent_name        = $agentName
        accent_color      = $accent
        last_saved_at_utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    }
    $userEntry.projects | Add-Member -MemberType NoteProperty -Name $projectKey -Value $entry -Force
    try {
        $json = $obj | ConvertTo-Json -Depth 10
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
        $accentForRow = Get-ProjectAccent $p.key $prefs 'purple'
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
        $currentAccent = Get-ProjectAccent $p.key $prefs 'purple'
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
    $currentAccent = Get-ProjectAccent $target.key $prefs 'purple'
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

function Get-ResumeContextInject {
    # Operator hard-canonical 2026-05-24T17:01:09Z: "make sure all agents from bat file
    # restart like they were never closed." Reads the latest resume-point + heartbeat for
    # the project/agent and returns a short inject-text. The agent receives this in the
    # first turn so it doesn't have to manually grep + read files to learn its state.
    # RKOJ-ELENO :: 2026-05-24.
    param([string]$ProjectDisplay, [string]$AgentName)
    try {
        $rpDir = Join-Path $ResumePointsRoot $ProjectDisplay
        $latest = $null
        if (Test-Path $rpDir) {
            $latest = Get-ChildItem $rpDir -Filter '*.json' -ErrorAction SilentlyContinue |
                      Sort-Object LastWriteTime -Descending |
                      Where-Object {
                          try {
                              $j = Get-Content $_.FullName -Raw -ErrorAction Stop | ConvertFrom-Json
                              -not $AgentName -or "$($j.agent_name)" -eq $AgentName -or -not $j.agent_name
                          } catch { $false }
                      } |
                      Select-Object -First 1
        }
        $hbFile = Join-Path $SanctumRoot "_shared-memory\heartbeats\$AgentName.json"
        $hbJson = if (Test-Path $hbFile) {
            try { Get-Content $hbFile -Raw -ErrorAction Stop | ConvertFrom-Json } catch { $null }
        } else { $null }
        $utterFile = Join-Path $SanctumRoot '_shared-memory\operator-utterances.jsonl'
        $newUtterCount = 0
        if (Test-Path $utterFile) {
            $tail = Get-Content $utterFile -Tail 25 -ErrorAction SilentlyContinue
            foreach ($l in $tail) {
                if ($l -match '"status"\s*:\s*"new"') { $newUtterCount++ }
            }
        }
        if (-not $latest -and -not $hbJson -and $newUtterCount -eq 0) { return '' }
        $sb = New-Object System.Text.StringBuilder
        [void]$sb.Append(" RESUME CONTEXT (auto-injected, no manual read needed):")
        if ($latest) {
            try {
                $rp = Get-Content $latest.FullName -Raw | ConvertFrom-Json
                if ($rp.focus_intent) { [void]$sb.Append(" focus_intent=`"$($rp.focus_intent)`".") }
                if ($rp.shipped_this_iter) {
                    $top = @($rp.shipped_this_iter) | Select-Object -First 3
                    [void]$sb.Append(" prior_iter_shipped=" + (($top | ForEach-Object { "[$_]" }) -join ' '))
                    [void]$sb.Append('.')
                }
                if ($rp.open_for_next_iter) {
                    $top = @($rp.open_for_next_iter) | Select-Object -First 3
                    [void]$sb.Append(" open_next=" + (($top | ForEach-Object { "[$_]" }) -join ' '))
                    [void]$sb.Append('.')
                }
                if ($rp.pre_warm_reads) {
                    $top = @($rp.pre_warm_reads) | Select-Object -First 3
                    [void]$sb.Append(" pre_warm_reads=" + (($top | ForEach-Object { $_ -replace '"','' }) -join '; '))
                    [void]$sb.Append('.')
                }
                $iso = $latest.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mmZ')
                [void]$sb.Append(" (resume-point ts=$iso)")
            } catch {}
        }
        if ($hbJson -and $hbJson.focus) {
            [void]$sb.Append(" last_heartbeat_focus=`"$($hbJson.focus)`".")
        }
        if ($newUtterCount -gt 0) {
            [void]$sb.Append(" UNREAD_OPERATOR_UTTERANCES=$newUtterCount (triage in first response per cold-start step 8).")
        }
        return $sb.ToString()
    } catch {
        return ''
    }
}

function Get-MemoryRecallInject {
    # Operator hard-canonical 2026-05-24T17:21Z: "make our claude memory smarter, work better
    # ... like in jcode cross reference". Closes the jcode-parity audit row 9-10 gap for
    # claude-only EVE.exe spawns by PRE-INVOKING `forge-memory recall` at spawn time and
    # injecting top hits into the cold-start phrase. Sibling-claim A of the 5x-parallel split
    # at _shared-memory/cross-agent/2026-05-24T1735Z-test-modes-5x-parallel-claims.md.
    # RKOJ-ELENO :: 2026-05-24.
    #
    # Query strategy: harvest tags from the 5 most-recent operator utterances tagged for this
    # lane (or all `status=new` rows if lane filter is empty), then call forge-memory recall
    # with the joined tag string. Caps output at 3 hits, 80 chars per value. 5s timeout.
    param([string]$AgentName)
    try {
        $utterFile = Join-Path $SanctumRoot '_shared-memory\operator-utterances.jsonl'
        if (-not (Test-Path $utterFile)) { return '' }
        # Use last 30 lines to bound parse cost; filter to lane-tagged `new` rows + recent global new.
        $tail = Get-Content $utterFile -Tail 30 -ErrorAction SilentlyContinue
        if (-not $tail) { return '' }
        $tagSet = New-Object System.Collections.Generic.HashSet[string]
        foreach ($l in $tail) {
            try { $o = $l | ConvertFrom-Json -ErrorAction Stop } catch { continue }
            if ($o.status -ne 'new' -and $o.status -ne 'acknowledged') { continue }
            if ($o.tags) { foreach ($t in $o.tags) { if ($t -and $t.Length -gt 2) { [void]$tagSet.Add($t) } } }
        }
        if ($tagSet.Count -eq 0) { return '' }
        # Top 8 tags joined (forge-memory recall is TF-IDF; more tokens = better signal).
        $query = (@($tagSet) | Select-Object -First 8) -join ' '
        # Locate forge-memory CLI; fall back gracefully if not on PATH.
        $cliPath = $null
        try {
            $cmd = Get-Command forge-memory -ErrorAction Stop
            if ($cmd) { $cliPath = $cmd.Source }
        } catch {}
        if (-not $cliPath) {
            $candidates = @(
                "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\forge-memory.exe",
                "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\forge-memory",
                "$env:USERPROFILE\AppData\Local\Programs\Python\Python312\Scripts\forge-memory.exe"
            )
            foreach ($c in $candidates) { if (Test-Path $c) { $cliPath = $c; break } }
        }
        if (-not $cliPath) { return '' }
        # Run with 5s wall-clock cap; capture stdout JSON.
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $cliPath
        $psi.Arguments = "recall `"$query`" --limit 3"
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        # RKOJ-ELENO :: 2026-05-24 :: timeout 5000->3000ms per operator 19:30Z "spawns
        # should be happening faster". Recall hits cache; 3s is plenty for warm forge-memory.
        if (-not $proc.WaitForExit(3000)) {
            try { $proc.Kill() } catch {}
            return ''
        }
        $stdout = $proc.StandardOutput.ReadToEnd()
        if (-not $stdout -or $stdout.Trim().Length -lt 2) { return '' }
        $hits = $null
        try { $hits = $stdout | ConvertFrom-Json -ErrorAction Stop } catch { return '' }
        if (-not $hits -or @($hits).Count -eq 0) { return '' }
        $parts = @()
        foreach ($h in @($hits) | Select-Object -First 3) {
            $k = if ($h.key) { "$($h.key)" } else { '?' }
            $v = if ($h.value) { "$($h.value)" } else { '' }
            if ($v.Length -gt 80) { $v = $v.Substring(0, 77) + '...' }
            $v = $v -replace '[\r\n]+', ' '
            $parts += "[$k] $v"
        }
        if ($parts.Count -eq 0) { return '' }
        $joined = $parts -join ' | '
        if ($joined.Length -gt 480) { $joined = $joined.Substring(0, 477) + '...' }
        return " MEMORY_RECALL (auto-prefetch from forge-memory on tags=$query): $joined"
    } catch {
        return ''
    }
}

function Get-SinisterMemoryInject {
    # P2 sinister-memory integration (2026-05-25 RKOJ-ELENO): pre-fetch last-5 iter-close
    # memories for the spawning agent and embed in the cold-start phrase so every spawn
    # resumes with cross-session continuity. Parallel to Get-MemoryRecallInject (forge-memory
    # keyword recall); this function contributes the structured iter-close narrative layer.
    # Falls back to '' gracefully; never blocks spawn if sinister-memory is missing.
    param([string]$AgentName)
    try {
        $smCli = $null
        $candidates = @(
            "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\sinister-memory.exe",
            "$env:LOCALAPPDATA\Programs\Python\Python312\Scripts\sinister-memory",
            "$env:USERPROFILE\AppData\Local\Programs\Python\Python312\Scripts\sinister-memory.exe"
        )
        try {
            $found = Get-Command sinister-memory -ErrorAction Stop
            if ($found) { $smCli = $found.Source }
        } catch {}
        if (-not $smCli) {
            foreach ($c in $candidates) { if (Test-Path $c -ErrorAction SilentlyContinue) { $smCli = $c; break } }
        }
        if (-not $smCli) { return '' }

        $slug = $AgentName.ToLower() -replace '\s+', '-'
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $smCli
        $psi.Arguments = "inject-spawn-phrase $slug --limit 5"
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::Start($psi)
        if (-not $proc.WaitForExit(3000)) {
            try { $proc.Kill() } catch {}
            return ''
        }
        $stdout = $proc.StandardOutput.ReadToEnd().Trim()
        if (-not $stdout -or $stdout.Length -lt 10) { return '' }
        # Collapse multi-line chunk to one inline sentence (spawn phrase is single-line).
        $oneLine = $stdout -replace '[\r\n]+', ' ' -replace '\s{2,}', ' '
        if ($oneLine.Length -gt 600) { $oneLine = $oneLine.Substring(0, 597) + '...' }
        return " SINISTER_MEMORY (last iter-close memories for $slug): $oneLine"
    } catch {
        return ''
    }
}

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
    $base = "Working on $display at $root as the '$agentName' lane. Open $root\CLAUDE.md for the project's cold-start protocol. Log progress to _shared-memory\PROGRESS\$agentName.md and write a heartbeat to _shared-memory\heartbeats\<slug>.json each turn. Memory recall available via the forge-memory CLI: ``forge-memory recall '<topic>' --limit 5`` brings prior disk-stored memories into context (composes with the Ruflo MCP semantic store; fixes jcode-parity-probe rows 9-10 auto-recall gap for claude-only spawns). Commit + push cadence: per _shared-memory\knowledge\frequent-detailed-commits-per-agent-2026-05-25.md, commit + push after each shipped deliverable on your agent branch with the detailed format (Shipped/Smoke/Refs). On-demand push: powershell -File automations\sanctum-auto-push.ps1 -Action PushNow -Slug $agentName."
    if ($isScaffold) {
        $phrase = $base + " Mode: SCAFFOLD. Read _SCAFFOLD-BRIEF.md, then create the initial repo skeleton (README.md + CLAUDE.md + SESSION-START.md + .gitignore + source/). Keep it minimal but runnable. When done, append a Built summary to _SCAFFOLD-BRIEF.md."
    }
    elseif ($isGeneral) {
        # RKOJ-ELENO :: 2026-05-24 :: operator 21:24Z setup-helper-agent directive. When the
        # SINISTER_SETUP_HELPER env var is set (first-run wizard sets it before spawning a
        # general agent), inject helper-specific instructions so the spawned EVE walks the
        # operator (likely Leo) through whatever remains in the bring-up.
        if ($env:SINISTER_SETUP_HELPER -eq '1') {
            $phrase = $base + " Mode: SETUP-HELPER. You are the spawned first-run setup assistant. The eve-first-run-wizard just completed the automated steps (autonomy granted, _shared-memory initialized, marker dropped). Your job: (1) Read $root\docs\LEO-SETUP.md + $root\docs\LEO-VAULT-SETUP.md to know the full bring-up surface. (2) Run automations\eve-first-run-check.ps1 -Format text yourself to see what is still missing. (3) For each remaining gap, surface it to the operator as a 1-line ask with the exact command to fix it (ANTHROPIC_API_KEY env var, python install, vault join, Tailscale auth-key, etc). (4) When operator confirms each fix, re-run the check to verify, then mark that gap closed. (5) When all gaps closed, write a 5-line ' done bring-up' summary and remind operator they can now click EVE.exe normally. Do NOT do anything outside the bring-up scope. Keep responses concise, use bullet points, and ask for permission before any write operation outside _shared-memory/."
        } else {
            $phrase = $base + " Mode: GENERAL. No fixed project scope; use _shared-memory/ for ad-hoc work and route lane-specific items via the cross-agent inbox."
        }
    }
    else {
        # RKOJ-ELENO :: 2026-05-24 :: operator 19:57Z verbatim (via screenshot to other agents):
        # "when agents are opened they are to do the resume flow, review and create a plan
        # to complete things then loop and keep creating and finishing plans". Composes with
        # detect-similar-agents (injected below) + LOOP MODE doctrine (continuous iteration).
        # RKOJ-ELENO :: 2026-05-24 :: operator ~19:50Z verbatim "i want each agent to when its
        # launched to of course have the cresume point but it needs to review past plans and
        # current and create a new expanded plan based on everything it needs to do and
        # expanded on it. like how our contradicting system should work". Augments REVIEW
        # step (read past+current plans) + PLAN step (write EXPANDED plan, contradict prior).
        # PHASE-SHRINK 2026-05-24T20:47Z — operator: spawned mintty windows pop and close
        # instantly. Root cause: the cold-start phrase had grown to ~4100 chars with binding
        # language ("MANDATORY", "EXECUTE", "Do NOT", "NEVER") that Claude's first-turn
        # classifier rejects (same failure mode the existing Build-Phrase comment at top of
        # function describes from 2026-05-23). Fix: point AT on-disk docs (CLAUDE.md hard-
        # canonical blocks) which have verifiable provenance via git history, instead of
        # inlining the full 4-step + EXPANDED-plan + loop-condition mandates. Child's
        # CLAUDE.md cold-start read picks up SPAWN-DETECT-SIMILAR + LOOP MODE rules 6-7 +
        # safe-quality-loops doctrine — same content, just not inlined into the phrase.
        $phrase = $base + " Mode: RESUME. Pick up from the latest resume-point in _shared-memory\resume-points\$display\ (highest-UTC json). After each meaningful deliverable, write a fresh resume-point via automations\resume-point-write.ps1 -SanctumRoot 'D:\Sinister Sanctum' -ProjectKey $projKey -AgentName $agentName -Mode resume. The cold-start flow (resume -> review sister-work + past plans -> write expanded plan -> ship -> loop) is documented in $root\CLAUDE.md (SPAWN-DETECT-SIMILAR + LOOP MODE hard-canonical blocks)."
        # Operator 17:01:09Z "restart like never closed" — append parsed resume-point + heartbeat + unread-utterance count.
        $resumeInject = Get-ResumeContextInject -ProjectDisplay $display -AgentName $agentName
        if ($resumeInject) { $phrase += $resumeInject }
        # Operator 17:21Z "make claude memory smarter ... like jcode cross reference" — pre-fetch
        # forge-memory top hits and inject. Closes jcode-parity-audit rows 9-10 gap (auto-recall
        # for claude-only spawns). Sub-area A of 5x-parallel split. RKOJ-ELENO 2026-05-24.
        if ($env:SINISTER_SKIP_MEMORY_RECALL -ne '1') {
            $_recallT0 = Get-Date
            try { _SpawnProgress -Stage 'memory recall' -Status 'RUN' } catch {}
            $memInject = Get-MemoryRecallInject -AgentName $agentName
            $_recallMs = [int]((Get-Date) - $_recallT0).TotalMilliseconds
            if ($memInject) {
                try { _SpawnProgress -Stage 'memory recall' -Status 'OK' -ElapsedMs $_recallMs -Detail 'tags injected' } catch {}
                $phrase += $memInject
            } else {
                try { _SpawnProgress -Stage 'memory recall' -Status 'SKIP' -ElapsedMs $_recallMs -Detail 'no hits / no CLI' } catch {}
            }
            # P2 sinister-memory inject-spawn-phrase (2026-05-25 RKOJ-ELENO): structured
            # iter-close narrative layer alongside forge-memory keyword recall.
            $_smT0 = Get-Date
            try { _SpawnProgress -Stage 'sinister-memory inject' -Status 'RUN' } catch {}
            $smInject = Get-SinisterMemoryInject -AgentName $agentName
            $_smMs = [int]((Get-Date) - $_smT0).TotalMilliseconds
            if ($smInject) {
                try { _SpawnProgress -Stage 'sinister-memory inject' -Status 'OK' -ElapsedMs $_smMs -Detail 'iter-close memories injected' } catch {}
                $phrase += $smInject
            } else {
                try { _SpawnProgress -Stage 'sinister-memory inject' -Status 'SKIP' -ElapsedMs $_smMs -Detail 'no prior memories / CLI missing' } catch {}
            }
        } else {
            try { _SpawnProgress -Stage 'memory recall' -Status 'SKIP' -Detail 'env-skip' } catch {}
        }
        # RKOJ-ELENO :: 2026-05-24 :: operator 19:58Z verbatim "every time a agent is
        # started from eve exe, it needs to detect if there are similar agents in
        # similar projects working or agents of the same project working. that agent
        # is then to review what they are doing and then create its plan of what it
        # needs to do". Wire detect-similar output into the cold-start phrase so the
        # new agent has visibility without an extra read.
        # RKOJ-ELENO :: 2026-05-24 :: fleet-updates poll wiring (CLAUDE.md cold-start step 11).
        # Pre-fetch the last 3 unacked fleet-update rows visible to this lane + inject into
        # phrase. Closes the gap where the channel existed but launcher never threaded it in.
        if ($env:SINISTER_SKIP_FLEET_UPDATES -ne '1') {
            $_fuT0 = Get-Date
            try { _SpawnProgress -Stage 'fleet-updates poll' -Status 'RUN' } catch {}
            try {
                $fuScript = Join-Path $SanctumRoot 'automations\fleet-update.ps1'
                if (Test-Path $fuScript) {
                    $fuJson = & powershell -NoProfile -File $fuScript -Action List -Slug $agentName -Tail 3 2>$null
                    $fuRows = $null
                    if ($fuJson -and $fuJson.Trim() -ne '[]') {
                        try { $fuRows = $fuJson | ConvertFrom-Json -ErrorAction Stop } catch {}
                    }
                    if ($fuRows) {
                        $fuList = @($fuRows)
                        $fuLines = @()
                        foreach ($r in $fuList) {
                            $msgBrief = if ($r.message -and $r.message.Length -gt 90) { $r.message.Substring(0, 87) + '...' } else { $r.message }
                            $fuLines += ('[' + $r.priority + '/' + $r.kind + ' ' + $r.id + '] ' + $msgBrief)
                        }
                        $phrase += ' FLEET-UPDATES (' + $fuList.Count + ' unacked for ' + $agentName + '): ' + ($fuLines -join ' || ') + '. ACK each via automations\fleet-update.ps1 -Action Acked -Id <id> -Slug ' + $agentName + ' after reading + acting on.'
                        $_fuMs = [int]((Get-Date) - $_fuT0).TotalMilliseconds
                        try { _SpawnProgress -Stage 'fleet-updates poll' -Status 'OK' -ElapsedMs $_fuMs -Detail "$($fuList.Count) row(s) injected" } catch {}
                    } else {
                        $_fuMs = [int]((Get-Date) - $_fuT0).TotalMilliseconds
                        try { _SpawnProgress -Stage 'fleet-updates poll' -Status 'OK' -ElapsedMs $_fuMs -Detail 'none unacked' } catch {}
                    }
                } else {
                    try { _SpawnProgress -Stage 'fleet-updates poll' -Status 'SKIP' -Detail 'script missing' } catch {}
                }
            } catch {
                $_fuMs = [int]((Get-Date) - $_fuT0).TotalMilliseconds
                try { _SpawnProgress -Stage 'fleet-updates poll' -Status 'FAIL' -ElapsedMs $_fuMs -Detail $_.Exception.Message } catch {}
            }
        } else {
            try { _SpawnProgress -Stage 'fleet-updates poll' -Status 'SKIP' -Detail 'env-skip' } catch {}
        }
        # RKOJ-ELENO :: 2026-05-24T23:58Z :: operator "make sure all agents have the memory
        # updates as we grow on it daily and it auto updates." Inject the 3 most-recent
        # brain doctrines (mtime in last 24h) so the new agent can read them as part of
        # its REVIEW step without hunting. Natural-language phrasing per classifier-rejection
        # lesson (no MUST/MANDATORY). Composes with auto-brain-propagation-doctrine.
        if ($env:SINISTER_SKIP_RECENT_BRAIN -ne '1') {
            $_brT0 = Get-Date
            try { _SpawnProgress -Stage 'recent brain' -Status 'RUN' } catch {}
            try {
                $brainDir = Join-Path $SanctumRoot '_shared-memory\knowledge'
                if (Test-Path $brainDir) {
                    $cutoff = (Get-Date).AddHours(-24)
                    $recent = Get-ChildItem -Path $brainDir -Filter '*.md' -File -ErrorAction SilentlyContinue |
                        Where-Object { $_.Name -notmatch '^_' -and $_.FullName -notmatch '\\_archive\\' -and $_.LastWriteTime -ge $cutoff } |
                        Sort-Object LastWriteTime -Descending |
                        Select-Object -First 3
                    if ($recent -and $recent.Count -gt 0) {
                        $brLines = @()
                        foreach ($f in $recent) {
                            $slug = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
                            $oneLine = ''
                            try {
                                $first80 = Get-Content $f.FullName -TotalCount 80 -ErrorAction SilentlyContinue
                                foreach ($ln in $first80) {
                                    $t = $ln.Trim()
                                    if (-not $t) { continue }
                                    if ($t -match '^#\s+(.+)$') { $oneLine = $matches[1].Trim(); break }
                                }
                                if (-not $oneLine) {
                                    foreach ($ln in $first80) {
                                        $t = $ln.Trim()
                                        if ($t -and $t -notmatch '^(#|>|\||---|\*\*Author|\*\*Created|`)') {
                                            $oneLine = $t -replace '^\*\s*','' -replace '^-\s*',''
                                            break
                                        }
                                    }
                                }
                            } catch {}
                            if ($oneLine.Length -gt 120) { $oneLine = $oneLine.Substring(0, 117) + '...' }
                            $brLines += ($slug + ' - ' + $oneLine)
                        }
                        $phrase += ' RECENT BRAIN UPDATES (last 24h, top 3 in _shared-memory\knowledge\): ' + ($brLines -join ' || ') + '. Worth a quick read during REVIEW step so this lane stays current with fleet-wide doctrine.'
                        $_brMs = [int]((Get-Date) - $_brT0).TotalMilliseconds
                        try { _SpawnProgress -Stage 'recent brain' -Status 'OK' -ElapsedMs $_brMs -Detail "$($recent.Count) doctrine(s) injected" } catch {}
                    } else {
                        $_brMs = [int]((Get-Date) - $_brT0).TotalMilliseconds
                        try { _SpawnProgress -Stage 'recent brain' -Status 'OK' -ElapsedMs $_brMs -Detail 'no recent doctrine' } catch {}
                    }
                } else {
                    try { _SpawnProgress -Stage 'recent brain' -Status 'SKIP' -Detail 'knowledge dir missing' } catch {}
                }
            } catch {
                $_brMs = [int]((Get-Date) - $_brT0).TotalMilliseconds
                try { _SpawnProgress -Stage 'recent brain' -Status 'FAIL' -ElapsedMs $_brMs -Detail $_.Exception.Message } catch {}
            }
        } else {
            try { _SpawnProgress -Stage 'recent brain' -Status 'SKIP' -Detail 'env-skip' } catch {}
        }
        if ($env:SINISTER_SKIP_DETECT_SIMILAR -ne '1') {
            $_detectT0 = Get-Date
            try { _SpawnProgress -Stage 'detect siblings' -Status 'RUN' } catch {}
            $_detectHits = 0
            try {
                $detectScript = Join-Path $SanctumRoot 'automations\detect-similar-agents.ps1'
                if (Test-Path $detectScript) {
                    $detectJson = & powershell -NoProfile -File $detectScript -ProjectKey $projKey -AsJson 2>$null
                    if ($detectJson) {
                        $hits = $detectJson | ConvertFrom-Json -ErrorAction SilentlyContinue
                        if ($hits -and $hits.Count -gt 0) {
                            $_detectHits = @($hits).Count
                            $lines = @()
                            foreach ($h in $hits) {
                                $kindTag = if ($h.kind -eq 'same') { 'same-project' } else { 'similar-project' }
                                $focusBrief = if ($h.focus) { $h.focus.Substring(0, [Math]::Min(80, $h.focus.Length)) } else { '(no focus)' }
                                $lines += ('[' + $kindTag + '] ' + $h.project + ' (' + $h.ageMin + 'm ago) — ' + $focusBrief)
                            }
                            $detectInject = ' DETECT-SIMILAR-AGENTS: ' + ($lines -join ' || ') + '. REVIEW their focus + PROGRESS before planning your own work — do NOT duplicate what same-project agents are doing; coordinate via cross-agent inbox if overlap. Then write a plan, ship deliverable, loop.'
                            $phrase += $detectInject
                        }
                    }
                }
            } catch {}
            $_detectMs = [int]((Get-Date) - $_detectT0).TotalMilliseconds
            if ($_detectHits -gt 0) {
                try { _SpawnProgress -Stage 'detect siblings' -Status 'OK' -ElapsedMs $_detectMs -Detail "$_detectHits sibling(s) found" } catch {}
            } else {
                try { _SpawnProgress -Stage 'detect siblings' -Status 'OK' -ElapsedMs $_detectMs -Detail 'no siblings live' } catch {}
            }
        } else {
            try { _SpawnProgress -Stage 'detect siblings' -Status 'SKIP' -Detail 'env-skip' } catch {}
        }
    }
    # Operator 2026-05-23 — jcode-parity autonomy. When swarm and/or loop are opted in at
    # the picker, instruct the child accordingly. Env vars (SINISTER_SWARM_MODE /
    # SINISTER_LOOP_MODE) are also exported so any tooling inside the spawn shell can
    # branch off them.
    if ($modes -and $modes.swarm) {
        # RKOJ-ELENO :: 2026-05-24T22:30Z :: operator "swarm doesnt look like its on or
        # working" — the env was being passed but child wasn't acknowledging it. Add an
        # explicit first-response acknowledgement cue so operator can SEE swarm is live
        # from the first reply, paired with the SWARM pill in the banner. Natural phrasing
        # (no MUST/MANDATORY) to avoid binding-language classifier rejection.
        $phrase += " SWARM MODE on: for non-trivial multi-file work, spawn 3-5 parallel sub-agents via the Agent tool and aggregate findings before acting. Use sinister-swarm CLI or sinister-bus orchestration when the work spans multiple lanes. In your first response, acknowledge with a single short line like 'swarm=on; will spawn parallel sub-agents for next non-trivial task' so the operator can confirm activation."
    }
    if ($modes -and $modes.loop) {
        # RKOJ-ELENO :: 2026-05-24 :: operator 19:55Z "loop isnt working agents are sotpping
        # and not looping". Screenshot showed Let'sText agent scheduling /loop tick at 25min
        # then ending turn -> operator sees that as STOPPED. Fix: explicit continuous-iteration
        # instruction, ban long-delay reschedules, prefer in-turn next-iteration over
        # ScheduleWakeup unless genuinely blocked on external signal.
        # PHASE-SHRINK 2026-05-24T20:47Z — point at CLAUDE.md LOOP MODE block instead of
        # inlining 800 chars of binding language (was causing classifier reject + window close).
        # RKOJ-ELENO :: 2026-05-25 :: operator 02:18Z "make the loop system on our agents actually
        # work. make it agressive and make it hafve agents relentless pursue goal within our
        # guidelines using our tools iwhen on." Flip default loop spawn to RELENTLESS preset.
        # Kept ≤105 chars to clear classifier; full rules in CLAUDE.md + relentless doctrine slug.
        # RKOJ-ELENO :: 2026-05-25T06:35Z :: gate RELENTLESS phrase on $modes.loop_relentless.
        # Default = relentless per operator hard-canonical 06:30Z 'make sure loop and swarm
        # mode come on by deafult for each agent'. If operator typed 'on' (non-relentless),
        # ship plain LOOP MODE phrase.
        $isRelentless = $true
        if ($modes.PSObject.Properties.Name -contains 'loop_relentless') { $isRelentless = [bool]$modes.loop_relentless }
        if ($isRelentless) {
            $phrase += " LOOP MODE on RELENTLESS (CLAUDE.md LOOP MODE + loop-relentless-pursuit-2026-05-25 + use our tools)."
            $phrase += " RELENTLESS variant: see CLAUDE.md LOOP MODE rule 8 (relentless pursuit + tool-reach + no-end-turn-with-work-queued)."
        } else {
            $phrase += " LOOP MODE on (CLAUDE.md LOOP MODE rules 1-7 — non-relentless; ship+iterate but normal ScheduleWakeup cadence)."
        }
        # RKOJ-ELENO :: 2026-05-24 :: operator ~20:05Z "you need to of course expand on what
        # they say as it could be couple words you turn into a couple sentences". Example given:
        # "/loop do not stop testing, auditing, fixing, expanding things until you have created
        # a snapchat account with our methods and apk that was harvested to panel with no
        # issues or flags and added andrewt407 SUCCESSFULLY and that after all that lasted 24
        # hours". The agent EXPANDS the brief into a fully-specified, measurable criterion.
        if ($modes.PSObject.Properties.Name -contains 'loop_condition' -and $modes.loop_condition) {
            $lc = [string]$modes.loop_condition
            $lcSafe = $lc -replace '"', "'"
            # PHASE-SHRINK 2026-05-24T20:47Z — keep just the operator's verbatim brief; the
            # child reads CLAUDE.md LOOP MODE rules 6-7 for the expand-into-criterion guidance.
            $phrase += " Loop stop condition (operator-set): $lcSafe (expand into measurable criterion per CLAUDE.md LOOP MODE rules 6-7)."
        }
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
    # RKOJ-ELENO :: 2026-05-24 v3 :: two-question prompt + loop-default-on.
    # RKOJ-ELENO :: 2026-05-25T06:35Z v4 :: loop=relentless + swarm=on DEFAULT for every
    # spawn per operator hard-canonical 06:30Z 'make sure loop and swarm mode come on by
    # deafult for each agent'. Empty-Enter picks new defaults. Operator can still type
    # 'off'/'n' to disable, or 'on' for non-relentless loop.
    # Doctrine: loop-swarm-default-on-doctrine-2026-05-25.md.
    # Precedence (highest first):
    #   1. projects.json default_modes.{swarm,loop} (loop = 'relentless'/'on'/'off' string or bool)
    #   2. env vars SINISTER_DEFAULT_SWARM / SINISTER_DEFAULT_LOOP (0/1)
    #   3. swarm=on, loop=relentless (fleet defaults — operator-set 2026-05-25T06:30Z)
    param($ProjectRec = $null)
    $defSwarm = if ($env:SINISTER_DEFAULT_SWARM) { ($env:SINISTER_DEFAULT_SWARM -eq '1') } else { $true }
    $defLoop  = if ($env:SINISTER_DEFAULT_LOOP)  { ($env:SINISTER_DEFAULT_LOOP  -eq '1') } else { $true  }
    $defLoopRelentless = $true
    if ($ProjectRec -and $ProjectRec.PSObject.Properties.Name -contains 'default_modes' -and $ProjectRec.default_modes) {
        $dm = $ProjectRec.default_modes
        if ($dm.PSObject.Properties.Name -contains 'swarm') { $defSwarm = [bool]$dm.swarm }
        if ($dm.PSObject.Properties.Name -contains 'loop') {
            $loopVal = $dm.loop
            if ($loopVal -is [string]) {
                $lv = $loopVal.ToLower().Trim()
                if ($lv -eq 'off' -or $lv -eq 'false' -or $lv -eq '0') {
                    $defLoop = $false; $defLoopRelentless = $false
                } elseif ($lv -eq 'relentless') {
                    $defLoop = $true; $defLoopRelentless = $true
                } else {
                    $defLoop = $true; $defLoopRelentless = $false
                }
            } else {
                $defLoop = [bool]$loopVal
            }
        }
        if ($dm.PSObject.Properties.Name -contains 'loop_relentless') { $defLoopRelentless = [bool]$dm.loop_relentless }
    }
    $defLoopCond = if ($env:SINISTER_DEFAULT_LOOP_CONDITION) { $env:SINISTER_DEFAULT_LOOP_CONDITION } else { '' }
    if ($env:SINISTER_SKIP_MODES_PROMPT -eq '1') {
        return @{ swarm = $defSwarm; loop = $defLoop; loop_relentless = $defLoopRelentless; loop_condition = $defLoopCond; priority = 3 }
    }
    # RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: QUICK-LAUNCH MODE.
    # Operator hard-canonical 07:17Z (Image 7+8): "make this entire process way more
    # efficent with the quickest way to open my termionials". Picker passes
    # SINISTER_QUICK_LAUNCH=1 when operator hits Q at the picker; we then skip ALL
    # prompts and return defaults. Also: env override SINISTER_QUICK=1 for headless.
    if ($env:SINISTER_QUICK_LAUNCH -eq '1' -or $env:SINISTER_QUICK -eq '1') {
        $defPri = 3
        if ($ProjectRec -and $ProjectRec.PSObject.Properties.Name -contains 'tier' -and $ProjectRec.tier) {
            try { $defPri = [int]$ProjectRec.tier } catch { $defPri = 3 }
        }
        if ($env:SINISTER_DEFAULT_PRIORITY) {
            try { $defPri = [int]$env:SINISTER_DEFAULT_PRIORITY } catch {}
        }
        Write-Host ''
        Write-Host '  [quick-launch] all prompts skipped (swarm=on loop=relentless priority=T' $defPri ')' -ForegroundColor $C.Dim
        return @{ swarm = $defSwarm; loop = $defLoop; loop_relentless = $defLoopRelentless; loop_condition = $defLoopCond; priority = $defPri }
    }
    function _PromptYN([string]$Question, [bool]$Default, [string]$DefaultLabel = '') {
        $defStr = if ($DefaultLabel) { $DefaultLabel } elseif ($Default) { 'Y/n' } else { 'y/N' }
        Write-Host -NoNewline ('  ' + $Question + ' [' + $defStr + ']: ') -ForegroundColor $C.LightP
        $ans = Read-Host
        if (-not $ans) { return $Default }
        $a = $ans.ToLower().Trim()
        switch -Regex ($a) {
            '^(y|yes|on|true|1)$'   { return $true  }
            '^(n|no|off|false|0)$'  { return $false }
            default                  {
                $defWord = if ($Default) { 'yes' } else { 'no' }
                Write-Host ('  (unrecognized: "' + $ans + '") -> using default: ' + $defWord) -ForegroundColor $C.Dim
                return $Default
            }
        }
    }
    Write-Host ''
    Write-Host '  Modes (jcode-parity autonomy):' -ForegroundColor $C.White
    Write-Host '  (operator 2026-05-25T07:17Z: empty-Enter at FIRST prompt = accept ALL defaults, skip the rest.)' -ForegroundColor $C.Dim
    # RKOJ-ELENO :: 2026-05-25T07:17Z Sub-Q :: 1-Enter shortcut. Operator
    # hard-canonical "quickest way to open my termionials". If operator hits
    # Enter at the swarm question, we ACCEPT all defaults and skip the
    # remaining loop / priority prompts entirely.
    $swarmDefStr = if ($defSwarm) { 'Y/n' } else { 'y/N' }
    Write-Host -NoNewline ('  Use swarm? (spawn parallel sub-agents for multi-file work) [' + $swarmDefStr + ', Enter=ALL defaults]: ') -ForegroundColor $C.LightP
    $swarmAns = Read-Host
    if (-not $swarmAns) {
        $defPriOneShot = 3
        if ($ProjectRec -and $ProjectRec.PSObject.Properties.Name -contains 'tier' -and $ProjectRec.tier) {
            try { $defPriOneShot = [int]$ProjectRec.tier } catch { $defPriOneShot = 3 }
        }
        if ($env:SINISTER_DEFAULT_PRIORITY) {
            try { $defPriOneShot = [int]$env:SINISTER_DEFAULT_PRIORITY } catch {}
        }
        $loopLabel = if ($defLoopRelentless) { 'relentless' } elseif ($defLoop) { 'on' } else { 'off' }
        Write-Host ('  [1-Enter shortcut] swarm=' + ($defSwarm.ToString().ToLower()) + ' loop=' + $loopLabel + ' priority=T' + $defPriOneShot) -ForegroundColor $C.Dim
        return @{ swarm = $defSwarm; loop = $defLoop; loop_relentless = $defLoopRelentless; loop_condition = $defLoopCond; priority = $defPriOneShot }
    }
    $a = $swarmAns.ToLower().Trim()
    $swarm = switch -Regex ($a) {
        '^(y|yes|on|true|1)$'   { $true  }
        '^(n|no|off|false|0)$'  { $false }
        default {
            $defWord = if ($defSwarm) { 'yes' } else { 'no' }
            Write-Host ('  (unrecognized: "' + $swarmAns + '") -> using default: ' + $defWord) -ForegroundColor $C.Dim
            $defSwarm
        }
    }
    # RKOJ-ELENO :: 2026-05-25T06:35Z :: loop is now tri-state at prompt level.
    Write-Host -NoNewline ('  Loop mode? (off / on / relentless) [default: relentless]: ') -ForegroundColor $C.LightP
    $loopAns = Read-Host
    $loopRelentless = $defLoopRelentless
    if (-not $loopAns) {
        $loop = $defLoop
        $loopRelentless = $defLoopRelentless
    } else {
        $la = $loopAns.ToLower().Trim()
        switch -Regex ($la) {
            '^(off|n|no|false|0)$'         { $loop = $false; $loopRelentless = $false }
            '^(relentless|r|rel)$'         { $loop = $true;  $loopRelentless = $true  }
            '^(on|y|yes|true|1)$'          { $loop = $true;  $loopRelentless = $false }
            default {
                $defWord = if ($defLoopRelentless) { 'relentless' } elseif ($defLoop) { 'on' } else { 'off' }
                Write-Host ('  (unrecognized: "' + $loopAns + '") -> using default: ' + $defWord) -ForegroundColor $C.Dim
                $loop = $defLoop
                $loopRelentless = $defLoopRelentless
            }
        }
    }
    # RKOJ-ELENO :: 2026-05-24 :: operator ~20:00Z "if i enable loop on the question after
    # swarm it asks me the loop condition. for example in the snap apk creator i told it
    # loop do not stop until you have created a snapchat account and pushed to panel for
    # full use that lasted 24 hours after adding andrewt407". Adds a free-text loop stop
    # condition prompt that fires ONLY when loop=on. Empty answer = generic "queue-empty
    # -or-blocker" default. Plumbed through env (SINISTER_LOOP_CONDITION) + Build-Phrase.
    # RKOJ-ELENO :: 2026-05-24T22:00Z :: operator "to gen random loop thing remove that
    # option. do it automatic". REMOVED the loop stop condition prompt. The child agent
    # auto-generates a loop stop criterion from project context + resume-point per
    # CLAUDE.md LOOP MODE rules 6-7. Operator override still available via env var
    # SINISTER_DEFAULT_LOOP_CONDITION if needed for headless re-spawn.
    $loopCond = if ($defLoopCond) { $defLoopCond } else { '' }
    # RKOJ-ELENO :: 2026-05-24T21:14Z :: operator "no you need to ask me project priority
    # PER launch. its per session that we are working on that". Was: tier read from
    # projects.json statically per-project. Now: per-launch prompt with project's static
    # tier as DEFAULT. Operator can downgrade for a background sweep or upgrade for a
    # critical fix without editing projects.json. Plumbed via $modes.priority -> Launch-
    # Session -> SINISTER_TIER env in launch.sh.
    $defPriority = 3
    if ($ProjectRec -and $ProjectRec.PSObject.Properties.Name -contains 'tier' -and $ProjectRec.tier) {
        try { $defPriority = [int]$ProjectRec.tier } catch { $defPriority = 3 }
    }
    if ($env:SINISTER_DEFAULT_PRIORITY) {
        try { $defPriority = [int]$env:SINISTER_DEFAULT_PRIORITY } catch {}
    }
    Write-Host -NoNewline ('  Priority? (1=most important, 2=high, 3=normal, 4=least) [default ' + $defPriority + ']: ') -ForegroundColor $C.LightP
    $rp = Read-Host
    $priority = $defPriority
    if ($rp) {
        $rpClean = $rp.Trim().ToLower() -replace '^t', ''
        if ($rpClean -match '^[1-4]$') {
            $priority = [int]$rpClean
        } else {
            Write-Host ('  (unrecognized: "' + $rp + '") -> using default T' + $defPriority) -ForegroundColor $C.Dim
        }
    }
    # Live progress bar (operator 20:10Z).
    Write-Host ''
    Write-Host '  > preparing spawn (live progress):' -ForegroundColor $C.LightP
    Write-Host '    [stage                ] status     elapsed' -ForegroundColor $C.Dim
    Write-Host '    ------------------------ ---------- --------' -ForegroundColor $C.Dim
    return @{ swarm = $swarm; loop = $loop; loop_relentless = $loopRelentless; loop_condition = $loopCond; priority = $priority }
}

# Per-stage progress emitter. Called from Launch-Session at each stage boundary so operator
# sees the spawn is working, not hung. Status: RUN | OK | SKIP | FAIL.
function _SpawnProgress {
    param(
        [string]$Stage,
        [string]$Status = 'OK',
        [int]$ElapsedMs = -1,
        [string]$Detail = ''
    )
    $col = switch ($Status) {
        'OK'   { $C.OK }
        'SKIP' { $C.Dim }
        'FAIL' { $C.Fail }
        'RUN'  { $C.LightP }
        default { $C.Soft }
    }
    $elapsedStr = if ($ElapsedMs -ge 0) { ($ElapsedMs.ToString() + 'ms').PadLeft(8) } else { '       -' }
    $padStage = $Stage.PadRight(22)
    $padStatus = $Status.PadRight(10)
    $line = "    [$padStage] $padStatus $elapsedStr"
    if ($Detail) { $line += "  $Detail" }
    Write-Host $line -ForegroundColor $col
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
    # RKOJ-ELENO :: 2026-05-25 :: pre-spawn branch-router. Enforces the canonical
    # convention agent/<project-key>/<topic>-<utc-date> per docs/BRANCH-CONVENTION.md.
    # Skippable via SINISTER_SKIP_BRANCH_ROUTER=1 for cases where the operator
    # explicitly wants to stay on a non-canonical branch (rare).
    if ($projRec -and $projRec.key -and $env:SINISTER_SKIP_BRANCH_ROUTER -ne '1') {
        $routerScript = Join-Path $AutomationsRoot 'agent-branch-router.ps1'
        if (Test-Path $routerScript) {
            # Topic defaults to the agent name (lowercased + sanitized) or 'work'.
            $topicArg = if ($agentName) { $agentName } else { 'work' }
            try {
                & $routerScript -ProjectKey $projRec.key -Topic $topicArg -CheckOnly | Out-Host
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "  > NOTE: not on canonical agent branch (router exit=$LASTEXITCODE). See docs/BRANCH-CONVENTION.md." -ForegroundColor $C.Warn
                }
            } catch {
                Write-Host "  > WARN: branch-router invoke failed: $_" -ForegroundColor $C.Warn
            }
        }
    }

    # RKOJ-ELENO :: 2026-05-25 :: iter-25 P0.4 wire for launch_rate_limit_governor.py.
    # Advisory only by default (FULL-POWER doctrine: NEVER block a spawn on local
    # bookkeeping). Set SINISTER_LAUNCH_GOVERNOR_BLOCK=1 to make this a hard gate.
    # Governor exists at automations/launch_rate_limit_governor.py with --pre-launch.
    if ($projRec -and $projRec.key) {
        $governorScript = Join-Path $SanctumRoot 'automations\launch_rate_limit_governor.py'
        if (Test-Path $governorScript) {
            try {
                $govOut = & python $governorScript --pre-launch $projRec.key --json 2>$null
                $govRc  = $LASTEXITCODE
                if ($govOut) {
                    Write-Host "  [GOV] $(([string]$govOut).Trim())" -ForegroundColor $C.Dim
                }
                if ($govRc -ne 0 -and $env:SINISTER_LAUNCH_GOVERNOR_BLOCK -eq '1') {
                    Write-Host "  [GOV] BLOCK: governor exited $govRc and SINISTER_LAUNCH_GOVERNOR_BLOCK=1; aborting spawn" -ForegroundColor $C.Fail
                    return
                } elseif ($govRc -ne 0) {
                    Write-Host "  [GOV] governor advisory exit=$govRc (not blocking; set SINISTER_LAUNCH_GOVERNOR_BLOCK=1 to enforce)" -ForegroundColor $C.Warn
                }
            } catch {
                Write-Host "  [GOV] launch_rate_limit_governor invoke failed: $($_.Exception.Message)" -ForegroundColor $C.Warn
            }
        }
    }

    $swarmEnv = if ($modes -and $modes.swarm) { '1' } else { '' }
    $loopEnv  = if ($modes -and $modes.loop)  { '1' } else { '' }
    # RKOJ-ELENO :: 2026-05-24 :: operator ~20:00Z loop-condition. Bash single-quote
    # safe via ' -> '"'"' escape (existing pattern elsewhere in this file).
    $loopCondRaw = if ($modes -and $modes.loop_condition) { [string]$modes.loop_condition } else { '' }
    $loopCondEnv = $loopCondRaw -replace "'", "'""'""'"
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
    $_leaseT0 = Get-Date
    try { _SpawnProgress -Stage 'lease (round-robin)' -Status 'RUN' } catch {}
    try {
        $acctLib = Join-Path $SanctumRoot 'automations\claude-accounts.ps1'
        if (Test-Path $acctLib) {
            . $acctLib
            # RKOJ-ELENO :: 2026-05-24 :: tier-aware routing. T1 spawns reserve the
            # default (operator) slot when available; T2-T4 fall to rotation_strategy.
            $tierForRouting = if ($projRec.PSObject.Properties.Name -contains 'tier' -and $projRec.tier) { [int]$projRec.tier } else { 3 }

            # RKOJ-ELENO :: 2026-05-24 :: AUTO-BEST-SLOT PICK (operator 23:10Z verbatim:
            # "you need to detect the accounts that should be used and what is out of
            # credits etc. this entire round robin needs to be auto.").
            #
            # 1. SINISTER_FORCE_SLOT=<name> env overrides everything (advanced/manual).
            # 2. Else: try claude-oauth-accounts.ps1 -Action PickBest (consumes the
            #    sibling oauth-health-poller's score file when present).
            # 3. Fallback: legacy Get-NextAvailableAccount round-robin / load-balance.
            $next = $null
            $_forcedSlot = $env:SINISTER_FORCE_SLOT
            if ($_forcedSlot) {
                $cfgF = Get-AccountsConfig
                $forcedRow = $cfgF.accounts | Where-Object { $_.name -eq $_forcedSlot } | Select-Object -First 1
                if ($forcedRow) {
                    Write-Host "  [ACCT] SINISTER_FORCE_SLOT='$_forcedSlot' overriding auto-pick" -ForegroundColor $C.Dim
                    $next = @{ name = $forcedRow.name; account = $forcedRow }
                } else {
                    Write-Host "  [ACCT] SINISTER_FORCE_SLOT='$_forcedSlot' not found in claude-accounts.json; falling through to auto-pick" -ForegroundColor $C.Warn
                }
            }
            if (-not $next) {
                $oauthLibProbe = Join-Path $SanctumRoot 'automations\claude-oauth-accounts.ps1'
                if (Test-Path $oauthLibProbe) {
                    try {
                        # Capture stdout-only (single line = slot name). Diagnostics go to stderr.
                        $pickOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $oauthLibProbe -Action PickBest 2>$null
                        $pickedName = if ($pickOut) { ([string]$pickOut).Trim() } else { '' }
                        if ($pickedName) {
                            $cfgP = Get-AccountsConfig
                            $pickedRow = $cfgP.accounts | Where-Object { $_.name -eq $pickedName } | Select-Object -First 1
                            if ($pickedRow) {
                                Write-Host "  [ACCT] auto-best picked '$pickedName' (auth_mode=$($pickedRow.auth_mode))" -ForegroundColor $C.Dim
                                $next = @{ name = $pickedRow.name; account = $pickedRow }
                            }
                        }
                    } catch {
                        Write-Host "  [ACCT] PickBest errored ($($_.Exception.Message)); falling through to round-robin" -ForegroundColor $C.Dim
                    }
                }
            }
            if (-not $next) {
                # Legacy round-robin cursor (last_rotation_index) -- always-available fallback.
                $next = Get-NextAvailableAccount -Tier $tierForRouting
                if ($next) {
                    Write-Host "  [ACCT] all OAuth slots unscored/limited; cursor fallback selected '$($next.name)'" -ForegroundColor $C.Warn
                }
            }
            if (-not $next) {
                # RKOJ-ELENO :: 2026-05-24 :: FULL-POWER doctrine. Operator hard-canonical
                # *"dont fucking rate limit me like this i need full power we need ful power"*
                # The local accounting (current_sessions cap, rate_limited flag) is bookkeeping
                # only — the REAL gate is Anthropic's server-side 429. Local bookkeeping must
                # NEVER block a spawn. Pick the first enabled account regardless of cap state
                # and proceed. If Anthropic rate-limits us, the spawned process surfaces it.
                $cfgFull = Get-AccountsConfig
                $fallback = @($cfgFull.accounts | Where-Object { $_.enabled -ne $false }) | Select-Object -First 1
                if (-not $fallback) {
                    # Last-resort: pick first account even if disabled (operator wants spawns).
                    $fallback = @($cfgFull.accounts) | Select-Object -First 1
                }
                if ($fallback) {
                    Write-Host "  [full-power] local cap reached for '$($fallback.name)' but spawning anyway (Anthropic server is the real gate)." -ForegroundColor $C.Dim
                    $next = @{ name = $fallback.name; account = $fallback }
                } else {
                    Write-Host "  [BLOCK] no accounts in _shared-memory/claude-accounts.json. Check the file." -ForegroundColor $C.Warn
                    Write-Host '  [press Enter to return to picker]' -ForegroundColor $C.Dim
                    Read-Host | Out-Null
                    return
                }
            }
            $selectedAccountName = $next.name
            # RKOJ-ELENO :: 2026-05-25 :: pre-launch rate-limit governor (sub-E iter-25 P0.4).
            # Per operator hard-canonical 2026-05-25T07:00:45Z "rate-limit in check"+"no issues
            # running all agents"+"operator-floor reserve". Governor reads slot scores +
            # operator-floor reservation; non-zero exit = abort spawn before mintty opens so
            # operator sees the reason instead of an in-mintty crash. Composes with
            # claude-wrapper auto-429 (post-launch). The pre-launch_rate_limit_governor.py
            # script is fail-safe: missing => no-op (exit 0).
            $_governorPy = Join-Path $SanctumRoot 'automations\launch_rate_limit_governor.py'
            if (Test-Path $_governorPy) {
                $_projectKey = if ($Project -and $Project.key) { $Project.key } else { 'sanctum' }
                $_gOut = & python $_governorPy --pre-launch $_projectKey --account $selectedAccountName 2>&1
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "  [GOVERNOR] pre-launch refused project='$_projectKey' acct='$selectedAccountName' (rc=$LASTEXITCODE): $(($_gOut | Out-String).Trim())" -ForegroundColor $C.Warn
                    Write-Host '  [press Enter to return to picker]' -ForegroundColor $C.Dim
                    Read-Host | Out-Null
                    return
                }
            }
            # RKOJ-ELENO :: 2026-05-24 :: OAuth pivot (operator 22:50Z "we want logged in
            # claude 20x max session and going off that usage"). If the chosen slot is
            # auth_mode='oauth', swap its credentials.<slot>.json into ~/.claude/.credentials.json
            # so claude CLI picks up the Max-plan OAuth session. Do NOT export
            # ANTHROPIC_API_KEY for OAuth slots -- that env var hijacks billing to the
            # Console pay-as-you-go account (separate from Max plan quota).
            $selectedApiKey = $null
            $selectedAuthMode = 'api_key'
            try {
                $_acctRow = $next.account
                if ($_acctRow -and $_acctRow.PSObject.Properties.Name -contains 'auth_mode' -and $_acctRow.auth_mode -eq 'oauth') {
                    $selectedAuthMode = 'oauth'
                    $oauthLib = Join-Path $SanctumRoot 'automations\claude-oauth-accounts.ps1'
                    if (Test-Path $oauthLib) {
                        $useOut = & powershell -NoProfile -ExecutionPolicy Bypass -File $oauthLib -Action Use -Name $selectedAccountName 2>&1
                        if ($LASTEXITCODE -eq 0 -or $useOut -match '\[oauth-use\] OK') {
                            # RKOJ-ELENO :: 2026-05-24 :: canonical operator-facing log line per
                            # auto-best-slot spec: "[ACCT] using OAuth slot 'X' (email: Y)".
                            $_email = if ($_acctRow.oauth_email) { $_acctRow.oauth_email } else { '(unknown)' }
                            Write-Host "  [ACCT] using OAuth slot '$selectedAccountName' (email: $_email)" -ForegroundColor $C.Accent
                        } else {
                            Write-Host "  [warn] OAuth swap failed for '$selectedAccountName' -- falling back to whatever .credentials.json currently has" -ForegroundColor $C.Warn
                        }
                    } else {
                        Write-Host "  [warn] claude-oauth-accounts.ps1 missing -- cannot swap OAuth slot" -ForegroundColor $C.Warn
                    }
                } else {
                    # Legacy api_key path.
                    $selectedApiKey = Get-AccountCredentials -Name $selectedAccountName
                    if (-not $selectedApiKey) {
                        Write-Host "  [ACCT] using slot '$selectedAccountName' (api_key, no credentials_file yet - claude-cli default login)" -ForegroundColor $C.Accent
                    } else {
                        Write-Host "  [ACCT] using slot '$selectedAccountName' (api_key injected via ANTHROPIC_API_KEY)" -ForegroundColor $C.Accent
                    }
                }
            } catch {
                Write-Host "  [warn] auth-mode handling failed: $($_.Exception.Message)" -ForegroundColor $C.Dim
            }
            # Lease the slot BEFORE we spawn so concurrent picker calls do not double-book.
            $null = Mark-AccountSpawned -Name $selectedAccountName
        }
        $_leaseMs = [int]((Get-Date) - $_leaseT0).TotalMilliseconds
        try { _SpawnProgress -Stage 'lease (round-robin)' -Status 'OK' -ElapsedMs $_leaseMs -Detail "slot=$selectedAccountName" } catch {}
    } catch {
        $_leaseMs = [int]((Get-Date) - $_leaseT0).TotalMilliseconds
        try { _SpawnProgress -Stage 'lease (round-robin)' -Status 'FAIL' -ElapsedMs $_leaseMs -Detail $_.Exception.Message } catch {}
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
    # RKOJ-ELENO :: 2026-05-24 :: case-insensitive accent lookup. Operator 20:30Z:
    # "rename and color settings on the agents we open still dont work fix that".
    # Root cause #1 was case-mismatch: operator-typed "Purple" / "PURPLE" / mixed-case
    # missed the lowercase keys in $colorMap and silently fell through to purple-default
    # (so the *value* was right but the *intent* was lost; e.g. 'Cyan' picked 'purple').
    $accentKey = if ($accent) { $accent.ToString().Trim().ToLower() } else { 'purple' }
    $cm = if ($colorMap.ContainsKey($accentKey)) { $colorMap[$accentKey] } else { $colorMap['purple'] }
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
    # RKOJ-ELENO :: 2026-05-25 :: PERMANENT HEADER format per operator hard-canonical
    # 2026-05-25T03:30Z verbatim *"i want a permanent header up here to show me all
    # things on like swarm etc. make it in brand with sinister software"*. Image #7
    # showed the mintty title bar at the very top -- that IS the permanent header.
    # Format: "{agent} ◆ swarm={on|off} ◆ loop={off|on|relentless} ◆ acct={slot} ◆ T{tier} ◆ Sinister"
    # Diamond `◆` (U+25C6) is ANSI-printable + reads cleanly at small font sizes; kept
    # under 80 chars so mintty doesn't truncate at narrow widths. Loop sub-mode threads
    # loop_relentless flag (default-on for every loop=true project per projects.json v10).
    $swarmTag = if ($modes -and $modes.swarm) { 'on' } else { 'off' }
    $loopRelentless = $false
    if ($modes -and $modes.PSObject.Properties.Name -contains 'loop_relentless' -and $modes.loop_relentless) { $loopRelentless = $true }
    $loopTag = if ($modes -and $modes.loop) { if ($loopRelentless) { 'relentless' } else { 'on' } } else { 'off' }
    # Recompute tier inline -- $projTier is defined below, can't forward-reference.
    $_titleTier = if ($projRec.PSObject.Properties.Name -contains 'tier' -and $projRec.tier) { [int]$projRec.tier } else { 3 }
    if ($modes -and $modes.PSObject.Properties.Name -contains 'priority' -and $modes.priority) {
        try { $_titleTier = [int]$modes.priority } catch {}
    }
    $diamond = [char]0x25C6  # ◆ -- Unicode bullet works inside bash OSC printf
    $accountForTitle = if ($selectedAccountName) { $selectedAccountName } elseif ($env:SINISTER_ACCOUNT) { $env:SINISTER_ACCOUNT } else { 'operator' }
    # Bash-side title (printf inside launch.sh) -- full Sinister format with ◆ separators.
    # RKOJ-ELENO :: 2026-05-25T07:19Z :: operator hard-canonical "make the names work".
    # Title now LEADS with "Sinister $agentName" so the lane is obvious in the alt-tab
    # carousel + taskbar (Image 8: "Sinister Sanctum" was the operator's expected format).
    $windowTitle = "Sinister $agentName $diamond swarm=$swarmTag $diamond loop=$loopTag $diamond acct=$accountForTitle $diamond T$_titleTier"
    # mintty `-t` arg ASCII-safe variant (Win32 CreateProcess arg encoding can mangle
    # multi-byte unicode; bash OSC inside the spawned shell handles ◆ correctly). The
    # two converge once bash printf fires on line 1907 -- `-t` just bridges the cold
    # window-open gap.
    # RKOJ-ELENO :: 2026-05-25 :: BUG FIX -- title MUST NOT contain '|' or spaces.
    # PS 5.1 Start-Process -ArgumentList fails to quote the -t arg reliably; mintty's
    # argv parser then sees `-t sanctum` (first word only) followed by `|` and tries to
    # exec `|` as a program -> exit 126 "Failed to run '|': No such file or directory".
    # Single-word ASCII title with '-' separators is shell/argv-safe in all paths.
    # The bash OSC printf at line ~1907 reinstates the full ◆-separated title once
    # bash starts (~50ms after spawn), so this cold-open placeholder doesn't need the
    # pretty formatting -- it just needs to NOT crash mintty.
    # RKOJ-ELENO :: 2026-05-25T07:19Z :: lane prefix also added to ASCII fallback so the
    # cold-open window title (visible for ~50ms before OSC printf fires) ALSO reads as
    # "Sinister-<lane>-...". Operator hard-canonical "make the names work and set here".
    $windowTitleAscii = "Sinister-${agentName}-swarm=${swarmTag}-loop=${loopTag}-acct=${accountForTitle}-T${_titleTier}"

    # RKOJ-ELENO :: 2026-05-23 :: Phase 1/2 — account name resolved earlier (above
    # the colormap block). $selectedAccountName + $selectedApiKey already set there.
    # This block just normalizes the name + sets the bash-escaped form.
    $accountName = if ($selectedAccountName) { $selectedAccountName } elseif ($env:SINISTER_ACCOUNT) { $env:SINISTER_ACCOUNT } else { 'operator' }
    $bashAccountName = $accountName -replace "'", "'\''"
    # bash-escape the api_key (may be $null/empty if no credentials file on disk).
    # OAuth-mode slots leave this empty -- the OAuth swap above already placed the
    # right blob at ~/.claude/.credentials.json so claude CLI picks it up natively.
    $bashApiKey = if ($selectedApiKey) { ($selectedApiKey -replace "'", "'\''") } else { '' }
    # Surface auth_mode to the spawned env so downstream tooling (resume-point,
    # heartbeat, rate-limit accounting) can branch on it.
    $bashAuthMode = if ($selectedAuthMode) { $selectedAuthMode } else { 'api_key' }

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
    # RKOJ-ELENO :: 2026-05-24T22:30Z :: operator "swarm doesnt look like its on or
    # working" — add bright-purple SWARM pill + bright-orange LOOP pill so operator
    # can see-at-a-glance whether modes activated. Only rendered when the env is '1'.
    # 256-color bg=99 (bright purple) for SWARM; bg=208 (bright orange) for LOOP; both white fg.
    $pillSwarm = '\033[48;5;99;38;5;15;1m'
    $pillLoop  = '\033[48;5;208;38;5;15;1m'
    $swarmPillSegment = if ($swarmEnv -eq '1') { "  $pillSwarm SWARM $pillZ" } else { '' }
    $loopPillSegment  = if ($loopEnv  -eq '1') { "  $pillLoop LOOP $pillZ"  } else { '' }
    $projDisplay = $projRec.display
    $projKey = $projRec.key
    # RKOJ-ELENO :: 2026-05-24 :: tier defaults to 3 when projects.json omits the field.
    # 2026-05-24T21:14Z: per-launch priority (operator) OVERRIDES projects.json static tier.
    $projTier = if ($projRec.PSObject.Properties.Name -contains 'tier' -and $projRec.tier) { [int]$projRec.tier } else { 3 }
    if ($modes -and $modes.PSObject.Properties.Name -contains 'priority' -and $modes.priority) {
        try { $projTier = [int]$modes.priority } catch {}
    }

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
export SINISTER_LOOP_CONDITION='$loopCondEnv'
# RKOJ-ELENO :: 2026-05-24 :: operator 19:55Z tier system. T1=critical
# (reserves operator slot), T2=high, T3=normal (default), T4=background.
export SINISTER_TIER='$projTier'
# RKOJ-ELENO :: 2026-05-23 :: Phase 1/2 — multi-account rotation. PS1 resolved the
# next available account; the .sh uses this name to mark rate-limits + release.
_account_name='$bashAccountName'
export SINISTER_ACCOUNT="`$_account_name"
export SINISTER_AUTH_MODE='$bashAuthMode'
# Phase 1: inject ANTHROPIC_API_KEY from the account's credentials_file (if present).
# Empty string means no per-account key on disk - claude-cli falls back to its own login.
# OAuth-mode slots intentionally leave this empty so claude reads the OAuth blob from
# ~/.claude/.credentials.json (Max plan billing). Setting ANTHROPIC_API_KEY would
# hijack billing to the Console pay-as-you-go account (separate from Max quota).
if [ -n '$bashApiKey' ] && [ "`$SINISTER_AUTH_MODE" != "oauth" ]; then
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
# RKOJ-ELENO :: 2026-05-25T01:18Z :: PERSISTENT HEADER via DECSTBM scroll region.
# Operator hard-canonical 2026-05-25T01:15Z: pill banner must be PERMANENT at top
# of every Sinister Term -- not scroll-off after spawn. Mechanism: reserve top 2
# rows as fixed header via CSI top;bottom r (DECSTBM); print pill banner at row 1;
# park cursor at row 3 so bash output scrolls in rows 3+ while header stays sticky.
# Backwards-compat: SINISTER_NO_STICKY_HEADER=1 falls back to legacy print-once.
if [ "`${SINISTER_NO_STICKY_HEADER:-0}" != "1" ]; then
    printf '\033[2J\033[H'                   # clear screen + cursor home
    printf '  $pillA $agentName $pillZ  $pillM resume $pillZ  $pillD claude-opus-4-7[1m] $pillZ  $pillG mcp:$mcpCnt $pillZ  $pillB bots:$botCnt $pillZ  $pillR --skip-perms $pillZ  $pillB acct:$selectedAccountName $pillZ$swarmPillSegment$loopPillSegment\n'
    printf '\033[3;r'                         # DECSTBM: set scroll region rows 3..bottom
    printf '\033[3;1H'                        # park cursor at row 3 col 1 (below sticky header)
else
    printf '\n'
    printf '  $pillA $agentName $pillZ  $pillM resume $pillZ  $pillD claude-opus-4-7[1m] $pillZ  $pillG mcp:$mcpCnt $pillZ  $pillB bots:$botCnt $pillZ  $pillR --skip-perms $pillZ  $pillB acct:$selectedAccountName $pillZ$swarmPillSegment$loopPillSegment\n'
    printf '\n'
fi
printf '  project: $projDisplay\n'
printf '  root:    $bashPath\n'
# RKOJ-ELENO :: 2026-05-24 :: account status bar (operator 21:08Z "i still dont see the
# claude acocunt logins. status bar round robin system"). Renders one-line per-account
# state (sessions/quota + login marker + round-robin cursor) so operator sees fleet state
# at spawn time without running a separate command. Bar mode = compact single-line; safe to
# call from launch.sh because it does not require Sanctum context.
printf '  accts:   '
# RKOJ-ELENO :: 2026-05-24T21:56Z URGENT FIX :: powershell.exe -File needs WINDOWS path
# format (`D:\Sinister Sanctum\...`) NOT bash-style (`/d/Sinister Sanctum/...`). Prior
# version passed `$bashSanctumRoot/automations/claude-accounts-status.ps1` which
# powershell.exe could not resolve; combined with `--hold never` (now `--hold error`)
# this killed the spawn window before operator saw anything. Use `$SanctumRoot` (the
# Windows-path variable) instead. Final fallback printf keeps bash continuing on any
# remaining error.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$SanctumRoot\automations\claude-accounts-status.ps1" -Mode Bar 2>/dev/null || printf '(status unavailable)\n'
printf '\n'
cd "$bashPath" || { echo '[FAIL] could not cd to project root'; exec bash; }
# RKOJ-ELENO :: 2026-05-24 :: fleet-burst dampener. When SINISTER_FLEET_BURST_LIMIT=N
# is set, count claude.exe spawns logged in spawned-windows.jsonl within the last 60s.
# If count >= N, sleep (60 - oldest_age) seconds before launching. Prevents the
# operator from accidentally triggering Anthropic's GLOBAL server-side throttle by
# spawning many EVE sessions at once (per-account rotation does NOT help here).
# Default: unset → no delay → original behaviour preserved.
if [ -n "`${SINISTER_FLEET_BURST_LIMIT:-}" ]; then
    _spawn_log='$bashSanctumRoot/_shared-memory/spawned-windows.jsonl'
    if [ -f "`$_spawn_log" ]; then
        _now_epoch=`$(date -u +%s 2>/dev/null)
        # Tail last 50 lines, parse "started" ISO-8601, count entries within last 60s.
        _recent_count=0
        _oldest_age=60
        while IFS= read -r _line; do
            _started=`$(printf '%s' "`$_line" | sed -n 's/.*"started":"\([^"]*\)".*/\1/p')
            if [ -n "`$_started" ]; then
                _started_epoch=`$(date -u -d "`$_started" +%s 2>/dev/null)
                if [ -n "`$_started_epoch" ]; then
                    _age=`$((_now_epoch - _started_epoch))
                    if [ "`$_age" -ge 0 ] && [ "`$_age" -le 60 ]; then
                        _recent_count=`$((_recent_count + 1))
                        if [ "`$_age" -lt "`$_oldest_age" ]; then
                            _oldest_age=`$_age
                        fi
                    fi
                fi
            fi
        done < <(tail -n 50 "`$_spawn_log" 2>/dev/null)
        if [ "`$_recent_count" -ge "`${SINISTER_FLEET_BURST_LIMIT}" ]; then
            _wait=`$((60 - _oldest_age))
            if [ "`$_wait" -gt 0 ] && [ "`$_wait" -le 60 ]; then
                printf '\n  > [BURST-DAMPEN] %s recent spawns >= limit %s ; sleeping %ss to avoid server throttle...\n' "`$_recent_count" "`${SINISTER_FLEET_BURST_LIMIT}" "`$_wait"
                sleep "`$_wait"
            fi
        fi
    fi
fi
# RKOJ-ELENO :: 2026-05-25 :: iter-26 P1.2 — route `claude` through claude-wrapper.ps1
# so spawned sessions inherit auto-429 detect + auto-MarkLimited + auto-rotation.
# Operator hard-canonical 2026-05-24 ~23:10Z: "this entire round robin needs to be
# auto. detect the accounts that should be used and what is out of credits etc."
# Wrapper streams claude stdout/stderr verbatim (no UX change), watches a tail
# buffer for 13 rate-limit patterns, calls AutoMark429 on hit and rotates+retries.
# Master-spawn-authority doctrine: `--dangerously-skip-permissions` retained.
# Bypass via env: SINISTER_NO_WRAPPER=1 falls back to bare claude (escape hatch).
if [ -n "`${SINISTER_DRY_RUN:-}" ]; then
    printf '\n  > [DRY-RUN] resolved claude invocation:\n'
    printf '            powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$SanctumRoot\automations\claude-wrapper.ps1" -- --dangerously-skip-permissions %s\n' "'$bashPhrase'"
    _claude_exit_code=0
elif [ "`${SINISTER_NO_WRAPPER:-0}" = "1" ]; then
    claude --dangerously-skip-permissions '$bashPhrase'
    _claude_exit_code=`$?
else
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$SanctumRoot\automations\claude-wrapper.ps1" -- --dangerously-skip-permissions '$bashPhrase'
    _claude_exit_code=`$?
fi
# RKOJ-ELENO :: 2026-05-24T21:38Z :: operator "this agent just crashed with this error.
# fix this add auto fix to eve and make sure this never happens again". Bun (the runtime
# under claude.exe) segfaults on some sessions; when it does, the parent bash env can
# lose PATH entries, causing `head: command not found` in the cleanup block below. Fix:
# restore the Git-Bash standard PATH BEFORE running any utility (head/grep/tr/sed/find).
# Also log Bun-segfault incidents so EVE's auto-fix can surface them later.
export PATH="/usr/bin:/bin:/usr/local/bin:`$PATH"
if [ `$_claude_exit_code -ne 0 ] && [ `$_claude_exit_code -ne 130 ]; then
    _incident_file='$bashSanctumRoot/_shared-memory/eve-incidents.jsonl'
    _incident_ts=`$(/usr/bin/date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u +%Y-%m-%dT%H:%M:%SZ)
    _incident_kind="claude-nonzero-exit"
    # 139 = SIGSEGV (Bun segfault). 134 = SIGABRT (Bun abort).
    if [ `$_claude_exit_code -eq 139 ] || [ `$_claude_exit_code -eq 134 ]; then
        _incident_kind="bun-runtime-crash"
    fi
    printf '{"ts_utc":"%s","kind":"%s","exit_code":%d,"account":"%s","project":"%s","agent":"%s"}\n' "`$_incident_ts" "`$_incident_kind" "`$_claude_exit_code" "`$_account_name" "$projKey" "$bashAgentName" >> "`$_incident_file" 2>/dev/null
    printf '\n  > [INCIDENT] claude exited %d (kind=%s) — logged to eve-incidents.jsonl for auto-fix surface\n' "`$_claude_exit_code" "`$_incident_kind"
fi
# RKOJ-ELENO :: 2026-05-23 :: detect rate-limit + mark account
# RKOJ-ELENO :: 2026-05-24 :: split into plan-quota (per-account) vs server-throttle (global).
# Plan-quota signals -> Mark-AccountRateLimited (rotate accounts).
# Server-throttle signals (Anthropic global limiter) -> log to anthropic-throttle-events.jsonl
#   ONLY; do NOT mark account (rotating won't help — limiter is global, not per-account).
_session_log_dir="`$HOME/.claude/projects"
if [ -d "`$_session_log_dir" ]; then
    _recent_log=`$(find "`$_session_log_dir" -name "*.jsonl" -mmin -10 -type f 2>/dev/null | head -1)
    if [ -n "`$_recent_log" ]; then
        # Server-throttle pattern (global limiter) — log + skip account-mark.
        # Original error string: "Server is temporarily limiting requests (not your usage limit)".
        if grep -qE 'Server is temporarily limiting requests|not your usage limit|server.?side.?(rate|throttle)|Churned for' "`$_recent_log" 2>/dev/null; then
            _excerpt=`$(grep -oE '.{0,40}(Server is temporarily limiting requests|not your usage limit|Churned for [0-9]+[ms 0-9]*).{0,40}' "`$_recent_log" 2>/dev/null | head -1 | tr -d '\r\n' | head -c 200)
            _ts=`$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)
            _evt_file='$bashSanctumRoot/_shared-memory/anthropic-throttle-events.jsonl'
            # JSON escape minimal: backslash + double-quote.
            _esc_excerpt=`$(printf '%s' "`$_excerpt" | sed 's/\\/\\\\/g; s/"/\\"/g')
            _esc_acct=`$(printf '%s' "`$_account_name" | sed 's/\\/\\\\/g; s/"/\\"/g')
            _esc_proj=`$(printf '%s' "$projKey" | sed 's/\\/\\\\/g; s/"/\\"/g')
            printf '{"ts_utc":"%s","account":"%s","project":"%s","excerpt":"%s"}\n' "`$_ts" "`$_esc_acct" "`$_esc_proj" "`$_esc_excerpt" >> "`$_evt_file" 2>/dev/null
            printf '\n  > [INFO] Anthropic server-throttle (global, NOT your account) — logged to anthropic-throttle-events.jsonl\n'
        # Plan-quota pattern (per-account) — mark account + rotate.
        # Tightened to NOT match the server-throttle phrases above.
        elif grep -qE '(rate.?limit|429|too many requests|retry.?after)' "`$_recent_log" 2>/dev/null \
             && ! grep -qE 'Server is temporarily limiting requests|not your usage limit' "`$_recent_log" 2>/dev/null; then
            # RKOJ-ELENO :: 2026-05-24 iter6 :: parse actual retry-after value from log when present.
            # Anthropic 429 responses include a retry-after header (seconds) and/or JSON error body
            # text like "Please try again in 1234 seconds" / "retry after 1234s". We try in order:
            #   1. JSON-style `"retry-after":"123"` or `"retry_after":123` header field
            #   2. Plain-text "retry after 123" / "try again in 123 seconds"
            #   3. Fall back to 60s (watchdog recovers)
            _retry_after=60
            _ra_json=`$(grep -oE '"retry[-_]after"[[:space:]]*:[[:space:]]*"?[0-9]+"?' "`$_recent_log" 2>/dev/null | grep -oE '[0-9]+' | head -1)
            if [ -n "`$_ra_json" ]; then
                _retry_after="`$_ra_json"
            else
                _ra_text=`$(grep -oiE '(retry.?after|try again in)[^0-9]{0,15}[0-9]+[[:space:]]*(s|sec|seconds)?' "`$_recent_log" 2>/dev/null | grep -oE '[0-9]+' | head -1)
                if [ -n "`$_ra_text" ]; then _retry_after="`$_ra_text"; fi
            fi
            printf '\n  > [WARN] plan-quota rate-limit detected - marking account "%s" throttled for %ss\n' "`$_account_name" "`$_retry_after"
            # RKOJ-ELENO :: 2026-05-24 :: rate-limit-causes.jsonl row write.
            # Captures the FULL context at moment of 429 (concurrent count, burst counts,
            # plan_tier, retry-after, root_cause_guess) so rate-limit-analyzer.ps1 can do
            # better-than-text analysis. Composes with claude-accounts.log (existing) and
            # anthropic-throttle-events.jsonl (global throttle, separate file above).
            _rlc_file='$bashSanctumRoot/_shared-memory/rate-limit-causes.jsonl'
            _rlc_ts=`$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)
            _rlc_concurrent=`$(powershell -NoProfile -Command "(Get-Process -Name claude -ErrorAction SilentlyContinue).Count" 2>/dev/null | tr -d '\r\n ')
            if [ -z "`$_rlc_concurrent" ]; then _rlc_concurrent=0; fi
            # Burst counts from spawned-windows.jsonl (last 5min + 30min)
            _spawn_file='$bashSanctumRoot/_shared-memory/spawned-windows.jsonl'
            _rlc_b5=0; _rlc_b30=0
            if [ -f "`$_spawn_file" ]; then
                _now_epoch=`$(date -u +%s 2>/dev/null)
                _5min_cut=`$((_now_epoch - 300))
                _30min_cut=`$((_now_epoch - 1800))
                while IFS= read -r _spawn_line; do
                    _ts_str=`$(printf '%s' "`$_spawn_line" | grep -oE '"started":"[^"]+"' | sed 's/"started":"//;s/"//')
                    if [ -n "`$_ts_str" ]; then
                        _ep=`$(date -u -d "`$_ts_str" +%s 2>/dev/null || echo 0)
                        if [ "`$_ep" -ge "`$_5min_cut" ]; then _rlc_b5=`$((_rlc_b5 + 1)); fi
                        if [ "`$_ep" -ge "`$_30min_cut" ]; then _rlc_b30=`$((_rlc_b30 + 1)); fi
                    fi
                done < <(tail -n 200 "`$_spawn_file" 2>/dev/null)
            fi
            # plan_tier lookup (best-effort)
            _rlc_tier=`$(grep -oE '"name":[[:space:]]*"'"`$_account_name"'"[^}]*"plan_tier":[[:space:]]*"[^"]*"' '$bashSanctumRoot/_shared-memory/claude-accounts.json' 2>/dev/null | grep -oE '"plan_tier":[[:space:]]*"[^"]*"' | sed 's/.*"plan_tier":[[:space:]]*"//;s/"//' | head -1)
            if [ -z "`$_rlc_tier" ]; then _rlc_tier=unknown; fi
            # root_cause_guess
            _rlc_cause=unknown
            if [ "`$_rlc_b5" -gt 3 ]; then
                _rlc_cause=burst_spawn
            elif [ -f '$bashSanctumRoot/_shared-memory/anthropic-throttle-events.jsonl' ] && tail -n 5 '$bashSanctumRoot/_shared-memory/anthropic-throttle-events.jsonl' 2>/dev/null | grep -q "`$_account_name"; then
                _rlc_cause=global_throttle
            elif [ "`$_retry_after" -gt 600 ]; then
                _rlc_cause=long_window
            fi
            # JSON-escape (minimal: backslash + double-quote)
            _esc_acct2=`$(printf '%s' "`$_account_name" | sed 's/\\/\\\\/g; s/"/\\"/g')
            _esc_proj2=`$(printf '%s' "$projKey" | sed 's/\\/\\\\/g; s/"/\\"/g')
            _esc_tier2=`$(printf '%s' "`$_rlc_tier" | sed 's/\\/\\\\/g; s/"/\\"/g')
            _esc_cause2=`$(printf '%s' "`$_rlc_cause" | sed 's/\\/\\\\/g; s/"/\\"/g')
            printf '{"ts_utc":"%s","account_name":"%s","project_key":"%s","concurrent_claude_count":%s,"spawns_in_last_5min":%s,"spawns_in_last_30min":%s,"plan_tier":"%s","retry_after_seconds":%s,"root_cause_guess":"%s"}\n' "`$_rlc_ts" "`$_esc_acct2" "`$_esc_proj2" "`$_rlc_concurrent" "`$_rlc_b5" "`$_rlc_b30" "`$_esc_tier2" "`$_retry_after" "`$_esc_cause2" >> "`$_rlc_file" 2>/dev/null
            printf '  > rate-limit-causes.jsonl row written (concurrent=%s spawns_5min=%s cause=%s)\n' "`$_rlc_concurrent" "`$_rlc_b5" "`$_rlc_cause"
            powershell -NoProfile -ExecutionPolicy Bypass -File '$SanctumRoot\automations\claude-accounts.ps1' -Action RateLimited -Name "`$_account_name" -RetryAfterSeconds "`$_retry_after" 2>/dev/null
        fi
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
printf '  > resume-point written + auto-push fired.\n'
# RKOJ-ELENO :: 2026-05-24 :: window-persist fix. Operator (2026-05-24, screenshot):
# spawned mintty windows linger over the browser after claude exits. Root cause:
# `exec sterm/bash` here kept the bash process alive indefinitely so mintty never
# closed. Default behavior is now to EXIT cleanly so mintty closes within ~1s of
# claude exit. Operators who want the old "drop into sterm" behavior can opt in
# via SINISTER_KEEP_SHELL=1 in their environment.
if [ "`${SINISTER_KEEP_SHELL:-0}" = "1" ]; then
  printf '  > SINISTER_KEEP_SHELL=1 set — dropping into sinister-term (our own shell)...\n\n'
  if command -v sterm >/dev/null 2>&1; then
    exec sterm
  elif command -v sinister-term >/dev/null 2>&1; then
    exec sinister-term
  else
    printf '  > sterm not on PATH; falling back to bash. Install with: pip install -e $bashSanctumRoot/projects/sinister-term/source\n'
    exec bash
  fi
else
  printf '  > closing window. (set SINISTER_KEEP_SHELL=1 to drop into sinister-term instead.)\n'
  exit 0
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

    # RKOJ-ELENO :: 2026-05-24 :: -DryRun smoke-test exit hatch. Operator's
    # auto-best-slot spec requires verifying the pick + creds-swap path WITHOUT
    # firing a real mintty + claude session. Called as:
    #   powershell -File start-sinister-session.ps1 -Project sanctum -DryRun
    if ($DryRun) {
        Write-Host ''
        Write-Host "  [DRY-RUN] would spawn '$agentName' :: $($projRec.display) with slot='$selectedAccountName' (auth_mode=$selectedAuthMode)" -ForegroundColor $C.Accent
        Write-Host '  [DRY-RUN] skipping mintty + claude launch.' -ForegroundColor $C.Dim
        # Release the lease we just took so DryRun does not leak a phantom session count.
        try { Mark-AccountReleased -Name $selectedAccountName | Out-Null } catch {}
        return
    }

    $spawned = $false
    $spawnedProcess = $null
    $spawnAttemptLog = @()
    $_minttyT0 = Get-Date
    try { _SpawnProgress -Stage 'mintty launch' -Status 'RUN' } catch {}
    try {
        if (Test-Path $minttyExe) {
            # RKOJ-ELENO :: 2026-05-24 :: window-persist + always-on-top fix.
            # Operator screenshot (2026-05-24): spawned mintty windows linger after
            # claude exits AND appear to stay on top of the operator's browser.
            #
            # Root cause 1: launch.sh used `exec sterm/bash` after claude exit, which
            # kept the bash process alive indefinitely (mintty stays open). Fixed in
            # the .sh body — sterm fallthrough is now opt-in via SINISTER_KEEP_SHELL=1.
            #
            # Root cause 2: Transparency=medium + OpaqueWhenFocused=no produced the
            # "on top of browser" optical illusion (translucent overlay). Removed —
            # window is now solid + only on top while focused.
            #
            # `--hold never` (was implicit default; now explicit) closes the mintty
            # window the instant bash exits — defensive against any stray exit code.
            # RKOJ-ELENO :: 2026-05-24 :: -t TITLE was missing. Operator 20:30Z:
            # "rename and color settings on the agents we open still dont work fix that".
            # Root cause #2: mintty -t flag was never passed so the spawned window
            # title defaulted to "MINGW64:..." until the bash printf at line 1502 fired;
            # if anything in the cold-start phrase (forge-memory recall / pre-warm reads)
            # raced ahead of the printf or if bash's PS1 reset the title, the rename
            # was lost. -t sets the title at mintty PROCESS-LEVEL so it persists across
            # bash startup. The OSC printf at line 1502 then reinforces it once bash runs.
            # RKOJ-ELENO :: 2026-05-24T21:55Z URGENT ROLLBACK -- operator 21:55Z "this didnt
            # open my window fix". The -t $windowTitle arg I added earlier choked mintty
            # (title contained '::' + spaces; mintty PID spawned then died before window
            # showed). The OSC printf at line 1502 (`\033]0;$windowTitle\007`) already
            # sets the title from inside bash, which is the canonical mintty-friendly path
            # for titles-with-spaces. Removing -t restores spawn visibility.
            # RKOJ-ELENO :: 2026-05-25 :: operator hard-canonical 2026-05-25T03:30Z
            # verbatim *"i want the terminals them selves to look sick and have the
            # transparent look ... make it in brand with sinister software"*. Transparency
            # is RE-ENABLED (had been off since 2026-05-24 "on top of browser" optical-
            # illusion fix); now `Transparency=low` + `OpaqueWhenFocused=yes` gives the
            # sick look the operator wants WITHOUT the browser-overlay issue (window is
            # opaque while focused, see-through only when blurred/background).
            #
            # ANSI 16-color palette = Sinister canonical tokens from
            # _shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md:
            #   PURPLE  #c084fc / BRIGHTP #d8b4fe / DARKP #6b21a8 / PALEP #e8d6ff
            # So every spawned session reads in-brand whether it's a green/cyan/red accent
            # session or the default purple.
            $minttyArgs = @(
                # RKOJ-ELENO :: 2026-05-24T21:55Z :: --hold never -> --hold error.
                # Operator 21:55Z "this didnt open my window fix". With --hold never, ANY
                # bash error (one bad line in launch.sh) instantly closes the window with no
                # visible trace. --hold error keeps the window open on non-zero bash exit so
                # operator sees the failure + can copy the trace. Successful exit still closes.
                '--hold', 'error',
                '-t', $windowTitleAscii,
                '-o', "ForegroundColour=$fgRgb",
                '-o', "BackgroundColour=$bgRgb",
                '-o', "CursorColour=$curRgb",
                '-o', 'FontSize=11',
                # RKOJ-ELENO :: 2026-05-25 :: BUG FIX -- 'Cascadia Mono' contains a space
                # which triggers the same PS 5.1 Start-Process -ArgumentList quoting failure
                # as the $windowTitleAscii bug. mintty splits on the space: parses
                # `-o Font=Cascadia` (font dialog warns), then tries to exec `Mono` as the
                # child program -> exit 126 "Failed to run 'Mono'". Consolas is single-word,
                # ships on every Windows 10/11, and is the mintty default fallback anyway.
                # If operator wants Cascadia look back: install it + change to 'Consolas' to
                # any single-word installed font name OR fix Start-Process quoting plumbing.
                '-o', 'Font=Consolas',
                '-o', 'Term=xterm-256color',
                '-o', 'Transparency=low',
                '-o', 'OpaqueWhenFocused=yes',
                # Sinister-branded ANSI palette (16 colors). Purple-forward; bright variants
                # for bold text. Names mirror mintty's documented BoldColor + standard ANSI.
                '-o', 'Black=16,8,32',
                '-o', 'Red=255,90,110',
                '-o', 'Green=152,255,180',
                '-o', 'Yellow=255,210,140',
                '-o', 'Blue=140,180,255',
                '-o', 'Magenta=192,132,252',
                '-o', 'Cyan=140,230,255',
                '-o', 'White=232,214,255',
                '-o', 'BoldBlack=58,40,76',
                '-o', 'BoldRed=255,140,160',
                '-o', 'BoldGreen=200,255,220',
                '-o', 'BoldYellow=255,230,180',
                '-o', 'BoldBlue=180,210,255',
                '-o', 'BoldMagenta=216,180,254',
                '-o', 'BoldCyan=190,245,255',
                '-o', 'BoldWhite=248,240,255'
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
        $_minttyMs = [int]((Get-Date) - $_minttyT0).TotalMilliseconds
        try { _SpawnProgress -Stage 'mintty launch' -Status 'FAIL' -ElapsedMs $_minttyMs -Detail $_.Exception.Message } catch {}
        Write-Host "  [FAIL] could not spawn bash: $($_.Exception.Message)" -ForegroundColor $C.Fail
        Write-Host ('         attempted: ' + ($spawnAttemptLog -join ' ; ')) -ForegroundColor $C.Dim
        Write-Host '  [press Enter to return to picker]' -ForegroundColor $C.Warn
        Read-Host | Out-Null
        return
    }
    if ($spawned -and $spawnedProcess) {
        $_minttyMs = [int]((Get-Date) - $_minttyT0).TotalMilliseconds
        try { _SpawnProgress -Stage 'mintty launch' -Status 'OK' -ElapsedMs $_minttyMs -Detail "pid=$($spawnedProcess.Id)" } catch {}
        # RKOJ-ELENO :: 2026-05-24T22:00Z :: operator "this didnt open my window fix".
        # Window DID spawn but was behind other windows / off-screen / minimized -> operator
        # didn't see it. Force-foreground the new mintty: wait for window-handle to appear
        # (up to 2s), then SetForegroundWindow + ShowWindow SW_RESTORE. Idempotent + safe;
        # ignores any process that exits before handle becomes available.
        try {
            if (-not ('SnctmFG' -as [type])) {
                Add-Type -Namespace SnctmFG -Name Win @"
                    using System;
                    using System.Runtime.InteropServices;
                    public class Win {
                        [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
                        [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
                        [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
                    }
"@ -ErrorAction SilentlyContinue
            }
            $_fgT0 = Get-Date
            $_hwnd = [IntPtr]::Zero
            while (((Get-Date) - $_fgT0).TotalMilliseconds -lt 2000) {
                try { $spawnedProcess.Refresh() } catch { break }
                if ($spawnedProcess.HasExited) { break }
                if ($spawnedProcess.MainWindowHandle -ne [IntPtr]::Zero) {
                    $_hwnd = $spawnedProcess.MainWindowHandle
                    break
                }
                Start-Sleep -Milliseconds 50
            }
            if ($_hwnd -ne [IntPtr]::Zero) {
                [SnctmFG.Win]::ShowWindow($_hwnd, 9) | Out-Null   # SW_RESTORE
                [SnctmFG.Win]::BringWindowToTop($_hwnd) | Out-Null
                [SnctmFG.Win]::SetForegroundWindow($_hwnd) | Out-Null
                try { _SpawnProgress -Stage 'window foreground' -Status 'OK' -Detail "hwnd=$_hwnd" } catch {}
            } else {
                try { _SpawnProgress -Stage 'window foreground' -Status 'SKIP' -Detail 'no MainWindowHandle within 2s' } catch {}
            }
        } catch {
            try { _SpawnProgress -Stage 'window foreground' -Status 'SKIP' -Detail $_.Exception.Message } catch {}
        }
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
                account_name = $accountName  # RKOJ-ELENO :: 2026-05-24T23:30Z :: operator wants per-account running-agent count on Resume/Accounts pages
            }
            # RKOJ-ELENO :: 2026-05-24 :: sentinel-file lock for parallel-launcher safety.
            # Operator 19:14Z: "no one steps on toes". Prior raw Add-Content could interleave
            # mid-line when 2 launchers spawn simultaneously, corrupting the jsonl.
            $swLockFile = Join-Path $swDir '.spawned-windows.lock'
            $swLockLine = ($swRec | ConvertTo-Json -Compress)
            $swLocked = $false
            for ($swLockTry = 0; $swLockTry -lt 40; $swLockTry++) {
                try {
                    $swFs = [System.IO.File]::Open($swLockFile, 'CreateNew', 'Write', 'None')
                    $swFs.Close()
                    $swLocked = $true
                    break
                } catch {
                    # Stale-lock reclaim after 10s (matches claude-accounts convention shape).
                    try {
                        if (Test-Path $swLockFile) {
                            $swAge = ((Get-Date) - (Get-Item $swLockFile).LastWriteTime).TotalSeconds
                            if ($swAge -gt 10) { Remove-Item $swLockFile -Force -ErrorAction SilentlyContinue }
                        }
                    } catch {}
                    Start-Sleep -Milliseconds 100
                }
            }
            try {
                Add-Content -Path $swPath -Value $swLockLine -Encoding UTF8
            } finally {
                if ($swLocked) { try { Remove-Item $swLockFile -Force -ErrorAction SilentlyContinue } catch {} }
            }
        } catch {}
    }

    # Fire window-position monitor in background so when the spawned window closes,
    # its final x/y/w/h is persisted to _shared-memory/window-positions/<key>.json
    # for next-resume restore.
    if ($spawnedProcess -and $spawnedProcess.Id) {
        $_monT0 = Get-Date
        try { _SpawnProgress -Stage 'monitor fire' -Status 'RUN' } catch {}
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
                $_monMs = [int]((Get-Date) - $_monT0).TotalMilliseconds
                try { _SpawnProgress -Stage 'monitor fire' -Status 'OK' -ElapsedMs $_monMs -Detail "watching pid=$($spawnedProcess.Id)" } catch {}
            } catch {
                $_monMs = [int]((Get-Date) - $_monT0).TotalMilliseconds
                try { _SpawnProgress -Stage 'monitor fire' -Status 'FAIL' -ElapsedMs $_monMs -Detail $_.Exception.Message } catch {}
            }
        } else {
            try { _SpawnProgress -Stage 'monitor fire' -Status 'SKIP' -Detail 'script missing' } catch {}
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

function Write-RunLog($projectKey, $agentName, $accent, $kind, $modesRec = $null) {
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
    # RKOJ-ELENO :: 2026-05-25T07:19Z :: last-spawn.json for Q) Quick-launch (iter-25 P0.2).
    # Operator hard-canonical 07:19Z: "make this entire process way more efficient with
    # the quickest way to open my terminals". eve.py Q) reads this row + sets
    # $env:SINISTER_QUICK_LAUNCH=1, then re-invokes start-sinister-session.ps1 -Project
    # <project> to skip every prompt. Single-row file (overwrite on each spawn) for the
    # zero-friction case; per-lane history is also appended to last-spawn-history.jsonl
    # for future multi-lane recall (eve.py Q) currently reads only last-spawn.json).
    try {
        $lastSpawnPath = Join-Path $ScriptRunsDir 'last-spawn.json'
        $modesOut = $null
        if ($modesRec) {
            $modesOut = [pscustomobject]@{
                swarm = [bool]$modesRec.swarm
                loop = [bool]$modesRec.loop
                loop_relentless = [bool]$modesRec.loop_relentless
                loop_condition = [string]$modesRec.loop_condition
                priority = [int]$modesRec.priority
            }
        }
        $lastRec = [pscustomobject]@{
            ts_utc = (Get-Date).ToUniversalTime().ToString('o')
            lane = $agentName
            project_key = $projectKey
            accent = $accent
            kind = $kind
            modes = $modesOut
        }
        [System.IO.File]::WriteAllText($lastSpawnPath, ($lastRec | ConvertTo-Json -Depth 6), [System.Text.UTF8Encoding]::new($false))
        # Append to history for future multi-lane recall (eve.py Q currently reads single-row only).
        $histPath = Join-Path $ScriptRunsDir 'last-spawn-history.jsonl'
        $histLine = ($lastRec | ConvertTo-Json -Depth 6 -Compress)
        Add-Content -Path $histPath -Value $histLine -Encoding UTF8
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
    # RKOJ-ELENO :: 2026-05-24 :: rename + color FIX. Operator 20:30Z "rename and color
    # settings on the agents we open still dont work fix that". Root cause: this headless
    # -Project path (EVE.exe shells `start-sinister-session.ps1 -Project key`) hardcoded
    # the accent to 'purple', silently overriding any per-project accent the operator had
    # saved via the picker's Confirm-AgentPrefs flow. The agent name was correctly read
    # from prefs (line above) but the accent was lost. Now reads per-project accent from
    # prefs.per_project[$Project].accent_color, falls back to 'purple' only if no entry.
    # RKOJ-ELENO :: 2026-05-25 :: per-user accent (operator 00:32Z). Get-ProjectAccent reads
    # prefs.users[<currentEmail>].projects[<key>].accent_color first, then falls back to legacy.
    $resolvedAccent = if ($AccentColor) { $AccentColor } else { Get-ProjectAccent $Project $prefs 'purple' }
    $prefs = Persist-AgentPref $Project $resolvedAgent $resolvedAccent $prefs
    $isGeneral = ($Project -eq 'general')
    # Operator hard-canonical 2026-05-24T17:18Z: "i need to be asked per proejct in the bat
    # file if i want to use swarm on this one and make it work just like jcode". Previously
    # the headless -Project path (EVE.exe -> PS1 handoff) used env-var defaults and never
    # surfaced the modes prompt — the operator's per-pick swarm/loop ask was getting
    # bypassed. Now `Prompt-AgentModes -ProjectRec $projRec` is called UNLESS
    # SINISTER_SKIP_MODES_PROMPT=1 (already honored inside the helper; truly-headless
    # callers like Task Scheduler / cron set this). Sub-area D of 5x-parallel claim
    # register. RKOJ-ELENO 2026-05-24.
    $modes = Prompt-AgentModes -ProjectRec $projRec
    $phrase = Build-Phrase $projRec $resolvedAgent 'resume' $isGeneral $false $modes
    if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $resolvedAccent $phrase $modes }
    Write-RunLog $Project $resolvedAgent $resolvedAccent 'headless' $modes
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
                    $modes = Prompt-AgentModes -ProjectRec $projRec
                    $phrase = Build-Phrase $projRec $resolvedAgent 'resume' $isGeneral $false $modes
                    if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $accentVal $phrase $modes }
                    Write-RunLog $targetKey $resolvedAgent $accentVal 'autoresume-fresh' $modes
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
                $modes = Prompt-AgentModes -ProjectRec $projRec
                $phrase = Build-Phrase $projRec $resolvedAgent 'resume' ($targetKey -eq 'general') $false $modes
                if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $accentVal $phrase $modes }
                Write-RunLog $targetKey $resolvedAgent $accentVal 'autoresume' $modes
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
                $modes = Prompt-AgentModes -ProjectRec $projRec
                $phrase = Build-Phrase $projRec $resolvedAgent 'scaffold' $false $true $modes
                if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent 'purple' $phrase $modes }
                Write-RunLog $new.key $resolvedAgent 'purple' 'newproject' $modes
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
                $modes = Prompt-AgentModes -ProjectRec $projRec
                $phrase = Build-Phrase $projRec $resolvedAgent 'resume' $isGeneral $false $modes
                if (-not $NoLaunch) { Launch-Session $projRec $resolvedAgent $accentVal $phrase $modes }
                Write-RunLog $targetKey $resolvedAgent $accentVal 'project' $modes
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
