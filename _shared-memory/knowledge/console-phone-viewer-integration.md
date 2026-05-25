<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: Console Phone-Viewer full integration (per-pane ADB exec + history + lane awareness)

**Slug:** console-phone-viewer-integration
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** fixed
**Tags:** phone-viewer, adb, console, lane, containerization, async

## Problem

The Sanctum Console's `Devices` panel showed a flat list from `adb devices -l` with
no per-phone state, no lane awareness, no way to run an `adb -s <serial> ...`
command from the UI, and no protection against the operator typing a bare
`adb shell` or `adb kill-server` (both blow up containerization — see
DIRECTIVES.md 165–201). Sequential enrichment also meant `/api/devices`
latency scaled linearly with phone count: N phones × 2 sub-procs × ~250 ms ≈
500 ms per phone.

## Why it matters

1. **Lane discipline (Snap-EMU vs TikTok-EMU vs master vs unowned)** — without
   surfacing the lane in the UI, an operator (or a careless agent) can push
   frida-server to the wrong phone and contaminate a clean lane. The
   `_shared-memory/notes/phones/<SERIAL>.md` file is the source of truth, but
   nobody was reading it.
2. **Containerization enforcement** — DIRECTIVES.md mandates every adb call
   carry `-s <SERIAL>`. The viewer already had `forbid_global_adb`, but the
   UI path bypassed it.
3. **Speed** — at 4 phones the old `/api/devices` round-trip felt sluggish
   (~2 s). The operator's "fast like gitbash" constraint demands sub-600 ms.

## Fix

### (a) Async fan-out speed pattern
A new primitive `serial_run(serial, args, timeout=10)` in `viewer.py` routes
EVERY adb call through `_safe_serial()` + `forbid_global_adb()` and then
`asyncio.create_subprocess_exec` directly (no `adb-shell` PyPI dep — keeps the
PyInstaller bundle lean). `enrich_devices_parallel(devices)` runs `dumpsys
battery` + `getprop ro.product.model` across N phones concurrently via
`asyncio.gather`, so max-latency ≈ one round-trip (~400 ms) regardless of N.

```python
res = await asyncio.gather(*[
    serial_run(d["serial"], ["shell", "dumpsys", "battery"], timeout=4)
    for d in online_devices
])
```

### (b) Lane comes from `parse_phone_md(serial)`
`parse_phone_md` reads `_shared-memory/notes/phones/<SERIAL>.md` (template at
`_TEMPLATE.md`), pulls `**Lane:**`, `**Attestation:**`, `**Installed
modules:**`, `**Current proxy:**` via regex, and normalizes lane to one of
`snap-emu` / `tiktok-emu` / `master` / `unowned`. Anything else becomes
`unowned`. Missing-file returns `{}` (absence of data, not error).

### (c) Rejecting bare `adb shell` at TWO layers
- **HTTP edge** (server.py `_reject_forbidden_adb`) returns HTTP 400 with a
  link to DIRECTIVES.md if the raw command string starts with `adb shell` (no
  -s), contains `kill-server` / `start-server`, or carries an inline `-s
  <OTHER_SERIAL>` mismatch.
- **`exec_adb` inside viewer.py** strips a leading `adb` / `adb.exe`, refuses
  any inline `-s <X>` (the UI scopes the serial for you via the pane), then
  calls `serial_run` which calls `forbid_global_adb`. Belt + suspenders + an
  audit log entry via `append_command_log` regardless of success/failure.

### (d) localStorage `adb_history_<serial>` for per-pane reload-persistence
The frontend keeps the last 20 entries per serial in `localStorage` under
key `adb_history_<serial>`. Each entry: `{ts, cmd, rc, stdout, stderr}`. The
pane re-hydrates on reload so the operator's command history survives a
browser refresh — even though the backend log (in the per-phone `.md`) is the
authoritative audit trail. The two are kept in sync best-effort but the .md is
canonical.

## Discoveries

- `asyncio.gather` over 4 concurrent `dumpsys battery` calls completes in
  ~380 ms wall-clock vs ~1100 ms sequential on the operator's PC + USB-2 hub.
- `shlex.split(posix=False)` is required on Windows so backslashes in paths
  don't get eaten before they hit `adb push`.
- `_safe_serial`'s regex `^[A-Za-z0-9._:\-]+$` correctly accepts both USB
  serials (e.g. `R5CN70EXAMP`) and TCP serials (e.g. `192.168.1.50:5555`).
- Appending to the per-phone `.md` "Recent commands" section is done
  **most-recent at top** — newest entries are inserted directly under the
  section header, never appended at the bottom (matches how Sanctum activity
  logs read in the UI).
- `_default_phone_md(serial)` creates a minimal valid file if none exists so
  `append_command_log` never fails on first-touch — caller code stays
  oblivious of file lifecycle.
- `install_frida` uses `nohup ... &` via `serial_run` (one shell call) rather
  than two round-trips; chmod has to come first or the `&` fork dies.
