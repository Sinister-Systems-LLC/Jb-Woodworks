# ===========================================================================
# grant-claude-autonomy.ps1
# Author: RKOJ-ELENO :: 2026-05-23 (v2 expanded from 2026-05-19 v1)
# ===========================================================================
#
# ONE-CLICK full-autonomy setup for Claude Code on Sinister Sanctum.
# Idempotent + verbose + reversible (timestamped backups + skippable steps).
#
# v2 covers the 7 steps advertised in Grant-Claude-Autonomy.bat header PLUS
# the 2 anti-revert protections shipped 2026-05-23 evening:
#
#   1. Project trust       :: hasTrustDialogAccepted=true for every Sinister
#                             project root in ~/.claude.json (kills first-edit
#                             trust prompt for spawned EVE sessions).
#   2. Env vars            :: SINISTER_SANCTUM_ROOT + SINISTER_USER (User scope).
#   3. Secrets status      :: surface ANTHROPIC_API_KEY / SINISTER_VAULT_PASSPHRASE /
#                             OPENAI_API_KEY / GEMINI_API_KEY / TELEGRAM_BOT_TOKEN /
#                             LEO_ANTHROPIC_API_KEY status (READ-only, never WRITE).
#   4. MCP verify          :: confirm key MCPs (ruflo + vault + sinister-bus) live in
#                             ~/.claude/.mcp.json. READ-ONLY (CLAUDE.md never-touches).
#   5. Scheduled tasks     :: ensure SinisterSanctumAutoPush + SinisterCustodian +
#                             SinisterSanctumDailyBackup installed + window-hidden.
#   6. Permission allowlist:: write ~/.claude/settings.json with bypassPermissions +
#                             dangerously-skip-permissions allow entries.
#   7. Verification        :: probe RKOJ + Vault + canonical-protections + summary.
#   8. SessionStart hook   :: install canonical-protections-check.ps1 in .claude/settings.json.
#   9. understand-anything :: verify plugin enabled in user + Sanctum project settings.
#
# Re-run anytime to refresh or onboard a new PC. Drop a marker file at
# ~/.sanctum-autonomy-granted on success so Sinister Start.bat can skip-on-rerun.
#
# Usage:
#   grant-claude-autonomy.ps1
#   grant-claude-autonomy.ps1 -Quiet
#   grant-claude-autonomy.ps1 -SkipTaskFix
#   grant-claude-autonomy.ps1 -ReadOnly        (audit-only; no writes)
# ===========================================================================

[CmdletBinding()]
param(
    [switch]$Quiet,
    [switch]$SkipTaskFix,
    [switch]$ReadOnly,
    [string]$SanctumRoot = ''
)

$ErrorActionPreference = 'Continue'
$ProgressPreference    = 'SilentlyContinue'

if (-not $SanctumRoot) {
    foreach ($candidate in @($env:SINISTER_SANCTUM_ROOT, 'D:\Sinister Sanctum', 'C:\Sinister Sanctum', (Join-Path $env:USERPROFILE 'Sinister Sanctum'))) {
        if ($candidate -and (Test-Path (Join-Path $candidate 'CLAUDE.md'))) { $SanctumRoot = $candidate; break }
    }
}
if (-not $SanctumRoot -or -not (Test-Path $SanctumRoot)) {
    Write-Host "  [FAIL] Sanctum root not found." -ForegroundColor Red
    exit 2
}

$UserClaudeJson = Join-Path $env:USERPROFILE '.claude.json'
$UserSettings   = Join-Path $env:USERPROFILE '.claude\settings.json'
$UserMcp        = Join-Path $env:USERPROFILE '.claude\.mcp.json'
$ProjSettings   = Join-Path $SanctumRoot '.claude\settings.json'
$CheckScript    = Join-Path $SanctumRoot 'automations\canonical-protections-check.ps1'
$MarkerFile     = Join-Path $env:USERPROFILE '.sanctum-autonomy-granted'
$Stamp          = (Get-Date -Format 'yyyy-MM-ddTHH-mm-ssZ')

