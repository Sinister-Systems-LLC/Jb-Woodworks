@echo off
REM Author: RKOJ-ELENO :: 2026-05-23
REM Smoke-test the nano-banana wrapper. Requires GEMINI_API_KEY set in user env.

setlocal
pushd "%~dp0"
if "%GEMINI_API_KEY%"=="" if "%NANO_BANANA_API_KEY%"=="" (
  echo [nano-banana] No API key set. See README for setx command.
  popd
  exit /b 1
)
set OUT=%TEMP%\nano-banana-smoke-%RANDOM%.png
python -m nano_banana --prompt "A single banana on a dark plate, studio lighting, photorealistic, no text" --output "%OUT%"
echo.
echo Wrote: %OUT%
popd
endlocal
