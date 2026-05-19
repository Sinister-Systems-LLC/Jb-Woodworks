# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
#
# Sanctum self-heal -- hourly drift detector across the fleet.
#
# Read-only: never modifies system state. Writes a per-run report to
# _shared-memory/self-heal-<UTC>.md and prunes reports older than 30 days.
#
# Checks performed:
#   1. Scheduled tasks present (4 expected)
#   2. ~/.claude.json parseable + each MCP server's cwd resolves
#   3. tools/_INDEX.md row paths resolve
#   4. skills/_INDEX.md row paths resolve (both tables)
#   5. Auto-push log freshness (mtime within last 60 min)
#   6. Per-project CLAUDE.md presence (from projects.json)
#   7. Heartbeat freshness (per-agent JSON, must be < 1h old)
#
# Exit codes:
#   0  -- all checks pass (or only warnings)
#   1  -- at least one fail
#   2  -- catastrophic error (path resolution / sanctum-root missing)

[CmdletBinding()]
param(
    [string]$SanctumRoot      = 'D:\Sinister Sanctum',
    [string]$ClaudeJson       = (Join-Path $env:USERPROFILE '.claude.json'),
    [int]$AutoPushFreshMinutes = 60,
    [int]$HeartbeatFreshMinutes = 60,
    [int]$RetentionDays       = 30
)

$ErrorActionPreference = 'Continue'
$Purple = 'Magenta'

function Pass($desc, $detail = '') { @{ Status='PASS'; Desc=$desc; Detail=$detail } }
function Warn($desc, $detail = '') { @{ Status='WARN'; Desc=$desc; Detail=$detail } }
function Fail($desc, $detail = '') { @{ Status='FAIL'; Desc=$desc; Detail=$detail } }

if (-not (Test-Path -LiteralPath $SanctumRoot)) {
    Write-Host "[FATAL] Sanctum root missing: $SanctumRoot" -ForegroundColor Red
    exit 2
}

$results = @{}

# --------------------------------------------- 1. Scheduled tasks ---
$expectedTasks = @('SinisterCustodian','SinisterSanctumAutoPush','RKOJ','SinisterVault')
$taskRows = @()
foreach ($t in $expectedTasks) {
    try {
        $st = Get-ScheduledTask -TaskName $t -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName $t -ErrorAction SilentlyContinue
        $lastRun = if ($info -and $info.LastRunTime) { $info.LastRunTime.ToString('s') } else { 'never' }
        $lastResult = if ($info) { $info.LastTaskResult } else { 'n/a' }
        $row = Pass $t ('state=' + $st.State + ' last=' + $lastRun + ' result=' + $lastResult)
    } catch {
        $row = Fail $t 'NOT REGISTERED'
    }
    $taskRows += $row
}
$results['scheduled-tasks'] = $taskRows

# ---------------------------------------------------- 2. MCP entries ---
$mcpRows = @()
if (Test-Path -LiteralPath $ClaudeJson) {
    try {
        $cj = Get-Content -LiteralPath $ClaudeJson -Raw | ConvertFrom-Json
        $servers = $cj.mcpServers
        if ($servers) {
            $names = $servers.PSObject.Properties.Name
            foreach ($n in $names) {
                $srv = $servers.$n
                $cmd = $srv.command
                # Probe whether the command itself or its primary arg resolves
                $argPath = if ($srv.args -and $srv.args.Count -gt 0) { $srv.args | Where-Object { $_ -match '\\' -or $_ -match '/' } | Select-Object -First 1 } else { $null }
                $missing = @()
                if ($cmd -and ($cmd -match '\\' -or $cmd -match '/') -and -not (Test-Path -LiteralPath $cmd)) {
                    $missing += 'command'
                }
                if ($argPath -and -not (Test-Path -LiteralPath $argPath)) {
                    $missing += "arg=$argPath"
                }
                if ($missing.Count -gt 0) {
                    $mcpRows += Warn $n ('paths missing: ' + ($missing -join ', '))
                } else {
                    $mcpRows += Pass $n ('command=' + $cmd)
                }
            }
            $mcpRows = ,(Pass 'mcp.json parses' ('servers=' + $names.Count)) + $mcpRows
        } else {
            $mcpRows += Warn 'mcpServers' 'key not present (no MCP servers registered)'
        }
    } catch {
        $mcpRows += Fail 'mcp.json' ('parse error: ' + $_.Exception.Message)
    }
} else {
    $mcpRows += Fail 'mcp.json' "missing at $ClaudeJson"
}
$results['mcp-entries'] = $mcpRows

