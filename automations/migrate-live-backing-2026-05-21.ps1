# Author: RKOJ-ELENO :: 2026-05-21
# Purpose: One-shot migration of 5 LIVE-BACKING dirs from D:\Sinister\01_Projects\Sinister\
#          into D:\Sinister Sanctum\projects\sinister-*\source\ per projects-audit-v2.md.
#
# Operator green-light 2026-05-21: "do the LIVE-BACKING migration and complete everything
# i said to do".
#
# Per-step pattern:
#   1. Remove-Item <junction> -Force (NO -Recurse — would traverse + delete backing data)
#   2. robocopy /MOVE /E from D:/Sinister source -> Sanctum source/
#   3. Log to D:\Sinister Sanctum\_shared-memory\migration-live-backing-2026-05-21.log
#
# Total payload ~11 GB. Wall-clock estimate 5-15 min depending on file count.

$ErrorActionPreference = "Continue"
$LogPath = "D:\Sinister Sanctum\_shared-memory\migration-live-backing-2026-05-21.log"

function Log($msg) {
    $stamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    $line = "$stamp $msg"
    Write-Host $line
    Add-Content -LiteralPath $LogPath -Value $line
}

Log "=== LIVE-BACKING migration START ==="

# 1a — Sinister-APK (3.72 GB; target = the dir ITSELF, not an inner source/)
Log "1a Sinister-APK : removing Sanctum junction"
Remove-Item -LiteralPath "D:\Sinister Sanctum\projects\sinister-kernel-apk\source" -Force -ErrorAction Continue
Log "1a Sinister-APK : robocopy /move start (3.72 GB)"
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-APK" "D:\Sinister Sanctum\projects\sinister-kernel-apk\source" /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs | Out-Null
Log "1a Sinister-APK : done"

# 1b — Sinister-Emulator-Bundle (363 MB; target = inner source/)
Log "1b Sinister-Emulator-Bundle : removing Sanctum junction"
Remove-Item -LiteralPath "D:\Sinister Sanctum\projects\sinister-emulator-bundle\source" -Force -ErrorAction Continue
Log "1b Sinister-Emulator-Bundle : robocopy /move start (363 MB)"
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle\source" "D:\Sinister Sanctum\projects\sinister-emulator-bundle\source" /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs | Out-Null
Log "1b Sinister-Emulator-Bundle : inner source moved; archiving shell"
$arch1b = "D:\Sinister Sanctum\_archive\d-sinister-01_projects-pointers-2026-05-21\Sinister\Sinister-Emulator-Bundle"
New-Item -ItemType Directory -Path $arch1b -Force | Out-Null
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Emulator-Bundle" $arch1b /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs | Out-Null
Log "1b Sinister-Emulator-Bundle : done"

# 1c — Sinister-Panel (1.16 GB; target = inner source/; 8 orphan .bat scripts at top level)
Log "1c Sinister-Panel : removing Sanctum junction"
Remove-Item -LiteralPath "D:\Sinister Sanctum\projects\sinister-panel\source" -Force -ErrorAction Continue
Log "1c Sinister-Panel : robocopy /move start (1.16 GB inner source/)"
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Panel\source" "D:\Sinister Sanctum\projects\sinister-panel\source" /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs | Out-Null
Log "1c Sinister-Panel : robocopy /move orphan scripts -> projects/sinister-panel/automations/"
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Panel" "D:\Sinister Sanctum\projects\sinister-panel\automations" /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs /xd source | Out-Null
Log "1c Sinister-Panel : done"

# 1d — Sinister-Snap-EMU (1.14 GB)
Log "1d Sinister-Snap-EMU : removing Sanctum junction"
Remove-Item -LiteralPath "D:\Sinister Sanctum\projects\sinister-snap-emu\source" -Force -ErrorAction Continue
Log "1d Sinister-Snap-EMU : robocopy /move inner source (1.14 GB)"
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source" "D:\Sinister Sanctum\projects\sinister-snap-emu\source" /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs | Out-Null
$arch1d = "D:\Sinister Sanctum\_archive\d-sinister-01_projects-pointers-2026-05-21\Sinister\Sinister-Snap-EMU"
New-Item -ItemType Directory -Path $arch1d -Force | Out-Null
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU" $arch1d /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs /xd source | Out-Null
Log "1d Sinister-Snap-EMU : done"

# 1e — Sinister-TikTok-EMU (4.87 GB; largest move)
Log "1e Sinister-TikTok-EMU : removing Sanctum junction"
Remove-Item -LiteralPath "D:\Sinister Sanctum\projects\sinister-tiktok-emu\source" -Force -ErrorAction Continue
Log "1e Sinister-TikTok-EMU : robocopy /move inner source (4.87 GB) - LARGEST"
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU\source" "D:\Sinister Sanctum\projects\sinister-tiktok-emu\source" /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs | Out-Null
$arch1e = "D:\Sinister Sanctum\_archive\d-sinister-01_projects-pointers-2026-05-21\Sinister\Sinister-TikTok-EMU"
New-Item -ItemType Directory -Path $arch1e -Force | Out-Null
robocopy "D:\Sinister\01_Projects\Sinister\Sinister-TikTok-EMU" $arch1e /move /e /r:1 /w:1 /np /nfl /ndl /njh /njs /xd source | Out-Null
Log "1e Sinister-TikTok-EMU : done"

Log "=== LIVE-BACKING migration END ==="
Log "Remaining at D:\Sinister\01_Projects\Sinister\ : $(Get-ChildItem 'D:\Sinister\01_Projects\Sinister\' -ErrorAction Continue | Select-Object -ExpandProperty Name | Sort-Object) "