function Write-Status { param([string]$Msg, [ConsoleColor]$Fg = 'White') if (-not $Quiet) { Write-Host $Msg -ForegroundColor $Fg } }
function Write-Step   { param([int]$N, [string]$Title) Write-Status ''; Write-Status "  [Step $N/9] $Title" Magenta; Write-Status "  $('-' * 70)" DarkMagenta }
function Read-Utf8    { param([string]$Path) [System.IO.File]::ReadAllText($Path, [System.Text.UTF8Encoding]::new($false)) }
function Write-Utf8   { param([string]$Path, [string]$Content) [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false)) }
function Backup-File  { param([string]$Path) if (Test-Path $Path) { $bak = "$Path.backup-$Stamp.json"; Copy-Item -Path $Path -Destination $bak -Force; Write-Status "    [OK] backup -> $bak" Gray } }

$summary = [ordered]@{}

Write-Status ''
Write-Status '  ====================================================================' Yellow
Write-Status '  Sinister Sanctum :: Grant Claude Autonomy (v2)' Yellow
Write-Status '  ====================================================================' Yellow
Write-Status "  Sanctum root: $SanctumRoot" White
Write-Status "  User:         $env:USERNAME" White
Write-Status "  Read-only:    $ReadOnly" White
Write-Status ''

# ---------------------------------------------------------------------------
# Step 1 -- Project trust (hasTrustDialogAccepted=true in ~/.claude.json)
# ---------------------------------------------------------------------------
Write-Step 1 'Project trust (hasTrustDialogAccepted=true for Sinister projects)'
try {
    if (Test-Path $UserClaudeJson) {
        if (-not $ReadOnly) { Backup-File $UserClaudeJson }
        $raw = Read-Utf8 $UserClaudeJson
        $cfg = $raw | ConvertFrom-Json
        $trustTargets = @()
        if ($cfg.projects) {
            foreach ($prop in $cfg.projects.PSObject.Properties) {
                $key = $prop.Name
                if ($key -match '(?i)Sinister|Showmasters|jb-woodworks|sanctum') {
                    if ($prop.Value.hasTrustDialogAccepted -ne $true) {
                        $trustTargets += $key
                        if (-not $ReadOnly) {
                            if (-not $prop.Value.PSObject.Properties['hasTrustDialogAccepted']) {
                                Add-Member -InputObject $prop.Value -MemberType NoteProperty -Name 'hasTrustDialogAccepted' -Value $true
                            } else {
                                $prop.Value.hasTrustDialogAccepted = $true
                            }
                        }
                    }
                }
            }
        }
        if ($trustTargets.Count -gt 0) {
            Write-Status "    [+] Will set trust on $($trustTargets.Count) project(s):" Green
            foreach ($t in $trustTargets) { Write-Status "      - $t" Gray }
            if (-not $ReadOnly) {
                $json = $cfg | ConvertTo-Json -Depth 32
                Write-Utf8 $UserClaudeJson $json
                Write-Status "    [OK] ~/.claude.json updated." Green
            }
        } else {
            Write-Status "    [OK] All Sinister projects already trusted." Green
        }
        $summary['Step1_ProjectTrust'] = "$($trustTargets.Count) updated"
    } else {
        Write-Status "    [SKIP] ~/.claude.json not found (Claude Code never run on this user)." Yellow
        $summary['Step1_ProjectTrust'] = 'skipped (no .claude.json)'
    }
} catch {
    Write-Status "    [ERR] Step 1 failed: $($_.Exception.Message)" Red
    $summary['Step1_ProjectTrust'] = 'ERROR'
}

