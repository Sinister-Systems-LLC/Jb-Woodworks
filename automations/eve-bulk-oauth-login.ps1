# Author: RKOJ-ELENO :: 2026-05-24
# eve-bulk-oauth-login.ps1 -- "Claude Login" wizard for the Sinister fleet's
# Max-plan account pool. Multi-account OAuth capture in one sitting.
#
# Operator (verbatim 2026-05-24 ~23:25Z):
#   "name this calude login. bake it into the accounts tab in eve exxe. make
#    sure it works and make sure it wont log out my accounts that are running
#    right now and is in a controled env to get what we need and they wont
#    interfere with each other"
#
# DESIGN: per-account ISOLATED HOME directory.
#   For each slot, the wizard:
#     1. Creates an isolated dir: %TEMP%\sinister-claude-login-<slot>-<rand>\
#     2. Spawns a NEW mintty/bash window with HOME pointed at the isolated dir
#     3. In that window: `claude login` -> browser OAuth -> creds written to
#        <isolated>\.claude\.credentials.json  (NOT ~/.claude/.credentials.json)
#     4. Wizard polls the isolated creds file for write
#     5. Copies the captured creds to ~/.claude/credentials.<slot>.json (per-slot
#        store consumed by claude-oauth-accounts.ps1 -Action Use during spawn)
#     6. Cleans up the isolated dir
#   Result: ~/.claude/.credentials.json is NEVER overwritten -- any claude
#   sessions you have open right now keep their creds untouched.
#   Concurrent logins to different slots use different isolated dirs and do not
#   interfere.
#
# USAGE:
#   powershell -NoProfile -ExecutionPolicy Bypass -File `
#     "D:\Sinister Sanctum\automations\eve-bulk-oauth-login.ps1"
#   (or double-click C:\Users\Zonia\Desktop\Login-All-Sinister-Accounts.bat,
#    or from EVE.exe picker: O -> 1 OR 2)
#
# FLAGS:
#   -DryRun        walk the prompts but DO NOT spawn isolated bash / capture
#   -Count <N>     skip the "how many" prompt (handy for re-runs)
#   -NoBanner      suppress the giant banner (for embedded callers)
#   -PollTimeout   how long to wait for the isolated creds file (default 600s)
#
# COMPOSES WITH:
#   automations/claude-oauth-accounts.ps1     -- MarkLimited, RotateToNext, List
#   tools/eve-picker/account_manager.py       -- EVE.exe Accounts page wraps this
#   _shared-memory/claude-accounts.json       -- where the slots land

[CmdletBinding()]
param(
    [switch]$DryRun,
    [int]$Count = 0,
    [switch]$NoBanner,
    [int]$PollTimeout = 600
)

$ErrorActionPreference = 'Continue'
$script:SanctumRoot = Split-Path -Parent $PSScriptRoot
if (-not $script:SanctumRoot -or -not (Test-Path $script:SanctumRoot)) {
    $script:SanctumRoot = 'D:\Sinister Sanctum'
}
$script:OAuthPs1    = Join-Path $script:SanctumRoot 'automations\claude-oauth-accounts.ps1'
$script:AccountsJson= Join-Path $script:SanctumRoot '_shared-memory\claude-accounts.json'
$script:LogFile     = Join-Path $script:SanctumRoot '_shared-memory\eve-bulk-oauth-login.log'
$script:CapturedSlots = New-Object System.Collections.ArrayList
$script:IsolatedDirsToCleanup = New-Object System.Collections.ArrayList

# Set the host window title.
try { $Host.UI.RawUI.WindowTitle = 'Claude Login -- Sinister Accounts' } catch {}

# ASCII-only color tokens.
function _Color {
    param([string]$Token)
    switch ($Token) {
        'PURPLE'  { return [char]27 + '[38;5;141m' }
        'BRIGHTP' { return [char]27 + '[38;5;177m' }
        'DARKP'   { return [char]27 + '[38;5;91m' }
        'WHITE'   { return [char]27 + '[97m' }
        'SOFT'    { return [char]27 + '[38;5;245m' }
        'DIM'     { return [char]27 + '[38;5;240m' }
        'OK'      { return [char]27 + '[38;5;46m' }
        'WARN'    { return [char]27 + '[38;5;220m' }
        'FAIL'    { return [char]27 + '[38;5;196m' }
        'BOLD'    { return [char]27 + '[1m' }
        'RESET'   { return [char]27 + '[0m' }
        default   { return '' }
    }
}
$PURPLE=_Color 'PURPLE'; $BRIGHTP=_Color 'BRIGHTP'; $DARKP=_Color 'DARKP'
$WHITE=_Color 'WHITE'; $SOFT=_Color 'SOFT'; $DIM=_Color 'DIM'
$OK=_Color 'OK'; $WARN=_Color 'WARN'; $FAIL=_Color 'FAIL'
$BOLD=_Color 'BOLD'; $RESET=_Color 'RESET'

function _Log {
    param([string]$Message, [string]$Level = 'INFO')
    try {
        $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
        Add-Content -Path $script:LogFile -Value "[$ts] [$Level] $Message" -ErrorAction SilentlyContinue
    } catch {}
}

function _Slugify {
    param([string]$Raw)
    $s = ($Raw -as [string]).ToLower().Trim()
    if (-not $s) { return '' }
    $s = ($s -replace '[^a-z0-9]+', '-').Trim('-_')
    if ($s.Length -gt 31) { $s = $s.Substring(0, 31).TrimEnd('-_') }
    if ($s -notmatch '^[a-z0-9][a-z0-9_-]{0,30}$') { return '' }
    return $s
}

