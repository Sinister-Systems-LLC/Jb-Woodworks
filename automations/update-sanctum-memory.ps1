# update-sanctum-memory.ps1 - operator entry-point to append cross-agent directives
# Triggered by C:\Users\Zonia\Desktop\Update-Sanctum-Memory.bat.
#
# Flow:
#   1. Pick target file (DIRECTIVES.md / WORK-TOWARD.md / new note)
#   2. Title (one line)
#   3. Body (multi-line; Ctrl+Z + Enter to finish)
#   4. Prepends a timestamped entry at the TOP of the file
#   5. Emits a runlog manifest

[CmdletBinding()]
param(
    [string]$Target = '',
    [string]$Title = '',
    [string]$Body = ''
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Update Sanctum Memory'

$SharedRoot = 'D:\Sinister Sanctum\_shared-memory'
if (-not (Test-Path $SharedRoot)) { New-Item -ItemType Directory -Path $SharedRoot -Force | Out-Null }

Write-Host ''
Write-Host '  =======================================' -ForegroundColor DarkMagenta
Write-Host '   UPDATE SANCTUM MEMORY (cross-agent)' -ForegroundColor Magenta
Write-Host '  =======================================' -ForegroundColor DarkMagenta
Write-Host ''
Write-Host '  This appends a directive every Claude agent reads on cold-start.' -ForegroundColor Gray
Write-Host ''

if (-not $Target) {
    Write-Host '  Which file?' -ForegroundColor White
    Write-Host '    1) DIRECTIVES.md   standing operator instructions' -ForegroundColor Gray
    Write-Host '    2) WORK-TOWARD.md  current shared goals' -ForegroundColor Gray
    Write-Host '    3) new note        new file in notes/' -ForegroundColor Gray
    $tpick = Read-Host '  choice [1]'
    if (-not $tpick) { $tpick = '1' }
    switch ($tpick) {
        '1' { $Target = 'DIRECTIVES.md' }
        '2' { $Target = 'WORK-TOWARD.md' }
        '3' { $Target = 'note' }
        default { $Target = 'DIRECTIVES.md' }
    }
}

if (-not $Title) {
    Write-Host ''
    Write-Host '  Title (one-line; e.g. "snap-emu: use new 5sim adapter")' -ForegroundColor White
    $Title = Read-Host '  >'
}
if (-not $Title) {
    Write-Host '  [ABORT] title required.' -ForegroundColor Red
    Start-Sleep -Seconds 3
    exit 2
}

if (-not $Body) {
    Write-Host ''
    Write-Host '  Body (multi-line; Ctrl+Z + Enter to finish, or just Enter for none)' -ForegroundColor White
    $bodyLines = @()
    while ($true) {
        $line = Read-Host
        if ($line -eq $null) { break }
        $bodyLines += $line
    }
    $Body = ($bodyLines -join "`n").TrimEnd()
}

$date = (Get-Date).ToString('yyyy-MM-dd HH:mm')

if ($Target -eq 'note') {
    $slug = ($Title -replace '[^a-zA-Z0-9-]', '-' -replace '-+', '-').Trim('-').ToLower()
    if ($slug.Length -gt 40) { $slug = $slug.Substring(0, 40) }
    $datePrefix = (Get-Date).ToString('yyyy-MM-dd')
    $notePath = Join-Path $SharedRoot ("notes\$datePrefix-$slug.md")
    if (-not (Test-Path (Split-Path $notePath))) { New-Item -ItemType Directory -Path (Split-Path $notePath) -Force | Out-Null }
    $noteContent = @"
# $Title

**Captured:** $date
**Origin:** Update-Sanctum-Memory.bat -> note

$Body
"@
    [System.IO.File]::WriteAllText($notePath, $noteContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host ''
    Write-Host "  [OK] note written: $notePath" -ForegroundColor Green
} else {
    $filePath = Join-Path $SharedRoot $Target
    $existing = if (Test-Path $filePath) { Get-Content $filePath -Raw } else { "# $Target`n`n" }
    # Find the divider after the header
    $headerEnd = $existing.IndexOf("`n---`n")
    if ($headerEnd -lt 0) { $headerEnd = $existing.IndexOf("---") }
    if ($headerEnd -lt 0) {
        $newEntry = "## $date - $Title`n`n$Body`n`n"
        $newContent = $existing.TrimEnd() + "`n`n" + $newEntry
    } else {
        $head = $existing.Substring(0, $headerEnd + 5)
        $tail = $existing.Substring($headerEnd + 5)
        $newEntry = "`n## $date - $Title`n`n$Body`n"
        $newContent = $head + $newEntry + $tail
    }
    [System.IO.File]::WriteAllText($filePath, $newContent, [System.Text.UTF8Encoding]::new($false))
    Write-Host ''
    Write-Host "  [OK] appended to $filePath" -ForegroundColor Green
}

# Runlog
$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) {
    . $runlogHelper
    $log = Start-Runlog -Script 'update-sanctum-memory'
    Add-RunlogStep -Log $log -Name 'write' -Ok $true -Summary "$Target :: $Title"
    Set-RunlogOutput -Log $log -Key 'target' -Value $Target
    Set-RunlogOutput -Log $log -Key 'title'  -Value $Title
    $null = Save-Runlog -Log $log -AutoClose $true
}

Write-Host ''
Write-Host '  Every Claude session spawned from now on will read this.' -ForegroundColor DarkGray
Write-Host '  Window auto-closes in 4 seconds.' -ForegroundColor DarkGray
Start-Sleep -Seconds 4
exit 0
