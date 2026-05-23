@echo off
REM Author: RKOJ-ELENO :: 2026-05-23
REM One-click first generation for the JKOR banner.

setlocal
pushd "%~dp0"

if "%GEMINI_API_KEY%"=="" if "%NANO_BANANA_API_KEY%"=="" if "%GOOGLE_API_KEY%"=="" (
  echo [JKOR] No API key set. Run this in PowerShell first:
  echo   [Environment]::SetEnvironmentVariable^('GEMINI_API_KEY','^<your-key^>','User'^)
  echo Then close this window and re-run.
  popd
  pause
  exit /b 1
)

set "PROMPT=A wide horizontal banner illustration. Center-left: a charismatic purple-skinned demon-jester character with small dark horns, a small gold crown, mischievous grin showing teeth, expressive purple-rimmed eyes. Holds a fan of playing cards in the left hand and a sorcerer's wand with a small star at the tip in the right hand. Wearing a regal purple-and-gold jester collar and cape. Looking at the viewer. Background: calm premium dark backdrop, deep near-black (#0A0B1E) at the edges with a subtle vertical Sanctum-purple gradient glow (#7A3DD4 to #4B1F8B) directly behind the character only. Clean and dark everywhere else. Wide cinematic banner aspect (4:1). Style: clean cinematic digital painting, smooth volumetric lighting on the character, premium video-game character-art quality, high contrast between lit subject and calm dark backdrop."

python -m nano_banana ^
  --prompt "%PROMPT%" ^
  --output "generated\banner-v1.png" ^
  --brand jkor ^
  --ref "reference\00-base-banner-original.png" ^
  --ref "reference\01-color-scheme-command-center.png"

popd
endlocal
pause