function _NextMondayIsoUtc {
    $now = (Get-Date).ToUniversalTime()
    $daysUntilMonday = (([int][DayOfWeek]::Monday - [int]$now.DayOfWeek + 7) % 7)
    if ($daysUntilMonday -eq 0) { $daysUntilMonday = 7 }
    $target = $now.Date.AddDays($daysUntilMonday)
    return $target.ToString('yyyy-MM-ddTHH:mm:ssZ')
}

function _BigBanner {
    if ($NoBanner) { return }
    Write-Host ''
    Write-Host "  $DARKP===================================================================$RESET"
    Write-Host "  $WHITE$BOLD  Claude Login$RESET  $DIM-- multi-account OAuth (Max 20x pool)$RESET"
    Write-Host "  $DARKP===================================================================$RESET"
    Write-Host ''
    Write-Host "  $SOFT Login multiple Claude accounts for round-robin rotation.$RESET"
    Write-Host ''
    Write-Host "  $WHITE PER-ACCOUNT FLOW (isolated -- your live sessions are safe):$RESET"
    Write-Host "    $PURPLE 1)$RESET  Type a display name (e.g. 'Sinister Gmail')."
    Write-Host "    $PURPLE 2)$RESET  Wizard creates an isolated sandbox dir for this login."
    Write-Host "    $PURPLE 3)$RESET  Wizard pops a NEW bash window with HOME=<sandbox>"
    Write-Host "         and auto-runs $WHITE claude login$RESET in there."
    Write-Host "    $PURPLE 4)$RESET  You complete OAuth in the browser as usual."
    Write-Host "    $PURPLE 5)$RESET  Wizard captures sandbox creds -> ~/.claude/credentials.<slot>.json"
    Write-Host "    $PURPLE 6)$RESET  Optional: mark slot as limited-til-<date>."
    Write-Host ''
    Write-Host "  $OK Your ~/.claude/.credentials.json is NEVER touched.$RESET"
    Write-Host "  $OK Any running claude sessions keep their current login.$RESET"
    Write-Host "  $OK Concurrent logins to different slots do not interfere.$RESET"
    Write-Host "  $OK Add as many accounts as you want -- one at a time, no preset count.$RESET"
    Write-Host "  $DIM Ctrl-C or X+Enter at any prompt aborts cleanly.$RESET"
    if ($DryRun) {
        Write-Host ''
        Write-Host "  $WARN[DRY-RUN]$RESET $WHITE no isolated bash spawned, no creds captured.$RESET"
    }
    Write-Host ''
}

function _PromptYesNo {
    param([string]$Question, [string]$Default = 'n')
    $tag = if ($Default -eq 'y') { '[Y/n]' } else { '[y/N]' }
    try {
        $resp = Read-Host "  $WHITE$Question $tag$RESET"
    } catch {
        return $false
    }
    if ([string]::IsNullOrWhiteSpace($resp)) { $resp = $Default }
    return ($resp.Trim().ToLower() -match '^(y|yes)$')
}

function _DecodeOAuthEmail {
    # Parse JWT from claudeAiOauth.accessToken; pull "email" claim from payload.
    param([string]$CredsPath)
    if (-not (Test-Path $CredsPath)) { return $null }
    try {
        $j = Get-Content -LiteralPath $CredsPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $tok = $null
        if ($j.claudeAiOauth -and $j.claudeAiOauth.accessToken) { $tok = $j.claudeAiOauth.accessToken }
        elseif ($j.accessToken) { $tok = $j.accessToken }
        if (-not $tok) { return $null }
        $parts = $tok -split '\.'
        if ($parts.Length -lt 2) { return $null }
        $payload = $parts[1]
        # JWT base64url -> base64 (pad)
        $pad = 4 - ($payload.Length % 4)
        if ($pad -lt 4) { $payload += ('=' * $pad) }
        $payload = $payload.Replace('-', '+').Replace('_', '/')
        $bytes = [Convert]::FromBase64String($payload)
        $json = [System.Text.Encoding]::UTF8.GetString($bytes) | ConvertFrom-Json
        if ($json.email) { return [string]$json.email }
        return $null
    } catch { return $null }
}

