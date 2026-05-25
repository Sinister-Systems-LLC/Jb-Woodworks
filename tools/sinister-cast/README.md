# SinisterCast — homegrown Android view system

> Author: RKOJ-ELENO :: 2026-05-24
> Lane: kernel-apk · Status: **PRE-FLIGHT (PC-side only)** · Plan: `_shared-memory/plans/kernel-apk-adb-view-system-2026-05-24/plan.md`

This is the PC-side scaffold for SinisterCast — the in-APK MediaProjection + ADB-reverse view system that replaces Panda. The APK-side companion (`SinisterCastService.kt`, Phase A.1 of the parent plan) is **NOT yet shipped**: the kernel-apk source tree is currently operator-gated (case-collision corruption + `pack has 19 unresolved deltas`). This PC-side scaffold is operator-reviewable on its own — bridge and viewer run, the CLI is parse-clean, and the WebSocket protocol is fixed so the APK companion can be slotted in once the source tree is restored.

## Architecture

```
[ Phone APK ]                                       [ PC ]
MediaProjection → MediaCodec(H.264) → TCP :9001  →  adb reverse  →  bridge.py  →  ws://localhost:9002/stream  →  viewer.html <video> (MediaSource)
AccessibilityService(dispatchGesture) ← TCP :9101 ← adb forward ←  bridge.py  ←  ws://localhost:9002/touch   ←  viewer.html pointer events
```

The only PC-side process Snap can fingerprint is `adbd` (operator's existing ADB daemon) + this `bridge.py`. No scrcpy-server, no Panda, no custom Windows USB driver. Touch source on the phone reads `SOURCE_TOUCHSCREEN` because the APK injects via `dispatchGesture()` (Accessibility), not `sendevent`.

## Install

```bash
pip install websockets
```

That's the only runtime dep. Python 3.10+ recommended.

## Run

```bash
python bridge.py --phone-serial <serial>           # default ws port 9002
# then open viewer.html in a browser:
#   file:///D:/Sinister Sanctum/tools/sinister-cast/viewer.html
#   (override resolution via hash, e.g. viewer.html#1080x2400)
```

`bridge.py` runs `adb -s <serial> reverse tcp:9001 tcp:9001` and `adb -s <serial> forward tcp:9101 tcp:9001` on startup. Phone TCP drops trigger exponential-backoff reconnect (0.5s → 8s cap); viewer drops trigger 500ms reconnect with a "Reconnecting…" overlay — no F5 ever required.

## Acceptance criteria (from plan.md Phase A.5)

The full SinisterCast system (APK + bridge + viewer) passes when:

1. **Process scan** — `pgrep -f scrcpy` and `pgrep -f panda` on the phone both return empty during an active SinisterCast session.
2. **Input-source fingerprint** — `InputDevice.getSources()` queried during a Snap touch event reads `SOURCE_TOUCHSCREEN` (not `SOURCE_MOUSE` / `SOURCE_STYLUS`).
3. **ADB-bridge fingerprint** — wireless-ADB only (`adb tcpip 5555` + `adb connect <ip>:5555`); no USB cable signature visible via `/proc/bus/usb/devices` or `getprop sys.usb.config`.
4. **Rotation timing** — display-rotation propagation matches real-hand profile (≥200ms), not the ~50ms scrcpy fingerprint.

Phase A.5 ties acceptance to a Snap account-create iteration: SS06/SS07/SS11 must NOT fire mid-flow with SinisterCast active.

## What this scaffold does NOT yet include

- **`SinisterCastService.kt`** (APK foreground service) — Phase A.1, source-gated.
- **MP4 fragment header injection** — current bridge forwards Annex-B framed NAL units (`00 00 00 01 + payload`). Some browsers' MediaSource will play this directly via `avc1.640028`; if the operator's test browser refuses, the APK side will be updated to emit fragmented-MP4 directly (cleaner contract), or the bridge will gain an fMP4 muxer (`av` or `pyav`). Decision deferred to the first end-to-end smoke test once the APK side ships.
- **`adb tcpip 5555` / `adb connect` automation** — Phase A.4 wireless-ADB primary-path setup remains a manual operator step (UAC + IP discovery); the bridge assumes the device is already reachable via `adb devices`.

## Files

- `bridge.py` — Python 3 asyncio WebSocket bridge (TCP ↔ WS, exponential-backoff reconnect, ADB tunnel setup).
- `viewer.html` — single-file dark-theme browser viewer (Sinister purple `#c084fc` accent, MediaSource consumer, 60Hz pointer batching).
- `README.md` — this file.
