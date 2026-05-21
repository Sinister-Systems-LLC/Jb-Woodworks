#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-21
# LIVE-BACKING migration v2 — uses cmd /c rmdir for junction removal (works
# non-interactively, unlike PowerShell Remove-Item which prompts).
#
# 5 LIVE-BACKING dirs from D:\Sinister\01_Projects\Sinister\ -> Sanctum projects/sinister-*\source\

set -e

LOG="D:/Sinister Sanctum/_shared-memory/migration-live-backing-v2-2026-05-21.log"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) === START LIVE-BACKING v2 ===" | tee -a "$LOG"

migrate() {
  local NAME="$1"
  local SRC_INNER="$2"   # the actual source dir on D:/ to move
  local DEST="$3"        # Sanctum dest source/ slot
  local SHELL_PARENT="$4"  # parent shell that becomes empty after move

  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$NAME] removing Sanctum junction" | tee -a "$LOG"
  # cmd /c rmdir works on junctions without prompting (PowerShell asks).
  cmd //c "rmdir \"$DEST\"" 2>&1 | head -1 | tee -a "$LOG" || true

  if [ -d "$DEST" ] || [ -L "$DEST" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$NAME] WARN: junction still present after rmdir" | tee -a "$LOG"
    return 1
  fi

  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$NAME] robocopy /move start" | tee -a "$LOG"
  # robocopy: copy then delete source. Use cmd to invoke since the path has spaces.
  # /MOVE /E /R:1 /W:1 /NP /NFL /NDL /NJH /NJS (no per-file logging for speed)
  cmd //c "robocopy \"$SRC_INNER\" \"$DEST\" /MOVE /E /R:1 /W:1 /NP /NFL /NDL /NJH /NJS" >/dev/null 2>&1 || true
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$NAME] robocopy done; verifying" | tee -a "$LOG"
  if [ -d "$DEST" ]; then
    local count
    count=$(ls "$DEST" 2>/dev/null | wc -l)
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$NAME] dest now has $count entries" | tee -a "$LOG"
  fi

  if [ -n "$SHELL_PARENT" ] && [ -d "$SHELL_PARENT" ]; then
    # Archive what's left of the shell parent (orphan .bat scripts etc)
    local archive="D:/Sinister Sanctum/_archive/d-sinister-01_projects-pointers-2026-05-21/Sinister/$NAME"
    mkdir -p "$archive"
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$NAME] archiving shell residual to $archive" | tee -a "$LOG"
    cmd //c "robocopy \"$SHELL_PARENT\" \"$archive\" /MOVE /E /R:1 /W:1 /NP /NFL /NDL /NJH /NJS" >/dev/null 2>&1 || true
  fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$NAME] done" | tee -a "$LOG"
}

# 1a — Sinister-APK (target = the dir ITSELF, no inner source/)
migrate "Sinister-APK" \
  "D:/Sinister/01_Projects/Sinister/Sinister-APK" \
  "D:/Sinister Sanctum/projects/sinister-kernel-apk/source" \
  ""

# 1b — Sinister-Emulator-Bundle (target = inner source/)
migrate "Sinister-Emulator-Bundle" \
  "D:/Sinister/01_Projects/Sinister/Sinister-Emulator-Bundle/source" \
  "D:/Sinister Sanctum/projects/sinister-emulator-bundle/source" \
  "D:/Sinister/01_Projects/Sinister/Sinister-Emulator-Bundle"

# 1c — Sinister-Panel (target = inner source/)
migrate "Sinister-Panel" \
  "D:/Sinister/01_Projects/Sinister/Sinister-Panel/source" \
  "D:/Sinister Sanctum/projects/sinister-panel/source" \
  "D:/Sinister/01_Projects/Sinister/Sinister-Panel"

# 1d — Sinister-Snap-EMU (target = inner source/)
migrate "Sinister-Snap-EMU" \
  "D:/Sinister/01_Projects/Sinister/Sinister-Snap-EMU/source" \
  "D:/Sinister Sanctum/projects/sinister-snap-emu/source" \
  "D:/Sinister/01_Projects/Sinister/Sinister-Snap-EMU"

# 1e — Sinister-TikTok-EMU (target = inner source/)
migrate "Sinister-TikTok-EMU" \
  "D:/Sinister/01_Projects/Sinister/Sinister-TikTok-EMU/source" \
  "D:/Sinister Sanctum/projects/sinister-tiktok-emu/source" \
  "D:/Sinister/01_Projects/Sinister/Sinister-TikTok-EMU"

echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) === END LIVE-BACKING v2 ===" | tee -a "$LOG"
ls "D:/Sinister/01_Projects/Sinister/" 2>&1 | tee -a "$LOG"
