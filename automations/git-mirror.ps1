# git-mirror.ps1 - mirror Sinister projects to the self-hosted Gitea instance
# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
#
# Commands:
#   git-mirror.ps1 -Cmd init     -ProjectKey <key>   Create the Gitea repo + add
#                                                    `sanctum` remote to the local
#                                                    project.
#   git-mirror.ps1 -Cmd push     -ProjectKey <key>   Push current branch to the
#                                                    `sanctum` remote.
#   git-mirror.ps1 -Cmd push-all                     Loop over every project in
#                                                    projects.json and push.
#   git-mirror.ps1 -Cmd status                       For each project: local HEAD,
#                                                    sanctum HEAD, github HEAD (if
#                                                    origin set), divergence.
#
# Reads creds from D:\Sinister Sanctum\tools\sanctum-git\.env. Gracefully fails
# (with a helpful message) if .env is absent or fields are placeholder values.
#
# Every push is logged to:
#   D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\script-runs\
#       git-mirror-<UTC>.json
#
# This script NEVER pushes for the operator without an explicit -Cmd push/push-all
# invocation. It does NOT touch ~/.claude/.mcp.json. It does NOT modify
# panel source, window-manager source, or start-sinister-session.ps1.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('init', 'push', 'push-all', 'status')]
    [string]$Cmd,

    [string]$ProjectKey = '',

    [string]$Branch = '',

    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'git-mirror :: sanctum-git'

# ---- palette ----
$Purple = 'DarkMagenta'
$LightP = 'Magenta'
$White  = 'White'
$Glow   = 'Green'
$Warn   = 'Yellow'
$Red    = 'Red'
$Dim    = 'DarkGray'
$Accent = 'Cyan'

function Say($t, $c = $White) { Write-Host $t -ForegroundColor $c }

# ---- paths ----
$SanctumRoot   = 'D:\Sinister Sanctum'
$ProjectsJson  = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
$EnvFile       = Join-Path $SanctumRoot 'tools\sanctum-git\.env'
$RunLogDir     = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\script-runs'
$GiteaBase     = 'http://localhost:3000'

# ---- helpers ----
function Read-Env([string]$path) {
    $h = @{}
    if (-not (Test-Path $path)) { return $h }
    foreach ($line in Get-Content $path) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith('#')) { continue }
        $eq = $t.IndexOf('=')
        if ($eq -lt 1) { continue }
        $k = $t.Substring(0, $eq).Trim()
        $v = $t.Substring($eq + 1).Trim()
        # strip surrounding quotes if present
        if ($v.Length -ge 2 -and (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'")))) {
            $v = $v.Substring(1, $v.Length - 2)
        }
        $h[$k] = $v
    }
    return $h
}

function Load-Projects {
    if (-not (Test-Path $ProjectsJson)) {
        Say "[FAIL] projects.json missing: $ProjectsJson" $Red
        exit 10
    }
    $raw = Get-Content $ProjectsJson -Raw
    return ($raw | ConvertFrom-Json)
}

function Find-Project($projects, [string]$key) {
    foreach ($p in $projects.projects) {
        if ($p.key -eq $key) { return $p }
    }
    return $null
}

function Gitea-Creds {
    if (-not (Test-Path $EnvFile)) {
        Say "[WARN] $EnvFile not found." $Warn
        Say '       Copy tools\sanctum-git\.env.example to .env and fill in creds.' $Dim
        return $null
    }
    $env = Read-Env $EnvFile
    $u = $env['GITEA_ADMIN_USER']
    $p = $env['GITEA_ADMIN_PASSWORD']
    if (-not $u -or -not $p) {
        Say '[WARN] .env missing GITEA_ADMIN_USER or GITEA_ADMIN_PASSWORD.' $Warn
        return $null
    }
    if ($p -eq 'set_in_gitea_ui_first_run') {
        Say '[WARN] GITEA_ADMIN_PASSWORD is still the placeholder value.' $Warn
        Say '       Complete the Gitea install wizard first, then fill in .env.' $Dim
        return $null
    }
    return @{ User = $u; Pass = $p }
}

