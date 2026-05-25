<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Sanctum master agent (Claude) :: 2026-05-19

# Topic: scrcpy's default mirror creates a VirtualDisplay Snapchat detects

**Slug:** scrcpy-virtual-display-detected
**First discovered:** 2026-05-19 by Sinister Sanctum
**Last updated:** 2026-05-19 by Sinister Sanctum
**Status:** known-issue
**Tags:** scrcpy, adb, snap, virtualdisplay, anti-detect, panda

## Problem

When using scrcpy (or scrcpy-wrappers like Panda / touping.exe) to mirror a physical phone to PC, Snapchat detects the operation and blocks camera access:

```
"Snapchat was unable to open the camera..."
```

The detection mechanism: `DisplayManager.getDisplays()` returns more than 1 display, with the second carrying `FLAG_PRIVATE`. Snap's anti-detect treats any non-physical secondary display as evidence of automation / screen recording / hidden mirror, and refuses to grant camera.

## Why it happens

scrcpy's default mode `--new-display` (or older `--display-overlay`) creates a **VirtualDisplay** on the phone side via `DisplayManager.createVirtualDisplay(...)`. That virtual display has `FLAG_PRIVATE` set by Android. Any user-space app querying displays sees TWO entries — the physical screen and the virtual mirror.

Source: scrcpy server pushes `XWCaptureScreen.jar` (Panda) or scrcpy's own `scrcpy-server.jar` to `/data/local/tmp/`, then the JAR calls into Android's framework to create the virtual display.

Panda specifically creates `VirtualDisplay` owned by `com.android.shell` with `FLAG_PRIVATE` — Snap's detection treats that as a hard block.

## Fix or workaround

Use scrcpy in **physical-display mirror** mode (NOT virtual-display mode):

```bash
# GOOD: mirrors display id 0 (the physical screen) — no virtual display created
scrcpy --serial <SERIAL> --display-id 0 --max-size 1280 --bit-rate 4M
```

DO NOT pass any of these flags:
- `--new-display` (creates a new virtual display)
- `--display-overlay` (legacy alias of new-display)
- `--virtual-display` (older naming)
- `--display=...` with a non-zero ID

Verify zero virtual displays:
```bash
adb -s <SERIAL> shell "dumpsys display | grep -c 'Display Id:'"
# Should return 1 (just the physical). Anything > 1 means a virtual display exists.
```

If you ALREADY have Panda installed and need to fully kill it:

```powershell
Stop-Process -Name 'touping' -Force
# Delete the Panda Desktop shortcut so it doesn't auto-restart
Remove-Item "$env:USERPROFILE\Desktop\Panda.lnk" -ErrorAction SilentlyContinue
# Optionally nuke the install dir
Remove-Item -Recurse "$env:LOCALAPPDATA\touping_*" -ErrorAction SilentlyContinue
```

Verify Panda is fully gone before launching the replacement Sinister Phone Viewer.

## Sanctum-specific note

The replacement tool is at `D:\Sinister Sanctum\tools\sinister-phone-viewer\`. It wraps scrcpy 3.3.4 in physical-display mode + adds per-phone containerization (each serial is its own command stream). The Sanctum Console exposes it via the **Devices** tab. Never invoke scrcpy from agent code without `--display-id 0`.

## Discoveries (append-only log, most-recent at top)

### 2026-05-19 03:30 by Sinister Sanctum
First documented after Panda blocked operator's Snap workflow. `--display-id 0` confirmed working: dumpsys reports `Display Id: 1` only. Snap camera access restored on test phone.

## Related topics

- [adb-containerization](./adb-containerization.md)
- [panda-uninstall](./panda-uninstall.md) (not yet written)