# ------------------------------------------------- 3. tools/_INDEX.md ---
$toolsIndex = Join-Path $SanctumRoot 'tools\_INDEX.md'
$toolRows = @()
if (Test-Path -LiteralPath $toolsIndex) {
    $idxLines = Get-Content -LiteralPath $toolsIndex
    foreach ($l in $idxLines) {
        # Markdown table rows look like `| name | path | desc |`
        if ($l -match '^\|\s*([\w\-]+)\s*\|\s*([^\|]+?)\s*\|') {
            $name = $matches[1].Trim()
            $path = $matches[2].Trim().Trim('`')
            if ($name -in @('Tool','Name','---')) { continue }  # header rows
            # Resolve a folder under tools/<name>/ if path is path-shaped
            if ($path -and ($path -like '*\*' -or $path -like '*/*')) {
                $resolved = $path -replace '`',''
                if (Test-Path -LiteralPath $resolved) {
                    $toolRows += Pass $name 'path resolves'
                } else {
                    $toolRows += Warn $name ('path missing: ' + $resolved)
                }
            } else {
                # Fall back to checking tools/<name>/
                $fld = Join-Path $SanctumRoot ('tools\' + $name)
                if (Test-Path -LiteralPath $fld) {
                    $toolRows += Pass $name 'folder present'
                } else {
                    $toolRows += Warn $name 'folder missing under tools/'
                }
            }
        }
    }
} else {
    $toolRows += Fail 'tools/_INDEX.md' 'file missing'
}
$results['tools-catalog'] = $toolRows

# -------------------------------------------- 4. skills/_INDEX.md ---
# Similar pattern; we just count rows whose first path looks plausible.
$skillsIndex = Join-Path $SanctumRoot 'skills\_INDEX.md'
$skillRows = @()
if (Test-Path -LiteralPath $skillsIndex) {
    $rowCount = 0
    $missing = 0
    foreach ($l in (Get-Content -LiteralPath $skillsIndex)) {
        if ($l -match '^\|\s*([\w\-]+)\s*\|\s*`?([^`|]+)`?\s*\|') {
            $name = $matches[1].Trim()
            $path = $matches[2].Trim().Trim('`')
            if ($name -in @('Slug','Name','---')) { continue }
            $rowCount++
            if ($path -and ($path -like '*\*' -or $path -like '*/*')) {
                if (-not (Test-Path -LiteralPath $path)) { $missing++ }
            }
        }
    }
    $skillRows += if ($missing -eq 0) { Pass 'skills/_INDEX.md' ("rows=$rowCount all paths resolve") } else { Warn 'skills/_INDEX.md' ("rows=$rowCount missing=$missing") }
} else {
    $skillRows += Fail 'skills/_INDEX.md' 'file missing'
}
$results['skills-catalog'] = $skillRows

# -------------------------------------------------- 5. Auto-push log ---
$autoLog = Join-Path $SanctumRoot '_shared-memory\auto-push.log'
$autoRows = @()
if (Test-Path -LiteralPath $autoLog) {
    $age = (Get-Date) - (Get-Item -LiteralPath $autoLog).LastWriteTime
    if ($age.TotalMinutes -lt $AutoPushFreshMinutes) {
        $autoRows += Pass 'auto-push.log' ('mtime=' + [int]$age.TotalMinutes + 'm ago')
    } else {
        $autoRows += Warn 'auto-push.log' ('stale=' + [int]$age.TotalMinutes + 'm ago (threshold=' + $AutoPushFreshMinutes + 'm)')
    }
} else {
    # No log can be normal: the daemon may skip-and-not-log when working tree is clean every time
    $autoRows += Warn 'auto-push.log' 'not present (daemon may always be skipping; check Get-ScheduledTaskInfo SinisterSanctumAutoPush)'
}
$results['auto-push-log'] = $autoRows

# -------------------------------------------------- 6. Per-project CLAUDE.md ---
$projectsJson = Join-Path $SanctumRoot 'automations\session-templates\projects.json'
$projRows = @()
if (Test-Path -LiteralPath $projectsJson) {
    try {
        $proj = Get-Content -LiteralPath $projectsJson -Raw | ConvertFrom-Json
        foreach ($p in $proj.projects) {
            $cm = $p.claude_md
            if ($cm) {
                if (Test-Path -LiteralPath $cm) {
                    $projRows += Pass ('project=' + $p.key) 'claude_md present'
                } else {
                    $projRows += Warn ('project=' + $p.key) ('claude_md missing: ' + $cm)
                }
            } else {
                $projRows += Warn ('project=' + $p.key) 'claude_md unset in projects.json'
            }
        }
    } catch {
        $projRows += Fail 'projects.json' ('parse error: ' + $_.Exception.Message)
    }
} else {
    $projRows += Fail 'projects.json' 'file missing'
}
$results['project-claude-md'] = $projRows

# ------------------------------------------------- 7. Heartbeats ---
$hbDir = Join-Path $SanctumRoot '_shared-memory\heartbeats'
$hbRows = @()
if (Test-Path -LiteralPath $hbDir) {
    $hbFiles = Get-ChildItem -LiteralPath $hbDir -Filter '*.json' -ErrorAction SilentlyContinue
    if ($hbFiles.Count -eq 0) {
        $hbRows += Warn 'heartbeats' 'no *.json files (only build-stamps?)'
    }
    foreach ($f in $hbFiles) {
        $age = (Get-Date) - $f.LastWriteTime
        if ($age.TotalMinutes -lt $HeartbeatFreshMinutes) {
            $hbRows += Pass $f.BaseName ('mtime=' + [int]$age.TotalMinutes + 'm ago')
        } else {
            $hbRows += Warn $f.BaseName ('stale=' + [int]$age.TotalMinutes + 'm ago')
        }
    }
} else {
    $hbRows += Fail 'heartbeats dir' 'missing'
}
$results['heartbeats'] = $hbRows

# ==================================================== Render + persist ===
$utc = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHHmmssZ')
$outDir = Join-Path $SanctumRoot '_shared-memory'
$outFile = Join-Path $outDir ('self-heal-' + $utc + '.md')

$totalPass = 0; $totalWarn = 0; $totalFail = 0
foreach ($key in $results.Keys) {
    foreach ($row in $results[$key]) {
        switch ($row.Status) {
            'PASS' { $totalPass++ }
            'WARN' { $totalWarn++ }
            'FAIL' { $totalFail++ }
        }
    }
}

$lines = @()
$lines += '# Sanctum self-heal report :: ' + $utc
$lines += ''
$lines += '> **Author:** sanctum-self-heal (Claude master agent) :: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm')
$lines += '> **Pass / Warn / Fail:** ' + $totalPass + ' / ' + $totalWarn + ' / ' + $totalFail
$lines += ''
$lines += 'Read-only fleet drift detector. See `tools/sanctum-self-heal/README.md` for thresholds + intent.'
$lines += ''