# ---------------------------------------------------------------------------
# Step 2 -- Env vars (SINISTER_SANCTUM_ROOT + SINISTER_USER, User scope)
# ---------------------------------------------------------------------------
Write-Step 2 'Env vars (SINISTER_SANCTUM_ROOT + SINISTER_USER, User scope)'
$envVars = @{
    'SINISTER_SANCTUM_ROOT' = $SanctumRoot
    'SINISTER_USER'         = $env:USERNAME
}
$envChanged = @()
foreach ($k in $envVars.Keys) {
    $current = [Environment]::GetEnvironmentVariable($k, 'User')
    if ($current -ne $envVars[$k]) {
        $envChanged += "$k -> $($envVars[$k])"
        if (-not $ReadOnly) {
            [Environment]::SetEnvironmentVariable($k, $envVars[$k], 'User')
        }
    }
}
if ($envChanged.Count -gt 0) {
    Write-Status "    [+] Set/updated $($envChanged.Count) env var(s):" Green
    foreach ($e in $envChanged) { Write-Status "      - $e" Gray }
    Write-Status "    NOTE: open shells need restart to pick up the new value." Yellow
} else {
    Write-Status "    [OK] All env vars already set correctly." Green
}
$summary['Step2_EnvVars'] = "$($envChanged.Count) changed"

# ---------------------------------------------------------------------------
# Step 3 -- Secrets status (READ-only surface; operator sets manually)
# ---------------------------------------------------------------------------
Write-Step 3 'Secrets status surface (read-only; operator owns the values)'
$secrets = @('ANTHROPIC_API_KEY','SINISTER_VAULT_PASSPHRASE','OPENAI_API_KEY','GEMINI_API_KEY','TELEGRAM_BOT_TOKEN','LEO_ANTHROPIC_API_KEY')
$secretsSet = 0
foreach ($s in $secrets) {
    $v = [Environment]::GetEnvironmentVariable($s, 'User')
    if ($v) {
        Write-Status ('    [SET]   {0,-32} ({1} chars)' -f $s, $v.Length) Green
        $secretsSet++
    } else {
        Write-Status ('    [UNSET] {0,-32}' -f $s) DarkYellow
    }
}
Write-Status "    NOTE: set via [Environment]::SetEnvironmentVariable('NAME','VALUE','User')" Gray
$summary['Step3_Secrets'] = "$secretsSet/$($secrets.Count) set"

# ---------------------------------------------------------------------------
# Step 4 -- MCP verify (READ-ONLY)
# Patched 2026-05-23: was grepping `~/.claude/.mcp.json` only, missing user-scope
# servers added via `claude mcp add -s user`. The authoritative source is
# `claude mcp list`. Falls back to .mcp.json grep if `claude` CLI not on PATH.
# ---------------------------------------------------------------------------
Write-Step 4 'MCP servers (claude mcp list; never edit ~/.claude/.mcp.json)'
$mcpKey = @('ruflo','vault','sinister-bus')
$mcpFound = @()
$claudeCmd = Get-Command claude -ErrorAction SilentlyContinue
if ($claudeCmd) {
    try {
        $listOutput = & claude mcp list 2>&1 | Out-String
        Write-Status "    [INFO] claude mcp list returned $((($listOutput -split [Environment]::NewLine).Count)) lines" Cyan
        foreach ($k in $mcpKey) {
            if ($listOutput -match "(?im)^$([regex]::Escape($k)):.*Connected") {
                Write-Status "    [OK]   $k Connected" Green
                $mcpFound += $k
            } elseif ($listOutput -match "(?im)^$([regex]::Escape($k)):") {
                Write-Status "    [WARN] $k registered but NOT Connected" Yellow
            } else {
                Write-Status "    [WARN] $k NOT registered in claude mcp list" Yellow
            }
        }
    } catch {
        Write-Status "    [ERR] claude mcp list failed: $($_.Exception.Message)" Red
    }
} elseif (Test-Path $UserMcp) {
    Write-Status "    [INFO] claude CLI not on PATH; falling back to ~/.claude/.mcp.json grep" Cyan
    try {
        $mcp = Get-Content $UserMcp -Raw -Encoding UTF8 | ConvertFrom-Json
        $registered = @($mcp.mcpServers.PSObject.Properties.Name)
        Write-Status "    [INFO] $($registered.Count) MCP server(s) registered in .mcp.json" Cyan
        foreach ($k in $mcpKey) {
            if ($registered -contains $k) {
                Write-Status "    [OK]   $k present (registration only; Connect status unknown)" Green
                $mcpFound += $k
            } else {
                Write-Status "    [WARN] $k NOT in .mcp.json" Yellow
            }
        }
    } catch {
        Write-Status "    [ERR] could not parse ~/.claude/.mcp.json: $($_.Exception.Message)" Red
    }
} else {
    Write-Status "    [WARN] neither claude CLI nor ~/.claude/.mcp.json available" Yellow
}
$summary['Step4_MCP'] = "$($mcpFound.Count)/$($mcpKey.Count) key MCPs"

