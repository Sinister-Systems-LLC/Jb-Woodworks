# capture-invention.ps1 - one-click stub creator for inventions/
# Operator triggers via C:\Users\Zonia\Desktop\Capture-Invention.bat.
#
# Flow:
#   1. Prompt for slug (3-5 dash-separated words)
#   2. Prompt for one-line summary
#   3. Create inventions/YYYY-MM-DD-<slug>.md from _template.md, pre-filled
#   4. Open in notepad
#   5. Emit runlog manifest

[CmdletBinding()]
param(
    [string]$Slug = '',
    [string]$Summary = '',
    [switch]$NoOpen
)

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Capture Invention'

$invDir = 'D:\Sinister Sanctum\inventions'
$tmplPath = Join-Path $invDir '_template.md'
if (-not (Test-Path $tmplPath)) {
    Write-Host '[FAIL] _template.md not found at $tmplPath' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host '  ====================================' -ForegroundColor Magenta
Write-Host '   C A P T U R E   I N V E N T I O N' -ForegroundColor White
Write-Host '  ====================================' -ForegroundColor Magenta
Write-Host ''

if (-not $Slug) {
    Write-Host '  Slug (3-5 dash-separated words, e.g. voice-trigger-deploy):' -ForegroundColor Cyan
    $Slug = Read-Host '  >'
}
$Slug = ($Slug -replace '[^a-zA-Z0-9-]', '-' -replace '-+', '-').Trim('-').ToLower()
if (-not $Slug) { Write-Host '[FAIL] slug required' -ForegroundColor Red; exit 2 }

if (-not $Summary) {
    Write-Host ''
    Write-Host '  One-line summary (what is the idea?):' -ForegroundColor Cyan
    $Summary = Read-Host '  >'
}

$date = (Get-Date).ToString('yyyy-MM-dd')
$timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm')
$fileName = "$date-$Slug.md"
$filePath = Join-Path $invDir $fileName

if (Test-Path $filePath) {
    Write-Host ''
    Write-Host "[WARN] $fileName already exists - opening it instead of overwriting." -ForegroundColor Yellow
} else {
    $tmpl = Get-Content $tmplPath -Raw
    # Pre-fill title + captured timestamp + status
    $tmpl = $tmpl -replace '# <Title of the invention>', "# $($Slug -replace '-', ' ' | ForEach-Object { (Get-Culture).TextInfo.ToTitleCase($_) })"
    $tmpl = $tmpl -replace '\*\*Captured:\*\* YYYY-MM-DD HH:MM', "**Captured:** $timestamp"
    $tmpl = $tmpl -replace '\*\*Status:\*\* idea \| sketching \| designing \| building \| shipped \| abandoned', '**Status:** idea'
    $tmpl = $tmpl -replace '\*\*Origin:\*\* <where the idea came from.*?>', "**Origin:** operator capture via Capture-Invention.bat"
    # Inject summary into Idea section
    $tmpl = $tmpl -replace 'One paragraph: what''s the thing\?', $Summary
    [System.IO.File]::WriteAllText($filePath, $tmpl, [System.Text.UTF8Encoding]::new($false))
    Write-Host ''
    Write-Host "  [OK] created $fileName" -ForegroundColor Green
}

if (-not $NoOpen) {
    Start-Process notepad.exe -ArgumentList "`"$filePath`"" -ErrorAction SilentlyContinue
    Write-Host "  [OK] opened in notepad - flesh out + save + close when done" -ForegroundColor Green
}

# Runlog
$runlogHelper = 'D:\Sinister\Sinister Skills\08_AUTOMATIONS\_runlog.ps1'
if (Test-Path $runlogHelper) {
    . $runlogHelper
    $log = Start-Runlog -Script 'capture-invention'
    Add-RunlogStep -Log $log -Name 'create' -Ok $true -Summary "$fileName"
    Set-RunlogOutput -Log $log -Key 'file' -Value $filePath
    Set-RunlogOutput -Log $log -Key 'slug' -Value $Slug
    $null = Save-Runlog -Log $log -AutoClose $true
}

Write-Host ''
Write-Host '  Window auto-closes in 4 seconds.' -ForegroundColor DarkGray
Start-Sleep -Seconds 4
exit 0
