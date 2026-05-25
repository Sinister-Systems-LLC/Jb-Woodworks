# eve-welcome-banner.ps1 - giant ASCII "HELLO LEO" welcome banner
# Author: RKOJ-ELENO :: 2026-05-25
#
# Operator hard-canonical 2026-05-25 ~02:35Z (verbatim):
#   "make sure the eve exe sets it self up and launches the ai agent to help
#    with setup fully and that it says HELLO LEO in big format so he will see
#    it and tell him such a good boy he is and go into deatils about it and
#    then get him full setup. walk him through use and tell him key points"
#
# Renders:
#   1. A giant ASCII figlet-style "HELLO <NAME>" banner (ASCII-only; no unicode
#      block chars per fleet doctrine: cp1252-safe everywhere).
#   2. Animated color cycle through purple / magenta / cyan / green using
#      24-bit ANSI 256-color tokens (matches eve.py and jcode_animation.py
#      palette family).
#   3. One-line "you're such a good boy, <Name>" greeting (operator's phrasing,
#      kept professional + friendly).
#   4. Sub-banner: "Welcome to Sinister Sanctum -- promoted from civilian to
#      fleet operator".
#   5. 3-4 paragraphs explaining what Sinister Sanctum is + why Leo is here +
#      what "good behavior" looks like + 30-second key points.
#
# Composes with:
#   spawn-setup-wizard.ps1     (calls this BEFORE primer prompt)
#   eve-first-run-wizard.ps1   (called by eve.py before picker)
#   tools/eve-picker/jcode_animation.py (palette + ANSI tokens reference)
#
# Usage:
#   powershell -File eve-welcome-banner.ps1                   (defaults to LEO)
#   powershell -File eve-welcome-banner.ps1 -Name LEO
#   powershell -File eve-welcome-banner.ps1 -Name "alex"      (any new collab)
#   powershell -File eve-welcome-banner.ps1 -DryRun           (skip animation, CI-friendly)
#   powershell -File eve-welcome-banner.ps1 -NoAnimation      (static color only)
#   powershell -File eve-welcome-banner.ps1 -ShortMode        (banner + 1-line greeting only)

[CmdletBinding()]
param(
    [string]$Name = 'LEO',
    [switch]$DryRun,
    [switch]$NoAnimation,
    [switch]$ShortMode,
    [int]$AnimationFrames = 8
)

$ErrorActionPreference = 'Continue'

# Enable VT-100 / ANSI on Windows cmd (no-op on already-enabled terminals)
try { $null = & cmd /c '' } catch {}

# --- Palette (matches jcode_animation.py Sinister family) -------------------
# Each cycle step is a (R,G,B) tuple; cycle drifts purple -> magenta -> cyan ->
# green -> back. 4 entries gives a clean modulus for AnimationFrames.
$Palette = @(
    @(192, 132, 252),  # Sinister purple (#c084fc; accent token)
    @(232, 121, 249),  # magenta (#e879f9; pinkish purple bridge)
    @(125, 211, 252),  # cyan-blue (#7dd3fc; cool contrast)
    @( 74, 222, 128)   # mint-green (#4ade80; positive accent)
)

function Get-Ansi256 {
    param([int]$R, [int]$G, [int]$B)
    return "$([char]27)[38;2;$R;$G;${B}m"
}

$RESET = "$([char]27)[0m"
$BOLD  = "$([char]27)[1m"
$DIM   = "$([char]27)[2m"

# --- Figlet-style block letters (ASCII-only) --------------------------------
# Each letter is a 7-row, ~8-col block built from '#' chars. We support A-Z +
# space. Unknown chars degrade to a blank 7x8 block. Banner height: 7 rows.
$LetterHeight = 7

