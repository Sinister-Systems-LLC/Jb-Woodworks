@echo off
REM Author: RKOJ-ELENO :: 2026-05-21
REM One-click launcher for the NEW Sinister Panel-style RKOJ pywebview UI.
REM
REM Frameless rounded window. Loads automations/window-manager/web/ which was
REM rewritten 2026-05-21 to match Sinister Panel layout (sidebar with sections +
REM chip-tabs header + KPI strip + project sub-tabs + 3 panes: agents / phones /
REM workstation).

set EXE="D:\Sinister Sanctum\automations\window-manager\dist\RKOJ\RKOJ.exe"

if not exist %EXE% (
    echo ERROR: %EXE% not found.
    echo The workstation EXE may still be building. Wait ~1 min and retry,
    echo or rebuild: cd "D:\Sinister Sanctum\automations\window-manager" ^&^& pyinstaller --noconfirm RKOJ.spec
    pause
    exit /b 1
)

echo [Launch-RKOJ-Panel] Starting frameless pywebview window...
start "" %EXE%
exit /b 0
