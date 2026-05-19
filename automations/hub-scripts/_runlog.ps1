# _runlog.ps1 - shared PowerShell helper for emitting runlog manifests.
# Dot-source this from any operator-run .ps1:
#   . "$PSScriptRoot\_runlog.ps1"        (or full path)
#   $log = Start-Runlog -Script 'my-script'
#   Add-RunlogStep -Log $log -Name 'step-a' -Ok $true -Ms 1234 -Summary '...'
#   Save-Runlog -Log $log -AutoClose $true
#
# Manifest written to:
#   D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\script-runs\<script>-<utc>.json
#
# Bots read these via sinister-bus.runlog_* tools (or directly via _shared/runlog.py).

$script:RunlogRoot = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\script-runs'
$null = New-Item -ItemType Directory -Force -Path $script:RunlogRoot -ErrorAction SilentlyContinue

function Start-Runlog {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Script)
    return [pscustomobject]@{
        schema       = 'sinister-runlog/v1'
        script       = $Script
        started      = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        finished     = $null
        exit_code    = 0
        ok           = $true
        steps        = @()
        outputs      = @{}
        warnings     = @()
        errors       = @()
        next_actions = @()
        auto_close   = $true
        _stepStart   = $null
    }
}

function Add-RunlogStep {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Log,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][bool]$Ok,
        [int]$Ms = 0,
        [string]$Produced = '',
        [string]$Summary = '',
        [string[]]$Warnings = @(),
        [string[]]$Errors = @()
    )
    $step = [ordered]@{
        step    = ($Log.steps.Count + 1)
        name    = $Name
        ok      = $Ok
        ms      = $Ms
        produced = $Produced
        summary  = $Summary
    }
    $Log.steps += [pscustomobject]$step
    if (-not $Ok) {
        $Log.ok = $false
        if ($Log.exit_code -eq 0) { $Log.exit_code = 1 }
    }
    foreach ($w in $Warnings) { $Log.warnings += "${Name}: $w" }
    foreach ($e in $Errors)   { $Log.errors   += "${Name}: $e" }
}

function Add-RunlogNextAction {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Log, [Parameter(Mandatory)][string]$Action)
    $Log.next_actions += $Action
}

function Set-RunlogOutput {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Log, [Parameter(Mandatory)][string]$Key, $Value)
    $Log.outputs[$Key] = $Value
}

function Save-Runlog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Log,
        [bool]$AutoClose = $true,
        [string]$PendingActionsPath = 'D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\runtime-state\PENDING-NEXT-ACTIONS.md'
    )
    $Log.finished   = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $Log.auto_close = $AutoClose

    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $safeName = ($Log.script -replace '[^a-zA-Z0-9_-]', '_')
    $outPath = Join-Path $script:RunlogRoot "$safeName-$stamp.json"

    $json = $Log | ConvertTo-Json -Depth 10
    $tmp  = "$outPath.tmp.$([guid]::NewGuid().Guid)"
    # PS 5.1 -Encoding utf8 writes BOM which trips Python json.loads in older code paths.
    # Use raw bytes (UTF-8 no-BOM) for cross-tool safety.
    [System.IO.File]::WriteAllBytes($tmp, [System.Text.UTF8Encoding]::new($false).GetBytes($json))
    Move-Item -Path $tmp -Destination $outPath -Force

    # Append unconsumed next_actions to PENDING-NEXT-ACTIONS.md
    # Dedup: if an existing UNCHECKED block from the same script has identical
    # action set, skip the append (avoid stale-noise accumulation across reruns).
    if ($Log.next_actions.Count -gt 0) {
        $null = New-Item -ItemType Directory -Force -Path (Split-Path $PendingActionsPath) -ErrorAction SilentlyContinue
        $header = "## $($Log.script) @ $($Log.finished) (manifest: $(Split-Path -Leaf $outPath))"
        $bodyLines = $Log.next_actions | ForEach-Object { "- [ ] $_" }
        $body   = $bodyLines -join "`n"

        $shouldAppend = $true
        if (Test-Path $PendingActionsPath) {
            $existing = Get-Content -Path $PendingActionsPath -Raw -Encoding utf8
            if ($existing) {
                $newSet = [System.Collections.Generic.HashSet[string]]::new()
                foreach ($a in $Log.next_actions) { [void]$newSet.Add($a) }
                $blocks = [regex]::Split($existing, '(?m)^(?=## )') | Where-Object { $_ -match '^## ' }
                foreach ($b in $blocks) {
                    if ($b -notmatch ('^## ' + [regex]::Escape($Log.script) + ' @ ')) { continue }
                    $unchecked = [regex]::Matches($b, '(?m)^- \[ \] (.+)$') | ForEach-Object { $_.Groups[1].Value }
                    if ($unchecked.Count -ne $newSet.Count) { continue }
                    $sameAll = $true
                    foreach ($u in $unchecked) { if (-not $newSet.Contains($u)) { $sameAll = $false; break } }
                    if ($sameAll) { $shouldAppend = $false; break }
                }
            }
        }

        if ($shouldAppend) {
            $entry  = "`n$header`n$body`n"
            Add-Content -Path $PendingActionsPath -Value $entry -Encoding utf8
        }
    }

    return $outPath
}
