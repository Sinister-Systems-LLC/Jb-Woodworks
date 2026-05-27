@echo off
REM git-headless.cmd -- silent git wrapper that ALWAYS uses the direct mingw64
REM git.exe (NOT the cmd/git.exe wrapper that pops a visible black window).
REM Author: RKOJ-ELENO :: 2026-05-26
REM Operator hard-canonical 2026-05-26T20:53Z (Image #8 verbatim):
REM   "random fucking windows keep opening i need those to all use our sinsiter
REM    terminal and i need it to be headless without loosing fucntion. im tired
REM    of fucking seeing the popups"
REM
REM Root cause: `git` on PATH resolves to `C:\Program Files\Git\cmd\git.exe`
REM which is a tiny launcher that ALWAYS allocates a console window even when
REM the parent is hidden. The real binary is `C:\Program Files\Git\mingw64\bin
REM \git.exe` which inherits stdio cleanly with no extra window.
REM
REM Use this wrapper instead of bare `git` in:
REM   - schtasks (TR = "C:\Users\Zonia\.eve\bin\git-headless.cmd <args>")
REM   - PowerShell scripts that auto-push
REM   - Python automations spawning git via subprocess
REM
REM Composes with: d-drive-unplug-resilience-doctrine-2026-05-26 + the
REM ~/.eve/headless-runner.vbs sibling that wraps non-git commands.

setlocal
set "GIT_DIRECT=C:\Program Files\Git\mingw64\bin\git.exe"
if not exist "%GIT_DIRECT%" (
    REM Fallback to PATH-resolved git if mingw64 missing (e.g. portable git).
    "git.exe" %*
    exit /b %ERRORLEVEL%
)
"%GIT_DIRECT%" %*
exit /b %ERRORLEVEL%