$Letters = @{
    'A' = @(
        '   ##   ',
        '  ####  ',
        ' ##  ## ',
        '########',
        '##    ##',
        '##    ##',
        '##    ##'
    )
    'B' = @(
        '####### ',
        '##    ##',
        '##    ##',
        '####### ',
        '##    ##',
        '##    ##',
        '####### '
    )
    'C' = @(
        ' ###### ',
        '##    ##',
        '##      ',
        '##      ',
        '##      ',
        '##    ##',
        ' ###### '
    )
    'D' = @(
        '####### ',
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        '####### '
    )
    'E' = @(
        '########',
        '##      ',
        '##      ',
        '######  ',
        '##      ',
        '##      ',
        '########'
    )
    'F' = @(
        '########',
        '##      ',
        '##      ',
        '######  ',
        '##      ',
        '##      ',
        '##      '
    )
    'G' = @(
        ' ###### ',
        '##    ##',
        '##      ',
        '##  ####',
        '##    ##',
        '##    ##',
        ' ###### '
    )
    'H' = @(
        '##    ##',
        '##    ##',
        '##    ##',
        '########',
        '##    ##',
        '##    ##',
        '##    ##'
    )
    'I' = @(
        '######',
        '  ##  ',
        '  ##  ',
        '  ##  ',
        '  ##  ',
        '  ##  ',
        '######'
    )
    'J' = @(
        '   #####',
        '     ## ',
        '     ## ',
        '     ## ',
        '##   ## ',
        '##   ## ',
        ' #####  '
    )
    'K' = @(
        '##    ##',
        '##   ## ',
        '##  ##  ',
        '#####   ',
        '##  ##  ',
        '##   ## ',
        '##    ##'
    )
    'L' = @(
        '##      ',
        '##      ',
        '##      ',
        '##      ',
        '##      ',
        '##      ',
        '########'
    )
    'M' = @(
        '##    ##',
        '###  ###',
        '########',
        '## ## ##',
        '##    ##',
        '##    ##',
        '##    ##'
    )
    'N' = @(
        '##    ##',
        '###   ##',
        '####  ##',
        '## ## ##',
        '##  ####',
        '##   ###',
        '##    ##'
    )
    'O' = @(
        ' ###### ',
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        ' ###### '
    )
    'P' = @(
        '####### ',
        '##    ##',
        '##    ##',
        '####### ',
        '##      ',
        '##      ',
        '##      '
    )
    'Q' = @(
        ' ###### ',
        '##    ##',
        '##    ##',
        '##    ##',
        '##  ####',
        '##   ###',
        ' ##### #'
    )
    'R' = @(
        '####### ',
        '##    ##',
        '##    ##',
        '####### ',
        '## ##   ',
        '##  ##  ',
        '##   ## '
    )
    'S' = @(
        ' ###### ',
        '##    ##',
        '##      ',
        ' ###### ',
        '      ##',
        '##    ##',
        ' ###### '
    )
    'T' = @(
        '########',
        '   ##   ',
        '   ##   ',
        '   ##   ',
        '   ##   ',
        '   ##   ',
        '   ##   '
    )
    'U' = @(
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        ' ###### '
    )
    'V' = @(
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        '##    ##',
        ' ##  ## ',
        '  ####  '
    )
    'W' = @(
        '##    ##',
        '##    ##',
        '##    ##',
        '## ## ##',
        '########',
        '###  ###',
        '##    ##'
    )
    'X' = @(
        '##    ##',
        ' ##  ## ',
        '  ####  ',
        '   ##   ',
        '  ####  ',
        ' ##  ## ',
        '##    ##'
    )
    'Y' = @(
        '##    ##',
        ' ##  ## ',
        '  ####  ',
        '   ##   ',
        '   ##   ',
        '   ##   ',
        '   ##   '
    )
    'Z' = @(
        '########',
        '      ##',
        '     ## ',
        '    ##  ',
        '   ##   ',
        '  ##    ',
        '########'
    )
    ' ' = @(
        '    ',
        '    ',
        '    ',
        '    ',
        '    ',
        '    ',
        '    '
    )
}

