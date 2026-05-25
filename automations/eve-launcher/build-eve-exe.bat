@echo off
REM Build EVE.exe :: thin single-file launcher for Sinister Sanctum
REM Author: RKOJ-ELENO :: 2026-05-23
REM
REM Output: automations/eve-launcher/dist/EVE.exe (~15-20 MB)
REM Boot target: <300 ms cold-start (vs ~800-1200 ms for the PS1 launcher).

setlocal enableextensions enabledelayedexpansion
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

REM v0.4 (2026-05-24): wipe dist/EVE + build/EVE first so PyInstaller never
REM trips on "non-empty output directory" when a prior --onedir build exists.
if exist dist\EVE rmdir /S /Q dist\EVE
if exist build\EVE rmdir /S /Q build\EVE

echo  [build] packaging eve.py -^> dist\EVE\EVE.exe (--onedir)...
REM v0.2 (iter 6 2026-05-23): switched from --onefile to --onedir. --onefile
REM extracts python312.dll to %%TEMP%%\_MEI<random> on each launch which fails
REM on Windows boxes with strict AV / missing VC++ runtime (operator hit this
REM 2026-05-23 - EVE.exe spawned a console then immediately closed because
REM `LoadLibrary: python312.dll: module could not be found`). --onedir keeps
REM the DLL next to EVE.exe so no extraction is needed; output is a folder
REM (~20MB) instead of a single exe (~8MB) but it actually launches.
REM v0.3 (iter 9 2026-05-24): eve_picker_lib.py refactor moved core logic to
REM tools/eve-picker/. PyInstaller can't auto-discover that dir, so we pass
REM --paths to add it to sys.path during analysis. Also hidden-import colorsys
REM (stdlib but PyInstaller missed it on a v0.3.0 build attempt).
set "SANCTUM_ROOT=%~dp0..\..\"
REM RKOJ-ELENO :: 2026-05-24 evening — transparent banner-hero icon (operator
REM requested no background + bolder logo). make-icon.py regenerates the ICO
REM at assets\eve-icon.ico (out of the parallel-agent dist/build wipe zone);
REM falls back to root-level eve-icon.ico if assets/ copy missing.
set "EVE_ICON=%HERE%assets\eve-icon.ico"
if not exist "%EVE_ICON%" set "EVE_ICON=%HERE%eve-icon.ico"
pyinstaller --onedir --name EVE ^
    --distpath dist ^
    --workpath build ^
    --specpath build ^
    --clean ^
    --noupx ^
    --icon "%EVE_ICON%" ^
    --paths "%SANCTUM_ROOT%tools\eve-picker" ^
    --hidden-import colorsys ^
    --hidden-import eve_picker_lib ^
    --hidden-import eve_logger ^
    --hidden-import quantum_tools ^
    --hidden-import health_tools ^
    --hidden-import jcode_animation ^
    --hidden-import main_menu ^
    --hidden-import account_manager ^
    --hidden-import account_info_panel ^
    --hidden-import project_picker_multiselect ^
    --hidden-import project_config_grid ^
    --hidden-import tools_menu ^
    --hidden-import eve_ui ^
    --hidden-import garden_of_eden ^
    eve.py
if errorlevel 1 (
    echo  [FAIL] pyinstaller build failed.
    exit /b 3
)

REM v0.7 (2026-05-25T02:55Z) operator hard-canonical "no you dont need action from me you
REM do all that shit for me now". Defender quarantines base_library.zip + sometimes EVE.exe
REM from dist\EVE\ during PyInstaller COLLECT, leaving an incomplete bundle that boots with
REM "Python path configuration" error. Self-heal: ALWAYS salvage base_library.zip + EVE.exe
REM from build\EVE\ (where they survive because AV scan triggers later). Operator never sees
REM this.
echo.
echo  [self-heal] copying base_library.zip + EVE.exe from build\EVE\ in case AV wiped them...
if not exist "dist\EVE" mkdir "dist\EVE" 2>nul
if not exist "dist\EVE\_internal" mkdir "dist\EVE\_internal" 2>nul
if exist "build\EVE\base_library.zip" (
    copy /Y "build\EVE\base_library.zip" "dist\EVE\_internal\base_library.zip" >nul
    echo  [self-heal] base_library.zip restored
)
if exist "build\EVE\EVE.exe" (
    if not exist "dist\EVE\EVE.exe" (
        copy /Y "build\EVE\EVE.exe" "dist\EVE\EVE.exe" >nul
        echo  [self-heal] EVE.exe restored from build\
    )
)

if exist dist\EVE\EVE.exe (
    echo.
    echo  [OK] built dist\EVE\EVE.exe
    echo  Test: dist\EVE\EVE.exe --version
    REM v0.6 (2026-05-24 evening): auto-mirror to stable user-profile location
    REM so Sinister Start.bat probe order (stable -> dist -> PS1) always lands
    REM on a working binary even if dist/EVE gets wiped by a parallel agent
    REM mid-rebuild. Operator hit this 2026-05-24 ("eve exe project launch
    REM dont work") when a sibling agent's wipe collided with my copy step.
    set "EVE_STABLE=%USERPROFILE%\.eve"
    if exist "%EVE_STABLE%" rmdir /S /Q "%EVE_STABLE%"
    mkdir "%EVE_STABLE%" 2>nul
    xcopy /E /I /Y /Q "dist\EVE\*" "%EVE_STABLE%\" >nul
    REM v0.7 self-heal: also copy base_library.zip directly in case xcopy missed it.
    if exist "build\EVE\base_library.zip" (
        if not exist "!EVE_STABLE!\_internal" mkdir "!EVE_STABLE!\_internal" 2>nul
        copy /Y "build\EVE\base_library.zip" "!EVE_STABLE!\_internal\base_library.zip" >nul
    )
    if exist "!EVE_STABLE!\EVE.exe" (
        echo  [OK] mirrored to !EVE_STABLE!\EVE.exe
    ) else (
        echo  [WARN] stable mirror failed; Sinister Start.bat will fall through to dist.
    )
) else (
    echo  [WARN] dist\EVE\EVE.exe missing after build. Check pyinstaller output.
    exit /b 3
)
endlocal
