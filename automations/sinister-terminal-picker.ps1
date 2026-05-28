# sinister-terminal-picker.ps1
# Interactive picker for the Sinister Terminal launcher (Desktop\Sinister Terminal.bat).
# ASCII-only (no em-dashes / smart quotes / ellipsis) so PS 5.1 parses cleanly.
# Rev: 2026-05-28T17:50Z  (EVE-styled banner + ANSI purple palette + arrow-key nav)
# Author: RKOJ-ELENO :: 2026-05-28

[CmdletBinding()]
param(
    [switch]$NoPicker,
    [string[]]$Projects = @()
)

$ErrorActionPreference = 'Continue'

# Force UTF-8 console BEFORE any Write-Host so block-glyph banner + ANSI palette
# render correctly. Operator hard-canonical 2026-05-28 (Image #17): top of launcher
# was showing mojibake like 'a-^a-^...' (Latin-1 render of U+2588 full-block char).
# Root cause: PowerShell 5.1 inherits console code page (often 1252) unless we
# explicitly switch to 65001 (UTF-8) and set [Console]::OutputEncoding before
# emitting any non-ASCII bytes. chcp + OutputEncoding are belt+suspenders.
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 | Out-Null
} catch {}

$Sanctum = 'D:\Sinister Sanctum'
$STermBat = "$Sanctum\projects\sinister-term\source\bin\sinister-shell.bat"
$ClaudeExe = 'C:\Users\Zonia\.local\bin\claude.exe'
$VaultDaemon = "$Sanctum\tools\sinister-vault\.venv\Scripts\pythonw.exe"
$VaultPort = 5078
$SinisterLinkPort = 5071
$LogPath = "$Sanctum\_shared-memory\sinister-terminal-picker.log"
$AccountsJson = "$Sanctum\_shared-memory\claude-accounts.json"
$AccountsMgr = "$Sanctum\automations\claude-accounts.ps1"
$ProjectsJson = "$Sanctum\automations\session-templates\projects.json"

# === SINISTER CANONICAL PALETTE (24-bit ANSI) ===
# PURPLE #c084fc / BRIGHTP #d8b4fe / DARKP #6b21a8 / PALEP #e8d6ff
# Sourced: _shared-memory/knowledge/sinister-ui-canonical-dashboard-skeleton-inheritance-2026-05-24.md
$ESC = [char]27
$PURPLE  = "$ESC[38;2;192;132;252m"
$BRIGHTP = "$ESC[38;2;216;180;254m"
$DARKP   = "$ESC[38;2;107;33;168m"
$PALEP   = "$ESC[38;2;232;214;255m"
$DIM     = "$ESC[38;2;100;100;120m"
$INV     = "$ESC[7m"   # inverse video for highlighted row
$RESET   = "$ESC[0m"
$BOLD    = "$ESC[1m"

function Get-ConsoleWidth {
    try { return [Math]::Max(60, [Console]::WindowWidth) } catch { return 100 }
}

function Write-Centered { param([string]$Text, [string]$Color = $PURPLE)
    $w = Get-ConsoleWidth
    $vis = ($Text -replace "$ESC\[[0-9;]*m", '')
    $pad = [Math]::Max(0, [int](($w - $vis.Length) / 2))
    Write-Host (' ' * $pad + $Color + $Text + $RESET)
}

function Log { param([string]$Msg)
    $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    Add-Content -LiteralPath $LogPath -Value "[$ts] $Msg"
}

