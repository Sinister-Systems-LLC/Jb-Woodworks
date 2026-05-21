@echo off
REM ============================================================================
REM  Sinister-Agent-Unlock.bat  --  grant the Panel agent SSH / git permissions
REM
REM  Author: Sinister Panel agent (Claude Opus 4.7 1M) :: 2026-05-20
REM  TODO: migrate to LetsText bat system per p.md 2026-05-19 directive once
REM        operator surfaces the bat-creator interface.
REM
REM  Operator directive 2026-05-20: "make a one click bat for all
REM  permissions you need so you can do all pushes and updates for panel
REM  for me no more bat files".
REM
REM  This bat merges SSH/scp/git permission rules into your
REM  ~/.claude/settings.json so the Panel agent can run prod-Hetzner
REM  operations directly. Idempotent — safe to re-run.
REM
REM  After running:
REM    1. Close + reopen Claude Code (so new permissions load)
REM    2. From then on the agent can run:
REM       - ssh root@95.216.240.227 ...
REM       - scp ... root@95.216.240.227:...
REM       - git push / pull / merge / fetch
REM       directly via Bash tool, no bat files needed.
REM ============================================================================

setlocal

set PS_SCRIPT=D:\Sinister\01_Projects\Sinister\Sinister-Panel\scripts\agent-unlock.ps1

if not exist "%PS_SCRIPT%" (
  echo [X] %PS_SCRIPT% not found. Re-run from the canonical D:\ Panel checkout.
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
exit /b %ERRORLEVEL%
