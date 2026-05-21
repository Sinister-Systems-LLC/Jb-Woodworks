# sinister-watchdog

> **Author:** RKOJ-ELENO :: 2026-05-21
> License: AGPL-3.0-or-later

Auto-online keeper for the Sanctum fleet. Watches local agent heartbeats + MCP
servers + (optional) docker-backed services. When something goes stale or
unresponsive, the watchdog respawns it — silently, no popups, in the background.

Operator directive 2026-05-21 (verbatim): *"make sure we are using our local
agents. if they are offline or anything like that have them auto come online.
same with mcp. you can use docker on my pc or things like that"*.

## What it watches

| Surface | Source of truth | Stale signal | Action |
|---|---|---|---|
| Local agents | `_shared-memory/heartbeats/<slug>.json|.beat` (file mtime) | mtime > 5 min old (configurable; per-slug overrides allowed) | look up slug in `registry.json` → spawn detached |
| MCP servers | `~/.claude/.mcp.json` (READ-ONLY — never written) | `initialize` request gets no response in 8s | spawn the same command detached |
| Docker services | `registry.json` entries with `kind: "docker"` | `docker ps --filter name=<...>` returns empty | `docker start <name>` (or `docker run` if not yet created) |

Everything is logged to `_shared-memory/watchdog.log` (rotated at 5 MB).

## Files

| File | Purpose |
|---|---|
| `sinister_watchdog/core.py` | Loop, scan, probe, revive |
| `sinister_watchdog/cli.py` | `status` / `start` / `stop` / `tail` / `probe` / `tick` / `registry` |
| `sinister_watchdog/__main__.py` | `python -m sinister_watchdog ...` entry |
| `registry.json` | Per-slug launch commands (hand-edited by operator) |
| `install-task.ps1` | Registers `SinisterWatchdog` scheduled task — fires at logon + at startup, hidden window |
| `watchdog.pid` | PID file (created when daemon is running) |
| `state.json` | Last-tick snapshot (consumed by Forge `/watchdog` slash command) |

## CLI

```powershell
# One-shot status snapshot
python -m sinister_watchdog status

# Start the loop in the foreground (you'll see log lines on stdout)
python -m sinister_watchdog start --interval 60 --stale-minutes 5

# Start detached, no window — what the scheduled task runs
python -m sinister_watchdog start --bg

# Probe MCP servers once and print results
python -m sinister_watchdog probe

# Stop the daemon
python -m sinister_watchdog stop

# Tail the log
python -m sinister_watchdog tail 80

# JSON status (for the Forge surface)
python -m sinister_watchdog status --json
```

## Install (one operator click)

```powershell
cd "D:\Sinister Sanctum\tools\sinister-watchdog"
.\install-task.ps1
```

That registers `SinisterWatchdog` to fire at:
- user logon
- system startup

The task runs `python -m sinister_watchdog start --foreground --interval 60`
with no console window. To stop the automation: `Unregister-ScheduledTask -TaskName SinisterWatchdog -Confirm:$false` or `.\install-task.ps1 -Uninstall`.

To run immediately after registering: `.\install-task.ps1 -RunNow`.

## Registry shape (`registry.json`)

```json
{
  "agents": {
    "sanctum": {
      "kind": "process",
      "command": "cmd.exe",
      "args": ["/c", "start", "", "C:\\Users\\Zonia\\Desktop\\Start-Sinister-Session.bat"],
      "cwd": "D:\\Sinister Sanctum"
    },
    "sinister-forge": {
      "auto_revive": false,
      "kind": "process",
      "command": "python",
      "args": ["-m", "forge"],
      "cwd": "D:\\Sinister Sanctum\\projects\\sinister-forge\\source"
    }
  },
  "services": {
    "ollama": {
      "kind": "docker",
      "enabled": false,
      "container": "ollama",
      "image": "ollama/ollama:latest",
      "docker_args": ["-p", "11434:11434"]
    }
  },
  "stale_minutes_override": {
    "rkoj": 120
  }
}
```

Notes:
- `auto_revive: false` is honored — the watchdog will log the stale state but won't respawn. Useful for things the operator wants to launch manually (Forge, RKOJ UI).
- If a stale slug has no registry entry, the watchdog logs a warning and skips. **Adding a new agent type? Drop a row into `registry.json`.**
- Docker entries are skipped if `docker` isn't on PATH.

## Lane discipline (what the watchdog NEVER does)

- Never writes to `~/.claude/.mcp.json` (operator-owned per Sanctum CLAUDE.md hard rule).
- Never pushes git.
- Never spawns interactive console windows (operator's "no popups" doctrine — all children get `CREATE_NO_WINDOW` on Windows, `start_new_session=True` on POSIX).
- Never touches `projects/<project>/source/` (those are per-project agent territory).
- Never edits `_vault/` or any secret file.

## Architecture

```
   ┌─────────────────────────────────────────────────────────────┐
   │   SinisterWatchdog scheduled task (AtLogOn + AtStartup)     │
   │                                                             │
   │   ┌──────────────────────────────────────────────┐          │
   │   │ python -m sinister_watchdog start --fg       │          │
   │   │                                              │          │
   │   │ every 60s:                                   │          │
   │   │   1. scan _shared-memory/heartbeats/*        │          │
   │   │   2. respawn any > 5 min stale (per regs)    │          │
   │   │   3. check docker services (if enabled)      │          │
   │   │   4. every 5 cycles: probe each MCP server   │          │
   │   │                       (read .mcp.json)       │          │
   │   │                                              │          │
   │   │ writes: _shared-memory/watchdog.log          │          │
   │   │         tools/sinister-watchdog/state.json   │          │
   │   │         tools/sinister-watchdog/watchdog.pid │          │
   │   └──────────────────────────────────────────────┘          │
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────────┐
                │ Forge `/watchdog` slash command │
                │ Reads state.json → renders pane │
                └─────────────────────────────────┘
```

## Composes with

- `tools/sanctum-self-heal` — the hourly **reporter** (what's drifted, no respawn). Watchdog is the **responder**.
- `_shared-memory/heartbeats/` — the truth surface every agent already writes to.
- `~/.claude/.mcp.json` — the operator's MCP config (we read it, never write).
- Forge `commands.py` `_cmd_watchdog` — the operator-facing read-only surface.

## Docker prerequisites (only if you enable docker-backed services)

If a registry entry sets `kind: "docker"`:
1. Docker Desktop must be installed and `docker` on PATH.
2. The container's image must be pullable (or pre-pulled).
3. First-time start: the watchdog will run `docker run -d --name <container> <docker_args> <image>` automatically.
4. Subsequent starts: `docker start <container>` (much faster).

If `docker` isn't installed, docker entries are silently skipped — non-docker agents continue working normally.