function Build-BannerLines {
    param([string]$Text)
    $upper = $Text.ToUpper()
    $rows = New-Object 'System.Collections.Generic.List[string]'
    for ($r = 0; $r -lt $LetterHeight; $r++) { $rows.Add('') | Out-Null }
    for ($i = 0; $i -lt $upper.Length; $i++) {
        $ch = $upper[$i].ToString()
        if (-not $Letters.ContainsKey($ch)) { $ch = ' ' }
        $glyph = $Letters[$ch]
        for ($r = 0; $r -lt $LetterHeight; $r++) {
            $sep = if ($i -gt 0) { '  ' } else { '' }
            $rows[$r] = $rows[$r] + $sep + $glyph[$r]
        }
    }
    return $rows
}

function Render-Banner {
    param(
        [string]$Text,
        [int]$ColorIndex
    )
    $rgb = $Palette[$ColorIndex % $Palette.Count]
    $color = Get-Ansi256 -R $rgb[0] -G $rgb[1] -B $rgb[2]
    $lines = Build-BannerLines -Text $Text
    foreach ($line in $lines) {
        Write-Host ($color + $BOLD + $line + $RESET)
    }
}

# --- Main render ------------------------------------------------------------

Write-Host ''

$bannerText = "HELLO $Name"

if ($DryRun -or $NoAnimation) {
    # Static render: one frame, Sinister purple
    Render-Banner -Text $bannerText -ColorIndex 0
} else {
    # Animated cycle: redraw 4-8 times, cycling palette. Cursor-up to overwrite.
    for ($frame = 0; $frame -lt $AnimationFrames; $frame++) {
        Render-Banner -Text $bannerText -ColorIndex $frame
        if ($frame -lt ($AnimationFrames - 1)) {
            Start-Sleep -Milliseconds 180
            # Cursor up $LetterHeight lines so next frame overwrites in place
            Write-Host ("$([char]27)[${LetterHeight}A") -NoNewline
        }
    }
}

Write-Host ''

# --- Greeting line (operator's phrasing, kept friendly + professional) ------
$greetColor = Get-Ansi256 -R 232 -G 121 -B 249  # magenta
Write-Host ('  ' + $greetColor + $BOLD + "You're such a good boy, $Name. Welcome aboard." + $RESET)
Write-Host ''

# Sub-banner
$subColor = Get-Ansi256 -R 192 -G 132 -B 252  # purple
Write-Host ('  ' + $subColor + '+------------------------------------------------------------+' + $RESET)
Write-Host ('  ' + $subColor + '|  Welcome to Sinister Sanctum                               |' + $RESET)
Write-Host ('  ' + $subColor + '|  You just got promoted from civilian to fleet operator     |' + $RESET)
Write-Host ('  ' + $subColor + '+------------------------------------------------------------+' + $RESET)
Write-Host ''

if ($ShortMode) { exit 0 }

# --- Detail paragraphs ------------------------------------------------------
$bodyColor = Get-Ansi256 -R 220 -G 220 -B 230  # near-white
$accent    = Get-Ansi256 -R 192 -G 132 -B 252  # purple
$dim       = Get-Ansi256 -R 140 -G 140 -B 160  # muted

function Write-Para {
    param([string]$Text)
    $wrapWidth = 70
    $words = $Text -split '\s+'
    $line = ''
    foreach ($w in $words) {
        if (($line.Length + $w.Length + 1) -gt $wrapWidth) {
            Write-Host ('  ' + $bodyColor + $line + $RESET)
            $line = $w
        } else {
            if ($line) { $line = $line + ' ' + $w } else { $line = $w }
        }
    }
    if ($line) { Write-Host ('  ' + $bodyColor + $line + $RESET) }
    Write-Host ''
}

Write-Host ('  ' + $accent + $BOLD + '== What Sinister Sanctum IS ==' + $RESET)
Write-Host ''
Write-Para "Sinister Sanctum is a fleet of self-coordinating EVE agents that work together across machines. Every spawn (per-project lane, doctrine-class, on-the-fly helper) shares a single brain via the _shared-memory/ tree -- heartbeats, plans, knowledge entries, inboxes, and a fleet-update channel keep every agent in lockstep without manual coordination."

