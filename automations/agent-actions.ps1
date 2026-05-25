# agent-actions.ps1 :: per-slug fleet-agent action backend
#
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator (verbatim 2026-05-25 ~00:15Z):
#   "i need you to change the kill fleet selection here to agents. and i need
#    it to be a menu that shows active proejcts that i can see all active
#    running agents and i can scroll through and select the ones i want then
#    i can run actions on them like. kill all, immediate close. save and
#    close button and 2-3 more you think i should have."
#
# Five actions, all per-slug:
#   KillAll        - Stop-Process -Force on PID(s) from spawned-windows.jsonl for <slug>
#   ImmediateClose - graceful close via taskkill /PID <pid> /T  (no /F first)
#   SaveAndClose   - write resume-point via resume-point-write.ps1, then graceful close
#   Pause          - flip _shared-memory/agent-modes/<slug>.json -> paused=true (toggle)
#   Message        - drop inbox row _shared-memory/inbox/<slug>/<utc>-from-operator-broadcast.json
#
# Every action appends a row to _shared-memory/agent-actions.log.
#
# Smoke green path (NO real agent harm):
#   powershell -File automations/agent-actions.ps1 -Action Message -Slug test-smoke -Message "smoke test"
#   powershell -File automations/agent-actions.ps1 -Action Pause -Slug test-smoke
#
# Composes with:
#   automations/eve-launcher/eve.py  _agents_page()        - operator UI (K-key)
#   automations/kill-fleet.ps1                              - fleet-wide variant
#   automations/resume-point-write.ps1                      - SaveAndClose backend
#   _shared-memory/spawned-windows.jsonl                    - PID source-of-truth
#   _shared-memory/heartbeats/<slug>.json                   - liveness source
#   _shared-memory/agent-modes/<slug>.json                  - Pause flag persistence

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('KillAll', 'ImmediateClose', 'SaveAndClose', 'Pause', 'Message')]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [string]$Slug,

    # For -Action Message
    [string]$Message = '',

    # For SaveAndClose: project key passed to resume-point-write.ps1 (defaults to $Slug)
    [string]$ProjectKey = '',

    # Override sanctum root
    [string]$SanctumRoot = $(if ($env:SINISTER_SANCTUM_ROOT) { $env:SINISTER_SANCTUM_ROOT } else { 'D:\Sinister Sanctum' }),

    # Actor for the audit log (defaults to USERNAME)
    [string]$Actor = $(if ($env:USERNAME) { $env:USERNAME } else { 'operator' }),

    # Skip the actual subprocess kill (for smoke tests)
    [switch]$DryRun
)

$ErrorActionPreference = 'Continue'
$script:Result = [ordered]@{
    action    = $Action
    slug      = $Slug
    actor     = $Actor
    ts_utc    = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    ok        = $false
    detail    = ''
    pids      = @()
    dry_run   = [bool]$DryRun
}

function Write-AuditLog {
    param([hashtable]$Row)
    $logPath = Join-Path $SanctumRoot '_shared-memory\agent-actions.log'
    $logDir = Split-Path -Parent $logPath
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
    $json = ($Row | ConvertTo-Json -Compress -Depth 5)
    Add-Content -LiteralPath $logPath -Value $json -Encoding UTF8
}

function Get-PidsForSlug {
    param([string]$TargetSlug)
    $jsonlPath = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'
    $pidsOut = New-Object System.Collections.Generic.HashSet[int]
    if (-not (Test-Path $jsonlPath)) { return @() }
    Get-Content -LiteralPath $jsonlPath -ErrorAction SilentlyContinue | ForEach-Object {
        $line = $_.Trim()
        if (-not $line) { return }
        try { $obj = $line | ConvertFrom-Json -ErrorAction Stop } catch { return }
        if ($obj.closed_at_utc) { return }
        $slugMatch = $false
        if ($obj.agent -and ($obj.agent -ieq $TargetSlug)) { $slugMatch = $true }
        if ($obj.project -and ($obj.project -ieq $TargetSlug)) { $slugMatch = $true }
        if (-not $slugMatch) { return }
        if ($obj.pid -and $obj.pid -gt 0) {
            [void]$pidsOut.Add([int]$obj.pid)
        }
    }
    return @($pidsOut)
}