foreach ($section in @('scheduled-tasks','mcp-entries','tools-catalog','skills-catalog','auto-push-log','project-claude-md','heartbeats')) {
    $lines += '## ' + $section
    $lines += ''
    $lines += '| Status | Item | Detail |'
    $lines += '|---|---|---|'
    foreach ($row in $results[$section]) {
        $sym = switch ($row.Status) {
            'PASS' { '[OK]' }
            'WARN' { '[WARN]' }
            'FAIL' { '[FAIL]' }
        }
        $lines += '| ' + $sym + ' | ' + $row.Desc + ' | ' + $row.Detail + ' |'
    }
    $lines += ''
}

if ($totalFail -gt 0) {
    $lines += '## Action required'
    $lines += ''
    $lines += "$totalFail check(s) FAILED. Investigate the rows tagged [FAIL] above. Common fixes:"
    $lines += '- task missing: re-run the install script in `tools/<service>/install-*-task.ps1`'
    $lines += '- mcp entry: re-run `claude mcp add <name> ...` per the relevant INSTALL doc'
    $lines += '- index row breaks: run a manual sweep over `tools/_INDEX.md` + `skills/_INDEX.md`'
    $lines += ''
} elseif ($totalWarn -gt 0) {
    $lines += '## Notes'
    $lines += ''
    $lines += "$totalWarn check(s) returned warnings (non-blocking). Worth a glance during routine maintenance."
    $lines += ''
}

[System.IO.File]::WriteAllText($outFile, ($lines -join "`n"), [System.Text.UTF8Encoding]::new($false))

Write-Host ''
Write-Host '===============================================' -ForegroundColor $Purple
Write-Host '  Sanctum self-heal :: ' -NoNewline -ForegroundColor $Purple
Write-Host ('PASS=' + $totalPass) -NoNewline -ForegroundColor Green
Write-Host (' WARN=' + $totalWarn) -NoNewline -ForegroundColor Yellow
Write-Host (' FAIL=' + $totalFail) -ForegroundColor Red
Write-Host ('  report: ' + $outFile) -ForegroundColor Gray
Write-Host '===============================================' -ForegroundColor $Purple

# Retention: prune reports older than $RetentionDays days.
$cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -LiteralPath $outDir -Filter 'self-heal-*.md' -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
        Write-Host ('  pruned (older than ' + $RetentionDays + 'd): ' + $_.Name) -ForegroundColor DarkGray
    }

if ($totalFail -gt 0) { exit 1 } else { exit 0 }