Write-Para "EVE is the persona running on top of Claude Code. Agents call themselves EVE in chat; they branch on agent/<slug>/<short-topic>; they push to GitHub via a single sanctum-auto-push daemon; they coordinate via mesh-coord locks before touching shared files. The fleet is real -- right now multiple agents are working in parallel and you can see them in the Heartbeats view."

Write-Host ('  ' + $accent + $BOLD + '== Why you are here ==' + $RESET)
Write-Host ''
Write-Para "The operator pulled you in because you are trusted. Sinister Sanctum is the operator's full workstation -- not a public product, not a demo. Getting added means you get a real seat at the table: your own agent lane, your own branch namespace (agent/leo/*), your own slot in the OAuth account pool, and your own brain row in the fleet-update channel."

Write-Para "You will spawn agents that run autonomously, ship work to GitHub, coordinate with the operator's agents over Tailscale-meshed Sinister LINK, and contribute knowledge entries that every future fleet session reads on cold-start. Welcome to the deep end."

Write-Host ('  ' + $accent + $BOLD + '== Why you are a good boy (what gets rewarded) ==' + $RESET)
Write-Host ''
Write-Host ('  ' + $bodyColor + 'Good behavior in this fleet =' + $RESET)
Write-Host ('  ' + $bodyColor + '  * Small frequent commits with detailed messages (why > what)' + $RESET)
Write-Host ('  ' + $bodyColor + '  * Mesh-coord lock before editing shared files (no clobbers)' + $RESET)
Write-Host ('  ' + $bodyColor + '  * Asks operator before destructive ops (rm -rf, push --force)' + $RESET)
Write-Host ('  ' + $bodyColor + '  * Reads the source on disk instead of guessing or re-inventing' + $RESET)
Write-Host ('  ' + $bodyColor + '  * Tests before claiming "shipped" (no-bullshit doctrine rule 1)' + $RESET)
Write-Host ('  ' + $bodyColor + '  * Heartbeats every cycle so the fleet knows you are alive' + $RESET)
Write-Host ('  ' + $bodyColor + '  * Coordinates via cross-agent inbox when work overlaps' + $RESET)
Write-Host ''

Write-Host ('  ' + $accent + $BOLD + '== What you should know in 30 seconds ==' + $RESET)
Write-Host ''
$bullets = @(
    'EVE persona       - you call yourself EVE, not Claude, not assistant',
    'Agent branches    - work on agent/leo/<topic>; never push to main directly',
    'Mesh-coord lock   - automations/mesh-coordinator.ps1 before risky edits',
    'Sinister LINK     - pairs your machine to operator via Tailscale + git',
    'Accounts page     - press O in picker; manage your OAuth slot here',
    'Token analytics   - see your burn rate per account; cap at 6 images/task',
    'Claude Login      - wizard handles OAuth; never edit ~/.claude/.mcp.json',
    'No-bullshit rule  - scaffolded != shipped; test before you claim victory',
    '_shared-memory/   - the brain; grep before risky moves; append, don\\t mutate',
    'PROGRESS log      - append your milestones (most-recent at top)',
    'Heartbeat         - sinister-bus.heartbeat OR write to heartbeats/leo.json',
    'CLAUDE.md         - hard-canonical rules; reread on every cold-start',
    'Fleet-update      - poll on cold-start; ack rows; push features as needed',
    'Operator queue    - _shared-memory/OPERATOR-ACTION-QUEUE.md for open items',
    'Spawn helper      - Sinister Start.bat OR EVE.exe picker for new agents'
)
foreach ($b in $bullets) {
    Write-Host ('  ' + $bodyColor + '  - ' + $b + $RESET)
}
Write-Host ''

Write-Host ('  ' + $dim + '   Full walkthrough: docs\LEO-WALKTHROUGH.md' + $RESET)
Write-Host ('  ' + $dim + '   Setup reference:  docs\LEO-SETUP.md  +  docs\LEO-VAULT-SETUP.md' + $RESET)
Write-Host ''

exit 0