function Mark-WindowsClosed {
    param([int[]]$ClosedPids, [string]$ClosedBy)
    if (-not $ClosedPids -or $ClosedPids.Count -eq 0) { return }
    $jsonlPath = Join-Path $SanctumRoot '_shared-memory\spawned-windows.jsonl'
    if (-not (Test-Path $jsonlPath)) { return }
    $closedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    $closedSet = New-Object System.Collections.Generic.HashSet[int]
    foreach ($p in $ClosedPids) { [void]$closedSet.Add([int]$p) }
    $rows = @()
    Get-Content -LiteralPath $jsonlPath -ErrorAction SilentlyContinue | ForEach-Object {
        $line = $_.Trim()
        if (-not $line) { return }
        try { $obj = $line | ConvertFrom-Json -ErrorAction Stop } catch { $rows += $line; return }
        if ($obj.pid -and $closedSet.Contains([int]$obj.pid) -and -not $obj.closed_at_utc) {
            $obj | Add-Member -NotePropertyName closed_at_utc -NotePropertyValue $closedAt -Force
            $obj | Add-Member -NotePropertyName closed_by -NotePropertyValue $ClosedBy -Force
        }
        $rows += ($obj | ConvertTo-Json -Compress -Depth 6)
    }
    [System.IO.File]::WriteAllLines($jsonlPath, $rows, [System.Text.UTF8Encoding]::new($false))
}

