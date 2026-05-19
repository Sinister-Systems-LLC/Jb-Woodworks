# aggregate-gotchas.ps1 - operator-run script that scans memory for known
# classifier/sandbox denial patterns and produces a canonical gotcha doc.
#
# The operator runs this. It is NOT called by any bot or by Claude directly.
# Output is operator-reviewed before bots absorb it.
#
# Usage:
#   .\08_AUTOMATIONS\aggregate-gotchas.ps1
#   .\08_AUTOMATIONS\aggregate-gotchas.ps1 -DryRun     # show what it would write
#   .\08_AUTOMATIONS\aggregate-gotchas.ps1 -OpenWhenDone

[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$OpenWhenDone,
    [string]$HubRoot = 'D:\Sinister\Sinister Skills',
    [string]$OutPath = 'D:\Sinister\Sinister Skills\09_REFERENCE\SANDBOX-GOTCHAS.md',
    [int]$MaxBytesPerFile = 1000000,
    [int]$ProgressEveryN = 25
)

$ErrorActionPreference = 'Continue'

# Runlog
. (Join-Path (Split-Path $MyInvocation.MyCommand.Path) '_runlog.ps1')
$log = Start-Runlog -Script 'aggregate-gotchas'
$scriptStart = Get-Date

# Search roots (memory + reference; deliberately NOT 02_MD_ARCHIVE which is huge)
$Roots = @(
    "$HubRoot\01_MEMORY",
    "$HubRoot\03_PROJECTS",
    "$HubRoot\09_REFERENCE",
    "$HubRoot\07_DASHBOARD",
    "$HubRoot\08_AUTOMATIONS",
    "$HubRoot\12_LLM_ORCHESTRATION",
    "$HubRoot\_logs"
) | Where-Object { Test-Path $_ }

# Patterns we treat as gotchas (classifier denials, anti-tamper trips, sandbox
# blocks the operator has documented while working). Each pattern = one category.
$Patterns = @(
    @{ key='gotcha';        regex='GOTCHA[S]?';            label='Operator-tagged GOTCHA' }
    @{ key='sandbox';       regex='sandbox.{0,40}(block|den|reject|flag)'; label='Sandbox block / deny' }
    @{ key='auto-mode';     regex='Denied by auto[- ]?mode\s+classif'; label='Auto-mode classifier deny' }
    @{ key='classifier';    regex='classifier.{0,40}(flag|den|reject|trip|trigger)'; label='Classifier flag/trip' }
    @{ key='anti-tamper';   regex='anti[- ]?tamper';      label='Anti-tamper trip' }
    @{ key='frida';         regex='frida[- ]?spawn|frida.{0,30}(blocked|denied)'; label='Frida-spawn deny' }
    @{ key='kill-rule';     regex='Policy\s*8\.?1?|kill-only-what-you-own|adb\.exe.{0,30}(do not kill|never kill)'; label='Policy 8/8.1 kill-rule trip' }
    @{ key='secret-leak';   regex='secret.{0,30}(leak|exposed)|REDACT(ED)?\s+secret'; label='Secret-leak guard' }
    @{ key='permission';    regex='Permission for this action has been denied'; label='Tool permission deny' }
)

$results = @{}
foreach ($p in $Patterns) { $results[$p.key] = @() }

