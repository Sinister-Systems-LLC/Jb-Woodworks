<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: runtime liveness heartbeats for Sanctum daemons

**Slug:** runtime-liveness-heartbeats
**First discovered:** 2026-05-19 13:30 by Sinister Sanctum master agent
**Last updated:** 2026-05-19 13:30 by Sinister Sanctum master agent
**Status:** fixed
**Tags:** heartbeat, daemon, asyncio, sanctum, rkoj, vault, monitor, standing-rule

## Problem

`_shared-memory/heartbeats/` historically contained only **build stamps**
(`rkoj-build.beat`, `sanctum-console-build.beat`). No daemon wrote a runtime
heartbeat, even though `install-rkoj-task.ps1` documented one as the liveness
signal (stale-if-mtime > 120s).

Fleet-monitor (and the RKOJ workbench's daemon-liveness dot indicator at
`web/app.js:_mountDaemonLivenessIndicator`) had no way to distinguish "process
alive" from "process responding." HR-B audit (PROGRESS 2026-05-19 11:17) tagged
this as Critical Failure #5.

## Why it happens

The build pipeline (`build-sanctum-console.sh`) writes a `*-build.beat` artifact
on each successful PyInstaller run as a build-success marker. Operators looking
in the heartbeat directory saw files dated minutes ago and assumed the daemons
were ticking — but those mtimes were build-time, not runtime.

The vault daemon (`tools/sinister-vault/daemon.py`) shipped a proper runtime
heartbeat loop on 2026-05-19 06:50, but the RKOJ workbench server.py never had
one. The install-rkoj-task.ps1 referenced the file but no code wrote it.

## Fix or workaround

**Tested 2026-05-19.** Add a 30s asyncio heartbeat loop to every long-running
daemon. Distinct file-name suffix (`-runtime.beat`) keeps build vs runtime
artifacts grep-able.

Pattern in `server.py` (RKOJ workbench):

```python
RUNTIME_HEARTBEAT_DIR = SANCTUM_ROOT / "_shared-memory" / "heartbeats"
RUNTIME_HEARTBEAT_FILE = RUNTIME_HEARTBEAT_DIR / "rkoj-runtime.beat"
RUNTIME_HEARTBEAT_INTERVAL_S = 30
_runtime_started_at = time.time()

def _write_runtime_heartbeat() -> None:
    RUNTIME_HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    uptime = int(time.time() - _runtime_started_at)
    line = (f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} "
            f"pid={os.getpid()} port={PORT} uptime={uptime}")
    RUNTIME_HEARTBEAT_FILE.write_text(line + "\n", encoding="utf-8")

async def _runtime_heartbeat_loop() -> None:
    while True:
        try:
            _write_runtime_heartbeat()
        except Exception:
            pass
        await asyncio.sleep(RUNTIME_HEARTBEAT_INTERVAL_S)

@app.on_event("startup")
async def _runtime_heartbeat_startup() -> None:
    try:
        _write_runtime_heartbeat()  # tick once immediately
    except Exception:
        pass
    asyncio.create_task(_runtime_heartbeat_loop())
```

Same shape in `tools/sinister-vault/daemon.py` (already shipped 2026-05-19 06:50).

## File-name convention (standing rule)

| Suffix | Purpose | Writer |
|---|---|---|
| `<slug>-build.beat` | Build success stamp | `build-sanctum-console.sh` (1-shot) |
| `<slug>-runtime.beat` | Runtime liveness (mtime cadence ~30s) | Daemon's `_runtime_heartbeat_loop` |
| `<slug>.beat` | Legacy single-purpose (treat as runtime if no `-runtime.beat`) | Vault daemon (kept for back-compat) |

When adding a new daemon, follow `-runtime.beat`. Vault's `.beat` (no suffix)
predates the convention; new code uses `<slug>-runtime.beat`.

## Stale detection

Consumers compute `age_s = now - file.mtime`. Thresholds:

| Age | Meaning |
|---|---|
| < 60s | Healthy |
| 60–120s | Slow but okay (single missed tick) |
| > 120s | Stale — alert / red dot |
| missing | Daemon never started OR cold-boot < 30s old |

RKOJ workbench reads via `/api/fleet-snapshot` → `heartbeats` (see
`server.py:_compute_heartbeat_states`).

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 13:30 by Sinister Sanctum master agent
Initial pattern shipped — `server.py` + `install-rkoj-task.ps1:116` aligned on
`rkoj-runtime.beat`. Vault's `sinister-vault.beat` pattern at
`tools/sinister-vault/daemon.py:_heartbeat_loop` was the model. Both feed
`_compute_heartbeat_states()` which powers `web/app.js`'s 3-dot indicator.

## Related topics

- [rkoj-fleet-state-sse](./rkoj-fleet-state-sse.md) — consumes the heartbeat state via SSE
- [sanctum-auto-push](./sanctum-auto-push.md) — same scheduled-task pattern minus the live heartbeat
