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

echo  [build] packaging eve.py -^> dist\EVE.exe ...
pyinstaller --onefile --name EVE ^
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

if exist dist\EVE.exe (
    echo.
    echo  [OK] built dist\EVE.exe
    for %%I in (dist\EVE.exe) do echo       size = %%~zI bytes
    echo.
    echo  Test: dist\EVE.exe
    echo  Install: copy dist\EVE.exe to a folder on PATH, or have Sinister Start.bat probe for it.
) else (
    echo  [WARN] dist\EVE.exe missing after build. Check pyinstaller output.
    exit /b 3
)
endlocal
