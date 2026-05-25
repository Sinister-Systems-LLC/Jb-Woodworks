<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 1
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: Daemon-liveness heartbeats — `_shared-memory/heartbeats/*.beat` (RKOJ + Vault)

**Slug:** daemon-liveness-heartbeats
**First discovered:** 2026-05-19 13:30 by Sinister Sanctum master (agent B wave 1)
**Last updated:** 2026-05-19 13:30 by Sinister Sanctum master (agent B + D wave 1/2)
**Status:** fixed
**Tags:** heartbeat, liveness, monitoring, rkoj, vault, scheduled-task, fleet-monitor, asyncio, console-daemon, sanctum-console, sinister-vault

## Problem

The HR-B audit at PROGRESS log 2026-05-19 11:17 (Section 8 — `_shared-memory`) flagged: `_shared-memory/heartbeats/` contains only build-stamps (`rkoj-build.beat`, `sanctum-console-build.beat`) — no LIVENESS heartbeats. The operator guide already referenced `sanctum-console.beat` and `sinister-vault.beat` as expected files, but those files didn't exist. Without them:

- Fleet-monitor scheduled task can't distinguish "process up" from "process responding"
- The "Daemon liveness" panel in the workbench UI has no data source
- After a crash + bat-respawn, no audit trail of when the daemon actually started serving

## Why it happens

Both daemons (RKOJ console + Sinister Vault) already had build-time stamps (written once at startup) but no recurring tick. PyInstaller-frozen builds inside Edge-WebView2 don't surface to PowerShell `Get-Process -Name RKOJ` reliably (the process name varies), so an external observer couldn't even count on `Get-Process` to detect liveness. A filesystem-side beat file is the canonical Sanctum convention (see WORKSTATION.md / OPERATOR-GUIDE.md / cold-start checklist).

## Fix or workaround

Two-tier fix shipped 2026-05-19 13:30:

### Tier 1 — RKOJ side (console-daemon.bat)

`automations/window-manager/console-daemon.bat` already had a background heartbeat-ticker (re-entrant via `__HEARTBEAT__` arg). Updated to write BOTH canonical files every tick:
- `_shared-memory/heartbeats/sanctum-console.beat` (canonical, matches OPERATOR-GUIDE)
- `_shared-memory/heartbeats/rkoj.beat` (back-compat alias; safe to drop once consumers migrate)

Each file is one line: `<UTC iso> pid=<pid> port=<port> uptime=<seconds>`. Tick cadence: 60 seconds (the existing bat tick).

### Tier 2 — Vault daemon (Python asyncio task)

`tools/sinister-vault/daemon.py` added:
- `HEARTBEATS_DIR` + `HEARTBEAT_FILE` constants
- `_write_heartbeat_line()` — one-line writer (UTF-8, no BOM)
- `_heartbeat_loop()` — asyncio task that primes immediately + ticks every 30 seconds
- Wired into `lifespan()` startup; stored on `RUNTIME`; cancelled in `_shutdown` for clean exit
- New endpoint `GET /api/vault/heartbeat` returning `{file, mtime_iso, last_line, alive: bool}`

### Tier 3 — Aggregator endpoints + UI (agent D wave 2)

- `GET /api/fleet/heartbeats` in RKOJ server.py — scans `_shared-memory/heartbeats/*.beat`, returns per-daemon `mtime_iso / age_s / alive (<120s) / last_line`
- `GET /api/fleet-stream` — same data pushed via SSE every 5 seconds (see `fleet-state-single-source.md`)
- UI: three colored dots in the workbench windows bar — green = alive, red = stale. Click → toast last_line.

```bash
# Smoke verify (RKOJ side):
ls -la "D:/Sinister Sanctum/_shared-memory/heartbeats/"
# Expected after both daemons up:
#   sanctum-console.beat  (mtime in last 60s)
#   sinister-vault.beat   (mtime in last 30s)
#   rkoj.beat             (back-compat alias; same content as sanctum-console.beat)

curl -s "http://127.0.0.1:5077/api/fleet/heartbeats" | python -m json.tool
curl -s "http://127.0.0.1:5078/api/vault/heartbeat" | python -m json.tool
```

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum master (agents B + D wave 1/2)
Shipped both tiers. Smoke test of the vault heartbeat: launched daemon at uptime=0, file written immediately (prime), then at uptime=31, 61, 97. Stop-then-start cycle verified — file mtime updates within 30s. Console-daemon.bat now writes both `sanctum-console.beat` + `rkoj.beat` (verified via re-entrant heartbeat tick). Aggregator endpoint + SSE stream verified syntactically; live curl deferred until scheduled tasks are operator-registered (current run was a one-off smoke that left the .beat stale on disk).

**Stale-but-shipped:** the `sinister-vault.beat` on disk shows `pid=58024 port=5079 uptime=97` from the smoke test. Once the operator runs `tools/sinister-vault/wire-everything.ps1` (or the install task is registered via elevated PowerShell), the daemon starts on canonical port 5078 and the heartbeat will refresh.

### Open: production-grade fleet-monitor task
The existing `Sinister-fleet-monitor` scheduled task (Section 10 of HR-B audit) should consume these .beat files. Today the consumer is the workbench UI + `/api/fleet/heartbeats`. A future iteration could have fleet-monitor alert (Telegram bot / inbox broadcast) when any beat goes stale > 5 minutes.

## Related topics

- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md)
- [sinister-vault-architecture](./sinister-vault-architecture.md)
- [fleet-state-single-source](./fleet-state-single-source.md)
- [sanctum-auto-push](./sanctum-auto-push.md)