# ---------------------------------------------------------------------------
# Step 5 -- Scheduled tasks (ensure installed + window-hidden)
# ---------------------------------------------------------------------------
Write-Step 5 'Scheduled tasks (Sinister auto-push + custodian + daily backup)'
$wantTasks = @('SinisterSanctumAutoPush','SinisterCustodian','SinisterSanctumDailyBackup','RKOJ','SinisterVault')
$tasksFound = @()
$tasksMissing = @()
foreach ($t in $wantTasks) {
    try {
        $q = & schtasks /Query /TN $t 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Status "    [OK]   $t installed" Green
            $tasksFound += $t
        } else {
            Write-Status "    [MISS] $t NOT installed" Yellow
            $tasksMissing += $t
        }
    } catch {
        Write-Status "    [MISS] $t NOT installed" Yellow
        $tasksMissing += $t
    }
}
if ($tasksMissing.Count -gt 0 -and -not $SkipTaskFix) {
    Write-Status "    NOTE: missing tasks have install-task.ps1 scripts; run them from elevated shell:" Gray
    Write-Status "      D:\Sinister Sanctum\tools\sinister-vault\install-task.ps1" Gray
    Write-Status "      D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian\install-task.ps1" Gray
}
$summary['Step5_Tasks'] = "$($tasksFound.Count)/$($wantTasks.Count) installed"

# ---------------------------------------------------------------------------
# Step 6 -- Permission allowlist (bypassPermissions + dangerously-skip)
# ---------------------------------------------------------------------------
Write-Step 6 'Permission allowlist in ~/.claude/settings.json'
$DANGEROUS_ALLOW = @(
    'Bash(claude *)',
    'Bash(claude:*)',
    'Bash(claude --dangerously-skip-permissions*)',
    'PowerShell(*start-sinister-session.ps1*)',
    'PowerShell(*Sinister Start.bat*)',
    'PowerShell(*claude --dangerously-skip-permissions*)',
    'Bash(*start-sinister-session.ps1*)',
    'Bash(*Sinister Start.bat*)',
    'Bash(*Sinister-Start.bat*)',
    'Bash(powershell.exe:*)'
)
$DEFENSIVE_DENY = @(
    'Bash(rm -rf /*)',
    'Bash(rm -rf C:*)',
    'Bash(rm -rf D:*)',
    'Bash(* --no-verify*)',
    'Bash(git push --force*)',
    'Bash(git push -f *)',
    'Bash(taskkill /F /IM adb.exe*)',
    'Bash(adb kill-server*)',
    'Bash(adb start-server*)'
)
if (Test-Path $UserSettings) {
    if (-not $ReadOnly) { Backup-File $UserSettings }
    try {
        $cfg = Get-Content $UserSettings -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $cfg.permissions) { Add-Member -InputObject $cfg -MemberType NoteProperty -Name 'permissions' -Value ([PSCustomObject]@{ allow = @(); deny = @() }) }
        if (-not $cfg.permissions.allow) { Add-Member -InputObject $cfg.permissions -MemberType NoteProperty -Name 'allow' -Value @() -Force }
        if (-not $cfg.permissions.deny) { Add-Member -InputObject $cfg.permissions -MemberType NoteProperty -Name 'deny' -Value @() -Force }

        $allowExisting = @($cfg.permissions.allow)
        $denyExisting  = @($cfg.permissions.deny)
        $allowAdded = @()
        foreach ($p in $DANGEROUS_ALLOW) { if ($allowExisting -notcontains $p) { $allowExisting += $p; $allowAdded += $p } }
        $denyAdded = @()
        foreach ($p in $DEFENSIVE_DENY) { if ($denyExisting -notcontains $p) { $denyExisting += $p; $denyAdded += $p } }

        $cfg.permissions.allow = $allowExisting
        $cfg.permissions.deny  = $denyExisting

        foreach ($flag in @{'bypassPermissions'=$true; 'skipDangerousModePermissionPrompt'=$true; 'skipAutoPermissionPrompt'=$true}.GetEnumerator()) {
            if (-not $cfg.PSObject.Properties[$flag.Key]) {
                Add-Member -InputObject $cfg -MemberType NoteProperty -Name $flag.Key -Value $flag.Value
            } else {
                $cfg.$($flag.Key) = $flag.Value
            }
        }
        if (-not $cfg.permissions.PSObject.Properties['defaultMode'] -or $cfg.permissions.defaultMode -ne 'bypassPermissions') {
            if ($cfg.permissions.PSObject.Properties['defaultMode']) { $cfg.permissions.defaultMode = 'bypassPermissions' }
            else { Add-Member -InputObject $cfg.permissions -MemberType NoteProperty -Name 'defaultMode' -Value 'bypassPermissions' }
        }

        if (-not $ReadOnly) {
            $json = $cfg | ConvertTo-Json -Depth 32
            Write-Utf8 $UserSettings $json
        }
        Write-Status "    [OK] allow: +$($allowAdded.Count) (total $($allowExisting.Count)) / deny: +$($denyAdded.Count) (total $($denyExisting.Count))" Green
        Write-Status "    [OK] bypassPermissions=true + defaultMode=bypassPermissions + skip prompts" Green
        $summary['Step6_Permissions'] = "+$($allowAdded.Count) allow / +$($denyAdded.Count) deny"
    } catch {
        Write-Status "    [ERR] Step 6 failed: $($_.Exception.Message)" Red
        $summary['Step6_Permissions'] = 'ERROR'
    }
} else {
    Write-Status "    [WARN] ~/.claude/settings.json missing; create by running Claude Code once." Yellow
    $summary['Step6_Permissions'] = 'skipped'
}