function Auth-Header($creds) {
    $pair = "$($creds.User):$($creds.Pass)"
    $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($pair))
    return @{ Authorization = "Basic $b64" }
}

function Gitea-RepoName($project) {
    # Use the same repo NAME as the github side (last segment after `/`).
    # e.g. "Sinister-Systems-LLC/Sinister-Snap-API-EMU" -> "Sinister-Snap-API-EMU"
    if ($project.github) {
        $parts = $project.github -split '/'
        return $parts[-1]
    }
    return $project.key
}

function Gitea-RepoExists($creds, [string]$owner, [string]$repo) {
    try {
        $h = Auth-Header $creds
        $r = Invoke-WebRequest -Uri "$GiteaBase/api/v1/repos/$owner/$repo" -Headers $h -UseBasicParsing -ErrorAction Stop -TimeoutSec 5
        return ($r.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Gitea-CreateRepo($creds, [string]$repoName, [string]$description) {
    $h = Auth-Header $creds
    $h['Content-Type'] = 'application/json'
    $body = @{
        name = $repoName
        description = $description
        private = $true
        auto_init = $false
        default_branch = 'main'
    } | ConvertTo-Json -Compress
    try {
        $r = Invoke-WebRequest -Uri "$GiteaBase/api/v1/user/repos" -Method POST -Headers $h -Body $body -UseBasicParsing -ErrorAction Stop -TimeoutSec 10
        return @{ Ok = $true; Body = $r.Content }
    } catch {
        return @{ Ok = $false; Error = $_.Exception.Message }
    }
}

function In-Repo($root) {
    if (-not (Test-Path $root)) { return $false }
    $g = Join-Path $root '.git'
    return (Test-Path $g)
}

function Git-Run($root, [string[]]$args) {
    Push-Location $root
    try {
        $out = & git @args 2>&1
        return @{ Code = $LASTEXITCODE; Out = ($out -join "`n") }
    } finally {
        Pop-Location
    }
}

function Current-Branch($root) {
    $r = Git-Run $root @('rev-parse', '--abbrev-ref', 'HEAD')
    if ($r.Code -eq 0) { return $r.Out.Trim() }
    return ''
}

function Remote-Url($root, [string]$remote) {
    $r = Git-Run $root @('remote', 'get-url', $remote)
    if ($r.Code -eq 0) { return $r.Out.Trim() }
    return ''
}

function Short-Sha($root, [string]$ref) {
    $r = Git-Run $root @('rev-parse', '--short', $ref)
    if ($r.Code -eq 0) { return $r.Out.Trim() }
    return '--------'
}

function Ensure-RunLogDir {
    if (-not (Test-Path $RunLogDir)) {
        try { New-Item -ItemType Directory -Path $RunLogDir -Force | Out-Null } catch {}
    }
}

function Write-RunLog([string]$cmd, [object]$payload) {
    Ensure-RunLogDir
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $file = Join-Path $RunLogDir "git-mirror-$stamp.json"
    $envelope = [ordered]@{
        manifest    = 'sinister-runlog/v1'
        script      = 'git-mirror'
        command     = $cmd
        agent       = ($env:SINISTER_AGENT_NAME ? $env:SINISTER_AGENT_NAME : 'sinister-sanctum-master')
        started_utc = $stamp
        dry_run     = [bool]$DryRun
        payload     = $payload
    }
    try {
        $envelope | ConvertTo-Json -Depth 8 | Set-Content -Path $file -Encoding UTF8
    } catch {
        # best-effort logging; never abort the user's command for a log write
    }
    return $file
}

# ---- subcommands ----

function Cmd-Init([string]$key) {
    $projects = Load-Projects
    $p = Find-Project $projects $key
    if (-not $p) { Say "[FAIL] no project with key '$key' in projects.json" $Red; exit 11 }

    $creds = Gitea-Creds
    if (-not $creds) { exit 12 }

    $repo = Gitea-RepoName $p
    $owner = $creds.User

    Say ''
    Say "[init] project='$($p.key)' repo='$repo' owner='$owner'" $LightP
    Say "       root=$($p.root)" $Dim

    if (-not (In-Repo $p.root)) {
        Say "[FAIL] $($p.root) is not a git repo (no .git/ folder)." $Red
        exit 13
    }

    # 1) create Gitea repo if missing
    if (Gitea-RepoExists $creds $owner $repo) {
        Say "[OK]    Gitea repo $owner/$repo already exists" $Glow
    } else {
        if ($DryRun) {
            Say "[dry]   would POST /api/v1/user/repos { name=$repo }" $Accent
        } else {
            $desc = "Mirror of $($p.github) — Sinister Sanctum self-host"
            $res = Gitea-CreateRepo $creds $repo $desc
            if ($res.Ok) {
                Say "[OK]    created Gitea repo $owner/$repo" $Glow
            } else {
                Say "[FAIL] create-repo error: $($res.Error)" $Red
                exit 14
            }
        }
    }

    # 2) add `sanctum` remote (auth embedded via http-basic)
    $sanctumUrl = "http://$($creds.User):$($creds.Pass)@localhost:3000/$owner/$repo.git"
    $sanctumUrlSafe = "http://localhost:3000/$owner/$repo.git"
    $existing = Remote-Url $p.root 'sanctum'
    if ($existing) {
        Say "[OK]    'sanctum' remote already set: $existing" $Glow
        Say "        (run 'git -C `"$($p.root)`" remote set-url sanctum <new>' to change)" $Dim
    } else {
        if ($DryRun) {
            Say "[dry]   would: git remote add sanctum $sanctumUrlSafe" $Accent
        } else {
            $r = Git-Run $p.root @('remote', 'add', 'sanctum', $sanctumUrl)
            if ($r.Code -eq 0) {
                Say "[OK]    added 'sanctum' remote -> $sanctumUrlSafe" $Glow
            } else {
                Say "[FAIL] git remote add failed: $($r.Out)" $Red
                exit 15
            }
        }
    }

    Write-RunLog 'init' @{ project = $p.key; owner = $owner; repo = $repo }
    Say ''
    Say "       Next: git-mirror -Cmd push -ProjectKey $($p.key)" $White
}

function Cmd-Push([string]$key) {
    $projects = Load-Projects
    $p = Find-Project $projects $key
    if (-not $p) { Say "[FAIL] no project with key '$key' in projects.json" $Red; exit 21 }

    if (-not (In-Repo $p.root)) {
        Say "[FAIL] $($p.root) is not a git repo." $Red
        exit 22
    }

    $sanctumUrl = Remote-Url $p.root 'sanctum'
    if (-not $sanctumUrl) {
        Say "[FAIL] no 'sanctum' remote on $($p.key). Run -Cmd init first." $Red
        exit 23
    }

    $br = if ($Branch) { $Branch } else { Current-Branch $p.root }
    if (-not $br -or $br -eq 'HEAD') {
        Say "[FAIL] could not resolve a branch (detached HEAD?)" $Red
        exit 24
    }

    Say ''
    Say "[push] project='$($p.key)' branch='$br' -> sanctum" $LightP
    Say "       remote=$sanctumUrl" $Dim

    if ($DryRun) {
        Say "[dry]   would: git push sanctum $br" $Accent
        Write-RunLog 'push' @{ project = $p.key; branch = $br; dry = $true }
        return
    }

    $r = Git-Run $p.root @('push', 'sanctum', $br)
    $logPayload = @{
        project = $p.key
        branch  = $br
        exit    = $r.Code
        out_tail = ($r.Out -split "`n" | Select-Object -Last 6) -join "`n"
    }
    Write-RunLog 'push' $logPayload

    if ($r.Code -eq 0) {
        Say "[OK]    pushed $br to sanctum/$($p.key)" $Glow
    } else {
        Say "[FAIL] git push exit=$($r.Code)" $Red
        Say $r.Out $Dim
        exit 25
    }
}

function Cmd-PushAll {
    $projects = Load-Projects
    $count = 0; $okN = 0; $failN = 0; $skipN = 0
    foreach ($p in $projects.projects) {
        $count++
        if (-not (In-Repo $p.root)) {
            Say "[skip] $($p.key) — not a git repo at $($p.root)" $Warn
            $skipN++
            continue
        }
        $hasSanctum = (Remote-Url $p.root 'sanctum')
        if (-not $hasSanctum) {
            Say "[skip] $($p.key) — no 'sanctum' remote (run -Cmd init first)" $Warn
            $skipN++
            continue
        }
        try {
            Cmd-Push $p.key
            $okN++
        } catch {
            $failN++
        }
    }
    Say ''
    Say "[push-all] total=$count ok=$okN fail=$failN skip=$skipN" $LightP
    Write-RunLog 'push-all' @{ total = $count; ok = $okN; fail = $failN; skip = $skipN }
}

function Cmd-Status {
    $projects = Load-Projects
    Say ''
    Say '  project           branch                          local      sanctum    github' $White
    Say '  ----------------- ------------------------------- ---------- ---------- ----------' $Dim
    foreach ($p in $projects.projects) {
        if (-not (In-Repo $p.root)) {
            $row = '  {0,-17} {1,-31} {2}' -f $p.key, '(not a repo)', $p.root
            Say $row $Warn
            continue
        }
        $br = Current-Branch $p.root
        $localSha = Short-Sha $p.root 'HEAD'
        $sanctumRemote = Remote-Url $p.root 'sanctum'
        $originRemote  = Remote-Url $p.root 'origin'
        $sanctumSha = '--------'
        $githubSha  = '--------'
        if ($sanctumRemote) {
            $r = Git-Run $p.root @('ls-remote', 'sanctum', $br)
            if ($r.Code -eq 0 -and $r.Out) {
                $line = ($r.Out -split "`n" | Select-Object -First 1).Trim()
                if ($line) { $sanctumSha = $line.Substring(0, [Math]::Min(8, $line.Length)) }
            }
        }
        if ($originRemote) {
            $r = Git-Run $p.root @('ls-remote', 'origin', $br)
            if ($r.Code -eq 0 -and $r.Out) {
                $line = ($r.Out -split "`n" | Select-Object -First 1).Trim()
                if ($line) { $githubSha = $line.Substring(0, [Math]::Min(8, $line.Length)) }
            }
        }
        $diverge = ''
        if ($sanctumRemote -and $sanctumSha -ne '--------' -and $sanctumSha -notlike "$localSha*") { $diverge += 'S' }
        if ($originRemote -and $githubSha -ne '--------' -and $githubSha -notlike "$localSha*") { $diverge += 'G' }
        $tag = if ($diverge) { " ($diverge diverges)" } else { '' }
        $row = '  {0,-17} {1,-31} {2,-10} {3,-10} {4,-10}{5}' -f $p.key, $br, $localSha, $sanctumSha, $githubSha, $tag
        Say $row $White
    }
    Say ''
    Say '  Legend: S=sanctum-branch-HEAD-differs-from-local  G=origin-branch-HEAD-differs-from-local' $Dim
    Write-RunLog 'status' @{ projects = ($projects.projects | ForEach-Object { $_.key }) }
}

# ---- dispatch ----
Write-Host ''
Write-Host '  =========================================================' -ForegroundColor $Purple
Write-Host '   G I T - M I R R O R   ::   sanctum-git' -ForegroundColor $LightP
Write-Host '  =========================================================' -ForegroundColor $Purple

switch ($Cmd) {
    'init' {
        if (-not $ProjectKey) { Say '[FAIL] -ProjectKey required for init' $Red; exit 30 }
        Cmd-Init $ProjectKey
    }
    'push' {
        if (-not $ProjectKey) { Say '[FAIL] -ProjectKey required for push' $Red; exit 31 }
        Cmd-Push $ProjectKey
    }
    'push-all' { Cmd-PushAll }
    'status'   { Cmd-Status }
}

exit 0
