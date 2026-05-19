# Sinister Vault - Auto-start (Scheduled Task)

> **Author:** Sinister Sanctum SV-E agent (Claude) :: 2026-05-19

Make the Vault daemon come up automatically when you log in, and
self-restart if it dies.

## What gets installed

A Windows Scheduled Task named **`SinisterVault`** that:

- Triggers at **logon** for the current user (the daemon reads per-user
  account files under `D:\sinister-vault\accounts\` that key off the
  logged-in user; cold-boot before logon would bind to the wrong
  identity; loopback port 5078 also needs the user session).
- Runs **hidden** (no console window flashes up).
- Runs `cmd.exe /c "D:\Sinister Sanctum\tools\sinister-vault\vault-daemon.bat"`.
- `IgnoreNew` if multiple logons fire (no duplicate daemons).
- `ExecutionTimeLimit = 0` (runs forever).
- `RestartCount = 5 / RestartInterval = 1 min` (outer cap on top of the
  bat's inner 5/hour cap).

The bat itself keeps `daemon.py` alive via a 3-second restart loop with
a 5-per-rolling-hour inner cap, and runs a backgrounded 60-second
heartbeat ticker.

## Install (operator only)

```powershell
# from PowerShell
cd 'D:\Sinister Sanctum\tools\sinister-vault'
.\install-vault-task.ps1
```

On success the script prints a "Verify / Run now / Logs / Uninstall" block.

## Verify

```powershell
Get-ScheduledTask -TaskName SinisterVault | Format-List State,LastRunTime,NextRunTime
```

Expected `State`: **`Ready`** between logons; **`Running`** once you're
logged in.

| State        | Meaning                                                                                                          | What to do |
| ------------ | ---------------------------------------------------------------------------------------------------------------- | ---------- |
| `Ready`      | Registered, not currently running.                                                                               | Log out + back in to fire the `AtLogOn` trigger, OR `Start-ScheduledTask -TaskName SinisterVault` to fire manually. |
| `Running`    | Daemon is alive.                                                                                                 | Nothing - confirm the heartbeat to be sure. |
| `Queued`     | Trigger fired but cannot start (resource block / earlier instance still finishing).                              | Wait 30s; if persistent, `Stop-ScheduledTask` + `Start-ScheduledTask`. |
| `Disabled`   | Someone disabled it (Task Scheduler UI or `Disable-ScheduledTask`).                                              | `Enable-ScheduledTask -TaskName SinisterVault`. |
| Not found    | Not installed yet, or uninstalled.                                                                               | Re-run `install-vault-task.ps1`. |

## Run now

```powershell
Start-ScheduledTask -TaskName SinisterVault
```

## Stop

```powershell
Stop-ScheduledTask -TaskName SinisterVault
```

The bat keeps respawning `daemon.py` until the outer task is stopped or
the rolling-hour cap is hit. `Stop-ScheduledTask` cleanly terminates the
chain.

## Logs

Per-launch (one log per `vault-daemon.bat` invocation):

```
D:\Sinister Sanctum\tools\sinister-vault\_daemon-logs\vault-<YYYYMMDDTHHMMSS>.log
```

Persistent audit trail (every log entry from every launch):

```
D:\Sinister Sanctum\tools\sinister-vault\_daemon-logs\daemon.log
```

Vault audit stream (daemon.py writes here every storage event - commits,
pushes, syncs, snapshots, quota warnings):

```
D:\sinister-vault\audit\<YYYY-MM-DD>.jsonl
```

## Heartbeat

The daemon touches this file every 60 seconds:

```
D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-vault.beat
```

Other agents check `(Get-Item ...).LastWriteTime` delta to know whether
the vault is alive. Rule of thumb: **mtime older than 120 seconds =
stuck / dead**.

```powershell
$beat = 'D:\Sinister Sanctum\_shared-memory\heartbeats\sinister-vault.beat'
$age  = (Get-Date) - (Get-Item $beat).LastWriteTime
"$([int]$age.TotalSeconds)s since last beat"
```

Live API check (no auth needed; loopback only):

```powershell
Invoke-RestMethod http://127.0.0.1:5078/api/vault/health
```

## Uninstall

```powershell
cd 'D:\Sinister Sanctum\tools\sinister-vault'
.\uninstall-vault-task.ps1
# or
.\install-vault-task.ps1 -Uninstall
```

Both are idempotent (silent no-op if the task is not registered). Note:
any in-flight `vault-daemon.bat` window keeps running until you close
it manually or kill the child `python.exe` running `daemon.py`.

## Troubleshooting matrix

| Symptom                                            | Likely cause                                                                                | Fix |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------- | --- |
| `State = Disabled`                                 | Manually disabled or Group Policy.                                                          | `Enable-ScheduledTask -TaskName SinisterVault`. Check `gpedit.msc` if it re-disables. |
| `State = Queued` for > 60 s                        | Earlier daemon hasn't released, or `MultipleInstances=IgnoreNew` is doing its job.          | `Get-Process python` to see what's running. `Stop-ScheduledTask` + `Start-ScheduledTask`. |
| Heartbeat stale (> 120 s) but task `Running`       | Backend stuck (uvicorn worker hung, port 5078 collision, quota walk on a huge tree).        | Read latest `_daemon-logs\vault-*.log`; kill `python.exe` manually - the bat restart loop will respawn it. |
| Heartbeat absent entirely                          | Daemon never started, or the bat re-entrant heartbeat dispatch broke.                       | Run `vault-daemon.bat` manually in a terminal; confirm "==== vault-daemon start ====" appears in `daemon.log`. |
| `[FATAL] venv python not found`                    | Operator never created `.venv` for the vault dir.                                           | `cd 'D:\Sinister Sanctum\tools\sinister-vault'; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt`. |
| `[FATAL] daemon.py not found`                      | SV-A's daemon file went missing or path drifted.                                            | Restore from git history (`tools\sanctum-git`) or re-run SV-A's setup. |
| `/api/vault/health` returns connection refused     | Daemon didn't bind, port 5078 in use by another process.                                    | `Get-NetTCPConnection -LocalPort 5078`; kill the owning process; restart the task. |
| Register-ScheduledTask: "Access is denied"         | Some hosts require admin for `-RunLevel Highest`.                                           | Right-click PowerShell -> Run as Administrator, then re-run `install-vault-task.ps1`. |

## See also

- `README.md` (this dir) - SV-A's vault daemon overview + HTTP surface.
- `ACCOUNTS.md` (this dir) - the multi-account system the daemon serves.
- `D:\Sinister Sanctum\automations\window-manager\AUTOSTART.md` - the
  RKOJ scheduled task this file is modeled on.
