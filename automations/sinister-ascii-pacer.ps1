# Sinister ASCII Pacer :: NO-OP STUB (was: 30fps ANSI animation player)
# Author: RKOJ-ELENO :: 2026-05-28
#
# Operator hard-canonical 2026-05-28 (Image #6): "the ascii on the terminal
# isterminal is dog shit fix it." The old pacer played
# projects\sinister-ascii-converter\output\eve-startup-combined.ans at 30fps
# in the spawn console -- frames were misaligned over wallpaper-style backgrounds
# (Image #6 shows broken splayed art); contributed to cluttered launch surface
# in Image #10 (banner spam).
#
# Stub now returns immediately. The launcher's Show-Banner block in
# sinister-terminal-picker.ps1 + start-sinister-session.ps1's compact EVE header
# are the canonical visual identity. Animation is intentionally killed -- the
# operator wants snappy "everything launches right + loop to ask if I want
# more" (Image #9), not a 6-second startup show.
#
# To re-enable for a specific lane, set $env:SINISTER_KEEP_PACER='1' before
# invoking the launcher. Operator override only.

if ($env:SINISTER_KEEP_PACER -ne '1') {
    return
}

# --- LEGACY PACER (gated; only runs when operator opts in) -------------------
$ErrorActionPreference = 'SilentlyContinue'
$combined = 'D:\Sinister Sanctum\projects\sinister-ascii-converter\output\eve-startup-combined.ans'
if (-not (Test-Path $combined)) {
    Write-Host "  [warn] ASCII combined file not found: $combined"
    return
}
$h = [char]27 + '[H'
$data = [IO.File]::ReadAllText($combined, [Text.Encoding]::UTF8)
$frames = $data -split [regex]::Escape($h)
[Console]::Out.Write([char]27 + '[?25l' + [char]27 + '[2J')
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$frameMs = 33
$i = 0
foreach ($f in $frames) {
    if ($f.Length -eq 0) { continue }
    $target = $i * $frameMs
    $wait = $target - $sw.ElapsedMilliseconds
    if ($wait -gt 0) { Start-Sleep -Milliseconds $wait }
    if ($sw.ElapsedMilliseconds -gt ($target + $frameMs)) { $i++; continue }
    [Console]::Out.Write($h + $f)
    $i++
}
[Console]::Out.Write([char]27 + '[?25h' + [char]27 + '[0m' + "`n")
