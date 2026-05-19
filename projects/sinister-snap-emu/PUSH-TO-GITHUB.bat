@echo off
REM PUSH-TO-GITHUB.bat - bulletproof one-click push.
REM Logs EVERY step to push-2026-05-19.log so we can diagnose exactly where things stop.
REM Window stays open no matter what (final pause is unconditional).

setlocal EnableDelayedExpansion

set "SOURCE=D:\Sinister Sanctum\projects\sinister-snap-emu\source"
set "REPO_NAME=Sinister-Snap-EMU-Snap-API-"
set "HTTPS_URL=https://github.com/Sinister-Systems-LLC/%REPO_NAME%.git"
set "SSH_URL=git@github.com:Sinister-Systems-LLC/%REPO_NAME%.git"
set "LOG=%~dp0push-2026-05-19.log"

REM Wipe + start fresh log
echo === PUSH-TO-GITHUB %DATE% %TIME% ===> "%LOG%"

echo ============================================================
echo PUSH-TO-GITHUB  Sinister Snap EMU
echo ============================================================
echo   Working dir:  %~dp0
echo   Source:       %SOURCE%
echo   Repo:         Sinister-Systems-LLC/%REPO_NAME%
echo   Log:          %LOG%
echo ============================================================
echo.

REM ===== [0/8] git on PATH =====
echo [0/8] Checking git on PATH... >> "%LOG%"
where git >> "%LOG%" 2>&1
if errorlevel 1 (
    echo FAIL: git.exe not on PATH. Add Git for Windows to PATH first.
    echo See log: %LOG%
    goto :end
)
echo   git: OK

REM ===== [1/8] inside the repo =====
echo. >> "%LOG%"
echo [1/8] cd into source + verify git repo... >> "%LOG%"
cd /d "%SOURCE%" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo FAIL: cannot cd to %SOURCE% - see %LOG%
    goto :end
)
git rev-parse --is-inside-work-tree >> "%LOG%" 2>&1
if errorlevel 1 (
    echo FAIL: not a git repo - see %LOG%
    goto :end
)
echo   in repo: OK

REM ===== [2/8] current state snapshot =====
echo. >> "%LOG%"
echo [2/8] Current state: >> "%LOG%"
git log --oneline -3 >> "%LOG%" 2>&1
echo --- branch --- >> "%LOG%"
git branch --show-current >> "%LOG%" 2>&1
echo --- remote --- >> "%LOG%"
git remote -v >> "%LOG%" 2>&1
echo --- status counts --- >> "%LOG%"
git status --short >> "%LOG%" 2>&1
echo   state snapshot logged

REM ===== [3/8] choose remote (SSH if works, else HTTPS) =====
echo. >> "%LOG%"
echo [3/8] Test SSH (BatchMode, 10s timeout)... >> "%LOG%"
ssh -T -o BatchMode=yes -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new git@github.com >> "%LOG%" 2>&1
set SSH_EC=!ERRORLEVEL!
echo SSH exit: !SSH_EC! >> "%LOG%"
REM SSH -T returns 1 on successful auth (ANY ssh -T returns 1 for "no shell access").
REM We grep the log for "successfully authenticated" to know for sure.
findstr /C:"successfully authenticated" "%LOG%" >NUL 2>&1
if not errorlevel 1 (
    set "REMOTE_URL=%SSH_URL%"
    echo   SSH: authenticated  using SSH
) else (
    set "REMOTE_URL=%HTTPS_URL%"
    echo   SSH: not authenticated  falling back to HTTPS
    echo   ^(Git Credential Manager will prompt on first push if no PAT cached^)
)
echo   chosen remote: !REMOTE_URL!
echo Chosen remote: !REMOTE_URL! >> "%LOG%"

REM ===== [4/8] set remote =====
echo. >> "%LOG%"
echo [4/8] git remote set-url origin !REMOTE_URL! ... >> "%LOG%"
git remote set-url origin "!REMOTE_URL!" >> "%LOG%" 2>&1
git remote -v >> "%LOG%" 2>&1
echo   remote set

REM ===== [5/8] verify reachable =====
echo. >> "%LOG%"
echo [5/8] git ls-remote origin HEAD ... >> "%LOG%"
git ls-remote origin HEAD >> "%LOG%" 2>&1
echo ls-remote exit: !ERRORLEVEL! >> "%LOG%"
echo   ls-remote done ^(empty repo = OK^)

REM ===== [6/8] stage =====
echo. >> "%LOG%"
echo [6/8] git add -A ^(can take 1-2 min on 6080 files^)... >> "%LOG%"
echo   staging... ^(may take 1-2 min^)
git add -A >> "%LOG%" 2>&1
echo add exit: !ERRORLEVEL! >> "%LOG%"
echo   --- diff --cached summary --- >> "%LOG%"
git diff --cached --shortstat >> "%LOG%" 2>&1
echo   staged

REM ===== [7/8] commit =====
echo. >> "%LOG%"
echo [7/8] git commit... >> "%LOG%"
git commit -m "migration C: to D: + Java-layer hook breakthrough + UA fix + memory + bot-network refs" -m "Physical move from C:\Users\Zonia\Desktop\Sinister Snap EMU.API to D:\Sinister\01_Projects\Sinister\Sinister-Snap-EMU\source. Path rewrite: 135 occurrences across 74 files. Memory layer: canonical_location + bot_network_root + MCP/agent fleet awareness in R.md + s.md + g.md. Java-layer hook: SnapTokenApiGatewayHttpInterface.fetchSnapAccessTokens(KJh) located, UnifiedGrpcService.unaryCall hooked. UA: Snapchat/13.88.1.0 (Pixel 6a; Android 14). .gitignore extended for keybox/auth-tokens/PEM/proxy creds. Bundle migration in parallel." >> "%LOG%" 2>&1
echo commit exit: !ERRORLEVEL! >> "%LOG%"
echo   committed ^(may be no-op if nothing to commit^)

REM ===== [8/8] push =====
echo. >> "%LOG%"
echo [8/8] git push -u origin main ... >> "%LOG%"
echo   pushing ^(this may take several minutes  uploading ~1.2 GB^)
git push -u origin main >> "%LOG%" 2>&1
set PUSH_EC=!ERRORLEVEL!
echo push exit: !PUSH_EC! >> "%LOG%"
echo. >> "%LOG%"
echo === FINAL HEAD === >> "%LOG%"
git log --oneline -3 >> "%LOG%" 2>&1
echo === REMOTE === >> "%LOG%"
git remote -v >> "%LOG%" 2>&1

echo.
if "!PUSH_EC!"=="0" (
    echo ============================================================
    echo PUSH SUCCESS
    echo ============================================================
    echo   Verify: https://github.com/Sinister-Systems-LLC/%REPO_NAME%
) else (
    echo ============================================================
    echo PUSH FAILED  exit !PUSH_EC!
    echo ============================================================
    echo   Read the log for the exact git error:
    echo     %LOG%
    echo.
    echo   Common causes:
    echo     - HTTPS auth: Git Credential Manager prompted and was dismissed
    echo     - SSH key not registered with this GitHub account
    echo     - Push rejected ^(remote not actually empty, or branch mismatch^)
)

:end
echo.
echo Press any key to close ^(window will stay open until you press a key^).
pause >NUL
exit /b !PUSH_EC!