function Show-Banner {
    Clear-Host
    Write-Host ""
    # 5-row "EVE" block-letter ASCII (block-glyph composed of full-block chars)
    $eve = @(
        "███████  ██    ██  ███████",
        "██       ██    ██  ██     ",
        "█████    ██    ██  █████  ",
        "██        ██  ██   ██     ",
        "███████    ████    ███████"
    )
    foreach ($row in $eve) { Write-Centered $row $PURPLE }
    Write-Host ""
    Write-Centered "Sinister LINK :: invited (awaiting acceptance ...)" $BRIGHTP
    $stats = $null
    try {
        $mcpCount = 0; $botCount = 0; $liveAgents = 0
        $mcpJson = "$env:USERPROFILE\.claude.json"
        if (Test-Path $mcpJson) {
            try {
                $mj = Get-Content $mcpJson -Raw | ConvertFrom-Json
                if ($mj.mcpServers) { $mcpCount = ($mj.mcpServers.PSObject.Properties | Measure-Object).Count }
            } catch {}
        }
        $hbDir = "$Sanctum\_shared-memory\heartbeats"
        if (Test-Path $hbDir) {
            $cutoff = (Get-Date).AddMinutes(-30)
            $liveAgents = (Get-ChildItem $hbDir -Filter '*.json' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -gt $cutoff } | Measure-Object).Count
        }
        $botCount = $mcpCount
        $stats = "EVE-OPUS-4.7 . v0.4.5 . mcp: $mcpCount bots: $botCount live: $liveAgents agents"
    } catch { $stats = "EVE-OPUS-4.7 . v0.4.5" }
    Write-Centered $stats $PALEP
    Write-Host ""
}

function Show-ServiceStatus {
    # Boot/start services SILENTLY (keep the banner clean per operator's centered look).
    # We still auto-start vault, but suppress the chatty per-service Write-Host block.
    $vaultUp = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $VaultPort }
    if (-not $vaultUp) {
        if (Test-Path $VaultDaemon) {
            Start-Process $VaultDaemon -ArgumentList 'daemon.py','--port',$VaultPort -WorkingDirectory "$Sanctum\tools\sinister-vault" -WindowStyle Hidden
            Start-Sleep -Milliseconds 800
            $vaultUp = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $VaultPort }
        }
    }
    $linkUp = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq $SinisterLinkPort }

    # One concise centered status line
    $vaultTag = if ($vaultUp) { "vault:on" } else { "vault:off" }
    $linkTag  = if ($linkUp)  { "link:on"  } else { "link:idle" }
    Write-Centered "[ $vaultTag . $linkTag ]" $DIM
    Write-Host ""
}

function Get-Projects {
    $list = @()
    if (Test-Path $ProjectsJson) {
        try {
            $pjson = Get-Content $ProjectsJson -Raw | ConvertFrom-Json
            if ($pjson.projects) {
                foreach ($p in $pjson.projects) {
                    if ($p.key) {
                        $list += [PSCustomObject]@{
                            Key   = $p.key
                            Label = if ($p.label) { $p.label } else { $p.key }
                            Slug  = if ($p.slug) { $p.slug } else { $p.key }
                        }
                    }
                }
            }
        } catch { Log "projects.json parse failed: $($_.Exception.Message)" }
    }
    if ($list.Count -eq 0) {
        $fallback = @('eve-exe','sinister-panel','kernel-apk','letstext','sinister-snap-api-quantum',
                      'sinister-overseer','sinister-os','sinister-mind','sinister-memory','sinister-forge',
                      'sinister-chess','sinister-designer','sinister-jokester','showmasters','jb-woodworks',
                      'sinister-imessage-bridge','sinister-tiktok-emu','sinister-snap-emu','sinister-chatbot',
                      'sinister-term','sinister-mcp','eve-compliance','sinister-letstext')
        foreach ($k in $fallback) {
            $list += [PSCustomObject]@{ Key = $k; Label = $k; Slug = $k }
        }
    }
    return $list
}

function Get-AvailableSlots {
    $slots = @()
    if (-not (Test-Path $AccountsJson)) { return $slots }
    try {
        $acc = Get-Content $AccountsJson -Raw | ConvertFrom-Json
        foreach ($a in $acc.accounts) {
            if (-not $a.enabled) { continue }
            if (-not $a.linked) { continue }
            if (-not $a.credentials_file) { continue }
            if (-not (Test-Path $a.credentials_file)) { continue }
            $slots += [PSCustomObject]@{
                Name = $a.name
                CredFile = $a.credentials_file
                Auth = $a.auth_mode
            }
        }
    } catch { Log "accounts parse error: $($_.Exception.Message)" }
    return $slots
}

