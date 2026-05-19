# Sinister Phone Viewer — replacement for broken Panda screen-mirror

**Captured:** 2026-05-19
**Status:** shipped
**Origin:** Operator directive after Panda began failing Snapchat camera —
Snapchat detects Panda's Android `VirtualDisplay` via
`DisplayManager.getDisplays()` and blocks the camera surface as a result.

## Idea

A Sanctum-native phone viewer that wraps `adb` + `scrcpy` with strict
**per-phone containerization** discipline. Built around the existing
`scrcpy --display-id 0` (mirror physical display) primitive, exposed through:

1. A small Python helper (`tools/sinister-phone-viewer/viewer.py`, stdlib only)
2. FastAPI endpoints on the Sanctum Console
   (`/api/devices`, `/api/devices/<serial>/view|stop|state|push`)
3. A real **Devices** tab in the Sanctum Console UI (replaces the phones stub)

## Why

Panda created an Android `VirtualDisplay` (with `FLAG_PRIVATE`). Snapchat
enumerates `DisplayManager.getDisplays()` on each session and refuses to
expose the camera when an unexpected display is present. Result: Panda mirror
worked, camera broke. Same issue would happen with any scrcpy flag that spins
up a virtual surface (`--new-display`, `--virtual-display`,
`--display-overlay`).

The fix is to mirror the **physical** display directly. `scrcpy --display-id 0`
already does this — the physical display is invisible to user-space app calls
to `DisplayManager.getDisplays()` (since it's just the device's main screen,
already enumerated). No new display, no detection vector.

In parallel: the operator has standing rules that **each phone is its own
container** (`_shared-memory/DIRECTIVES.md` 2026-05-19). PC-side flags (frida,
proxies, env vars) must not leak between phones. The viewer enforces this:

- `forbid_global_adb(cmd)` raises `ValueError` if any adb call lacks `-s <serial>`.
- `push_frida_to(serial, ...)` and `adb_push_file(serial, ...)` are the
  only push paths; both require a serial and update the phone's notes file.
- `stop_view(pid)` terminates exactly one scrcpy process — never all of them.

## Sketch

```
Console (browser)
  └─ Devices tab (web/index.html "tpl-phones" template, web/app.js PaneRegistry.phones)
        ├─ yellow containerization banner
        ├─ device-card grid (one per phone serial)
        │     ├─ serial + model + state badge (ONLINE/UNAUTHORIZED/OFFLINE)
        │     ├─ VIEW   → POST /api/devices/<serial>/view
        │     ├─ STOP   → POST /api/devices/<serial>/stop   (only when viewing)
        │     └─ STATE NOTES (collapsible)
        │          └─ GET /api/devices/<serial>/state
        └─ refreshDevices() every 15s while tab active

Server (FastAPI, port 5077)
  └─ /api/devices                       → viewer.list_devices()
  └─ /api/devices/{serial}/view (POST)  → viewer.start_view(serial, …)
        spawn scrcpy --serial S --display-id 0 --max-size 1280 --video-bit-rate 4M
        (NEVER --new-display / --virtual-display / --display-overlay)
        record pid in _DEVICE_VIEWERS[serial]
  └─ /api/devices/{serial}/stop  (POST) → viewer.stop_view(_DEVICE_VIEWERS[serial])
        terminate that pid only
  └─ /api/devices/{serial}/state        → read _shared-memory/notes/phones/<serial>.md
  └─ /api/devices/{serial}/push  (POST) → viewer.adb_push_file(serial, file, dest)

Tool (sinister-phone-viewer)
  └─ viewer.list_devices()        parse `adb devices -l`
  └─ viewer.start_view(serial, …) spawn scrcpy --display-id 0
  └─ viewer.stop_view(pid)        kill exactly that pid
  └─ viewer.get_phone_state(s)    read _shared-memory/notes/phones/<s>.md
  └─ viewer.push_frida_to(s, p)   explicit per-serial frida push + note update
  └─ viewer.forbid_global_adb(c)  raise ValueError if -s missing
```

## Status

- [x] idea captured
- [x] design sketched
- [x] implementation started
- [x] shipped (viewer.py, endpoints, Devices tab)

## Linked-to

- Tool card: `D:\Sinister Sanctum\tools\sinister-phone-viewer\README.md`
- Operator directive: `D:\Sinister Sanctum\_shared-memory\notes\2026-05-19-adb-phone-containerization.md`
- Standing rules: `D:\Sinister Sanctum\_shared-memory\DIRECTIVES.md`
- Sanctum Console: `D:\Sinister Sanctum\automations\window-manager\`
- scrcpy binary: `C:\Users\Zonia\Desktop\Apps\scrcpy-win64-v3.3.4\scrcpy.exe`

## Notes

- The tool deliberately does NOT auto-start scrcpy from any agent's first
  action — the operator pushes the VIEW button (or hits the endpoint) per
  phone. No automation of camera-adjacent operations on the master lane.
- The tool deliberately does NOT auto-push frida-server. That helper exists
  (`push_frida_to`) but only operator-or-authorized-lane invokes it.
- Future work: add `screenshot` (`adb -s <serial> exec-out screencap -p`),
  `logcat-tail` (websocket of `adb -s <serial> logcat`), and a control
  toggle (mouse/keyboard route into the scrcpy window). Each must remain
  per-serial.
