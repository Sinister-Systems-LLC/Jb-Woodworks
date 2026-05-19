# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# sync-fleet.ps1 -- the Skills Hub sync engine.
#
# Single source of truth: D:\Sinister Sanctum\skills\_REGISTRY.yaml
#
# What this script does (READ-ONLY by default; -Apply to commit changes):
#   1. Parse skills/_REGISTRY.yaml (via Python helper since PS 5.1 has no native YAML).
#   2. Diff registry.bots[*] against ~/.claude/.mcp.json -> MUST REGISTER / MUST UNREGISTER list.
#   3. Print install_state summary (registered / pending / operator-click / not-applicable).
#   4. With -Apply: regenerate skills/HUB.md from the registry.
#   5. Write a runlog manifest to 12_LLM_ORCHESTRATION/runtime-state/script-runs/sync-fleet-<UTC>.json.
#
# This script NEVER modifies ~/.claude/.mcp.json (lane discipline -- operator owns that file).
#
# Exit codes:
#   0  clean (no drift, or -Apply succeeded)
#   1  drift detected (without -Apply -- info-only)
#   2  registry parse failure (YAML broken)
#   3  Python unavailable / pyyaml missing
#
# Usage:
#   .\sync-fleet.ps1                  # default dry-run; prints summary + drift list
#   .\sync-fleet.ps1 -Apply           # regenerate HUB.md
#   .\sync-fleet.ps1 -Apply -Verbose  # noisy mode

[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$RegistryPath = 'D:\Sinister Sanctum\skills\_REGISTRY.yaml',
    [string]$HubPath      = 'D:\Sinister Sanctum\skills\HUB.md',
    [string]$McpJsonPath  = (Join-Path $env:USERPROFILE '.claude\.mcp.json'),       # project-scope MCP entries
    [string]$McpUserPath  = (Join-Path $env:USERPROFILE '.claude.json'),             # user-scope MCP entries (claude mcp add -s user)
    [string]$RunlogDir    = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\script-runs'
)

$ErrorActionPreference = 'Continue'
$Purple = 'Magenta'

# --------- pretty printers ---------
function Write-Section { param([string]$T) Write-Host ''; Write-Host ('== ' + $T + ' ==') -ForegroundColor $Purple }
function Write-OK     { param([string]$M) Write-Host ('[ OK ] ' + $M) -ForegroundColor Green }
function Write-Warn   { param([string]$M) Write-Host ('[WARN] ' + $M) -ForegroundColor Yellow }
function Write-Fail   { param([string]$M) Write-Host ('[FAIL] ' + $M) -ForegroundColor Red }
function Write-Info   { param([string]$M) Write-Host ('[INFO] ' + $M) -ForegroundColor White }
function Write-Dim    { param([string]$M) Write-Host ('  ' + $M) -ForegroundColor DarkGray }

Write-Host ''
Write-Host '################################################################' -ForegroundColor $Purple
Write-Host '##  Sanctum Skills Hub :: sync-fleet.ps1                       ##' -ForegroundColor $Purple
Write-Host '##  source of truth: skills\_REGISTRY.yaml                     ##' -ForegroundColor $Purple
Write-Host '################################################################' -ForegroundColor $Purple

# --------- step 1: parse YAML via python helper ---------
Write-Section 'Step 1: parse skills/_REGISTRY.yaml'

if (-not (Test-Path -LiteralPath $RegistryPath)) {
    Write-Fail ('registry not found at: ' + $RegistryPath)
    exit 2
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Fail 'python not on PATH; YAML parse impossible'
    exit 3
}

$yamlToJsonScript = @'
import sys, json
try:
    import yaml
except ImportError:
    print(json.dumps({"_error": "pyyaml not installed; pip install pyyaml"}))
    sys.exit(1)