function Get-Categories {
    # Returns ordered array of @{Label; Keys=@(...)}. Empty array if absent.
    $cats = @()
    if (Test-Path $ProjectsJson) {
        try {
            $pjson = Get-Content $ProjectsJson -Raw | ConvertFrom-Json
            if ($pjson.picker -and $pjson.picker.categories) {
                foreach ($c in $pjson.picker.categories) {
                    if ($c.label -and $c.keys) {
                        $cats += [PSCustomObject]@{ Label = $c.label; Keys = @($c.keys) }
                    }
                }
            }
        } catch { Log "projects.json categories parse failed: $($_.Exception.Message)" }
    }
    return $cats
}

function Show-ProjectMenu { param([object[]]$Projects, [bool[]]$Selected, [int]$CursorIdx = -1)
    # Centered, category-grouped, arrow-cursor highlighted.
    # Falls back to flat list if categories absent.
    #
    # Operator hard-canonical 2026-05-28 (Image #17): "i want this way better
    # formated and all in the same orientation". Across categories, raw row
    # lengths differ (varying label length), so per-row independent centering
    # caused [NN] columns to drift between categories. Fix: pre-compute ALL
    # row strings, find max raw length across the ENTIRE visible menu, pad
    # every row to that fixed width, then center using the SAME pad value.
    # Result: every row's '[NN]' column lands in the same console column,
    # regardless of which category it belongs to.
    $w = Get-ConsoleWidth
    Write-Centered "--- Projects ---" $BRIGHTP
    Write-Host ""

    $cats = Get-Categories
    $keyToIdx = @{}
    for ($i = 0; $i -lt $Projects.Count; $i++) { $keyToIdx[$Projects[$i].Key] = $i }

    # PASS 1: build raw (ANSI-free) row strings for EVERY visible row, find max length.
    $rawRows = @{}
    for ($i = 0; $i -lt $Projects.Count; $i++) {
        $tag = if ($Selected[$i]) { '[X]' } else { '[ ]' }
        $num = '{0,2}' -f ($i + 1)
        $rawRows[$i] = ('[{0}] {1} {2}' -f $num, $tag, $Projects[$i].Label)
    }
    $maxLen = 0
    foreach ($k in $rawRows.Keys) { if ($rawRows[$k].Length -gt $maxLen) { $maxLen = $rawRows[$k].Length } }
    # Single shared pad value -> every row lands in identical console column.
    $sharedPad = [Math]::Max(0, [int](($w - $maxLen) / 2))
    $sharedPadStr = ' ' * $sharedPad

    # PASS 2: emit each row padded to $maxLen, prefixed by shared pad.
    $rowFmt = {
        param($idx)
        $line = $rawRows[$idx].PadRight($maxLen)
        if ($idx -eq $CursorIdx) {
            # Inverse-video highlight on the selected row, bright-purple foreground
            Write-Host ($sharedPadStr + $INV + $BRIGHTP + $line + $RESET)
        } elseif ($Selected[$idx]) {
            Write-Host ($sharedPadStr + $PURPLE + $line + $RESET)
        } else {
            Write-Host ($sharedPadStr + $PALEP + $line + $RESET)
        }
    }

    if ($cats.Count -gt 0) {
        $seen = @{}
        foreach ($cat in $cats) {
            Write-Centered "--- $($cat.Label) ---" $DARKP
            foreach ($k in $cat.Keys) {
                if ($keyToIdx.ContainsKey($k)) {
                    $idx = $keyToIdx[$k]
                    if (-not $seen.ContainsKey($idx)) {
                        & $rowFmt $idx
                        $seen[$idx] = $true
                    }
                }
            }
            Write-Host ""
        }
        # Trailing uncategorized
        $orphans = @()
        for ($i = 0; $i -lt $Projects.Count; $i++) { if (-not $seen.ContainsKey($i)) { $orphans += $i } }
        if ($orphans.Count -gt 0) {
            Write-Centered "--- Other ---" $DARKP
            foreach ($i in $orphans) { & $rowFmt $i }
            Write-Host ""
        }
    } else {
        for ($i = 0; $i -lt $Projects.Count; $i++) { & $rowFmt $i }
        Write-Host ""
    }

    Write-Centered "type numbers (e.g. 2,3,4) + ENTER  .  A=all  M=master  N=none  L=login  S=health  Q=quit" $DIM
    Write-Centered "--- ENTER alone launches current selection . Ctrl-C anywhere to quit ---" $DIM
    Write-Host ""
}

