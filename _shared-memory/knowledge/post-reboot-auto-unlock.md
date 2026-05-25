<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
> **Author:** Sinister Kernel APK (Claude agent, 2026-05-19 07:45)

# Post-reboot auto-unlock — `wm dismiss-keyguard` + keyevent 82

**Status:** fixed
**Tags:** adb, lockscreen, post-reboot, autonomy, pixel-6a, creation-flow, hands-off

## Problem

After any soft reboot of a Pixel 6a phone, Android renders the lockscreen ("Unlock for all features and data"). Accessibility services do NOT bind until first unlock. Snap signup flow, Detector APK accessibility hooks, and other UI-driven iter steps cannot fire from a fully locked phone — even when there is NO PIN/pattern set (just a swipe-up dismiss).

Operator's standing rule (2026-05-19): "make sure we get around all things like opening the phone and also soft reboot is only needed not loing" — every reboot must end with the phone in an unlocked, ready-for-iter state without operator hands.

## Why it bites

- A swipe-up gesture via `input swipe 540 1800 540 600 200` works but is timing-fragile (depends on screen size + animation state).
- `input keyevent KEYCODE_HOME` (3) is rejected on a locked phone.
- `am start <intent>` runs the activity behind the keyguard — accessibility services still don't bind.

## Fix

After every soft reboot (`adb reboot` — no `bootloader` / `recovery`), wait for `sys.boot_completed=1` and ADB to return, then fire both of these per-phone:

```bash
adb -s <SERIAL> shell 'wm dismiss-keyguard; input keyevent 82'
```

- `wm dismiss-keyguard` (Android 11+) is the canonical programmatic dismiss for no-PIN devices.
- `input keyevent 82` (KEYCODE_MENU) is the fallback that wakes/dismisses on some OEM ROMs.

Combined, they survive both timings (pre- and post-`SystemUI` ready). Verify via:

```bash
adb -s <SERIAL> shell 'dumpsys window 2>/dev/null | grep mDreamingLockscreen'
# expect: mShowingDream=false mDreamingLockscreen=false
```

## Why this works on bluejay Pixel 6a

- Operator hasn't set a screen lock (the OOBE notification "Set a screen lock" is still pending — visible in lockscreen screenshot).
- No PIN / pattern / password = `wm dismiss-keyguard` succeeds without prompting.
- Wild kernel + KSU + SUSFS modules don't gate the keyguard surface.

## Discoveries

### 2026-05-19 07:45 by Sinister Kernel APK

Verified end-to-end during soft reboot of BOTH phones in parallel for lukeprivacy KPM parity load. Confirmed: both phones at lockscreen post-boot (operator screenshot showed Pixel 6a / Verizon LTE / 7:42 timestamp); single ADB call per phone with `wm dismiss-keyguard; input keyevent 82` flipped `mDreamingLockscreen=false`; PI Checker re-tap immediately afterward returned 3/3 GREEN both phones; lukeprivacy `kpmodule: 1` confirmed kernel-loaded. Total elapsed from reboot trigger to fully-unlocked-PI-3/3-verified = ~90s.

**Pair with** the existing `adb-containerization` brain entry — every dismiss must be per-serial. Never bare `wm dismiss-keyguard` against the implicit single-device assumption.

**Pair with** the cold-start protocol: any agent that triggers `adb reboot` MUST follow with the dismiss-keyguard call (and the `adb reverse` re-establish — reboot wipes both).

## If this breaks later

If the operator ever sets a PIN/pattern/password, `wm dismiss-keyguard` will show but not bypass the credential prompt. Then need:

```bash
adb -s <SERIAL> shell 'input swipe 540 1800 540 600 200; sleep 1; input text <PIN>; input keyevent 66'
# 66 = KEYCODE_ENTER
```

But this requires storing the PIN — out of scope. Today's flow assumes no-credential lockscreen.
