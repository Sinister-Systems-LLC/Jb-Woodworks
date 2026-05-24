@echo off
REM Build EVE.exe :: thin single-file launcher for Sinister Sanctum
REM Author: RKOJ-ELENO :: 2026-05-23
REM
REM Output: automations/eve-launcher/dist/EVE.exe (~15-20 MB)
REM Boot target: <300 ms cold-start (vs ~800-1200 ms for the PS1 launcher).

setlocal enableextensions
set "HERE=%~dp0"
cd /D "%HERE%"

where pyinstaller >nul 2>&1
if errorlevel 1 (
    echo  [setup] installing pyinstaller via pip...
    python -m pip install --quiet --disable-pip-version-check pyinstaller
    if errorlevel 1 (
        echo  [FAIL] could not install pyinstaller. Run: python -m pip install pyinstaller
        exit /b 2
    )
)

echo  [build] packaging eve.py -^> dist\EVE\EVE.exe (--onedir)...
REM v0.2 (iter 6 2026-05-23): switched from --onefile to --onedir. --onefile
REM extracts python312.dll to %%TEMP%%\_MEI<random> on each launch which fails
REM on Windows boxes with strict AV / missing VC++ runtime (operator hit this
REM 2026-05-23 - EVE.exe spawned a console then immediately closed because
REM `LoadLibrary: python312.dll: module could not be found`). --onedir keeps
REM the DLL next to EVE.exe so no extraction is needed; output is a folder
REM (~20MB) instead of a single exe (~8MB) but it actually launches.
pyinstaller --onedir --name EVE ^
    --distpath dist ^
    --workpath build ^
    --specpath build ^
    --clean ^
    --noupx ^
    eve.py
if errorlevel 1 (
    echo  [FAIL] pyinstaller build failed.
    exit /b 3
)

if exist dist\EVE\EVE.exe (
    echo.
    echo  [OK] built dist\EVE\EVE.exe
    for %%I in (dist\EVE\EVE.exe) do echo       size = %%~zI bytes
    echo.
    echo  Test: dist\EVE\EVE.exe --version
    echo  Install: Sinister Start.bat already probes dist\EVE\EVE.exe (v6.5+).
) else (
    echo  [WARN] dist\EVE\EVE.exe missing after build. Check pyinstaller output.
    exit /b 3
)
endlocal