function _SpawnIsolatedClaudeLoginWindow {
    # Spawn a NEW mintty/git-bash window with HOME pointed at the isolated dir
    # and auto-run `claude login` inside. Returns the spawned process object.
    #
    # RKOJ-ELENO :: 2026-05-25T01:30Z :: P0 fix -- operator screenshot showed
    # mintty error: "Failed to run 'Login': No such file or directory" + exit 126.
    # Root cause: PowerShell's Start-Process -ArgumentList joins arrays into a
    # naive space-separated cmdline; the title "Claude Login -- <sandbox>" was
    # split by mintty's arg parser as `-t Claude` (title=Claude), then `Login`
    # was treated as the executable to spawn. Two-part fix:
    #   1. Title contains no spaces (`Sinister-Claude-Login-<slot>`)
    #   2. Use `--exec` to make the command boundary unambiguous (mintty docs:
    #      "Treat remaining arguments as the command to execute" -- safer than
    #      bare `--` separator which can collide with title strings)
    # PATH safety added inside launch.sh in case mintty inherits a stripped env.
    param([string]$IsolatedHome)
    $minttyExe = 'C:\Program Files\Git\usr\bin\mintty.exe'
    $bashExe   = 'C:\Program Files\Git\bin\bash.exe'
    # Write a tiny launch.sh inside the isolated dir that sets HOME + runs claude login.
    $launchSh = Join-Path $IsolatedHome 'login.sh'
    $launchContent = @"
#!/usr/bin/env bash
# PATH safety: ensure `claude` and core unix tools resolve even when mintty
# strips PATH on isolated spawn. RKOJ-ELENO :: 2026-05-25 P0 hardening.
_BASH_USER="`$(whoami 2>/dev/null || echo Zonia)"
export PATH="/c/Users/`${_BASH_USER}/.local/bin:/c/Users/`${_BASH_USER}/bin:/usr/local/bin:/usr/bin:/bin:/c/Program Files/Git/usr/bin:/c/Program Files/Git/bin:`$PATH"
export HOME='$($IsolatedHome -replace '\\','/')'
export USERPROFILE='$($IsolatedHome -replace '\\','/')'
export CLAUDE_CONFIG_DIR="`$HOME/.claude"
mkdir -p "`$HOME/.claude"
cd "`$HOME"
echo ''
echo '=== Sinister isolated claude-login window ==='
echo "    HOME=`$HOME"
echo "    (this is a sandbox; your real ~/.claude is untouched)"
echo ''
# Resolve `claude` location for visibility + debug.
CLAUDE_BIN=`$(command -v claude 2>/dev/null)
if [ -z "`$CLAUDE_BIN" ]; then
    echo "[FAIL] 'claude' CLI not found on PATH. Install Claude Code: https://docs.anthropic.com/claude-code"
    echo "Window auto-closes in 10s (or press any key now)."
    read -t 10 -n 1 _ 2>/dev/null || true
    exit 127
fi
echo "    claude = `$CLAUDE_BIN"
echo ''
# RKOJ-ELENO :: 2026-05-25 :: P0 fix -- `claude login` was renamed to
# `claude auth login` in newer Claude Code CLI builds. Old `claude login`
# returns "unknown command" exit=1 and never opens the browser. Operator
# screenshot 2026-05-25 ~01:50Z: "login didnt work fix this shits".
# Detect which subcommand the installed claude binary supports, then call
# the correct one so we work on BOTH legacy and current CLI versions.
if claude auth --help >/dev/null 2>&1; then
    LOGIN_CMD='auth login'
    echo 'Running: claude auth login'
else
    LOGIN_CMD='login'
    echo 'Running: claude login (legacy CLI)'
fi
echo ''
claude `$LOGIN_CMD
ec=`$?
echo ''
# RKOJ-ELENO :: 2026-05-25T03:15Z :: paste-back path. If `claude auth login`
# exited without writing creds, watch for an .oauth-paste-relay.txt file the
# wizard's parent window may write when the operator pastes the redirect URL
# back. On detection, re-spawn `claude auth login` with the code on stdin so
# the second-pass attempt completes the OAuth exchange and writes creds.
# `--hold always` keeps THIS window open for the watch loop; the wizard's
# poll loop is the one that decides the per-slot timeout.
_RELAY="`$HOME/.claude/.oauth-paste-relay.txt"
_CREDS="`$HOME/.claude/.credentials.json"
if [ `$ec -ne 0 ] && [ ! -f "`$_CREDS" ]; then
    echo "[paste-relay] watching for `$_RELAY (paste URL or code in the wizard window)..."
    # Up to 600s watch (10 min) -- wizard's outer timeout governs the real cap.
    for _i in `$(seq 1 300); do
        if [ -f "`$_RELAY" ]; then
            _CODE=`$(head -n 1 "`$_RELAY" 2>/dev/null)
            if [ -n "`$_CODE" ]; then
                echo ''
                echo "[paste-relay] picked up code (kind=`$(sed -n '2p' "`$_RELAY" 2>/dev/null)); re-running claude `$LOGIN_CMD with stdin..."
                # Pipe the code (and a final newline + a second blank line so
                # the CLI's read loop terminates if it expects 2 responses).
                printf '%s\n\n' "`$_CODE" | claude `$LOGIN_CMD
                ec=`$?
                # Move the relay aside so we don't loop on it again.
                mv "`$_RELAY" "`$_RELAY.consumed" 2>/dev/null || true
                if [ `$ec -eq 0 ] && [ -f "`$_CREDS" ]; then
                    echo '[paste-relay] OK -- creds written from pasted code.'
                fi
                break
            fi
        fi
        # If creds appeared via another path (operator pasted directly into
        # the original claude prompt window before it gave up), bail too.
        [ -f "`$_CREDS" ] && { ec=0; break; }
        sleep 2
    done
fi
if [ `$ec -eq 0 ] && [ -f "`$_CREDS" ]; then
    echo '[OK] login complete. Window auto-closes in 5s (or press any key now).'
else
    echo "[FAIL] claude `$LOGIN_CMD exit=`$ec. Window auto-closes in 30s (or press any key now)."
    echo "      If browser redirect failed, paste the FULL redirect URL or just"
    echo "      the auth code in the wizard's parent window at the [paste]> prompt."
fi
# RKOJ-ELENO :: 2026-05-25T01:40Z :: operator "enter here doesnt work i need
# allow flows to allow for unlimited use ... and now it wont fucking close".
# Replaced dead `read _` (Enter-only, no timeout) with -t (timeout) + -n 1
# (any single char). Window auto-closes even if operator walks away or hits
# the wrong key, so control always returns to the parent Account Manager.
# 2026-05-25T03:15Z :: bumped failure timeout to 30s so operator has time to
# read the paste-relay instructions before window closes.
_TIMEOUT=5
[ `$ec -ne 0 ] && _TIMEOUT=30
read -t `$_TIMEOUT -n 1 _ 2>/dev/null || true
exit `$ec
"@
    # Convert to LF and write UTF-8 (no BOM) so bash reads cleanly.
    $launchContent = $launchContent -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($launchSh, $launchContent, [System.Text.UTF8Encoding]::new($false))

    # RKOJ-ELENO :: 2026-05-25T01:30Z :: P0 fix #2 -- the scriptblock-substitution
    # form ` -replace '^([A-Z]):', { '/' + ... } ` only works in PowerShell 7+.
    # In Windows PowerShell 5.1 the scriptblock is treated as a literal string,
    # producing a mangled path that mintty cannot exec. Use explicit -match +
    # rewrite instead -- compatible with both PS 5.1 and 7+.
    $launchBashPath = $launchSh -replace '\\', '/'
    if ($launchBashPath -match '^([A-Za-z]):(.*)$') {
        $launchBashPath = '/' + $matches[1].ToLower() + $matches[2]
    }

    if (Test-Path $minttyExe) {
        # P0 fix (RKOJ-ELENO :: 2026-05-25T01:30Z): title MUST NOT contain spaces or
        # `--` substring -- PowerShell Start-Process arg-joining collides with mintty
        # parser. Use `--exec` (not bare `--`) to unambiguously begin the command list.
        $sandboxLeaf = ($IsolatedHome | Split-Path -Leaf)
        $title = "Sinister-Claude-Login-$sandboxLeaf"
        # RKOJ-ELENO :: 2026-05-25T03:15Z :: paste-back support. `--hold always`
        # (was `--hold error`) so the window survives BOTH success and failure
        # exits of `claude auth login`. When the browser-redirect path fails
        # back to manual-paste, claude prints "If the browser didn't open,
        # visit: <url>" and waits on stdin -- but the wizard previously closed
        # the window on the first non-error exit, swallowing the prompt. Keeping
        # it open lets the operator paste the redirect URL OR auth code back
        # into the running `claude auth login` directly. Operator can also use
        # the wizard's parent-window paste-back fallback (relay file) which the
        # bash script polls for and replays via stdin pipe.
        $minttyArgs = @(
            '--hold', 'always',
            '-t', $title,
            '-o', 'FontSize=11',
            '-o', 'Term=xterm-256color',
            '--exec', '/bin/bash', $launchBashPath
        )
        return Start-Process -FilePath $minttyExe -ArgumentList $minttyArgs -PassThru
    } elseif (Test-Path $bashExe) {
        # Fallback: spawn bare bash in a new console window.
        return Start-Process -FilePath $bashExe -ArgumentList @('-l', '-i', $launchBashPath) -PassThru
    } else {
        throw "No mintty or bash found at $minttyExe / $bashExe -- install Git for Windows."
    }
}

function _HandlePasteBack {
    # RKOJ-ELENO :: 2026-05-25T03:15Z :: paste-back fallback.
    # When the poll loop concludes without creds (timeout OR window closed
    # before creds landed), give the operator ONE chance to paste the redirect
    # URL (or just the bare auth code) from their browser back into the wizard.
    # We delegate parsing to automations/claude_oauth_pasteback.py (Python per
    # no-bat-no-ps1 doctrine; pure parsing, no auth side-effects) which extracts
    # the `code` query param + writes a relay file inside the sandbox. The
    # bash login window's watch loop picks up the relay and re-runs
    # `claude auth login` with the code piped on stdin.
    #
    # Returns: the captured creds file path on success, $null on bail/junk.
    param([string]$IsolatedHome, [int]$ReadyTimeoutSec = 180)
    $credsFile = Join-Path $IsolatedHome '.claude\.credentials.json'
    $relayHelper = Join-Path $script:SanctumRoot 'automations\claude_oauth_pasteback.py'
    if (-not (Test-Path $relayHelper)) {
        Write-Host "  $WARN[paste-back] helper missing at $relayHelper -- cannot offer paste recovery.$RESET"
        return $null
    }
    Write-Host ''
    Write-Host "  $DARKP-----------------------------------------------------------$RESET"
    Write-Host "  $WHITE$BOLD Paste-back fallback$RESET"
    Write-Host "  $DARKP-----------------------------------------------------------$RESET"
    Write-Host "  $SOFT If the browser redirect didn't land back in the login window,$RESET"
    Write-Host "  $SOFT copy the FULL redirect URL from your browser's address bar$RESET"
    Write-Host "  $SOFT (or just the 'code=...' value) and paste it here.$RESET"
    Write-Host "  $DIM Press Enter on a blank line to skip.$RESET"
    Write-Host ''
    try {
        $paste = Read-Host "  $WHITE[paste]>$RESET"
    } catch { return $null }
    if ([string]::IsNullOrWhiteSpace($paste)) {
        Write-Host "  $DIM(no paste -- skipping recovery)$RESET"
        return $null
    }
    # Write the relay file via the Python helper. We pass the paste on argv
    # rather than stdin because PowerShell stdin-piping to native exe is
    # fragile under git-bash redirects.
    $pyArgs = @($relayHelper, 'write-relay', $IsolatedHome, $paste)
    try {
        $pyOut = & python @pyArgs 2>&1
        $pyExit = $LASTEXITCODE
    } catch {
        Write-Host "  $FAIL[paste-back] python helper crashed: $_$RESET"
        return $null
    }
    if ($pyExit -ne 0) {
        Write-Host "  $WARN[paste-back] could not parse paste: $pyOut$RESET"
        return $null
    }
    Write-Host "  $OK[paste-back] code accepted; relay file written. Waiting for sandbox bash to consume...$RESET"
    # Re-poll with the post-paste timeout window. The login bash window's
    # watch loop will detect the relay file, re-run `claude auth login` with
    # the code on stdin, and the creds file should land within a few seconds
    # of network round-trip.
    $start = Get-Date
    while ($true) {
        $elapsed = [int]((Get-Date) - $start).TotalSeconds
        if ($elapsed -ge $ReadyTimeoutSec) {
            Write-Host "  $WARN[paste-back] no creds appeared within ${ReadyTimeoutSec}s of paste. Sandbox bash window may have already closed.$RESET"
            return $null
        }
        if (Test-Path $credsFile) {
            try {
                $j = Get-Content -LiteralPath $credsFile -Raw -Encoding UTF8 | ConvertFrom-Json
                $hasOauth = ($j.claudeAiOauth -and $j.claudeAiOauth.accessToken) -or $j.accessToken
                if ($hasOauth) {
                    return $credsFile
                }
            } catch {}
        }
        Start-Sleep -Seconds 2
    }
}

function _PollForIsolatedCreds {
    param([string]$IsolatedHome, [int]$TimeoutSec, $LoginProcess)
    $credsFile = Join-Path $IsolatedHome '.claude\.credentials.json'
    $start = Get-Date
    $lastSize = -1
    while ($true) {
        $elapsed = [int]((Get-Date) - $start).TotalSeconds
        if ($elapsed -ge $TimeoutSec) {
            Write-Host "  $WARN[poll] timed out after ${TimeoutSec}s waiting for creds at $credsFile$RESET"
            # RKOJ-ELENO :: 2026-05-25T03:15Z :: instead of returning null,
            # offer paste-back recovery. The bash login window stays open
            # (`--hold always`) and its watch loop will pick up a relay file
            # the helper writes. Re-poll until the second-pass attempt either
            # writes creds or times out separately.
            return (_HandlePasteBack -IsolatedHome $IsolatedHome -ReadyTimeoutSec 180)
        }
        if (Test-Path $credsFile) {
            $size = (Get-Item -LiteralPath $credsFile).Length
            # Wait until size stabilises across two polls (avoid reading partially-written JSON).
            if ($size -gt 0 -and $size -eq $lastSize) {
                # Validate JSON + JWT shape before accepting.
                try {
                    $j = Get-Content -LiteralPath $credsFile -Raw -Encoding UTF8 | ConvertFrom-Json
                    $hasOauth = ($j.claudeAiOauth -and $j.claudeAiOauth.accessToken) -or $j.accessToken
                    if ($hasOauth) {
                        return $credsFile
                    }
                } catch {}
            }
            $lastSize = $size
        }
        if ($LoginProcess -and $LoginProcess.HasExited -and -not (Test-Path $credsFile)) {
            # Window closed before creds landed. With `--hold always` (RKOJ
            # 2026-05-25T03:15Z) this should be rare; if it still happens it
            # means the operator hit a key inside the window to dismiss it
            # before the wizard could relay paste-back. Still offer recovery
            # via paste -- on success the wizard re-spawns a minimal claude
            # exchange path. On failure, return null cleanly.
            Write-Host "  $WARN[poll] login window closed without writing creds.$RESET"
            return (_HandlePasteBack -IsolatedHome $IsolatedHome -ReadyTimeoutSec 180)
        }
        Start-Sleep -Seconds 2
    }
}

function _AccountSetup {
    param([int]$Index)
    Write-Host ''
    Write-Host "  $BRIGHTP--- Account $Index ---$RESET"

    # Display name
    try {
        $display = Read-Host "  $WHITE> display name (e.g. 'Sinister Gmail'; Enter to stop; X to abort)$RESET"
    } catch { return @{ keep = $false; stop = $true } }
    if ([string]::IsNullOrWhiteSpace($display)) {
        return @{ keep = $false; stop = $true }  # operator hit Enter = stop
    }
    if ($display.Trim().ToLower() -match '^(x|q|quit|exit)$') {
        Write-Host "  $WARN(abort requested)$RESET"
        return @{ keep = $false; stop = $true }
    }
    $slot = _Slugify $display
    if (-not $slot) {
        Write-Host "  $WARN[skip] could not slugify '$display' -- need at least one alphanumeric char$RESET"
        return @{ keep = $true; stop = $false }
    }
    if ($slot -ne $display.ToLower()) {
        Write-Host "  $DIM  normalized -> slot='$slot'$RESET"
    }

    if ($DryRun) {
        Write-Host "  $DIM[dry-run] would spawn isolated bash with HOME=<temp>, run claude login, capture creds.$RESET"
        $email = "$slot@example.com"
    } else {
        # Create isolated HOME.
        $rand = [Guid]::NewGuid().ToString('N').Substring(0, 8)
        $isolated = Join-Path $env:TEMP "sinister-claude-login-$slot-$rand"
        try {
            New-Item -ItemType Directory -Path $isolated -Force -ErrorAction Stop | Out-Null
            New-Item -ItemType Directory -Path (Join-Path $isolated '.claude') -Force -ErrorAction Stop | Out-Null
        } catch {
            Write-Host "  $FAIL[!] could not create isolated dir: $_$RESET"
            return @{ keep = $true; stop = $false }
        }
        $null = $script:IsolatedDirsToCleanup.Add($isolated)

        Write-Host "  $SOFT> sandbox: $isolated$RESET"
        Write-Host "  $SOFT> spawning isolated bash window for 'claude login'...$RESET"
        Write-Host "  $DIM   ~/.claude/.credentials.json is NOT touched. Sign in with the$RESET"
        Write-Host "  $DIM   email for slot '$slot' in the browser that pops up.$RESET"

        try {
            $loginProc = _SpawnIsolatedClaudeLoginWindow -IsolatedHome $isolated
        } catch {
            Write-Host "  $FAIL[!] could not spawn login window: $_$RESET"
            return @{ keep = $true; stop = $false }
        }

        Write-Host "  $WHITE> waiting up to $PollTimeout sec for creds to land (browser OAuth in progress)...$RESET"
        $credsPath = _PollForIsolatedCreds -IsolatedHome $isolated -TimeoutSec $PollTimeout -LoginProcess $loginProc
        if (-not $credsPath) {
            Write-Host "  $FAIL[!] no creds captured for slot '$slot'. Skipping.$RESET"
            return @{ keep = $true; stop = $false }
        }

        # Decode email from JWT for the slot row.
        $email = _DecodeOAuthEmail -CredsPath $credsPath
        if ($email) {
            Write-Host "  $OK[+] captured creds; detected email: $email$RESET"
        } else {
            Write-Host "  $OK[+] captured creds; email decode failed (set manually later).$RESET"
            $email = $null
        }

        # Copy isolated creds -> per-slot store consumed by claude-oauth-accounts.ps1 -Action Use.
        $perSlotCreds = Join-Path $env:USERPROFILE ".claude\credentials.$slot.json"
        try {
            $perSlotParent = Split-Path -Parent $perSlotCreds
            if (-not (Test-Path $perSlotParent)) {
                New-Item -ItemType Directory -Path $perSlotParent -Force | Out-Null
            }
            Copy-Item -LiteralPath $credsPath -Destination $perSlotCreds -Force
            Write-Host "  $OK[+] per-slot creds saved -> $perSlotCreds$RESET"
        } catch {
            Write-Host "  $FAIL[!] could not copy creds to per-slot store: $_$RESET"
            return @{ keep = $true; stop = $false }
        }

        # Register the slot in claude-accounts.json via OAuth ps1 RegisterSlot (or fallback inline edit).
        # Use a thin shell: invoke claude-oauth-accounts.ps1 -Action MarkLimited with $null to trigger
        # row insert? No -- safer to do an inline JSON edit here that's idempotent.
        _RegisterOAuthSlot -Name $slot -Display $display -Email $email -CredsFile $perSlotCreds | Out-Null

        # Cleanup isolated dir.
        try {
            Remove-Item -Path $isolated -Recurse -Force -ErrorAction SilentlyContinue
        } catch {}
    }

    # Limited-til prompt
    $iso = $null
    if (_PromptYesNo "Is this account limited til a specific date?" 'n') {
        try {
            $dateRaw = Read-Host "  $WHITE> date YYYY-MM-DD (Enter for next Monday)$RESET"
        } catch { return @{ keep = $false; stop = $true } }
        if ([string]::IsNullOrWhiteSpace($dateRaw)) {
            $iso = _NextMondayIsoUtc
            Write-Host "  $DIM  defaulting to next Monday: $iso$RESET"
        } else {
            try {
                $dt = [datetime]::Parse($dateRaw).Date.ToUniversalTime()
                $iso = $dt.ToString('yyyy-MM-ddTHH:mm:ssZ')
            } catch {
                Write-Host "  $WARN[skip] could not parse '$dateRaw' as date$RESET"
                $iso = $null
            }
        }
        if ($iso -and -not $DryRun) {
            $days = ([datetime]::Parse($iso).ToUniversalTime() - (Get-Date).ToUniversalTime()).TotalDays
            $weekly = ($days -gt 6)
            $extra = @('-Name', $slot, '-Until', $iso)
            if ($weekly) { $extra += '-Weekly' }
            $argList = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$script:OAuthPs1,'-Action','MarkLimited') + $extra
            $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -Wait -PassThru -NoNewWindow
            if ($proc.ExitCode -eq 0) {
                Write-Host "  $OK[+] '$slot' marked limited until $iso$(if ($weekly){' (weekly)'})$RESET"
            } else {
                Write-Host "  $WARN[!] MarkLimited exit $($proc.ExitCode)$RESET"
            }
        }
    }

    $null = $script:CapturedSlots.Add([pscustomobject]@{
        slot     = $slot
        display  = $display
        email    = $email
        limited  = $iso
    })
    return @{ keep = $true; stop = $false }
}

function _RegisterOAuthSlot {
    # Idempotently add/update a slot row in claude-accounts.json.
    param(
        [string]$Name, [string]$Display, [string]$Email, [string]$CredsFile
    )
    if (-not (Test-Path $script:AccountsJson)) {
        Write-Host "  $WARN[register] $script:AccountsJson missing -- skipping registration.$RESET"
        return $false
    }
    try {
        $cfg = Get-Content -LiteralPath $script:AccountsJson -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $cfg.accounts) { $cfg | Add-Member -MemberType NoteProperty -Name accounts -Value @() -Force }
        $existing = $cfg.accounts | Where-Object { $_.name -eq $Name } | Select-Object -First 1
        if ($existing) {
            $existing.auth_mode = 'oauth'
            $existing.credentials_file = $CredsFile
            $existing.enabled = $true
            if ($Email) { $existing.oauth_email = $Email; $existing.label = "$Email ($Name)" }
            if ($Display) { $existing | Add-Member -MemberType NoteProperty -Name display_name -Value $Display -Force }
        } else {
            $row = [pscustomobject]@{
                name                    = $Name
                label                   = $(if ($Email) { "$Email ($Name)" } else { $Name })
                display_name            = $Display
                enabled                 = $true
                auth_mode               = 'oauth'
                oauth_email             = $Email
                credentials_file        = $CredsFile
                env_key                 = 'ANTHROPIC_API_KEY'
                current_sessions        = 0
                max_sessions_concurrent = 5
                plan_tier               = 'max'
                successful_spawns_today = 0
                rate_limited_until_utc  = $null
                last_429_at_utc         = $null
                last_spawn_at_utc       = $null
                quota_resets_at_utc     = $null
                weekly_reset_at_utc     = $null
                fleet_share             = 0.0
            }
            $cfg.accounts = @($cfg.accounts) + @($row)
        }
        $json = $cfg | ConvertTo-Json -Depth 8
        [System.IO.File]::WriteAllText($script:AccountsJson, $json, [System.Text.UTF8Encoding]::new($false))
        return $true
    } catch {
        Write-Host "  $FAIL[register] write failed: $_$RESET"
        return $false
    }
}

function _AccountSetupWithInjected {
    # Same as _AccountSetup but reuses a pre-supplied display name (no prompt).
    # Used when operator typed a display name at the count prompt.
    param([int]$Index, [string]$InjectedDisplay)
    Write-Host ''
    Write-Host "  $BRIGHTP--- Account $Index ---$RESET"
    $slot = _Slugify $InjectedDisplay
    if (-not $slot) {
        Write-Host "  $WARN[skip] could not slugify '$InjectedDisplay'$RESET"
        return @{ keep = $true; stop = $false }
    }
    Write-Host "  $WHITE> display: $InjectedDisplay  ($DIM slot=$slot$WHITE)$RESET"

    if ($DryRun) {
        Write-Host "  $DIM[dry-run] would spawn isolated bash for slot '$slot'$RESET"
        $email = "$slot@example.com"
    } else {
        $rand = [Guid]::NewGuid().ToString('N').Substring(0, 8)
        $isolated = Join-Path $env:TEMP "sinister-claude-login-$slot-$rand"
        try {
            New-Item -ItemType Directory -Path $isolated -Force -ErrorAction Stop | Out-Null
            New-Item -ItemType Directory -Path (Join-Path $isolated '.claude') -Force -ErrorAction Stop | Out-Null
        } catch {
            Write-Host "  $FAIL[!] could not create isolated dir: $_$RESET"
            return @{ keep = $true; stop = $false }
        }
        $null = $script:IsolatedDirsToCleanup.Add($isolated)

        Write-Host "  $SOFT> sandbox: $isolated$RESET"
        Write-Host "  $SOFT> spawning isolated bash window for 'claude login'...$RESET"
        try {
            $loginProc = _SpawnIsolatedClaudeLoginWindow -IsolatedHome $isolated
        } catch {
            Write-Host "  $FAIL[!] could not spawn login window: $_$RESET"
            return @{ keep = $true; stop = $false }
        }
        Write-Host "  $WHITE> waiting up to $PollTimeout sec for creds to land...$RESET"
        $credsPath = _PollForIsolatedCreds -IsolatedHome $isolated -TimeoutSec $PollTimeout -LoginProcess $loginProc
        if (-not $credsPath) {
            Write-Host "  $FAIL[!] no creds captured for '$slot'. Skipping.$RESET"
            return @{ keep = $true; stop = $false }
        }
        $email = _DecodeOAuthEmail -CredsPath $credsPath
        if ($email) {
            Write-Host "  $OK[+] captured creds; email: $email$RESET"
        } else {
            Write-Host "  $OK[+] captured creds (email decode failed)$RESET"
            $email = $null
        }
        $perSlotCreds = Join-Path $env:USERPROFILE ".claude\credentials.$slot.json"
        try {
            $perSlotParent = Split-Path -Parent $perSlotCreds
            if (-not (Test-Path $perSlotParent)) { New-Item -ItemType Directory -Path $perSlotParent -Force | Out-Null }
            Copy-Item -LiteralPath $credsPath -Destination $perSlotCreds -Force
            Write-Host "  $OK[+] saved -> $perSlotCreds$RESET"
        } catch {
            Write-Host "  $FAIL[!] copy failed: $_$RESET"
            return @{ keep = $true; stop = $false }
        }
        _RegisterOAuthSlot -Name $slot -Display $InjectedDisplay -Email $email -CredsFile $perSlotCreds | Out-Null
        try { Remove-Item -Path $isolated -Recurse -Force -ErrorAction SilentlyContinue } catch {}
    }

    $iso = $null
    if (_PromptYesNo "Is this account limited til a specific date?" 'n') {
        try {
            $dateRaw = Read-Host "  $WHITE> date YYYY-MM-DD (Enter for next Monday)$RESET"
        } catch { return @{ keep = $false; stop = $true } }
        if ([string]::IsNullOrWhiteSpace($dateRaw)) {
            $iso = _NextMondayIsoUtc
        } else {
            try { $iso = ([datetime]::Parse($dateRaw).Date.ToUniversalTime()).ToString('yyyy-MM-ddTHH:mm:ssZ') }
            catch { $iso = $null }
        }
        if ($iso -and -not $DryRun) {
            $days = ([datetime]::Parse($iso).ToUniversalTime() - (Get-Date).ToUniversalTime()).TotalDays
            $weekly = ($days -gt 6)
            $extra = @('-Name', $slot, '-Until', $iso)
            if ($weekly) { $extra += '-Weekly' }
            $argList = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$script:OAuthPs1,'-Action','MarkLimited') + $extra
            Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -Wait -NoNewWindow | Out-Null
            Write-Host "  $OK[+] '$slot' marked limited until $iso$RESET"
        }
    }

    $null = $script:CapturedSlots.Add([pscustomobject]@{
        slot = $slot; display = $InjectedDisplay; email = $email; limited = $iso
    })
    return @{ keep = $true; stop = $false }
}


function _PrintSummary {
    Write-Host ''
    Write-Host "  $DARKP---------------------------------------------------------------$RESET"
    Write-Host "  $WHITE$BOLD Summary -- captured this session$RESET"
    Write-Host "  $DARKP---------------------------------------------------------------$RESET"
    if ($script:CapturedSlots.Count -eq 0) {
        Write-Host "  $DIM(no slots processed)$RESET"
        return
    }
    Write-Host ("  {0,-3} {1,-18} {2,-26} {3,-30} {4}" -f '#','SLOT','DISPLAY','EMAIL','LIMITED_UNTIL') -ForegroundColor Cyan
    $i = 0
    foreach ($r in $script:CapturedSlots) {
        $i += 1
        $em = if ($r.email) { $r.email } else { '-' }
        $lim = if ($r.limited) { $r.limited } else { '-' }
        Write-Host ("  {0,-3} {1,-18} {2,-26} {3,-30} {4}" -f $i, $r.slot, $r.display, $em, $lim)
    }
    Write-Host ''
    Write-Host "  $SOFT All slots in claude-accounts.json (source-of-truth):$RESET"
    if ((-not $DryRun) -and (Test-Path $script:OAuthPs1)) {
        $argList = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$script:OAuthPs1,'-Action','List')
        $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList $argList -Wait -PassThru -NoNewWindow
        if ($proc.ExitCode -ne 0) {
            Write-Host "  $WARN(list exited $($proc.ExitCode))$RESET"
        }
    } else {
        Write-Host "  $DIM[dry-run] skipping List$RESET"
    }
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

try {
    _BigBanner
    _Log "wizard start dry-run=$DryRun count-flag=$Count" 'INFO'

    # RKOJ-ELENO :: 2026-05-25T01:30Z :: P0 -- operator directive (image #62):
    # stop hardcoding 4-account default. Add accounts ONE AT A TIME, unbounded,
    # with "Add another? [y/N]" between each. Operator can stop whenever.
    # The legacy -Count flag is still honored for batch/scripted callers.
    $n = $Count
    $unbounded = ($n -le 0)
    if (-not $unbounded -and $n -lt 1) { $n = 1 }
    $maxIters = if ($unbounded) { 999 } else { $n }

    $processed = 0
    for ($i = 1; $i -le $maxIters; $i++) {
        $result = _AccountSetup -Index $i
        if ($result.keep -and -not $result.stop) { $processed++ }
        if ($result.stop) { break }
        # Always ask after each iteration whether to continue (default N so a stray
        # Enter exits cleanly instead of opening another login window).
        if ($unbounded -or $i -lt $maxIters) {
            $more = _PromptYesNo "Add another account?" 'n'
            if (-not $more) { break }
        }
    }

    _PrintSummary

    Write-Host ''
    Write-Host "  $DARKP---------------------------------------------------------------$RESET"
    Write-Host "  $OK[done]$RESET $WHITE Your existing claude sessions are UNCHANGED. Returning to Account Manager...$RESET"
    Write-Host "  $DARKP---------------------------------------------------------------$RESET"
    # RKOJ-ELENO :: 2026-05-25T01:40Z :: operator "enter here doesnt work i need
    # allow flows to allow for unlimited use ... and now it wont fucking close".
    # Replaced dead-end Read-Host with a brief auto-close pause so operator sees
    # the summary then control returns to account_manager.show_account_manager()
    # loop (which re-renders the menu automatically). No keystroke required.
    # 2026-05-25T01:35Z :: bumped 1500->2500ms so operator can read the
    # summary table before the window closes; still no dead-end prompt.
    Start-Sleep -Milliseconds 2500
    _Log "wizard end processed=$($script:CapturedSlots.Count) (auto-close 2500ms)" 'INFO'
}
catch {
    Write-Host ''
    Write-Host "  $FAIL[wizard] unhandled exception: $_$RESET"
    _Log "unhandled: $_" 'ERROR'
    exit 1
}
finally {
    # Cleanup any sandboxes left behind (best-effort).
    foreach ($d in $script:IsolatedDirsToCleanup) {
        try { Remove-Item -Path $d -Recurse -Force -ErrorAction SilentlyContinue } catch {}
    }
}