with open(sys.argv[1], "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
print(json.dumps(data))
'@

# Write helper to temp file (PowerShell -c mangles quotes in here-strings when passed to python)
$tempPy = Join-Path $env:TEMP ('_yaml_to_json_' + [Guid]::NewGuid().ToString('N').Substring(0,8) + '.py')
[System.IO.File]::WriteAllText($tempPy, $yamlToJsonScript, [System.Text.UTF8Encoding]::new($false))
try {
    $jsonRaw = & python $tempPy $RegistryPath 2>&1
} finally {
    if (Test-Path -LiteralPath $tempPy) { Remove-Item -LiteralPath $tempPy -ErrorAction SilentlyContinue }
}
if ($LASTEXITCODE -ne 0) {
    Write-Fail ('YAML parse failed: ' + ($jsonRaw -join ' '))
    exit 2
}

try {
    $registry = $jsonRaw | ConvertFrom-Json
} catch {
    Write-Fail ('JSON conversion failed: ' + $_.Exception.Message)
    exit 2
}

if ($registry.PSObject.Properties.Name -contains '_error') {
    Write-Fail $registry._error
    exit 3
}

$nBots       = ($registry.bots       | Measure-Object).Count
$nTools      = ($registry.tools      | Measure-Object).Count
$nSkills     = ($registry.skills     | Measure-Object).Count
$nExternals  = ($registry.externals  | Measure-Object).Count
$nInventions = ($registry.inventions | Measure-Object).Count
$nTotal      = $nBots + $nTools + $nSkills + $nExternals + $nInventions

Write-OK ('registry version ' + $registry.version + ' parsed -- ' + $nTotal + ' artifacts')
Write-Dim ('  bots       : ' + $nBots)
Write-Dim ('  tools      : ' + $nTools)
Write-Dim ('  skills     : ' + $nSkills)
Write-Dim ('  externals  : ' + $nExternals)
Write-Dim ('  inventions : ' + $nInventions)

# --------- step 2: diff bots[*] against ~/.claude/.mcp.json ---------
Write-Section 'Step 2: diff registry.bots[*] vs ~/.claude/.mcp.json'

$mustRegister   = @()
$mustUnregister = @()
$alreadyOk      = @()

$mcpServerNames = @()
$projectScopeNames = @()
$userScopeNames    = @()

# Project-scope mcp.json
if (Test-Path -LiteralPath $McpJsonPath) {
    try {
        $mcpProject = Get-Content -LiteralPath $McpJsonPath -Raw | ConvertFrom-Json
        if ($mcpProject.mcpServers) {
            $projectScopeNames = @($mcpProject.mcpServers.PSObject.Properties.Name)
            Write-OK ('.mcp.json (project-scope) has ' + $projectScopeNames.Count + ' servers')
        }
    } catch {
        Write-Warn ('.mcp.json parse failed: ' + $_.Exception.Message)
    }
} else {
    Write-Warn ('.mcp.json not found at: ' + $McpJsonPath)
}

# User-scope ~/.claude.json (populated by `claude mcp add -s user ...`)
if (Test-Path -LiteralPath $McpUserPath) {
    try {
        $mcpUser = Get-Content -LiteralPath $McpUserPath -Raw | ConvertFrom-Json
        if ($mcpUser.mcpServers) {
            $userScopeNames = @($mcpUser.mcpServers.PSObject.Properties.Name)
            Write-OK ('.claude.json (user-scope) has ' + $userScopeNames.Count + ' servers')
        }
    } catch {
        Write-Warn ('.claude.json parse failed: ' + $_.Exception.Message)
    }
} else {
    Write-Info ('.claude.json (user-scope) not found at: ' + $McpUserPath)
}

$mcpServerNames = @($projectScopeNames + $userScopeNames | Sort-Object -Unique)
if ($mcpServerNames.Count -eq 0) {
    Write-Warn 'no MCP servers found in either project or user scope'
    Write-Info 'every bot will be reported as MUST REGISTER below.'
}

foreach ($bot in $registry.bots) {
    $slug = $bot.slug
    if ($mcpServerNames -contains $slug) {
        if ($bot.install_state -eq 'registered') {
            $alreadyOk += $slug
        } else {
            # bot is in .mcp.json BUT registry says pending -- registry drift, not action item
            $alreadyOk += $slug
            Write-Warn ("registry says '" + $slug + "' is " + $bot.install_state + " but it IS in mcp.json; update registry")
        }
    } else {
        if ($bot.install_state -eq 'registered') {
            Write-Warn ("registry says '" + $slug + "' is registered but mcp.json doesn't have it")
            $mustRegister += $slug
        } elseif ($bot.install_state -eq 'pending' -or $bot.install_state -eq 'operator-click') {
            $mustRegister += $slug
        }
    }
}

# Servers in .mcp.json that aren't bots in our registry (i.e. external or unknown)
$registryBotSlugs = @($registry.bots | ForEach-Object { $_.slug })
$registryAllSlugs = @($registry.bots + $registry.tools + $registry.externals | ForEach-Object { $_.slug })

foreach ($mcpName in $mcpServerNames) {
    if (-not ($registryAllSlugs -contains $mcpName)) {
        $mustUnregister += $mcpName  # actually "registry doesn't know about it" -- not necessarily wrong
    }
}

Write-Info ('registered + matching   : ' + $alreadyOk.Count)
Write-Info ('MUST REGISTER (gaps)    : ' + $mustRegister.Count)
Write-Info ('in mcp but not registry : ' + $mustUnregister.Count + '  (informational; not actionable)')

if ($mustRegister.Count -gt 0) {
    Write-Host ''
    Write-Host '  MUST REGISTER (operator action):' -ForegroundColor Yellow
    $mustRegister | ForEach-Object { Write-Dim ('  - ' + $_) }
    Write-Host ''
    Write-Info 'how to register: see tools/sinister-vault/INSTALL-MCP.md for the vault pattern;'
    Write-Info 'for vendor MCPs (playwright/context7/sequential-thinking/memory) run:'
    Write-Dim '  & "D:\Sinister Sanctum\automations\install-mcp-servers.ps1"'
}

if ($mustUnregister.Count -gt 0) {
    Write-Host ''
    Write-Host '  in mcp.json but missing from registry (FYI -- maybe non-Sanctum MCPs):' -ForegroundColor DarkYellow
    $mustUnregister | ForEach-Object { Write-Dim ('  - ' + $_) }
}

# --------- step 3: install_state summary ---------
Write-Section 'Step 3: install_state summary'

$allArtifacts = @($registry.bots + $registry.tools + $registry.skills + $registry.externals + $registry.inventions)
$stateSummary = $allArtifacts | Group-Object -Property install_state | Sort-Object -Property Name
foreach ($g in $stateSummary) {
    $color = switch ($g.Name) {
        'registered'      { 'Green' }
        'pending'         { 'Yellow' }
        'operator-click'  { 'Yellow' }
        'not-applicable'  { 'DarkGray' }
        default           { 'White' }
    }
    Write-Host ('  ' + ('{0,-18}' -f $g.Name) + ': ' + $g.Count) -ForegroundColor $color
}

# --------- step 4: regenerate HUB.md (only with -Apply) ---------
Write-Section 'Step 4: regenerate skills/HUB.md'

if (-not $Apply) {
    Write-Info '(dry-run) skipping regeneration. Re-run with -Apply to commit.'
} else {
    $now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mmZ')
    $hub = @()
    $hub += '> **Author:** Sanctum sync-fleet.ps1 (regenerated)  ::  ' + $now
    $hub += '> **Source of truth:** [`skills/_REGISTRY.yaml`](./_REGISTRY.yaml)'
    $hub += '> **Regenerate:** `D:\Sinister Sanctum\automations\sync-fleet.ps1 -Apply`'
    $hub += ''
    $hub += '# Sanctum Skills Hub'
    $hub += ''
    $hub += '**The one place every Sanctum agent reads on cold-start** (per `SESSION-START/00-RULES.md`) to discover every available bot, tool, skill, external import, and invention. Status, install state, security posture, and one-line "when to use it" for each.'
    $hub += ''
    $hub += '## How to use this file'
    $hub += ''
    $hub += '- **As an agent:** read this on cold-start AFTER `DIRECTIVES.md` + `WORK-TOWARD.md`. Skim categories; if you spot a tool that fits your task, follow its `path` for usage.'
    $hub += '- **As the operator:** scan `install_state` columns -- `pending` and `operator-click` rows are what need your action.'
    $hub += '- **To add a new artifact:** append an entry under the right category in `skills/_REGISTRY.yaml`, then run `automations/sync-fleet.ps1 -Apply` to regenerate this file. Never hand-edit `HUB.md` -- the next regen overwrites manual changes.'
    $hub += '- **To remove an artifact:** flip its `status` to `archived` in the registry and run `sync-fleet -Apply`. Source files can then `git mv` into `_archive/`.'
    $hub += ''
    $hub += ('## Counts (as of ' + $now + ')')
    $hub += ''
    $hub += ('- **Bots:**       ' + $nBots + ' (MCP-server agents -- the Sinister Bots fleet)')
    $hub += ('- **Tools:**      ' + $nTools + ' (operator-facing entry points)')
    $hub += ('- **Skills:**     ' + $nSkills + ' (reusable modules consumed by tools/automations/bots)')
    $hub += ('- **Externals:**  ' + $nExternals + ' (imported from public sources via the inflow loop)')
    $hub += ('- **Inventions:** ' + $nInventions + ' (idea cards; some shipped, some building)')
    $hub += ('- **Total:**      ' + $nTotal)
    $hub += ''
    $hub += '## Pending operator clicks'
    $hub += ''
    $pendingItems = $allArtifacts | Where-Object { $_.install_state -in @('pending', 'operator-click') }
    if ($pendingItems.Count -eq 0) {
        $hub += '_(none -- fleet is fully wired)_'
    } else {
        $hub += '| Artifact | Kind | Why it''s pending |'
        $hub += '|---|---|---|'
        foreach ($p in $pendingItems) {
            $hub += ('| **' + $p.name + '** | ' + $p.kind + ' | ' + $p.install_state + ' |')
        }
    }
    $hub += ''
    foreach ($category in @('bots','tools','skills','externals','inventions')) {
        $items = $registry.$category
        if (-not $items -or $items.Count -eq 0) { continue }
        $hub += ('## ' + $category.ToUpper())
        $hub += ''
        $hub += '| Name | Slug | Status | Install state | Description |'
        $hub += '|---|---|---|---|---|'
        foreach ($it in $items) {
            $descShort = if ($it.description.Length -gt 80) { $it.description.Substring(0,77) + '...' } else { $it.description }
            $hub += ('| **' + $it.name + '** | `' + $it.slug + '` | ' + $it.status + ' | ' + $it.install_state + ' | ' + $descShort + ' |')
        }
        $hub += ''
    }
    $hub += '## Security overview'
    $hub += ''
    $hub += 'See [`skills/SECURITY.md`](./SECURITY.md) for the full security posture: deny-list, allow-list scope, Vault Fernet encryption, Codex peer-review gate, lane discipline, external-imports workflow, MCP hygiene.'
    $hub += ''
    $hub += '## Quick links'
    $hub += ''
    $hub += '- [`_REGISTRY.yaml`](./_REGISTRY.yaml) -- the source of truth this file is generated from'
    $hub += '- [`_INDEX.md`](./_INDEX.md) -- the legacy skills catalog (folder + code-library tables)'
    $hub += '- [`../tools/_INDEX.md`](../tools/_INDEX.md) -- the tools catalog'
    $hub += '- [`SECURITY.md`](./SECURITY.md) -- security overview'
    $hub += '- [`../_shared-memory/external-imports/CANDIDATES.md`](../_shared-memory/external-imports/CANDIDATES.md) -- inflow loop'
    $hub += '- [`../_shared-memory/DIRECTIVES.md`](../_shared-memory/DIRECTIVES.md) -- standing operator directives'
    $hub += '- [`../_shared-memory/knowledge/_INDEX.md`](../_shared-memory/knowledge/_INDEX.md) -- the Sanctum brain'
    $hub += '- [`../SESSION-START/00-RULES.md`](../SESSION-START/00-RULES.md) -- cold-start contract'
    $hub += ''
    [System.IO.File]::WriteAllText($HubPath, ($hub -join "`r`n") + "`r`n", [System.Text.UTF8Encoding]::new($true))
    Write-OK ('regenerated: ' + $HubPath + ' (' + $hub.Count + ' lines)')
}

# --------- step 5: runlog manifest ---------
Write-Section 'Step 5: runlog manifest'

if (-not (Test-Path -LiteralPath $RunlogDir)) {
    Write-Warn ('runlog dir missing: ' + $RunlogDir + ' -- skipping manifest')
} else {
    $runlogPath = Join-Path $RunlogDir ('sync-fleet-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '.json')
    $manifest = [pscustomobject]@{
        schema       = 'sinister-runlog/v1'
        script       = 'sync-fleet'
        ran_at       = (Get-Date).ToUniversalTime().ToString('o')
        applied      = [bool]$Apply
        registry     = $RegistryPath
        counts       = @{
            bots = $nBots; tools = $nTools; skills = $nSkills
            externals = $nExternals; inventions = $nInventions; total = $nTotal
        }
        diff = @{
            already_ok      = $alreadyOk
            must_register   = $mustRegister
            must_unregister = $mustUnregister
        }
    }
    $manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $runlogPath -Encoding UTF8
    Write-OK ('runlog: ' + $runlogPath)
}

# --------- exit code ---------
Write-Host ''
if ($mustRegister.Count -gt 0 -and -not $Apply) {
    Write-Warn ('drift detected -- ' + $mustRegister.Count + ' artifact(s) need registration.')
    Write-Info 'this is info-only; re-run with -Apply only regenerates HUB.md (mcp.json stays operator-owned).'
    exit 1
} else {
    Write-OK ('done -- exit 0' + $(if ($Apply) { ' (applied)' } else { ' (dry-run)' }))
    exit 0
}
