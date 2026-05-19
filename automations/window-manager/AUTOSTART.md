> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# RKOJ.exe - Auto-start (Scheduled Task)

Make RKOJ come up automatically when you log in, and self-restart if it dies.

## What gets installed

A Windows Scheduled Task named **`RKOJ`** that:

- Triggers at **logon** for the current user (HWID-bound auth needs a user session; loopback network ordering is finicky at cold-boot, so we deliberately do not use `AtStartup`).
- Runs **hidden** (no console window flashes up).
- Runs `cmd.exe /c "D:\Sinister Sanctum\automations\window-manager\console-daemon.bat"`.
- `IgnoreNew` if multiple logons fire (no duplicate daemons).
- `ExecutionTimeLimit = 0` (runs forever).
- `RestartCount = 5 / RestartInterval = 1 min` (outer cap on top of the bat's inner 5/hour cap).

The bat itself keeps the console alive via a 3-second restart loop with a 5-per-rolling-hour inner cap, and runs a backgrounded 60-second heartbeat ticker.

## Install (operator only)

```powershell
# from PowerShell
cd 'D:\Sinister Sanctum\automations\window-manager'
.\install-console-task.ps1
```

On success the script prints a "Verify / Run now / Logs / Uninstall" block.

## Verify

```powershell
Get-ScheduledTask -TaskName RKOJ | Format-List State,LastRunTime,NextRunTime
```

Expected `State`: **`Ready`** between logons; **`Running`** once you're logged in.

| State | Meaning | What to do |
|---|---|---|
| `Ready` | Registered, not currently running. | Log out + back in to fire the `AtLogOn` trigger, OR `Start-ScheduledTask -TaskName RKOJ` to fire manually. |
| `Running` | Daemon is alive. | Nothing - check the heartbeat to confirm. |
| `Queued` | Trigger fired but cannot start (resource block / earlier instance still finishing). | Wait 30s; if persistent, `Stop-ScheduledTask` + `Start-ScheduledTask`. |
| `Disabled` | Someone disabled it (Task Scheduler UI or `Disable-ScheduledTask`). | `Enable-ScheduledTask -TaskName RKOJ`. |
| Not found | Not installed yet, or uninstalled. | Re-run `install-console-task.ps1`. |

## Run now

```powershell
Start-ScheduledTask -TaskName RKOJ
```

## Stop

```powershell
Stop-ScheduledTask -TaskName RKOJ
```

The bat keeps respawning the backend until the outer task is stopped or the rolling-hour cap is hit. `Stop-ScheduledTask` cleanly terminates the chain.

## Logs

Per-launch (one log per `console-daemon.bat` invocation):

```
D:\Sinister Sanctum\automations\window-manager\_daemon-logs\console-<YYYYMMDDTHHMMSS>.log
```

Persistent audit trail (every log entry from every launch):

```
D:\Sinister Sanctum\automations\window-manager\_daemon-logs\daemon.log
```

PyInstaller build logs (separate concern):

```
D:\Sinister Sanctum\automations\window-manager\_build-logs\build-<UTC-stamp>.log
```

## Heartbeat

The daemon touches this file every 60 seconds:

```
D:\Sinister Sanctum\_shared-memory\heartbeats\rkoj.beat
```

Other agents check `(Get-Item ...).LastWriteTime` delta to know whether the console is alive. Rule of thumb: **mtime older than 120 seconds = stuck / dead**.

```powershell
$beat = 'D:\Sinister Sanctum\_shared-memory\heartbeats\rkoj.beat'
$age  = (Get-Date) - (Get-Item $beat).LastWriteTime
"$([int]$age.TotalSeconds)s since last beat"
```

## Uninstall

```powershell
cd 'D:\Sinister Sanctum\automations\window-manager'
.\uninstall-console-task.ps1
# or
.\install-console-task.ps1 -Uninstall
```

Both are idempotent (silent no-op if the task is not registered). Note: any in-flight `console-daemon.bat` window keeps running until you close it manually or kill the child `python.exe` / `RKOJ.exe`.

## Troubleshooting matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `State = Disabled` | Manually disabled or Group Policy. | `Enable-ScheduledTask -TaskName RKOJ`. Check `gpedit.msc` if it re-disables. |
| `State = Queued` for > 60 s | Earlier daemon hasn't released, or `MultipleInstances=IgnoreNew` is doing its job. | `Get-Process RKOJ, Sanctum-Console, python` to see if anything is running. `Stop-ScheduledTask` + `Start-ScheduledTask`. |
| Heartbeat stale (> 120 s) but task `Running` | Backend stuck (uvicorn worker hung, port collision, infinite loop). | Read latest `_daemon-logs\console-*.log`; kill `RKOJ.exe` / `python.exe` manually - the bat restart loop will respawn it. |
| Heartbeat absent entirely | Daemon never started, or the bat re-entrant heartbeat dispatch broke. | Run `console-daemon.bat` manually in a terminal; confirm "==== console-daemon start ====" appears in `daemon.log`. |
| `Failed to load Python DLL` popup | Onedir EXE missing `_internal\python312.dll` (incomplete deploy copy). | Re-run `Build-Sanctum-Console.bat` (step 9 robocopy `/MIR` mirrors `dist\RKOJ\` → `Desktop\RKOJ\`). Knowledge: `exe-dll-crash-incomplete-copy.md`. |
| Register-ScheduledTask: "Access is denied" | Some hosts require admin for `-RunLevel Highest`. | Right-click PowerShell -> Run as Administrator, then re-run `install-console-task.ps1`. |
| Console up but `/api/health` 401 | HWID token not seeded for this session - normal until first browser visit. | Visit `http://127.0.0.1:5077/` once; the page seeds the token via localStorage. |

## See also

- `BUILD.md` - how the EXE itself is built (the daemon prefers it over source python).
- `D:\Sinister\Sinister Skills\12_LLM_ORCHESTRATION\agents\custodian\install-task.ps1` - the canonical scheduled-task pattern this file is modeled on.
