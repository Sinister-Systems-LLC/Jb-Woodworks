# Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
# browse-knowledge.ps1 - TUI for the Sanctum brain.
# Triggered by C:\Users\Zonia\Desktop\Browse-Knowledge.bat.

$ErrorActionPreference = 'Continue'
$Host.UI.RawUI.WindowTitle = 'Browse Knowledge (Sanctum brain)'

$BrainDir = 'D:\Sinister Sanctum\_shared-memory\knowledge'

function Show-Header {
    Clear-Host
    Write-Host ''
    Write-Host '  ============================================' -ForegroundColor DarkMagenta
    Write-Host '   THE SANCTUM BRAIN  (browse knowledge)' -ForegroundColor Magenta
    Write-Host '  ============================================' -ForegroundColor DarkMagenta
    Write-Host ''
}

function List-Topics {
    Show-Header
    $topics = Get-ChildItem -Path $BrainDir -Filter '*.md' -ErrorAction SilentlyContinue |
              Where-Object { -not $_.Name.StartsWith('_') } | Sort-Object LastWriteTime -Descending
    if ($topics.Count -eq 0) {
        Write-Host '  (no topics yet — agents will write them as they discover things)' -ForegroundColor DarkGray
        Write-Host ''
        Read-Host 'press Enter to exit'
        exit 0
    }
    Write-Host ("  {0} topic(s) in the brain:" -f $topics.Count) -ForegroundColor White
    Write-Host ''
    $i = 1
    foreach ($t in $topics) {
        $title = $t.BaseName
        $statusLine = ''
        # Try extract title + status from file
        try {
            $head = Get-Content $t.FullName -TotalCount 20 -ErrorAction SilentlyContinue
            foreach ($line in $head) {
                if ($line.StartsWith('# Topic:')) { $title = $line.Replace('# Topic:', '').Trim() }
                if ($line.StartsWith('**Status:**')) { $statusLine = $line.Replace('**Status:**', '').Trim() }
            }
        } catch {}
        $statusColor = switch ($statusLine.Split()[0]) {
            'fixed'       { 'Green' }
            'workaround'  { 'Yellow' }
            'known-issue' { 'Yellow' }
            'open'        { 'Red' }
            default       { 'DarkGray' }
        }
        Write-Host ("   {0,3}) " -f $i) -NoNewline -ForegroundColor Magenta
        Write-Host ("{0,-50}" -f $title) -NoNewline -ForegroundColor White
        Write-Host ("  [" + $statusLine + "]") -ForegroundColor $statusColor
        Write-Host ("        " + $t.BaseName) -ForegroundColor DarkGray
        $i++
    }
    Write-Host ''
    Write-Host '   S) search by keyword' -ForegroundColor Gray
    Write-Host '   Q) quit' -ForegroundColor DarkGray
    Write-Host ''
    $pick = Read-Host '  >'
    if ($pick -match '^\d+$') {
        $idx = [int]$pick - 1
        if ($idx -ge 0 -and $idx -lt $topics.Count) {
            Read-Topic $topics[$idx]
            List-Topics
            return
        }
    } elseif ($pick -match '^[Ss]') {
        Search-Topics
        return
    } elseif ($pick -match '^[Qq]') {
        exit 0
    }
    List-Topics
}

function Read-Topic([System.IO.FileInfo]$file) {
    Show-Header
    Write-Host ("  Reading: " + $file.Name) -ForegroundColor Cyan
    Write-Host ('  ' + ('-' * 60)) -ForegroundColor DarkMagenta
    Write-Host ''
    Get-Content $file.FullName | ForEach-Object {
        if ($_.StartsWith('# Topic:')) { Write-Host $_ -ForegroundColor Magenta }
        elseif ($_.StartsWith('## ')) { Write-Host $_ -ForegroundColor Cyan }
        elseif ($_.StartsWith('### ')) { Write-Host $_ -ForegroundColor White }
        elseif ($_.StartsWith('**')) { Write-Host $_ -ForegroundColor Yellow }
        elseif ($_.StartsWith('```')) { Write-Host $_ -ForegroundColor DarkGray }
        else { Write-Host $_ -ForegroundColor Gray }
    }
    Write-Host ''
    Write-Host ('  ' + ('-' * 60)) -ForegroundColor DarkMagenta
    Read-Host '  press Enter to return to list'
}

function Search-Topics {
    Show-Header
    $q = Read-Host '  search query'
    if (-not $q) { List-Topics; return }
    $hits = Get-ChildItem -Path $BrainDir -Filter '*.md' -ErrorAction SilentlyContinue |
            Where-Object { -not $_.Name.StartsWith('_') } |
            ForEach-Object {
                $matches = Select-String -Path $_.FullName -Pattern $q -SimpleMatch -ErrorAction SilentlyContinue
                if ($matches) { $_ }
            }
    if ($hits.Count -eq 0) {
        Write-Host ('  no topics match "' + $q + '".') -ForegroundColor DarkGray
        Read-Host '  press Enter to return'
        List-Topics
        return
    }
    Write-Host ('  ' + $hits.Count + ' topic(s) match:') -ForegroundColor White
    $i = 1
    foreach ($h in $hits) {
        Write-Host ("   {0,3}) {1}" -f $i, $h.BaseName) -ForegroundColor White
        $i++
    }
    Write-Host ''
    $pick = Read-Host '  pick number to read (or Enter to return)'
    if ($pick -match '^\d+$') {
        $idx = [int]$pick - 1
        if ($idx -ge 0 -and $idx -lt $hits.Count) { Read-Topic $hits[$idx] }
    }
    List-Topics
}

List-Topics
