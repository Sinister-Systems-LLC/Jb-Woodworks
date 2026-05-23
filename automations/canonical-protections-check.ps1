# canonical-protections-check.ps1 :: verify the six "do not revert" operator-canonical protections.
# Author: RKOJ-ELENO :: 2026-05-23
#
# Runs on every session start (registered as a SessionStart hook in .claude/settings.json).
# Verifies the six protections from
#   _shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md
# and logs PASS/FAIL per protection. On any FAIL it prints a high-visibility warning to stderr
# and appends a [REVERT-DETECTED] row to OPERATOR-ACTION-QUEUE.md.
#
# Optional auto-restore: set $env:SINISTER_CANONICAL_PROTECTIONS_AUTORESTORE = '1' to splice
# missing lines back from _shared-memory/canonical-protections-reference/. Default OFF.

[CmdletBinding()]
param(
    [string]$SanctumRoot = 'D:\Sinister Sanctum',
    [switch]$Quiet,
    [switch]$AutoRestore
)

$ErrorActionPreference = 'Continue'
$UserSettings = Join-Path $env:USERPROFILE '.claude\settings.json'
$SanctumSettings = Join-Path $SanctumRoot '.claude\settings.json'
$ClaudeMd = Join-Path $SanctumRoot 'CLAUDE.md'
$Rules = Join-Path $SanctumRoot 'SESSION-START\00-RULES.md'
$KnowledgeDir = Join-Path $SanctumRoot '_shared-memory\knowledge'
$IndexMd = Join-Path $KnowledgeDir '_INDEX.md'
$ViolationsLog = Join-Path $SanctumRoot '_shared-memory\canonical-protections-violations.log'
$OperatorQueue = Join-Path $SanctumRoot '_shared-memory\OPERATOR-ACTION-QUEUE.md'

if ($env:SINISTER_CANONICAL_PROTECTIONS_AUTORESTORE -eq '1') { $AutoRestore = $true }

$results = @()

function Test-Protection {
    param([string]$Id, [string]$Description, [scriptblock]$Check)
    $ok = $false
    $detail = ''
    try {
        $r = & $Check
        if ($r -is [bool]) { $ok = $r } else { $ok = [bool]$r; $detail = "$r" }
    } catch {
        $ok = $false
        $detail = "EXCEPTION: $($_.Exception.Message)"
    }
    $script:results += [PSCustomObject]@{ id = $Id; desc = $Description; ok = $ok; detail = $detail }
    return $ok
}

# P1 -- user settings.json has bypassPermissions:true + dangerously-skip allow entry
Test-Protection -Id 'P1' -Description 'user settings.json bypassPermissions + dangerously-skip allowlist' -Check {
    if (-not (Test-Path $UserSettings)) { return $false }
    $j = Get-Content $UserSettings -Raw | ConvertFrom-Json
    $hasBypass = ($j.bypassPermissions -eq $true) -and ($j.permissions.defaultMode -eq 'bypassPermissions')
    $allow = @($j.permissions.allow)
    $hasDangerous = ($allow | Where-Object { $_ -like '*claude --dangerously-skip-permissions*' }).Count -gt 0
    return ($hasBypass -and $hasDangerous)
} | Out-Null

# P2 -- both settings.json files have understand-anything enabled
Test-Protection -Id 'P2' -Description 'understand-anything plugin enabled (user + Sanctum project)' -Check {
    $ok = $true
    foreach ($f in @($UserSettings, $SanctumSettings)) {
        if (-not (Test-Path $f)) { $ok = $false; continue }
        $j = Get-Content $f -Raw | ConvertFrom-Json
        $ep = $j.enabledPlugins
        if (-not $ep -or -not $ep.'understand-anything@understand-anything') { $ok = $false }
    }
    return $ok
} | Out-Null

# P3 -- CLAUDE.md cold-start step 0 invokes understand-anything
Test-Protection -Id 'P3' -Description 'CLAUDE.md cold-start step 0 = understand-anything pre-call' -Check {
    if (-not (Test-Path $ClaudeMd)) { return $false }
    $c = Get-Content $ClaudeMd -Raw
    return ($c -match 'understand-anything:understand-explain') -and ($c -match 'Cold-start in 7 steps')
} | Out-Null

# P4 -- CLAUDE.md references hidden memory hub
Test-Protection -Id 'P4' -Description 'CLAUDE.md references 01_MEMORY\master\OPERATOR-DIRECTIVES.md hub' -Check {
    if (-not (Test-Path $ClaudeMd)) { return $false }
    $c = Get-Content $ClaudeMd -Raw
    return $c -match '01_MEMORY\\master\\OPERATOR-DIRECTIVES\.md'
} | Out-Null

