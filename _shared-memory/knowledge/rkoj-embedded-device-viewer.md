<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: RKOJ in-EXE embedded ADB device viewer (no scrcpy popup, no flags)

**Slug:** rkoj-embedded-device-viewer
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** fixed
**Tags:** embedded, screen, adb, exec-out, mjpeg, no-flags, agent-visibility

## Problem

Before this fix, the only way to see what was on an attached phone from RKOJ
was the `VIEW` button, which spawned a **scrcpy.exe popup window** outside the
EXE. Three downsides for an agent-driven workflow:

1. **Agents can't see the popup** — scrcpy renders to a native OS window, not
   into the RKOJ DOM. An LLM agent inspecting `/api/...` has zero visibility
   into the actual phone screen.
2. **Window-management noise** — every viewed phone meant another floating
   window on the operator's screen. At 4+ phones the desktop became unusable.
3. **Anti-detect dance** — `scrcpy-virtual-display-detected.md` documents why
   we have to pin `--display-id 0`, refuse `--new-display`, etc. That gate is
   defensible, but it makes scrcpy feel like a minefield every time we touch it.

## Why it matters

Agents need to be able to **see** the phone to make decisions — "is the Snap
camera open?", "did the OTP arrive?", "is the install dialog up?". Without
in-EXE visibility, every visual decision required an operator-in-the-loop.

Also, the operator confirmed: **"since it's all spoofed"** — i.e. the
anti-detect layer is handled upstream by the rebrand + sister-app + frida
modules. We don't need scrcpy's `--display-id 0` workaround for a *read-only*
screen capture: `adb exec-out screencap -p` does not create a VirtualDisplay
at all (it asks SurfaceFlinger for a raw framebuffer and pipes it back over
the existing ADB transport). So this codepath has **zero detection surface**
beyond ADB itself.

## Fix

### (a) `viewer.py` — `capture_screen(serial, timeout=5.0)`

Single async function. Runs:

```
adb -s <serial> exec-out screencap -p
```

…via `asyncio.create_subprocess_exec`, reads stdout, validates the PNG
magic `\x89PNG`, and returns the raw bytes. On Windows, also performs a
defensive `\r\r\n` → `\r\n` → `\n` collapse for old ADB versions that
mis-translate the pipe. Returns `None` on any failure (timeout, non-zero rc,
unrecognized magic). No `print`, no exception bubble — quiet primitive.

### (b) `server.py` — two new endpoints

```
GET /api/devices/{serial}/screen           → image/png  (single shot)
GET /api/devices/{serial}/screen.mjpeg     → multipart/x-mixed-replace
                                              boundary=rkoj-screen
                                              ?fps=<0.2..10>  (default 2)
```

The MJPEG generator loops `capture_screen` → yields a boundary header
+ PNG bytes → `asyncio.sleep(1/fps)`. `asyncio.CancelledError` is swallowed
cleanly when the client disconnects, so a closed browser tab does NOT leak
ADB subprocesses.

### (c) `app.js` — `_renderEmbeddedScreen(serial, container)`

Creates an `<img>` whose `src` points at the MJPEG endpoint. Browsers
natively decode `multipart/x-mixed-replace`, swapping the frame in place —
no JS frame-pump needed. The helper appends an `.embedded-screen-wrap`
into the device card with a header (`serial` + `✕ close` + `⟳ reconnect`).
Second click on `EMBED SCREEN` toggles the wrap off. Exposed on
`window.RkojHelpers.renderEmbeddedScreen` for popouts to consume too.

The device card now has both buttons:

- `VIEW` → still spawns scrcpy in a popup (control + audio path).
- `EMBED SCREEN` → renders inline, read-only, agent-visible.

### (d) `theme.css` — `.embedded-screen-wrap` + `.embedded-screen`

Glass-card matching the rest of RKOJ. `max-height: 600px` clamps tall
phones so the card stays inside the viewport. Black background on the
`<img>` itself so the first frame doesn't flash white before MJPEG arrives.

## Limitations (intentional, not bugs)

- **~2 fps default.** The cap is 10 fps. ADB `screencap` is ~200–500 ms per
  frame on a USB-2 connection, and each PNG is 50–200 KB. At 4 phones × 10
  fps × 100 KB = ~4 MB/s sustained — fine on LAN, painful on Wi-Fi-tethered
  ADB. Operator can override per-card via `?fps=` if needed.
- **No touch / no control.** This is a read-only view. Use scrcpy
  (`VIEW` button) when you need to tap/swipe/type. See "Future" below.
- **No anti-detect flags.** Operator-confirmed: spoofing is upstream. We do
  NOT pass `--display-id 0` because `screencap` does not create a display.
  We also do not pass `--new-display` / `--virtual-display`
  (`scrcpy-virtual-display-detected.md` only applies to scrcpy.exe, not to
  `adb screencap`).
- **Bandwidth.** PNG is uncompressed-ish. A WebP / JPEG transcoding pass
  would cut traffic by ~5×, but adds a CPU cost and a Pillow dep — not
  worth it until we have >6 phones streaming simultaneously.

## Future

1. **Touch control.** Add a WebSocket endpoint `/api/devices/{serial}/touch`
   that takes `{x, y}` (in device pixels) and runs
   `adb -s <serial> shell input tap X Y`. Wire a click handler on the
   `<img>` that maps offsetX/offsetY → device coordinates via
   `wm size` (cached). That makes the embedded view fully interactive
   without bringing scrcpy back.
2. **WebP transcoding.** If we ever hit bandwidth pain, slot a Pillow
   `screencap → PIL → WebP @ 75q` step in `capture_screen` behind a
   `?fmt=webp` query.
3. **Per-agent visibility hooks.** When an agent calls
   `/api/devices/<serial>/screen` the response could include a tiny
   `X-Frame-Hash` header so the agent knows whether the screen changed
   since its last poll — cheap diffing.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 by Sinister Sanctum
Implemented end-to-end: `capture_screen` in viewer.py (async, PNG-magic
guarded), `/screen` + `/screen.mjpeg` in server.py, `_renderEmbeddedScreen`
helper in app.js, `EMBED SCREEN` button wired into the device card next to
`VIEW` / `STOP` / `PUSH` / `STATE NOTES`, `.embedded-screen-wrap` glass
styling in theme.css. Operator confirmed "since it's all spoofed" so we
omit `--display-id 0` and friends — `screencap` doesn't create a display.

## Related topics

- [console-phone-viewer-integration](./console-phone-viewer-integration.md)
- [scrcpy-virtual-display-detected](./scrcpy-virtual-display-detected.md)
- [adb-containerization](./adb-containerization.md)
- [rkoj-workbench-architecture](./rkoj-workbench-architecture.md)
