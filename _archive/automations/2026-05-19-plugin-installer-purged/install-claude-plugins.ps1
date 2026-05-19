# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19 (v2 — actually installs)
# install-claude-plugins.ps1 -- iterates the claude-plugins-official marketplace
# and calls `claude plugin install <name>@claude-plugins-official` for each.
#
# v1 just copied install commands to clipboard (broken: pasting 171 slash commands
# into the Claude Code prompt didn't trigger 171 plugin installs).
# v2 calls the `claude` CLI directly — same effect as typing /plugin install,
# but works non-interactively and survives restarts.
#
# Args:
#   -Category <name>  install only one category (database/development/etc.)
#   -List             show category counts and exit
#   -DryRun           print what would be installed, but don't actually run claude
#   -SkipRunning      don't pause for confirmation before the install loop

[CmdletBinding()]
param(
    [string]$Category,
    [switch]$List,
    [switch]$DryRun,
    [switch]$SkipRunning
)

$ErrorActionPreference = 'Continue'
$Purple = 'Magenta'

$mpDir  = 'C:\Users\Zonia\.claude\plugins\marketplaces\claude-plugins-official'
$mpJson = Join-Path $mpDir '.claude-plugin\marketplace.json'

if (-not (Test-Path -LiteralPath $mpJson)) {
    Write-Host '[FAIL] marketplace.json not found at: ' -ForegroundColor Red -NoNewline
    Write-Host $mpJson
    exit 1
}

