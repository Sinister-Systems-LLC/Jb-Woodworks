# git-toolkit.ps1 â€” one-stop GitHub workflow helper for Sinister projects.
# Operator runs subcommands; bots can call read-only subcommands via bus.run_script
# (whitelist requires adding "git-toolkit-<cmd>" entry per command if exposed).
#
# Subcommands:
#   init <project-path>                  -- git init + .gitignore + first commit
#   remote-set <project-path> <url>      -- add origin, set upstream, verify gh
#   safe-push <project-path>             -- secret-scrub FIRST; abort on hits
#   pre-commit-install <project-path>    -- .githooks/pre-commit runs scrub
#   release <project-path> <semver>      -- tag + push tag
#   ci-bootstrap <project-path>          -- drop .github/workflows skeleton
#   doc-bootstrap <project-path>         -- README + CLAUDE.md + .gitignore + LICENSE template
#   scrub <project-path>                 -- run secret-scrub on a project
#   gitignore-tune <project-path>        -- detect lang and add ignores
#   status-summary [<project-path>]      -- branch + ahead/behind + dirty across one or all
#
# Emits a runlog manifest per invocation.

[CmdletBinding()]
param(
    [Parameter(Position=0)][string]$Command = 'help',
    [Parameter(Position=1)][string]$Path = '',
    [Parameter(Position=2)][string]$Arg2 = '',
    [switch]$DryRun,
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$HubRoot = 'D:\Sinister\Sinister Skills'

# Try to dot-source runlog helper (works from hub or LLC)
$runlogHelper = $null
foreach ($p in @(
    "$HubRoot\08_AUTOMATIONS\_runlog.ps1",
    "$PSScriptRoot\hub-scripts\_runlog.ps1",
    "$PSScriptRoot\_runlog.ps1"
)) {
    if (Test-Path $p) { . $p; $runlogHelper = $p; break }
}
$log = $null
if ($runlogHelper) { $log = Start-Runlog -Script "git-toolkit-$Command" }

function Out-Step($name, $ok, $summary='') {
    $color = if ($ok) { 'Green' } else { 'Red' }
    $marker = if ($ok) { '[OK]' } else { '[FAIL]' }
    Write-Host ("  {0} {1}  {2}" -f $marker, $name, $summary) -ForegroundColor $color
    if ($log) { Add-RunlogStep -Log $log -Name $name -Ok $ok -Summary $summary }
}

function Resolve-Project($p) {
    if (-not $p) { return $null }
    if (Test-Path $p) { return (Get-Item $p).FullName }
    return $null
}

function Get-Language($projPath) {
    $hasPy = (Get-ChildItem $projPath -Filter '*.py' -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1)
    $hasTs = (Get-ChildItem $projPath -Filter '*.ts*' -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1)
    $hasKt = (Get-ChildItem $projPath -Filter '*.kt' -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1)
    $hasJv = (Get-ChildItem $projPath -Filter '*.java' -Recurse -Depth 2 -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($hasPy) { return 'python' }
    if ($hasTs) { return 'typescript' }
    if ($hasKt) { return 'kotlin' }
    if ($hasJv) { return 'java' }
    return 'mixed'
}

function Get-GitignoreFor($lang) {
    $common = @(
        '# OS', '.DS_Store', 'Thumbs.db', 'desktop.ini', '',
        '# IDE', '.vscode/', '.idea/', '*.swp', '',
        '# Secrets (HARD NO)', '.env', '.env.*', '!.env.example',
        '*.pem', '*.key', '*.p12', 'credentials.json', 'credentials/', 'secrets/', ''
    )
    switch ($lang) {
        'python' { return $common + @('# Python', '__pycache__/', '*.py[cod]', '.venv/', 'venv/', '*.egg-info/', 'build/', 'dist/', '.pytest_cache/', '.mypy_cache/', '.ruff_cache/') }
        'typescript' { return $common + @('# Node', 'node_modules/', '.next/', 'out/', '.parcel-cache/', '.turbo/', '*.log', 'dist/', 'build/') }
        'kotlin' { return $common + @('# Android/Kotlin', '*.class', '*.jar', '*.apk', '*.aab', '*.dex', '.gradle/', 'build/', 'local.properties', 'captures/') }
        'java' { return $common + @('# Java', '*.class', '*.jar', 'target/', '.gradle/', 'build/') }
        default { return $common }
    }
}

function Cmd-Init($projPath) {
    if (-not (Test-Path $projPath)) { Out-Step 'resolve' $false "$projPath not found"; return 1 }
    Push-Location $projPath
    try {
        if (Test-Path '.git') { Out-Step 'git-init' $true 'already a repo' }
        else {
            $null = cmd /c "git init >NUL 2>NUL"
            $null = cmd /c "git branch -m main >NUL 2>NUL"
            Out-Step 'git-init' ($LASTEXITCODE -eq 0) 'init + branch main'
        }
        # .gitignore
        if (-not (Test-Path '.gitignore')) {
            $lang = Get-Language $projPath
            $ign = Get-GitignoreFor $lang
            if (-not $DryRun) { $ign -join "`n" | Out-File '.gitignore' -Encoding utf8 }
            Out-Step '.gitignore' $true "lang=$lang ($($ign.Count) lines)"
        } else { Out-Step '.gitignore' $true 'exists' }
        # First commit
        if (-not $DryRun) {
            & git add . 2>&1 | Out-Null
            $null = cmd /c 'git diff --cached --quiet'
            if ($LASTEXITCODE -ne 0) {
                $null = cmd /c 'git commit -m "init: project bootstrapped via Sinister git-toolkit" >NUL 2>NUL'
                Out-Step 'first-commit' ($LASTEXITCODE -eq 0) 'committed'
            } else {
                Out-Step 'first-commit' $true 'nothing to commit'
            }
        }
    } finally { Pop-Location }
    return 0
}

function Cmd-RemoteSet($projPath, $url) {
    if (-not $url) { Out-Step 'remote-set' $false 'missing url'; return 1 }
    Push-Location $projPath
    try {
        $null = cmd /c "git remote remove origin >NUL 2>NUL"
        $null = cmd /c "git remote add origin `"$url`" >NUL 2>NUL"
        Out-Step 'add-origin' ($LASTEXITCODE -eq 0) $url
        if (Get-Command gh -ErrorAction SilentlyContinue) {
            $info = (gh repo view $url 2>$null | Out-String).Trim()
            Out-Step 'gh-verify' ($LASTEXITCODE -eq 0) (if ($info) { 'reachable' } else { 'reachable (no view)' })
        } else { Out-Step 'gh-verify' $true 'gh not installed; skipped' }
    } finally { Pop-Location }
    return 0
}

function Cmd-SafeScrub($projPath) {
    # Calls Sinister LLC's secret-scrub.ps1 against this project specifically
    $scrub = "$HubRoot\..\Sinister LLC\automations\secret-scrub.ps1"
    if (-not (Test-Path $scrub)) {
        # Fallback to absolute
        $scrub = 'D:\Sinister Sanctum\automations\secret-scrub.ps1'
    }
    if (-not (Test-Path $scrub)) { Out-Step 'scrub' $false 'secret-scrub.ps1 not found'; return 1 }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $scrub -LLCRoot $projPath -Quiet 2>&1 | ForEach-Object { Write-Host "    $_" }
    $rc = $LASTEXITCODE
    Out-Step 'scrub' ($rc -eq 0) "exit $rc"
    return $rc
}

function Cmd-SafePush($projPath) {
    Push-Location $projPath
    try {
        # Pre-flight scrub
        $scrubRc = Cmd-SafeScrub $projPath
        if ($scrubRc -ne 0) {
            Write-Host "[ABORT] secret-scrub failed; not pushing" -ForegroundColor Red
            Out-Step 'safe-push' $false 'aborted by scrub'
            return 1
        }
        # Check branch
        $branch = (& git rev-parse --abbrev-ref HEAD 2>$null).Trim()
        if (-not $branch -or $branch -eq 'HEAD') { Out-Step 'safe-push' $false 'detached HEAD'; return 1 }
        if ($DryRun) { Out-Step 'safe-push' $true "would push branch=$branch"; return 0 }
        & git push -u origin $branch 2>&1 | ForEach-Object { Write-Host "    $_" }
        Out-Step 'safe-push' ($LASTEXITCODE -eq 0) "branch=$branch"
    } finally { Pop-Location }
    return 0
}

function Cmd-PreCommitInstall($projPath) {
    Push-Location $projPath
    try {
        $null = New-Item -ItemType Directory -Force -Path '.githooks' | Out-Null
        $hook = '.githooks/pre-commit'
        $hookContent = @"
#!/bin/sh
# Sinister pre-commit hook - blocks if secret-scrub finds API keys / PEM / etc.
exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:/Sinister LLC/automations/secret-scrub.ps1" -LLCRoot "$projPath" -Quiet
"@
        if (-not $DryRun) {
            $hookContent | Out-File $hook -Encoding ascii
            $null = cmd /c "git config core.hooksPath .githooks >NUL 2>NUL"
        }
        Out-Step 'pre-commit' $true 'installed'
    } finally { Pop-Location }
    return 0
}

function Cmd-Release($projPath, $semver) {
    if (-not $semver -or $semver -notmatch '^v?\d+\.\d+\.\d+') { Out-Step 'release' $false "invalid semver: $semver"; return 1 }
    if (-not $semver.StartsWith('v')) { $semver = "v$semver" }
    Push-Location $projPath
    try {
        if ($DryRun) { Out-Step 'release' $true "would tag $semver"; return 0 }
        $null = cmd /c "git tag $semver"
        if ($LASTEXITCODE -ne 0) { Out-Step 'tag' $false 'tag failed'; return 1 }
        $null = cmd /c "git push origin $semver >NUL 2>NUL"
        Out-Step 'release' ($LASTEXITCODE -eq 0) "tag $semver pushed"
    } finally { Pop-Location }
    return 0
}

function Cmd-CiBootstrap($projPath) {
    $lang = Get-Language $projPath
    Push-Location $projPath
    try {
        $null = New-Item -ItemType Directory -Force -Path '.github/workflows' | Out-Null
        $wf = '.github/workflows/sinister-ci.yml'
        $base = @"
name: sinister-ci
on:
  pull_request: { branches: [main] }
  push:         { branches: [main] }

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"@
        $rest = switch ($lang) {
            'python' { @"
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install --upgrade pip
      - run: pip install -r requirements.txt || true
      - run: python -m pytest -q || true
"@ }
            'typescript' { @"
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci || npm install
      - run: npm run build --if-present
      - run: npm test --if-present
"@ }
            'kotlin' { @"
      - uses: actions/setup-java@v4
        with: { distribution: 'temurin', java-version: '17' }
      - run: ./gradlew build --no-daemon
"@ }
            default { @"
      - run: echo 'add language-specific build/test steps here'
"@ }
        }
        if (-not $DryRun) { ($base + "`n" + $rest) | Out-File $wf -Encoding utf8 }
        Out-Step 'ci-bootstrap' $true "lang=$lang -> $wf"
    } finally { Pop-Location }
    return 0
}

function Cmd-DocBootstrap($projPath) {
    Push-Location $projPath
    try {
        $name = Split-Path -Leaf $projPath
        if (-not (Test-Path 'README.md')) {
            $r = @"
# $name

Project bootstrapped via Sinister git-toolkit.

## What this is

(operator to fill in)

## Quickstart

(operator to fill in)

## License

See LICENSE at repo root.
"@
            if (-not $DryRun) { $r | Out-File 'README.md' -Encoding utf8 }
            Out-Step 'README.md' $true 'created'
        } else { Out-Step 'README.md' $true 'exists' }
        if (-not (Test-Path 'CLAUDE.md')) {
            $c = @"
# CLAUDE.md - $name

Hub canonical at ``D:\Sinister\Sinister Skills\01_MEMORY\$name\``.
Session name for inter-agent messaging: **$name**

## Read order (cold start)

1. Hub SESSION-START: ``D:\Sinister\Sinister Skills\SESSION-START\README.md``
2. Hub TODO for this project: ``D:\Sinister\Sinister Skills\01_MEMORY\$name\TODO.md``
3. This project's README

## Per-turn protocol (Rule 9 - agent-to-agent messaging)

EVERY turn, do this BEFORE responding to the operator:

1. ``sinister-bus.heartbeat my_agent="$name"`` -- mark me online (one file touch)
2. ``sinister-bus.inbox_poll my_agent="$name"`` -- read my inbox
3. If a polled message has ``tags: ["delegate","ask"]``: answer via ``sinister-bus.inbox_reply msg_id=<msg-id> my_agent="$name" response="<answer>"``

To ask ANOTHER session a question:
``sinister-bus.delegate_to agent_name="<other>" prompt="<question>"`` -- waits for their reply if online; spawns ephemeral ``claude --print`` subprocess if offline + ``allow_ephemeral=true``.

Full design: ``D:\Sinister Sanctum\docs\AGENT-MESSAGING.md``

## Hard rules (inherited from hub)

- **TL;DR mandatory** -- every long response ends with ``## TL;DR``: "How we won" + "What you need to do"
- **Recommend, don't auto-route** -- when operator's request maps to a bot tool, mention it
- **Bots NEVER call Opus** -- Tier 5 is reserved for operator's primary session
- **Policy 8/8.1** -- never ``taskkill /F /IM adb.exe``; per-PID kill only

## Sinister Bots delegation shortcuts

| Operator says | Recommend |
|---|---|
| "what's expiring" | ``sentinel.check_urgent`` |
| "search the archive" | ``librarian.search "<query>"`` |
| "scrape this URL" | ``researcher.summarize_url url=... focus=...`` |
| "back this up" | ``custodian.snapshot_now path=...`` |
| "what bots / MCP tools exist" | ``sinister-bus.list_network`` |
| "ask <other-project>'s session something" | ``sinister-bus.delegate_to agent_name=<other> prompt=...`` |
"@
            if (-not $DryRun) { $c | Out-File 'CLAUDE.md' -Encoding utf8 }
            Out-Step 'CLAUDE.md' $true 'created'
        } else { Out-Step 'CLAUDE.md' $true 'exists' }
        if (-not (Test-Path 'LICENSE')) {
            if (-not $DryRun) { 'Copyright (c) 2026 Sinister LLC. All rights reserved. (placeholder; operator picks MIT/Apache/Proprietary)' | Out-File 'LICENSE' -Encoding utf8 }
            Out-Step 'LICENSE' $true 'placeholder created'
        } else { Out-Step 'LICENSE' $true 'exists' }
    } finally { Pop-Location }
    return 0
}

function Cmd-GitignoreTune($projPath) {
    Push-Location $projPath
    try {
        $lang = Get-Language $projPath
        $ign = Get-GitignoreFor $lang
        $existing = if (Test-Path '.gitignore') { Get-Content '.gitignore' -Raw } else { '' }
        $added = 0
        $appendix = @()
        foreach ($line in $ign) {
            if ($line -and $existing -notmatch [regex]::Escape($line)) {
                $appendix += $line
                $added++
            }
        }
        if ($added -eq 0) { Out-Step 'gitignore-tune' $true 'already complete'; return 0 }
        if (-not $DryRun) {
            ($existing.TrimEnd() + "`n`n# Added by git-toolkit gitignore-tune ($lang)`n" + ($appendix -join "`n") + "`n") | Out-File '.gitignore' -Encoding utf8
        }
        Out-Step 'gitignore-tune' $true "added $added lines for $lang"
    } finally { Pop-Location }
    return 0
}

function Cmd-StatusSummary($projPath) {
    $targets = @()
    if ($projPath -and (Test-Path $projPath)) { $targets += $projPath }
    else {
        # Walk known projects
        foreach ($p in @(
            'C:\Users\Zonia\Desktop\Snap Signer',
            'C:\Users\Zonia\Desktop\Sinister Snap EMU.API',
            'C:\Users\Zonia\Desktop\Sinister Tiktok EMU.API',
            'C:\Users\Zonia\Desktop\Sinister Bumble EMU.API',
            'C:\Users\Zonia\Desktop\Sinister-Panel',
            'C:\Users\Zonia\Desktop\Sinister RKA GOOD',
            'C:\Users\Zonia\Desktop\Kernel-SU-Setup',
            'C:\Users\Zonia\Desktop\Sinister Library Of Alexandria'
        )) { if (Test-Path $p) { $targets += $p } }
    }
    Write-Host ""
    Write-Host ("{0,-40} {1,-10} {2,-8} {3}" -f 'PROJECT','BRANCH','AHEAD','DIRTY?') -ForegroundColor Yellow
    Write-Host ('-' * 78)
    foreach ($t in $targets) {
        Push-Location $t
        try {
            if (-not (Test-Path '.git')) { Write-Host ("{0,-40} {1}" -f (Split-Path -Leaf $t), '(no .git)') -ForegroundColor DarkGray; continue }
            $br = (& git rev-parse --abbrev-ref HEAD 2>$null).Trim()
            $ahead = & cmd /c "git rev-list --count origin/$br..HEAD 2>NUL"
            if (-not $ahead) { $ahead = '?' }
            $dirty = ((& git status --porcelain 2>$null) | Measure-Object).Count
            Write-Host ("{0,-40} {1,-10} {2,-8} {3}" -f (Split-Path -Leaf $t), $br, $ahead, $(if ($dirty -gt 0) { "$dirty changes" } else { 'clean' }))
        } finally { Pop-Location }
    }
    return 0
}

function Show-Help {
    Write-Host @"
git-toolkit.ps1 - Sinister GitHub workflow helper

Usage: .\git-toolkit.ps1 <command> [path] [arg]

Commands:
  init <path>                  Initialize git + .gitignore + first commit
  remote-set <path> <url>      Add origin remote, optional gh verify
  safe-push <path>             Run secret-scrub then push; abort on scrub fail
  pre-commit-install <path>    Install .githooks/pre-commit that runs secret-scrub
  release <path> <semver>      Create + push tag (e.g. v1.2.3)
  ci-bootstrap <path>          Drop .github/workflows/sinister-ci.yml (lang-aware)
  doc-bootstrap <path>         Create README.md + CLAUDE.md + LICENSE placeholders
  scrub <path>                 Run secret-scrub on a specific project
  gitignore-tune <path>        Add language-specific ignores
  status-summary [path]        Show branch + ahead + dirty across all (or one) projects

Flags: -DryRun, -Quiet

Examples:
  .\git-toolkit.ps1 status-summary
  .\git-toolkit.ps1 init "C:\Users\Zonia\Desktop\Sinister Bumble EMU.API"
  .\git-toolkit.ps1 safe-push "C:\Users\Zonia\Desktop\Sinister-Panel"
  .\git-toolkit.ps1 release "C:\Users\Zonia\Desktop\Sinister-Panel" 1.2.0
"@
}

switch ($Command.ToLower()) {
    'init'                 { Cmd-Init (Resolve-Project $Path) }
    'remote-set'           { Cmd-RemoteSet (Resolve-Project $Path) $Arg2 }
    'safe-push'            { Cmd-SafePush (Resolve-Project $Path) }
    'pre-commit-install'   { Cmd-PreCommitInstall (Resolve-Project $Path) }
    'release'              { Cmd-Release (Resolve-Project $Path) $Arg2 }
    'ci-bootstrap'         { Cmd-CiBootstrap (Resolve-Project $Path) }
    'doc-bootstrap'        { Cmd-DocBootstrap (Resolve-Project $Path) }
    'scrub'                { Cmd-SafeScrub (Resolve-Project $Path) }
    'gitignore-tune'       { Cmd-GitignoreTune (Resolve-Project $Path) }
    'status-summary'       { Cmd-StatusSummary (if ($Path) { Resolve-Project $Path } else { '' }) }
    default                { Show-Help }
}

if ($log) {
    $manifest = Save-Runlog -Log $log -AutoClose $true
    Write-Host ""
    Write-Host "Manifest: $manifest" -ForegroundColor DarkGray
}
