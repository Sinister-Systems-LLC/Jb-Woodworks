> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# sinister-phone-viewer

Replacement for the broken Panda screen-mirror. Lists ADB-attached phones and
mirrors a single device's main physical display via `scrcpy --display-id 0`.
Wired into the Sanctum Console as the **Devices** tab.

## What it does

- Lists every ADB-attached phone (`adb devices -l`) with serial / model / state.
- Spawns one `scrcpy` process per phone, targeted by serial, mirroring the
  **physical display only** (`--display-id 0`). One viewer process per phone,
  tracked by pid.
- Reads per-phone state notes from `_shared-memory/notes/phones/<serial>.md`
  (capabilities, installed modules, current proxy, last attestation).
- Exposes an explicit per-serial `push_frida_to(serial, local_path)` helper
  that updates the phone's state file after the push.
- Refuses any `adb` command that doesn't carry `-s <serial>`
  (see `forbid_global_adb` guard).

## What it does NOT do

Per operator's containerization directive
(`_shared-memory/notes/2026-05-19-adb-phone-containerization.md`):

- **No virtual display.** Never `--new-display`, never `--virtual-display`,
  never `--display-overlay`. Snapchat (and others) detect VirtualDisplays via
  `DisplayManager.getDisplays()` and block camera access — that's why Panda
  broke. We mirror the real physical display, which is invisible to user apps.
- **No automatic frida-server push.** Frida is per-phone and operator-driven.
  `push_frida_to(serial, ...)` exists, but the operator (or an authorized agent
  lane) calls it explicitly per serial.
- **No proxy injection.** Proxy is per-phone (`adb -s <serial> shell settings
  put global http_proxy ...`) and never set system-wide.
- **No bare `adb` calls.** Every shell invocation routes through
  `forbid_global_adb` which raises `ValueError` if `-s <serial>` is missing.
- **No `adb kill-server` / `adb start-server`.** Both affect all attached
  phones at once and are forbidden. Use `adb -s <serial> reconnect`.

## Per-phone containerization

Each phone is its own container. PC-side state (frida-server, mitmproxy, env
vars, anti-tamper bypasses) never leaks to phones unless explicitly pushed to
that serial. State for each phone lives at:

```
D:\Sinister Sanctum\_shared-memory\notes\phones\<SERIAL>.md
```

Read this **before** any push; update it **after**. The Devices tab in the
Sanctum Console surfaces this file inline as the "STATE NOTES" preview on
each device card.

## scrcpy invocation cheat sheet

```
scrcpy --serial <SERIAL> --display-id 0 --max-size 1280 --bit-rate 4M
```

| Flag | Why |
| --- | --- |
| `--serial <SER>` | Target exactly one phone. Mandatory if >1 phone attached. |
| `--display-id 0` | Mirror the **physical** main display — invisible to user apps. |
| `--max-size 1280` | Cap longer-edge resolution; smaller streams play smoother. |
| `--bit-rate 4M` | Video bit-rate. Tune up for fidelity, down for bandwidth. |
| `--no-audio` (optional) | Faster start, no extra USB load. |
| `--record <path>` (optional) | Record the session to file. |

**Forbidden flags** (would create a VirtualDisplay → detectable):

- `--new-display`
- `--virtual-display ...`
- `--display-overlay`
- `--display=<id>` to any id other than `0`

## How to invoke (operator-facing)

The Sanctum Console's **Devices** tab is the primary UI. CLI use:

```python
from viewer import list_devices, start_view, stop_view, get_phone_state

devices = list_devices()                 # → [{serial, model, transport_id, state}, ...]
pid = start_view(devices[0]["serial"])   # spawn scrcpy mirroring phone-0
# ... operator works ...
stop_view(pid)                           # terminate only that pid
```

Or via the FastAPI endpoints exposed by `automations/window-manager/server.py`:

```
GET  /api/devices
POST /api/devices/<serial>/view
POST /api/devices/<serial>/stop
GET  /api/devices/<serial>/state
POST /api/devices/<serial>/push       body {file_path, dest_path}
```

All endpoints require the HWID-auth bearer token (same middleware as the
rest of the Sanctum Console).

## Implementation files

- `D:\Sinister Sanctum\tools\sinister-phone-viewer\viewer.py` (Python helper)
- `D:\Sinister Sanctum\tools\sinister-phone-viewer\requirements.txt` (empty — stdlib only)
- `D:\Sinister Sanctum\automations\window-manager\server.py` (HTTP endpoints)
- `D:\Sinister Sanctum\automations\window-manager\web\index.html` (Devices view template)
- `D:\Sinister Sanctum\automations\window-manager\web\app.js` (Devices tab logic)
- `D:\Sinister Sanctum\automations\window-manager\web\theme.css` (`.device-card` styles)

## Dependencies

- Python 3.10+ (stdlib only — no pip packages).
- `adb` on PATH (Android platform-tools).
- `scrcpy` on PATH **or** at the operator's known location
  (`C:\Users\Zonia\Desktop\Apps\scrcpy-win64-v3.3.4\scrcpy.exe`).

## Lane

Master agent (Sanctum orchestration). Per-phone push operations are
operator-only; agents do not push to phones without explicit operator OK.

## Captured

2026-05-19 — Initial registration. Replaces broken Panda mirror.

## Status

`shipped` (viewer + endpoints + UI tab) — but operator runs scrcpy themselves;
this agent does not invoke it.

## Linked-inventions

- `D:\Sinister Sanctum\inventions\2026-05-19-sinister-phone-viewer.md`

## Changelog

- **2026-05-19** — Initial registration. Replaces Panda; per-phone
  containerization enforced; `--display-id 0` mandatory.
