# sweep-md-trash.ps1 - md-trash-bin sweeper.
#
# Scans C:\Users\Zonia\Desktop\MD-Trash-Bin for *.md files (excluding README.md),
# extracts title + summary, detects topic via keyword match, prepends an
# auto-categorized timestamp, and moves each file to:
#   D:\Sinister Sanctum\library\<topic>\YYYY-MM-DD-<slug>.md
#
# After all files: writes a sweep manifest to
#   D:\Sinister Sanctum\library\_manifests\sweep-YYYY-MM-DD-HHMM.json
# and emits a runlog manifest via the shared _runlog.ps1 helper if present.
#
# Triggered by:
#   - C:\Users\Zonia\Desktop\Sweep-MD-Trash.bat   (manual)
#   - Windows scheduled task "SinisterMDSweep"    (every ~6h)

[CmdletBinding()]
param(
    [switch]$Quiet
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'MD Trash Sweeper'

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
$TrashDir    = 'C:\Users\Zonia\Desktop\MD-Trash-Bin'
$LibraryDir  = 'D:\Sinister Sanctum\library'
$ManifestDir = Join-Path $LibraryDir '_manifests'

# Topic map. First match wins; topics evaluated in this order.
# Operator: edit this hashtable to extend.
$TopicMap = [ordered]@{
    'snap'     = @('snap','snapchat','snap-emu','cvd','argos','snap-signer')
    'tiktok'   = @('tiktok','tt-emu','tiktok-api')
    'panel'    = @('panel','dashboard','hetzner','sinijkr')
    'kernel'   = @('kernel','kernelsu','apk','detector','lukeshield')
    'signing'  = @('sign','signer','libclient','jni')
    'api'      = @('api','pure-api','endpoint')
    'ui'       = @('ui','ux','design','theme','css','react','tailwind')
    'ops'      = @('deploy','build','ci','pipeline','automation')
    'security' = @('secret','vault','audit','scrub','credential')
    'idea'     = @('idea','invention','sketch','prototype','plan')
}
$DefaultTopic = 'misc'

# UTF-8 BOM encoding (PS 5.1 unicode safety for downstream tools)
$Utf8Bom = [System.Text.UTF8Encoding]::new($true)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Banner {
    if ($Quiet) { return }
    Write-Host ''
    Write-Host '  ==============================================' -ForegroundColor Magenta
    Write-Host '   S I N I S T E R   M D   T R A S H   S W E E P' -ForegroundColor White
    Write-Host '  ==============================================' -ForegroundColor Magenta
    Write-Host "   Source : $TrashDir"  -ForegroundColor DarkGray
    Write-Host "   Sink   : $LibraryDir" -ForegroundColor DarkGray
    Write-Host ''
}

function Get-Slug {
    param([string]$Text)
    $s = ($Text -replace '[^a-zA-Z0-9-]', '-' -replace '-+', '-').Trim('-').ToLower()
    if (-not $s) { $s = 'untitled' }
    if ($s.Length -gt 60) { $s = $s.Substring(0, 60).Trim('-') }
    return $s
}

function Get-Title {
    param([string[]]$Lines, [string]$FallbackName)
    foreach ($line in $Lines) {
        if ($line -match '^\s*#\s+(.+?)\s*$') {
            return $Matches[1].Trim()
        }
    }
    # Fall back to filename (strip extension, kebab-ize spaces)
    return [System.IO.Path]::GetFileNameWithoutExtension($FallbackName)
}

function Get-Summary {
    param([string[]]$Lines)
    # Find first paragraph: skip blanks + headings, capture until next blank.
    $started = $false
    $buf = @()
    foreach ($line in $Lines) {
        $trim = $line.Trim()
        if (-not $started) {
            if ($trim -eq '' -or $trim.StartsWith('#')) { continue }
            $started = $true
            $buf += $trim
        } else {
            if ($trim -eq '') { break }
            if ($trim.StartsWith('#')) { break }
            $buf += $trim
        }
    }
    if (-not $buf) { return '' }
    $summary = ($buf -join ' ')
    if ($summary.Length -gt 280) { $summary = $summary.Substring(0, 277) + '...' }
    return $summary
}

function Get-Topic {
    param([string]$Haystack)
    $lower = $Haystack.ToLower()
    foreach ($topic in $TopicMap.Keys) {
        foreach ($kw in $TopicMap[$topic]) {
            # Word-boundary-ish: surround keyword with non-alnum (or string boundary).
            $pattern = '(^|[^a-z0-9])' + [regex]::Escape($kw.ToLower()) + '([^a-z0-9]|$)'
            if ($lower -match $pattern) {
                return $topic
            }
        }
    }
    return $DefaultTopic
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        $null = New-Item -ItemType Directory -Force -Path $Path -ErrorAction SilentlyContinue
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
Write-Banner

Ensure-Dir $LibraryDir
Ensure-Dir $ManifestDir

if (-not (Test-Path $TrashDir)) {
    Write-Host "  [FAIL] trash dir not found: $TrashDir" -ForegroundColor Red
    exit 2
}

$candidates = Get-ChildItem -Path $TrashDir -Filter '*.md' -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ne 'README.md' }

if (-not $candidates -or $candidates.Count -eq 0) {
    if (-not $Quiet) {
        Write-Host '  [SWEEP] nothing to sweep (trash bin is empty).' -ForegroundColor DarkGray
        Write-Host ''
    }
    # Still emit an empty-sweep runlog so we can see the task fired.
    $runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
    if (Test-Path $runlogHelper) {
        . $runlogHelper
        $log = Start-Runlog -Script 'sweep-md-trash'
        Add-RunlogStep -Log $log -Name 'scan' -Ok $true -Summary 'no files to sweep'
        Set-RunlogOutput -Log $log -Key 'moved_count' -Value 0
        $null = Save-Runlog -Log $log -AutoClose $true
    }
    exit 0
}

$nowStamp = (Get-Date).ToString('yyyy-MM-dd HH:mm')
$dateStamp = (Get-Date).ToString('yyyy-MM-dd')
$manifestStamp = (Get-Date).ToString('yyyy-MM-dd-HHmm')

$moved = @()
$failed = @()
$byTopic = @{}

foreach ($file in $candidates) {
    try {
        $raw = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
        $lines = $raw -split "`r?`n"

        $title   = Get-Title -Lines $lines -FallbackName $file.Name
        $summary = Get-Summary -Lines $lines
        $topic   = Get-Topic -Haystack ($file.Name + "`n" + $title + "`n" + $summary + "`n" + $raw)

        $slug = Get-Slug -Text $title
        $destDir = Join-Path $LibraryDir $topic
        Ensure-Dir $destDir

        $destName = "$dateStamp-$slug.md"
        $destPath = Join-Path $destDir $destName

        # Collision handling: append -2, -3, ...
        $n = 2
        while (Test-Path $destPath) {
            $destName = "$dateStamp-$slug-$n.md"
            $destPath = Join-Path $destDir $destName
            $n++
            if ($n -gt 50) { throw "too many collisions for slug $slug" }
        }

        # Prepend the auto-categorized timestamp under the title.
        $stampLine = "**Auto-categorized:** $nowStamp by md-trash-bin sweeper."
        $hasTitle  = ($lines | Where-Object { $_ -match '^\s*#\s+' } | Select-Object -First 1)
        if ($hasTitle) {
            # Insert blank line + stampLine after the first heading line.
            $newLines = New-Object System.Collections.Generic.List[string]
            $inserted = $false
            foreach ($line in $lines) {
                $newLines.Add($line)
                if (-not $inserted -and $line -match '^\s*#\s+') {
                    $newLines.Add('')
                    $newLines.Add($stampLine)
                    $inserted = $true
                }
            }
            $newContent = [string]::Join("`r`n", $newLines)
        } else {
            # No heading - synthesize one from the filename + prepend.
            $newContent = "# $title`r`n`r`n$stampLine`r`n`r`n$raw"
        }

        # Write to destination (UTF-8 BOM) then remove source.
        [System.IO.File]::WriteAllText($destPath, $newContent, $Utf8Bom)
        Remove-Item -Path $file.FullName -Force -ErrorAction Stop

        $entry = [pscustomobject]@{
            source       = $file.FullName
            destination  = $destPath
            topic        = $topic
            title        = $title
            slug         = $slug
            summary      = $summary
            moved_at     = $nowStamp
        }
        $moved += $entry

        if (-not $byTopic.ContainsKey($topic)) { $byTopic[$topic] = 0 }
        $byTopic[$topic]++

        if (-not $Quiet) {
            Write-Host ("  [MOVED] {0,-30} -> {1}\{2}" -f $file.Name, $topic, $destName) -ForegroundColor Green
        }
    } catch {
        $failed += [pscustomobject]@{
            source = $file.FullName
            error  = "$_"
        }
        if (-not $Quiet) {
            Write-Host ("  [FAIL]  {0}: {1}" -f $file.Name, $_) -ForegroundColor Red
        }
    }
}

# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
$manifest = [pscustomobject]@{
    schema      = 'md-trash-bin/sweep/v1'
    swept_at    = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    source_dir  = $TrashDir
    library_dir = $LibraryDir
    moved_count = $moved.Count
    failed_count = $failed.Count
    by_topic    = $byTopic
    moved       = $moved
    failed      = $failed
}

$manifestPath = Join-Path $ManifestDir "sweep-$manifestStamp.json"
$manifestJson = $manifest | ConvertTo-Json -Depth 8
# Use UTF-8 (no BOM) for the JSON manifest so Python json.loads is happy.
[System.IO.File]::WriteAllText($manifestPath, $manifestJson, [System.Text.UTF8Encoding]::new($false))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
if (-not $Quiet) {
    Write-Host ''
    Write-Host '  ----------------------------------------------' -ForegroundColor Magenta
    Write-Host ("   [OK] swept {0} file(s); {1} failure(s)" -f $moved.Count, $failed.Count) -ForegroundColor White
    if ($byTopic.Count -gt 0) {
        Write-Host '   by topic:' -ForegroundColor DarkGray
        foreach ($t in ($byTopic.Keys | Sort-Object)) {
            Write-Host ("     - {0,-10} {1}" -f $t, $byTopic[$t]) -ForegroundColor Cyan
        }
    }
    Write-Host "   manifest: $manifestPath" -ForegroundColor DarkGray
    Write-Host '  ----------------------------------------------' -ForegroundColor Magenta
    Write-Host ''
}

# ---------------------------------------------------------------------------
# Runlog
# ---------------------------------------------------------------------------
$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) {
    . $runlogHelper
    $log = Start-Runlog -Script 'sweep-md-trash'
    Add-RunlogStep -Log $log -Name 'scan' -Ok $true -Summary "$($candidates.Count) candidate(s)"
    Add-RunlogStep -Log $log -Name 'move' -Ok ($failed.Count -eq 0) -Summary "moved=$($moved.Count) failed=$($failed.Count)"
    Set-RunlogOutput -Log $log -Key 'moved_count' -Value $moved.Count
    Set-RunlogOutput -Log $log -Key 'failed_count' -Value $failed.Count
    Set-RunlogOutput -Log $log -Key 'manifest'    -Value $manifestPath
    Set-RunlogOutput -Log $log -Key 'by_topic'    -Value $byTopic
    if ($failed.Count -gt 0) {
        Add-RunlogNextAction -Log $log -Action "Review $($failed.Count) failed md-trash-bin sweep entries (see manifest $manifestPath)."
    }
    $null = Save-Runlog -Log $log -AutoClose $true
}

if ($failed.Count -gt 0) { exit 1 }
exit 0