# ---------------------------------------------------------------------------
# Step 7 -- Verification (canonical-protections-check)
# ---------------------------------------------------------------------------
Write-Step 7 'Verification (canonical-protections-check.ps1)'
if (Test-Path $CheckScript) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $CheckScript -Quiet | Out-Null
    $code = $LASTEXITCODE
    if ($code -eq 0) {
        Write-Status "    [OK] canonical-protections-check PASSED (all 8 protections)" Green
        $summary['Step7_Verify'] = 'PASS'
    } else {
        Write-Status "    [FAIL] canonical-protections-check returned $code; see _shared-memory\canonical-protections-violations.log" Red
        $summary['Step7_Verify'] = "FAIL exit=$code"
    }
} else {
    Write-Status "    [SKIP] canonical-protections-check.ps1 not found at $CheckScript" Yellow
    $summary['Step7_Verify'] = 'skipped (no script)'
}

# ---------------------------------------------------------------------------
# Step 8 -- SessionStart hook installer
# ---------------------------------------------------------------------------
Write-Step 8 'SessionStart hook installer (.claude/settings.json -> canonical-protections-check.ps1)'
if (Test-Path $ProjSettings) {
    if (-not $ReadOnly) { Backup-File $ProjSettings }
    try {
        $proj = Get-Content $ProjSettings -Raw -Encoding UTF8 | ConvertFrom-Json
        $expectCmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$CheckScript`" -Quiet"
        $hookOk = $false
        if ($proj.hooks -and $proj.hooks.SessionStart) {
            foreach ($entry in $proj.hooks.SessionStart) {
                foreach ($h in $entry.hooks) {
                    if ($h.command -like '*canonical-protections-check*') { $hookOk = $true }
                }
            }
        }
        if ($hookOk) {
            Write-Status "    [OK] SessionStart hook already registered." Green
            $summary['Step8_Hook'] = 'already-installed'
        } else {
            if (-not $proj.PSObject.Properties['hooks']) {
                $hookBlock = [PSCustomObject]@{
                    SessionStart = @(
                        [PSCustomObject]@{
                            matcher = ''
                            hooks = @(
                                [PSCustomObject]@{ type = 'command'; command = $expectCmd }
                            )
                        }
                    )
                }
                Add-Member -InputObject $proj -MemberType NoteProperty -Name 'hooks' -Value $hookBlock
            } else {
                if (-not $proj.hooks.PSObject.Properties['SessionStart']) {
                    Add-Member -InputObject $proj.hooks -MemberType NoteProperty -Name 'SessionStart' -Value @()
                }
                $proj.hooks.SessionStart += [PSCustomObject]@{
                    matcher = ''
                    hooks = @([PSCustomObject]@{ type = 'command'; command = $expectCmd })
                }
            }
            if (-not $ReadOnly) {
                $json = $proj | ConvertTo-Json -Depth 32
                Write-Utf8 $ProjSettings $json
            }
            Write-Status "    [OK] SessionStart hook installed in $ProjSettings" Green
            $summary['Step8_Hook'] = 'installed'
        }
    } catch {
        Write-Status "    [ERR] Step 8 failed: $($_.Exception.Message)" Red
        $summary['Step8_Hook'] = 'ERROR'
    }
} else {
    Write-Status "    [WARN] Sanctum project settings.json missing at $ProjSettings" Yellow
    $summary['Step8_Hook'] = 'skipped (no settings)'
}

# ---------------------------------------------------------------------------
# Step 9 -- understand-anything plugin enablement (user + Sanctum project)
# ---------------------------------------------------------------------------
Write-Step 9 'understand-anything plugin enablement'
$pluginKey = 'understand-anything@understand-anything'
foreach ($target in @(@{ label='user';path=$UserSettings }, @{ label='sanctum-project';path=$ProjSettings })) {
    $label = $target.label; $path = $target.path
    if (-not (Test-Path $path)) {
        Write-Status "    [WARN] $label settings missing" Yellow
        continue
    }
    try {
        $cfg = Get-Content $path -Raw -Encoding UTF8 | ConvertFrom-Json
        $alreadyOn = ($cfg.enabledPlugins -and $cfg.enabledPlugins.$pluginKey -eq $true)
        if ($alreadyOn) {
            Write-Status "    [OK] $label understand-anything already enabled" Green
        } else {
            if (-not $ReadOnly) { Backup-File $path }
            if (-not $cfg.PSObject.Properties['enabledPlugins']) {
                Add-Member -InputObject $cfg -MemberType NoteProperty -Name 'enabledPlugins' -Value ([PSCustomObject]@{})
            }
            if (-not $cfg.enabledPlugins.PSObject.Properties[$pluginKey]) {
                Add-Member -InputObject $cfg.enabledPlugins -MemberType NoteProperty -Name $pluginKey -Value $true
            } else {
                $cfg.enabledPlugins.$pluginKey = $true
            }
            if (-not $ReadOnly) {
                Write-Utf8 $path ($cfg | ConvertTo-Json -Depth 32)
            }
            Write-Status "    [+] $label understand-anything ENABLED" Green
        }
    } catch {
        Write-Status "    [ERR] $label step 9 failed: $($_.Exception.Message)" Red
    }
}
$summary['Step9_UnderstandAnything'] = 'verified'

# ---------------------------------------------------------------------------
# Marker file (Sinister Start.bat first-run detection)
# ---------------------------------------------------------------------------
if (-not $ReadOnly) {
    $markerBody = @"
Sinister Sanctum :: autonomy granted
ts_utc        : $((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))
user          : $env:USERNAME
sanctum_root  : $SanctumRoot
script_version: v2 (2026-05-23)
"@
    Write-Utf8 $MarkerFile $markerBody
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Status ''
Write-Status '  ====================================================================' Yellow
Write-Status '  Summary' Yellow
Write-Status '  ====================================================================' Yellow
foreach ($k in $summary.Keys) {
    Write-Status ('    {0,-26} : {1}' -f $k, $summary[$k]) White
}
Write-Status ''
Write-Status "  Marker: $MarkerFile" Gray
if ($ReadOnly) {
    Write-Status "  Read-only mode: no files were written. Re-run without -ReadOnly to apply." Yellow
} else {
    Write-Status "  Re-run anytime: Grant-Claude-Autonomy.bat" Gray
}
Write-Status ''

exit 0