# ---------------------------------------------------------------------------
# Action: KillAll  (force kill PIDs for <slug>)
# ---------------------------------------------------------------------------
function Invoke-KillAll {
    $pids = Get-PidsForSlug -TargetSlug $Slug
    $script:Result.pids = $pids
    if (-not $pids -or $pids.Count -eq 0) {
        $script:Result.detail = "no live PIDs for slug '$Slug' in spawned-windows.jsonl"
        $script:Result.ok = $true
        return
    }
    $killed = @()
    foreach ($targetPid in $pids) {
        if ($DryRun) {
            Write-Host "  [dry-run] would Stop-Process -Force -Id $targetPid"
            $killed += $targetPid
            continue
        }
        try {
            Stop-Process -Id $targetPid -Force -ErrorAction Stop
            $killed += $targetPid
        } catch {
            Write-Host "  [warn] Stop-Process $targetPid failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    if (-not $DryRun -and $killed.Count -gt 0) {
        Mark-WindowsClosed -ClosedPids $killed -ClosedBy "agent-actions:KillAll:$Actor"
    }
    $script:Result.detail = "force-killed $($killed.Count) of $($pids.Count) PID(s)"
    $script:Result.ok = $true
}

# ---------------------------------------------------------------------------
# Action: ImmediateClose  (graceful taskkill /T without /F)
# ---------------------------------------------------------------------------
function Invoke-ImmediateClose {
    $pids = Get-PidsForSlug -TargetSlug $Slug
    $script:Result.pids = $pids
    if (-not $pids -or $pids.Count -eq 0) {
        $script:Result.detail = "no live PIDs for slug '$Slug'"
        $script:Result.ok = $true
        return
    }
    $closed = @()
    foreach ($targetPid in $pids) {
        if ($DryRun) {
            Write-Host "  [dry-run] would taskkill /PID $targetPid /T"
            $closed += $targetPid
            continue
        }
        try {
            & taskkill.exe /PID $targetPid /T 2>$null | Out-Null
            $closed += $targetPid
        } catch {
            Write-Host "  [warn] taskkill $targetPid failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    if (-not $DryRun -and $closed.Count -gt 0) {
        Mark-WindowsClosed -ClosedPids $closed -ClosedBy "agent-actions:ImmediateClose:$Actor"
    }
    $script:Result.detail = "sent graceful close to $($closed.Count) of $($pids.Count) PID(s)"
    $script:Result.ok = $true
}

# ---------------------------------------------------------------------------
# Action: SaveAndClose  (write resume-point, then graceful close)
# ---------------------------------------------------------------------------
function Invoke-SaveAndClose {
    $rpScript = Join-Path $SanctumRoot 'automations\resume-point-write.ps1'
    $project = if ($ProjectKey) { $ProjectKey } else { $Slug }
    $rpOk = $false
    if (Test-Path $rpScript) {
        if ($DryRun) {
            Write-Host "  [dry-run] would invoke resume-point-write.ps1 -ProjectKey $project"
            $rpOk = $true
        } else {
            try {
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $rpScript `
                    -SanctumRoot $SanctumRoot -ProjectKey $project -AgentName $Slug `
                    -FocusIntent "save-and-close via agent-actions ($Actor)" -Mode 'resume' 2>$null | Out-Null
                $rpOk = $true
            } catch {
                Write-Host "  [warn] resume-point-write failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  [warn] resume-point-write.ps1 missing at $rpScript" -ForegroundColor Yellow
    }
    # Now graceful-close. Reuse ImmediateClose's path but tag closed_by differently.
    $pids = Get-PidsForSlug -TargetSlug $Slug
    $script:Result.pids = $pids
    $closed = @()
    foreach ($targetPid in $pids) {
        if ($DryRun) {
            Write-Host "  [dry-run] would taskkill /PID $targetPid /T"
            $closed += $targetPid
            continue
        }
        try {
            & taskkill.exe /PID $targetPid /T 2>$null | Out-Null
            $closed += $targetPid
        } catch {
            Write-Host "  [warn] taskkill $targetPid failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
    if (-not $DryRun -and $closed.Count -gt 0) {
        Mark-WindowsClosed -ClosedPids $closed -ClosedBy "agent-actions:SaveAndClose:$Actor"
    }
    $rpTag = if ($rpOk) { 'resume-point=ok' } else { 'resume-point=skipped' }
    $script:Result.detail = "$rpTag; graceful-closed $($closed.Count) PID(s)"
    $script:Result.ok = $true
}

# ---------------------------------------------------------------------------
# Action: Pause  (toggle paused flag in agent-modes/<slug>.json)
# ---------------------------------------------------------------------------
function Invoke-Pause {
    $modePath = Join-Path $SanctumRoot "_shared-memory\agent-modes\$Slug.json"
    $modeDir = Split-Path -Parent $modePath
    if (-not (Test-Path $modeDir)) { New-Item -ItemType Directory -Path $modeDir -Force | Out-Null }
    $obj = $null
    if (Test-Path $modePath) {
        try { $obj = Get-Content -LiteralPath $modePath -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $obj = $null }
    }
    if (-not $obj) {
        $obj = [pscustomobject]@{ slug = $Slug }
    }
    $currentlyPaused = $false
    if ($obj.PSObject.Properties.Name -contains 'paused') {
        $currentlyPaused = [bool]$obj.paused
    }
    $newPaused = -not $currentlyPaused
    if ($obj.PSObject.Properties.Name -contains 'paused') {
        $obj.paused = $newPaused
    } else {
        $obj | Add-Member -NotePropertyName paused -NotePropertyValue $newPaused -Force
    }
    $obj | Add-Member -NotePropertyName paused_at_utc -NotePropertyValue (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ") -Force
    $obj | Add-Member -NotePropertyName paused_by -NotePropertyValue $Actor -Force
    if ($DryRun) {
        Write-Host "  [dry-run] would write paused=$newPaused to $modePath"
    } else {
        $json = $obj | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText($modePath, $json, [System.Text.UTF8Encoding]::new($false))
    }
    $script:Result.detail = "paused -> $newPaused (was $currentlyPaused) at $modePath"
    $script:Result.ok = $true
}

# ---------------------------------------------------------------------------
# Action: Message  (drop operator broadcast into inbox/<slug>/)
# ---------------------------------------------------------------------------
function Invoke-Message {
    if (-not $Message) {
        $script:Result.detail = "ERR: -Message <text> required for Message action"
        $script:Result.ok = $false
        return
    }
    $inboxDir = Join-Path $SanctumRoot "_shared-memory\inbox\$Slug"
    if (-not (Test-Path $inboxDir)) { New-Item -ItemType Directory -Path $inboxDir -Force | Out-Null }
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHHmmZ")
    $fname = "$stamp-from-operator-broadcast.json"
    $fpath = Join-Path $inboxDir $fname
    $row = [ordered]@{
        tag           = '[BROADCAST]'
        from          = 'operator'
        from_display  = 'Operator (via EVE Agents page)'
        to            = $Slug
        ts_utc        = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        subject       = 'operator broadcast from EVE Agents page'
        summary       = $Message
        message_full  = $Message
        reply_required = $false
        ack_required  = $false
        author        = 'RKOJ-ELENO :: 2026-05-25'
    }
    if ($DryRun) {
        Write-Host "  [dry-run] would write inbox row $fpath"
    } else {
        $json = $row | ConvertTo-Json -Depth 5
        [System.IO.File]::WriteAllText($fpath, $json, [System.Text.UTF8Encoding]::new($false))
    }
    $script:Result.detail = "inbox row -> $fpath"
    $script:Result.ok = $true
}

# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------
switch ($Action) {
    'KillAll'        { Invoke-KillAll }
    'ImmediateClose' { Invoke-ImmediateClose }
    'SaveAndClose'   { Invoke-SaveAndClose }
    'Pause'          { Invoke-Pause }
    'Message'        { Invoke-Message }
}

# Audit + stdout
$auditRow = @{
    action  = $script:Result.action
    slug    = $script:Result.slug
    actor   = $script:Result.actor
    ts_utc  = $script:Result.ts_utc
    ok      = $script:Result.ok
    detail  = $script:Result.detail
    pids    = $script:Result.pids
    dry_run = $script:Result.dry_run
}
Write-AuditLog -Row $auditRow

# Emit a single JSON line on stdout so eve.py can parse the result
$resultJson = ($script:Result | ConvertTo-Json -Compress -Depth 5)
Write-Output $resultJson

if ($script:Result.ok) { exit 0 } else { exit 1 }