$filesScanned = 0
$filesSkippedSize = 0
$filesSkippedAutogen = 0
foreach ($root in $Roots) {
    Write-Host "Scanning $root ..." -ForegroundColor Cyan
    $rootCount = 0
    Get-ChildItem -Path $root -Recurse -File -Include *.md, *.txt -ErrorAction SilentlyContinue | ForEach-Object {
        $path = $_.FullName
        if ($_.Length -gt $MaxBytesPerFile) {
            $filesSkippedSize++
            return
        }
        if ($_.Name -eq '_AUTOGEN-NOTE.md') {
            $filesSkippedAutogen++
            return
        }
        $filesScanned++
        $rootCount++
        if (($filesScanned % $ProgressEveryN) -eq 0) {
            Write-Host ("  [..] {0} files scanned ({1} in {2})" -f $filesScanned, $rootCount, (Split-Path -Leaf $root)) -ForegroundColor DarkGray
        }
        try {
            $content = Get-Content -Path $path -Raw -Encoding utf8 -ErrorAction Stop
        } catch { return }
        foreach ($p in $Patterns) {
            $matchInfo = [regex]::Matches($content, $p.regex, 'IgnoreCase')
            if ($matchInfo.Count -gt 0) {
                # Capture 3 lines of context around the first match
                $idx = $matchInfo[0].Index
                $before = [Math]::Max(0, $idx - 120)
                $after = [Math]::Min($content.Length - $before, 240)
                $snippet = $content.Substring($before, $after) -replace "`r`n", ' ' -replace "`n", ' '
                $snippet = $snippet.Trim() -replace '\s+', ' '
                if ($snippet.Length -gt 240) { $snippet = $snippet.Substring(0, 240) + '...' }
                $rel = $path.Replace($HubRoot + '\', '')
                $results[$p.key] += [pscustomobject]@{
                    path = $rel
                    hits = $matchInfo.Count
                    snippet = $snippet
                }
            }
        }
    }
}

# Build the markdown doc
$now = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ssZ')
$sb = [System.Text.StringBuilder]::new()
$null = $sb.AppendLine("# SANDBOX-GOTCHAS - aggregated classifier deny + anti-tamper trip catalog")
$null = $sb.AppendLine()
$null = $sb.AppendLine("**AUTO-GENERATED** by ``08_AUTOMATIONS/aggregate-gotchas.ps1``.")
$null = $sb.AppendLine("**Last run:** $now")
$null = $sb.AppendLine("**Files scanned:** $filesScanned (across $($Roots.Count) roots; ``02_MD_ARCHIVE`` deliberately excluded)")
$null = $sb.AppendLine()
$null = $sb.AppendLine("## What this doc is for")
$null = $sb.AppendLine()
$null = $sb.AppendLine("When the operator (or a bot) attempts an action that has historically been")
$null = $sb.AppendLine("blocked by the sandbox / auto-mode classifier / project policy, the bot should")
$null = $sb.AppendLine("**propose the known-green alternative up front** instead of attempting the")
$null = $sb.AppendLine("blocked path. This doc is the canonical lookup. Bots load it via")
$null = $sb.AppendLine("``12_LLM_ORCHESTRATION/agents/_shared/bot_memory.py``.")
$null = $sb.AppendLine()
$null = $sb.AppendLine("**This is documentation, not bypass.** No bot tries to circumvent a deny;")
$null = $sb.AppendLine("they route the operator to a path that does not trip the deny in the first place.")
$null = $sb.AppendLine()
$null = $sb.AppendLine("## Categories")
$null = $sb.AppendLine()

foreach ($p in $Patterns) {
    $hits = $results[$p.key]
    $null = $sb.AppendLine("### $($p.label)  ($($hits.Count) files)")
    $null = $sb.AppendLine()
    if ($hits.Count -eq 0) {
        $null = $sb.AppendLine("_No hits in scanned roots._")
        $null = $sb.AppendLine()
        continue
    }
    $null = $sb.AppendLine("| File | Hits | Snippet |")
    $null = $sb.AppendLine("|---|---|---|")
    foreach ($h in ($hits | Sort-Object -Property hits -Descending | Select-Object -First 20)) {
        $cleanSnippet = $h.snippet -replace '\|', '\|'
        $null = $sb.AppendLine("| ``$($h.path)`` | $($h.hits) | $cleanSnippet |")
    }
    $null = $sb.AppendLine()
}

$null = $sb.AppendLine("## Operator-curated section (hand-edited; survives regeneration)")
$null = $sb.AppendLine()
$null = $sb.AppendLine("> Re-running this script REPLACES everything above. Append manual notes BELOW the marker.")
$null = $sb.AppendLine()
$null = $sb.AppendLine("<!-- HAND-EDITED-BELOW -->")
$null = $sb.AppendLine()
$null = $sb.AppendLine("Add operator-known gotchas + their known-green alternatives here. Format:")
$null = $sb.AppendLine()
$null = $sb.AppendLine("- **Trip:** what blows up. **Green path:** what to do instead. **Source:** where this was learned.")
$null = $sb.AppendLine()
$null = $sb.AppendLine("Example:")
$null = $sb.AppendLine("- **Trip:** Frida-spawn against TT (TikTok) is sandbox-blocked as anti-tamper-trip per the GOTCHAS doc.")
$null = $sb.AppendLine("  **Green path:** Pure-API path (task #26) - real ideas left untested that don't need Frida.")
$null = $sb.AppendLine("  **Source:** Operator session 2026-05-18, screenshot in chat.")

$output = $sb.ToString()

if ($DryRun) {
    Write-Host ""
    Write-Host "=== DRY RUN - would write $($output.Length) chars to: $OutPath ===" -ForegroundColor Yellow
    Write-Host ""
    Write-Host ($output.Substring(0, [Math]::Min(2000, $output.Length)))
    Write-Host ""
    Write-Host "... (truncated; re-run without -DryRun to write the full file)"
    exit 0
}

# Preserve hand-edited section if file exists
$existing = ''
if (Test-Path $OutPath) {
    $existing = Get-Content $OutPath -Raw -Encoding utf8
    if ($existing -match '(?ms)<!-- HAND-EDITED-BELOW -->(.*)$') {
        $existingHand = $Matches[1].Trim()
        if ($existingHand.Length -gt 50) {
            # Replace our placeholder with the operator's existing content
            $output = $output -replace '(?ms)<!-- HAND-EDITED-BELOW -->.*$', "<!-- HAND-EDITED-BELOW -->`n`n$existingHand"
        }
    }
}

# Atomic write
$tmp = "$OutPath.tmp.$([guid]::NewGuid().Guid)"
$null = New-Item -ItemType Directory -Force -Path (Split-Path $OutPath) -ErrorAction SilentlyContinue
$output | Set-Content -Path $tmp -Encoding utf8 -NoNewline
Move-Item -Path $tmp -Destination $OutPath -Force

Write-Host ""
Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "Wrote: $OutPath"
Write-Host "Files scanned: $filesScanned"
$totalHits = ($results.Values | ForEach-Object { $_.Count } | Measure-Object -Sum).Sum
Write-Host "Total file matches: $totalHits"
if ($filesSkippedSize -gt 0)     { Write-Host "Files skipped (size cap): $filesSkippedSize" -ForegroundColor DarkGray }
if ($filesSkippedAutogen -gt 0)  { Write-Host "Files skipped (autogen):  $filesSkippedAutogen" -ForegroundColor DarkGray }

# Runlog manifest
$ms = [int]((Get-Date) - $scriptStart).TotalMilliseconds
Add-RunlogStep -Log $log -Name 'scan-and-aggregate' -Ok $true -Ms $ms `
    -Produced ($OutPath -replace [regex]::Escape($HubRoot + '\'), '') `
    -Summary "$filesScanned files, $totalHits hits across $($Patterns.Count) patterns"
Set-RunlogOutput -Log $log -Key 'files_scanned' -Value $filesScanned
Set-RunlogOutput -Log $log -Key 'total_hits' -Value $totalHits
Set-RunlogOutput -Log $log -Key 'out_path' -Value $OutPath
if ($filesSkippedSize -gt 0)     { Set-RunlogOutput -Log $log -Key 'skipped_size' -Value $filesSkippedSize }
if ($filesSkippedAutogen -gt 0)  { Set-RunlogOutput -Log $log -Key 'skipped_autogen' -Value $filesSkippedAutogen }
Add-RunlogNextAction -Log $log -Action 'Operator: edit 09_REFERENCE/SANDBOX-GOTCHAS.md below the HAND-EDITED marker to add curated trip -> green-path pairs.'
$manifestPath = Save-Runlog -Log $log -AutoClose $true
Write-Host "Manifest: $manifestPath" -ForegroundColor DarkGray

if ($OpenWhenDone) { Start-Process notepad.exe $OutPath }