# P5 -- CLAUDE.md references SANDBOX-GOTCHAS.md
Test-Protection -Id 'P5' -Description 'CLAUDE.md references 09_REFERENCE\SANDBOX-GOTCHAS.md' -Check {
    if (-not (Test-Path $ClaudeMd)) { return $false }
    $c = Get-Content $ClaudeMd -Raw
    return $c -match '09_REFERENCE\\SANDBOX-GOTCHAS\.md'
} | Out-Null

# P6 -- brain entries present + indexed
Test-Protection -Id 'P6' -Description 'Brain entries (do-not-revert + sanctioned-bypasses) present + indexed' -Check {
    $f1 = Join-Path $KnowledgeDir 'do-not-revert-operator-canonical-protections-2026-05-23.md'
    $f2 = Join-Path $KnowledgeDir 'sanctioned-bypasses-doctrine-2026-05-21.md'
    if (-not (Test-Path $f1) -or -not (Test-Path $f2)) { return $false }
    if (-not (Test-Path $IndexMd)) { return $false }
    $idx = Get-Content $IndexMd -Raw
    return ($idx -match 'do-not-revert-operator-canonical-protections-2026-05-23') -and ($idx -match 'sanctioned-bypasses-doctrine-2026-05-21')
} | Out-Null

# Bonus: Rule 11 in 00-RULES.md
Test-Protection -Id 'P7' -Description '00-RULES.md Rule 11 mandates understand-anything pre-call' -Check {
    if (-not (Test-Path $Rules)) { return $false }
    $r = Get-Content $Rules -Raw
    return ($r -match 'Rule 11') -and ($r -match 'understand-anything')
} | Out-Null

# P8 -- every project root in projects.json exists on disk (caught the freeze archived-but-in-picker bug)
Test-Protection -Id 'P8' -Description 'projects.json: every project root exists on disk' -Check {
    $projectsPath = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
    if (-not (Test-Path $projectsPath)) { return $false }
    $proj = Get-Content $projectsPath -Raw | ConvertFrom-Json
    $missing = @()
    foreach ($p in $proj.projects) {
        $root = $p.root
        if (-not $root) { continue }
        if (-not (Test-Path $root)) { $missing += "$($p.key) -> $root" }
    }
    if ($missing.Count -gt 0) {
        $script:p8Missing = $missing
        return $false
    }
    return $true
} | Out-Null

# If P8 failed, include the missing list in the violations log
if ($p8Missing -and $p8Missing.Count -gt 0) {
    Add-Content -Path $ViolationsLog -Value "  P8 missing roots:" -Encoding UTF8 -ErrorAction SilentlyContinue
    foreach ($m in $p8Missing) {
        Add-Content -Path $ViolationsLog -Value "    - $m" -Encoding UTF8 -ErrorAction SilentlyContinue
    }
}

# Report
$ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$fails = $results | Where-Object { -not $_.ok }
$passCount = ($results | Where-Object { $_.ok }).Count
$failCount = $fails.Count

$logLine = "[$ts] canonical-protections-check :: PASS=$passCount FAIL=$failCount"
Add-Content -Path $ViolationsLog -Value $logLine -Encoding UTF8 -ErrorAction SilentlyContinue
foreach ($r in $results) {
    Add-Content -Path $ViolationsLog -Value ("  [$($r.id)] " + ($(if ($r.ok) {'PASS'} else {'FAIL'})) + " :: $($r.desc)" + $(if ($r.detail) { ' :: ' + $r.detail } else { '' })) -Encoding UTF8 -ErrorAction SilentlyContinue
}

if (-not $Quiet) {
    Write-Host ''
    Write-Host '  canonical-protections-check ::' -ForegroundColor DarkMagenta -NoNewline
    Write-Host " PASS=$passCount FAIL=$failCount" -ForegroundColor $(if ($failCount -eq 0) { 'Green' } else { 'Yellow' })
    foreach ($r in $results) {
        $sym = if ($r.ok) { '[OK]' } else { '[FAIL]' }
        $col = if ($r.ok) { 'Green' } else { 'Red' }
        Write-Host "    $sym $($r.id) $($r.desc)" -ForegroundColor $col
    }
    Write-Host ''
}

if ($failCount -gt 0) {
    $banner = "`n## [REVERT-DETECTED] $ts -- $failCount canonical protection(s) FAILED`n"
    $body = ($fails | ForEach-Object { "- $($_.id) :: $($_.desc)" }) -join "`n"
    $note = "`nDoctrine: _shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md`n"
    Add-Content -Path $OperatorQueue -Value ($banner + $body + $note) -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not $Quiet) {
        Write-Host "    [!] Surfaced to OPERATOR-ACTION-QUEUE.md" -ForegroundColor Yellow
    }
}

if ($AutoRestore -and $failCount -gt 0) {
    Write-Host "    [auto-restore enabled but not yet implemented; logging intent only]" -ForegroundColor DarkGray
}

exit $(if ($failCount -eq 0) { 0 } else { 1 })