function Show-SlotHealth {
    Clear-Host
    Show-Banner
    $slots = Get-AvailableSlots
    Write-Host "  Available slots (enabled + linked, round-robin order):" -ForegroundColor Cyan
    if ($slots.Count -eq 0) {
        Write-Host "    (none)" -ForegroundColor Red
    } else {
        for ($i = 0; $i -lt $slots.Count; $i++) {
            $s = $slots[$i]
            Write-Host ("    {0}. {1,-12} auth={2,-7} cred={3}" -f ($i+1), $s.Name, $s.Auth, (Split-Path $s.CredFile -Leaf)) -ForegroundColor Green
        }
    }
    Write-Host ""
    $healthFile = "$Sanctum\_shared-memory\oauth-slot-health.json"
    if (Test-Path $healthFile) {
        try {
            $h = Get-Content $healthFile -Raw | ConvertFrom-Json
            Write-Host "  Health snapshot (oauth-slot-health.json, ts=$($h.measured_at_utc)):" -ForegroundColor Cyan
            foreach ($s in $h.slots) {
                $bar = '#' * [Math]::Min(20, [int]($s.usage_pct_5h / 5))
                Write-Host ("    {0,-12} usage={1,3}%  {2}" -f $s.name, $s.usage_pct_5h, $bar) -ForegroundColor DarkGray
            }
        } catch {}
    }
    Write-Host ""
    Write-Host "  Press any key to return..." -ForegroundColor DarkYellow
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Login-NewAccount {
    Clear-Host
    Show-Banner
    Write-Host "  Add new Claude account" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  STEPS:" -ForegroundColor DarkYellow
    Write-Host "    1. Pick a slot name (e.g. slot3, slot4, leo)" -ForegroundColor DarkGray
    Write-Host "    2. Backup will be made of your current ~/.claude/.credentials.json" -ForegroundColor DarkGray
    Write-Host "    3. 'claude login' opens browser — sign in to the NEW account" -ForegroundColor DarkGray
    Write-Host "    4. Resulting creds get copied to credentials.<slot>.json" -ForegroundColor DarkGray
    Write-Host "    5. Your operator creds get restored automatically" -ForegroundColor DarkGray
    Write-Host "    6. Slot gets registered in claude-accounts.json (round-robin auto-picks it up)" -ForegroundColor DarkGray
    Write-Host ""
    $name = Read-Host "  slot name (or empty to cancel)"
    if (-not $name) { Write-Host "  cancel"; Start-Sleep 1; return }
    $name = $name.Trim() -replace '\s', '-'
    $opCred = 'C:\Users\Zonia\.claude\.credentials.json'
    $newCred = "C:\Users\Zonia\.claude\credentials.$name.json"
    $bakCred = "$opCred.bak-$(Get-Date -Format yyyyMMddHHmmss)"

    if (Test-Path $newCred) {
        Write-Host "  [FAIL] $newCred already exists. Delete first or pick a new name." -ForegroundColor Red
        Start-Sleep 2; return
    }
    if (Test-Path $opCred) {
        Copy-Item $opCred $bakCred -Force
        Write-Host "  [OK] backed up operator creds to $bakCred" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "  Launching 'claude login' — sign in to the NEW account in the browser..." -ForegroundColor Yellow
    & $ClaudeExe login
    if (-not (Test-Path $opCred)) {
        Write-Host "  [FAIL] claude login produced no creds at $opCred" -ForegroundColor Red
        if (Test-Path $bakCred) { Copy-Item $bakCred $opCred -Force }
        Start-Sleep 3; return
    }

    Move-Item $opCred $newCred -Force
    if (Test-Path $bakCred) { Copy-Item $bakCred $opCred -Force; Write-Host "  [OK] operator creds restored from backup" -ForegroundColor Green }
    Write-Host "  [OK] new creds saved at $newCred" -ForegroundColor Green

    if (Test-Path $AccountsMgr) {
        Write-Host "  Registering '$name' in claude-accounts.json..." -ForegroundColor Cyan
        & powershell -NoProfile -ExecutionPolicy Bypass -File $AccountsMgr -Action Add -Name $name -CredentialsFile $newCred -Label "$name (added $(Get-Date -Format yyyy-MM-dd))"
    } else {
        Write-Host "  [WARN] claude-accounts.ps1 missing - register manually" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "  Round-robin will auto-include '$name' on next project spawn." -ForegroundColor Green
    Write-Host "  Press any key to return..." -ForegroundColor DarkYellow
    $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
}

function Resolve-ProjectRoot { param([string]$slug)
    $candidates = @("$Sanctum\projects\$slug", "$Sanctum\projects\sinister-$slug", $Sanctum)
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    return $Sanctum
}

function Pick-Color { param([string]$slug)
    if ($slug -like 'eve*')         { return '#BF5AF2' }
    if ($slug -like 'letstext*')    { return '#0A84FF' }
    if ($slug -like 'kernel*')      { return '#FF6FB5' }
    if ($slug -like 'showmasters*') { return '#FFD60A' }
    if ($slug -like 'jb*')          { return '#30D158' }
    if ($slug -like 'sinister-*')   { return '#7B2CBF' }
    if ($slug -eq 'sanctum')        { return '#FF453A' }
    return '#A0A0A0'
}

function Spawn-Terminal { param([string]$projectKey, [string]$slot = '')
    # CANONICAL PATH: hand off to start-sinister-session.ps1 which already does:
    #   - .claude.json pre-trust for project root
    #   - source dir auto-clone if missing
    #   - multi-account auto-best-slot pick (or honors SINISTER_FORCE_SLOT)
    #   - forge-memory recall pre-fetch
    #   - sinister-memory cross-session continuity inject
    #   - themed mintty spawn (Sinister palette, no-space icon, etc.)
    #   - sub-agents + tools + per-project context via the project's _SCAFFOLD-BRIEF.md
    # We just pass -Project + -Fast and (optionally) SINISTER_FORCE_SLOT.
    $sessionScript = "$Sanctum\automations\start-sinister-session.ps1"
    if (-not (Test-Path $sessionScript)) {
        Write-Host "    [FAIL] start-sinister-session.ps1 missing" -ForegroundColor Red
        return
    }
    $envPrefix = ''
    if ($slot) {
        $slotName = (Split-Path $slot -Leaf) -replace '^credentials\.' , '' -replace '\.json$', ''
        if ($slotName -eq '.credentials') { $slotName = 'operator' }
        $envPrefix = "set SINISTER_FORCE_SLOT=$slotName & "
    }
    # SINISTER_AUTO_ACCEPT lets us skip all Read-Host prompts (we don't echo into stdin
    # because the script may need TTY interaction; instead the env var pre-answers).
    # If start-sinister-session doesn't read it (yet), we ALSO pipe 5 blank lines into
    # stdin so any Read-Host call gets an empty "accept default" answer. Belt + suspenders.
    $envPrefix += 'set SINISTER_AUTO_ACCEPT=1 & set SINISTER_SKIP_MEMORY_RECALL=0 & '
    $sessionArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$sessionScript`" -Project $projectKey -Fast"
    $cmd = "$envPrefix (echo. & echo. & echo. & echo. & echo.) | powershell $sessionArgs"
    Start-Process cmd.exe -ArgumentList '/c', $cmd -WindowStyle Hidden | Out-Null
    Log "session-start spawned project=$projectKey slot=$slot"
}

# ===== MAIN =====

$projs = Get-Projects
$sel = @($false) * $projs.Count

if ($NoPicker) {
    for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $true }
    Log "no-picker mode: launching all $($projs.Count) projects + master"
} else {
    $cursorIdx = 0
    $useRawKey = $true
    try { $null = $Host.UI.RawUI.ReadKeyAvailable } catch { $useRawKey = $false }

    :outer while ($true) {
        Show-Banner
        Show-ServiceStatus
        Show-ProjectMenu -Projects $projs -Selected $sel -CursorIdx $cursorIdx

        if (-not $useRawKey) {
            # Fallback: legacy numeric/letter Read-Host path
            $choice = Read-Host "  > pick a letter or number(s) (comma-separated)"
            $choice = $choice.Trim()
            if ($choice -eq '' -or $choice.ToUpper() -eq 'GO') { break }
            if ($choice.ToUpper() -eq 'Q') { Write-Host "  cancel"; exit 0 }
            if ($choice.ToUpper() -eq 'M') {
                for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $false }
                Write-Host "  master only" -ForegroundColor Green; Start-Sleep -Seconds 1; break
            }
            if ($choice.ToUpper() -eq 'A') { for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $true }; continue }
            if ($choice.ToUpper() -eq 'N') { for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $false }; continue }
            if ($choice.ToUpper() -eq 'L') { Login-NewAccount; continue }
            if ($choice.ToUpper() -eq 'S') { Show-SlotHealth; continue }
            $tokens = $choice -split '[\s,]+' | Where-Object { $_ }
            foreach ($t in $tokens) {
                if ($t -match '^\d+$') {
                    $idx = [int]$t - 1
                    if ($idx -ge 0 -and $idx -lt $sel.Count) { $sel[$idx] = -not $sel[$idx] }
                }
            }
            continue
        }

        # Operator hard-canonical 2026-05-28 Image #24: "i cant fucking type
        # numbers here to select things. i need the menu system to login and
        # then select projects." Switch DEFAULT path to Read-Host (typed line,
        # multi-digit numbers OK). Arrow-key path moved behind ':a' prefix.
        $choice = Read-Host ($PURPLE + "  > pick number(s) e.g. 2,3,4 or letter (A=all M=master N=none L=login S=health Q=quit ENTER=launch)" + $RESET)
        $choice = $choice.Trim()
        if ($choice -eq '' -or $choice.ToUpper() -eq 'GO' -or $choice.ToUpper() -eq 'G') {
            # Plain Enter or GO: launch with current selection. If nothing
            # selected, master-only (operator's "M" muscle memory).
            $anySel = $false
            foreach ($s in $sel) { if ($s) { $anySel = $true; break } }
            if (-not $anySel) {
                for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $false }
                Write-Host "  > nothing selected; launching master only" -ForegroundColor $C.Soft
            }
            break
        }
        $up = $choice.ToUpper()
        if ($up -eq 'Q') { Write-Host "  cancel"; exit 0 }
        if ($up -eq 'M') {
            for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $false }
            Write-Host "  master only" -ForegroundColor Green
            Start-Sleep -Seconds 1
            break
        }
        if ($up -eq 'A') { for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $true }; continue }
        if ($up -eq 'N') { for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $false }; continue }
        if ($up -eq 'L') { Login-NewAccount; continue }
        if ($up -eq 'S') { Show-SlotHealth; continue }
        # Comma- / space-separated number list (the muscle-memory path).
        $tokens = $choice -split '[\s,]+' | Where-Object { $_ }
        $anyDigit = $false
        foreach ($t in $tokens) {
            if ($t -match '^\d+$') {
                $anyDigit = $true
                $idx = [int]$t - 1
                if ($idx -ge 0 -and $idx -lt $sel.Count) { $sel[$idx] = -not $sel[$idx] }
            }
        }
        if ($anyDigit) { continue }
        # Unknown input: do nothing, redraw.
        continue

        # --- legacy arrow-key path (kept for future ':a' opt-in) ---
        $key = $null
        try {
            $key = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
        } catch {
            $useRawKey = $false
            continue
        }
        Write-Host ""
        $vk = $key.VirtualKeyCode
        $ch = $key.Character

        # ENTER (13) = toggle current row (matches existing toggle-by-number semantics).
        # If NO rows are selected, ENTER instead launches (master-only) so plain Enter still launches.
        if ($vk -eq 13) {
            $anySel = $false
            foreach ($s in $sel) { if ($s) { $anySel = $true; break } }
            if (-not $anySel) { break }
            if ($cursorIdx -ge 0 -and $cursorIdx -lt $sel.Count) { $sel[$cursorIdx] = -not $sel[$cursorIdx] }
            continue
        }
        if ($vk -eq 38) { # Up
            $cursorIdx = ($cursorIdx - 1 + $projs.Count) % $projs.Count; continue
        }
        if ($vk -eq 40) { # Down
            $cursorIdx = ($cursorIdx + 1) % $projs.Count; continue
        }
        if ($vk -eq 27) { Write-Host "  cancel" -ForegroundColor DarkYellow; exit 0 } # Esc
        if ($vk -eq 32) {  # Space = toggle current row (alt to Enter)
            if ($cursorIdx -ge 0 -and $cursorIdx -lt $sel.Count) { $sel[$cursorIdx] = -not $sel[$cursorIdx] }
            continue
        }

        # Letter shortcuts (uppercase the char)
        if ($ch) {
            $up = ([string]$ch).ToUpper()
            switch ($up) {
                'Q' { Write-Host "  cancel"; exit 0 }
                'M' {
                    for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $false }
                    Write-Host "  master only" -ForegroundColor Green; Start-Sleep -Seconds 1
                    break outer
                }
                'A' { for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $true }; continue outer }
                'N' { for ($i = 0; $i -lt $sel.Count; $i++) { $sel[$i] = $false }; continue outer }
                'L' { Login-NewAccount; continue outer }
                'S' { Show-SlotHealth; continue outer }
                'G' { break outer }  # G=GO (launch with current selection)
            }
            # Digit shortcut: typed digit jumps cursor to row N (1-based).
            if ($up -match '^\d$') {
                $idx = [int]$up - 1
                if ($idx -ge 0 -and $idx -lt $sel.Count) { $cursorIdx = $idx }
                continue
            }
            # Allow legacy multi-digit numeric input via ':' prefix entering Read-Host mode.
            if ($up -eq ':' -or $up -eq '/') {
                $line = Read-Host "  numeric (comma-separated, e.g. 2,3,7)"
                $tokens = $line -split '[\s,]+' | Where-Object { $_ }
                foreach ($t in $tokens) {
                    if ($t -match '^\d+$') {
                        $idx = [int]$t - 1
                        if ($idx -ge 0 -and $idx -lt $sel.Count) { $sel[$idx] = -not $sel[$idx] }
                    }
                }
                continue
            }
        }
    }
}

# === SPAWN ===
Show-Banner
Write-Centered "Launching..." $BRIGHTP
Write-Host ""

# Operator hard-canonical 2026-05-28: "dont worry about the master agent in
# the bat file just launch projects". Master sanctum auto-spawn REMOVED;
# operator runs sanctum master in its own session. Only spawn master if it
# was EXPLICITLY selected by index in $sel (toggled true above).
$anySelected = $false
foreach ($s in $sel) { if ($s) { $anySelected = $true; break } }
if (-not $anySelected) {
    Write-Host "  > nothing selected -- exiting without spawn." -ForegroundColor $C.Soft
    Start-Sleep -Seconds 1
    exit 0
}

# Round-robin distribute project terminals across all non-operator slots.
$allSlots = Get-AvailableSlots
$rotation = @($allSlots | Where-Object { $_.Name -ne 'operator' })
if ($rotation.Count -eq 0) { $rotation = $allSlots }
$rotationNames = ($rotation | ForEach-Object { $_.Name }) -join ', '
Write-Host "  [slot rotation] $($rotation.Count) slot(s) for project terminals: $rotationNames" -ForegroundColor DarkCyan

$count = 0
$slotIdx = 0
for ($i = 0; $i -lt $projs.Count; $i++) {
    if (-not $sel[$i]) { continue }
    $p = $projs[$i]
    if ($rotation.Count -gt 0) {
        $slot = $rotation[$slotIdx % $rotation.Count]
        $slotPath = $slot.CredFile
        $slotName = $slot.Name
        $slotIdx++
    } else {
        $slotPath = ''
        $slotName = 'parent'
    }
    Spawn-Terminal -projectKey $p.Key -slot $slotPath
    Write-Host "  [+] $($p.Label)  slot=$slotName" -ForegroundColor Cyan
    $count++
    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "  Launched: 1 Master + $count project terminals" -ForegroundColor Green
Write-Host "  Log: $LogPath" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Vault is live on :$VaultPort - use mcp__vault__* tools inside any claude session." -ForegroundColor DarkGray
Write-Host "  Press any key to exit this launcher (terminals stay open)..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