# Sanity-check claude CLI is on PATH
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if (-not $claudeCmd) {
    Write-Host '[FAIL] claude CLI not on PATH. Cannot install plugins.' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host '##  Claude Code plugin bulk-installer (v2 — actually installs)##' -ForegroundColor $Purple
Write-Host '##  marketplace: claude-plugins-official (172 plugins)         ##' -ForegroundColor $Purple
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host ''

# PS5's ConvertFrom-Json is case-insensitive and barfs on duplicate keys.
# Use Python to parse via a temp script (same trick as sync-fleet.ps1).
$pyScript = @'
import json, sys, collections
mp = json.load(open(sys.argv[1], "r", encoding="utf-8"))
inst_path = sys.argv[2]
try:
    inst = json.load(open(inst_path, "r", encoding="utf-8"))
    installed = {k.split("@")[0] for k in inst.get("plugins", {})}
except Exception:
    installed = set()
by_cat = collections.defaultdict(list)
for p in mp["plugins"]:
    by_cat[p.get("category", "uncategorized")].append(p["name"])
out = {
    "name": mp["name"],
    "categories": dict(by_cat),
    "installed": sorted(installed),
}
print(json.dumps(out))
'@
$tempPy = Join-Path $env:TEMP ('_plugin_parse_' + [Guid]::NewGuid().ToString('N').Substring(0,8) + '.py')
[System.IO.File]::WriteAllText($tempPy, $pyScript, [System.Text.UTF8Encoding]::new($false))
$instJson = 'C:\Users\Zonia\.claude\plugins\installed_plugins.json'
try {
    $jsonRaw = & python $tempPy $mpJson $instJson 2>&1
} finally {
    if (Test-Path -LiteralPath $tempPy) { Remove-Item -LiteralPath $tempPy -ErrorAction SilentlyContinue }
}
try {
    $parsed = $jsonRaw | ConvertFrom-Json
} catch {
    Write-Host ('[FAIL] python helper output not parseable: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host $jsonRaw -ForegroundColor DarkGray
    exit 2
}
$mpName = $parsed.name
$byCat = @{}
foreach ($prop in $parsed.categories.PSObject.Properties) {
    $byCat[$prop.Name] = @($prop.Value)
}
$installed = @{}
foreach ($n in $parsed.installed) { $installed[$n] = $true }

if ($List) {
    Write-Host 'Categories (sorted):' -ForegroundColor Cyan
    foreach ($cat in ($byCat.Keys | Sort-Object)) {
        $count = $byCat[$cat].Count
        $alreadyIn = ($byCat[$cat] | Where-Object { $installed.ContainsKey($_) }).Count
        Write-Host ('  {0,-18} {1,3} plugins  ({2} already installed)' -f $cat, $count, $alreadyIn) -ForegroundColor White
    }
    Write-Host ''
    Write-Host 'Re-run with -Category <name> for one category, no args for all, or -DryRun to preview.' -ForegroundColor DarkGray
    exit 0
}

# Build the install queue
$queue = @()
if ($Category) {
    if (-not $byCat.ContainsKey($Category)) {
        Write-Host ('[FAIL] unknown category: ' + $Category) -ForegroundColor Red
        Write-Host 'Available: ' -NoNewline; Write-Host ((($byCat.Keys | Sort-Object) -join ', '))
        exit 1
    }
    $queue = $byCat[$Category] | Sort-Object | Where-Object { -not $installed.ContainsKey($_) }
    Write-Host ('Category: ' + $Category + '  (' + $queue.Count + ' to install)') -ForegroundColor Cyan
} else {
    foreach ($cat in ($byCat.Keys | Sort-Object)) {
        foreach ($n in ($byCat[$cat] | Sort-Object)) {
            if (-not $installed.ContainsKey($n)) { $queue += $n }
        }
    }
    Write-Host ('All ' + $queue.Count + ' plugins (skipping ' + $installed.Count + ' already installed)') -ForegroundColor Cyan
}

if ($queue.Count -eq 0) {
    Write-Host '[OK] nothing to install -- everything in scope is already installed.' -ForegroundColor Green
    exit 0
}

if ($DryRun) {
    Write-Host ''
    Write-Host 'DRY RUN -- would install:' -ForegroundColor Yellow
    foreach ($n in $queue) { Write-Host ('  claude plugin install ' + $n + '@' + $mpName) -ForegroundColor DarkGray }
    Write-Host ''
    Write-Host ('Total: ' + $queue.Count) -ForegroundColor Cyan
    exit 0
}

Write-Host ''
Write-Host 'About to invoke `claude plugin install` for each.' -ForegroundColor Yellow
Write-Host 'First-time installs may be slow (npm/git fetch per plugin); plan on 1-3 min each.' -ForegroundColor DarkGray
Write-Host ('Estimate: ' + [Math]::Ceiling($queue.Count * 0.5) + ' to ' + ($queue.Count * 2) + ' minutes for ' + $queue.Count + ' plugins.') -ForegroundColor DarkGray
Write-Host ''

if (-not $SkipRunning) {
    Write-Host 'Continue? (y/N): ' -ForegroundColor Cyan -NoNewline
    $ans = Read-Host
    if ($ans -notmatch '^[yY]') {
        Write-Host 'Cancelled. Re-run with -SkipRunning to skip this prompt.' -ForegroundColor DarkGray
        exit 0
    }
}

# Install loop
$ok = 0
$fail = 0
$failed = @()
$logFile = Join-Path 'D:\Sinister Sanctum\_shared-memory' ('plugin-bulk-install-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '.log')
"# plugin bulk install log - $(Get-Date -Format 'o')" | Out-File -FilePath $logFile -Encoding utf8

Write-Host ''
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host '##  installing...                                              ##' -ForegroundColor $Purple
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host ''

# Plugins with relative source paths (./external_plugins/<name>, ./plugins/<name>) fail
# when `claude plugin install` is called from outside the marketplace dir — the CLI
# resolves the relative path against cwd. Fix: cd into the marketplace first.
$priorCwd = Get-Location
Set-Location -Path $mpDir
try {
    for ($i = 0; $i -lt $queue.Count; $i++) {
        $name = $queue[$i]
        $idx = $i + 1
        Write-Host ('[' + $idx.ToString().PadLeft(3) + '/' + $queue.Count + '] installing ' + $name + '...') -ForegroundColor White -NoNewline
        $out = & claude plugin install ($name + '@' + $mpName) 2>&1
        $exitcode = $LASTEXITCODE
        $outStr = ($out | ForEach-Object { $_.ToString() }) -join ' '
        if ($exitcode -eq 0 -and ($outStr -match 'Successfully installed' -or $outStr -match 'already installed')) {
            Write-Host ' OK' -ForegroundColor Green
            $ok++
            "[$idx/$($queue.Count)] OK   $name" | Add-Content -Path $logFile -Encoding utf8
        } else {
            Write-Host ' FAIL' -ForegroundColor Red
            $errSnip = if ($outStr.Length -gt 120) { $outStr.Substring(0,120) } else { $outStr }
            Write-Host ('     ' + $errSnip) -ForegroundColor DarkRed
            $fail++
            $failed += $name
            "[$idx/$($queue.Count)] FAIL $name :: $outStr" | Add-Content -Path $logFile -Encoding utf8
        }
    }
} finally {
    Set-Location -Path $priorCwd
}

Write-Host ''
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host ('##  summary: ' + $ok + ' OK / ' + $fail + ' FAIL / ' + $queue.Count + ' total') -ForegroundColor $Purple
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host ''
Write-Host ('log: ' + $logFile) -ForegroundColor DarkGray
if ($fail -gt 0) {
    Write-Host 'Failed plugins:' -ForegroundColor Yellow
    foreach ($n in $failed) { Write-Host ('  - ' + $n) -ForegroundColor DarkYellow }
    Write-Host ''
}
Write-Host 'NEXT STEPS:' -ForegroundColor Yellow
Write-Host '  1. (optional) Run /reload-plugins in any open Claude Code session'
Write-Host '  2. (optional) Restart Claude Code to fully load all the new plugins'
Write-Host ''
Write-Host 'Window auto-closes in 30s. Ctrl+C to keep open.' -ForegroundColor DarkGray
Start-Sleep -Seconds 30
