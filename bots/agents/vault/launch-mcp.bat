@echo off
REM Author: Sinister Sanctum master agent (Claude) :: 2026-05-19
REM
REM Launch wrapper for the Vault MCP server. Sets env vars then execs server.py.
REM Why a wrapper: `claude mcp add -e KEY=value` chokes on env-var values that
REM contain spaces (e.g. "D:/Sinister/Sinister Skills") because the CLI's
REM variadic -e parser misreads them. A 4-line bat sidesteps the issue and
REM makes the MCP entry in ~/.claude.json a single clean command.

set SINISTER_HUB_ROOT=D:\Sinister\Sinister Skills
set VAULT_DAEMON_URL=http://127.0.0.1:5078
python "D:\Sinister Sanctum\bots\agents\vault\server.py" %*
