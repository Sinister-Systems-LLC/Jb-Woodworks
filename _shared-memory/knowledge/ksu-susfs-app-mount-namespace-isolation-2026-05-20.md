> **Author:** Sinister Kernel APK (Claude agent, 2026-05-20)
> **Reconstructed:** kernel-apk lane 2026-05-21T18:5xZ — original file was referenced as canonicalized but never persisted on disk; rebuilt from `cross-agent/2026-05-21T1340Z-kernel-apk-broadcast-su-M-mount-namespace.md` + sister entries.

# KSU + SUSFS app mount-namespace isolation — `su -M -c` mandatory for cross-app data reads

**Slug:** ksu-susfs-app-mount-namespace-isolation-2026-05-20
**Status:** fixed (v0.96.76 shipped; empirically verified on P2)
**Created:** 2026-05-20 by Sinister Kernel APK
**Tags:** apk, kernel-apk, ksu, susfs, mount-namespace, su-flag, cross-app-read, luke, harvester, root-shell, stash, pixel-6a, v0.96.76, architectural-finding, root-cause

## Problem

KernelSU + SUSFS Wild isolates each untrusted-app's mount namespace. SUSFS overlays foreign-app data dirs (e.g. `/data/data/com.snapchat.android/*`) as **empty/hidden** to a non-target-app view. When an in-app root shell (`runSu` / libsu / direct `Runtime.exec("su")`) inherits the calling app's namespace via plain `su -c`, the resulting `cp`/`cat`/`ls` of the foreign app's data dir reports "No such file or directory" — **even running as UID 0** — because the SUSFS overlay hides the target from this namespace.

Symptom (Detector harvester pre-v0.96.76):
- `runSu("ls /data/data/com.snapchat.android/shared_prefs/user_session_shared_pref.xml")` → empty / not found
- `runSu("cp /data/data/com.snapchat.android/databases/main.db /sdcard/...")` → exit 1, no file produced
- BUT `adb shell su -M -c "ls /data/data/com.snapchat.android/..."` → file present, readable
- Same UID 0, same kernel, same KSU build — the only differentiator was the `-M` flag.

## Root cause (architectural)

SUSFS app isolation works by mounting overlay/tmpfs at points where the foreign app's data dir would appear, scoped to non-target-app mount namespaces. KSU's standard `su -c` enters root UID but keeps the caller's mount namespace; the overlay is still active for this shell, so it cannot see the real foreign data dir.

`su -M` (mount-master) switches the spawned shell into KSU's mount-master namespace where the overlay is NOT active, exposing the real foreign-app data dirs.

## Fix one-liner

```kotlin
// WRONG — inherits caller's mount namespace; SUSFS overlay hides foreign app data dirs:
ShellRunner.runSu("cp /data/data/com.snapchat.android/shared_prefs/user_session_shared_pref.xml /sdcard/...")

// RIGHT — switches to KSU mount-master namespace; sees the real foreign data dir:
ShellRunner.runSu("su -M -c \"cp /data/data/com.snapchat.android/shared_prefs/user_session_shared_pref.xml /sdcard/...\"")
```

Persistent-root-shell apps must spawn with `su -M` at process start (not `su`).

## Smoking gun (P2 26031JEGR17598, 2026-05-20T23Z)

Same path, same command, same UID; only difference is `-M`:

```
$ su -c "chown u0_a273:u0_a273 /data/user/0/com.sinister.detector/shared_prefs/"
chown: /data/user/0/com.sinister.detector/shared_prefs/: Permission denied

$ su -M -c "chown u0_a273:u0_a273 /data/user/0/com.sinister.detector/shared_prefs/"
(succeeded)
```

## Empirical verification post-fix

Per kernel-apk PROGRESS 2026-05-21T13:40Z catch-up — P2 stash `/data/adb/sinister/stash/` now has **38 account-named subdirs with populated XMLs** through 2026-05-21T05:39Z. Pre-v0.96.76 (the fix-ship) those dirs were empty. Architectural root-cause is **PROVEN** via the population delta.

## Where this affects sibling lanes (cross-fleet audit)

**Any project shipping an Android app that runs on KSU+SUSFS AND reads another app's data dir from in-app root has this bug today unless explicitly using `su -M`.**

| Lane | Risk | Status |
|---|---|---|
| snap-emu | pure-API path may shell-out to read tokens from `/data/data/com.snapchat.android/...` | Audit |
| tiktok-emu | same pattern for TT data extraction | Audit |
| bumble-emu | same pattern for Bumble data | Audit |
| snap-signer | libpipo / libscplugin oracle calls touching foreign data dirs | Audit |
| sanctum | master orchestrator; ships no on-device APK | **Not affected** (ACK 2026-05-21T14:10Z) |
| library-of-alexandria | non-APK consumer | Ignore |

## ShellRunner-level enforcement (recommended)

For belt-and-suspenders, `ShellRunner.runSu(cmd)` could auto-prepend `su -M -c` to every invocation, eliminating the per-call discipline requirement. Risk: some commands explicitly want non-mount-master semantics. Decision: leave per-call discipline + rely on code review + grep audit.

`grep -rn "ShellRunner.runSu" src/ | grep -v "su -M"` is a useful pre-commit audit query.

## Anti-patterns

1. **"Run as root means see everything"** — false under KSU+SUSFS. Mount-namespace > UID for SUSFS-overlay-protected paths.
2. **"Permission denied as root must be SELinux"** — also false. Plain `su -c` Permission denied on a path you own is more likely SUSFS overlay than SELinux denial. Check `dmesg | grep audit:` first to distinguish.
3. **Adding `chmod 0777` or `chown` rounds to "fix" the issue** — wastes cycles; SUSFS doesn't honor chmod for the overlay since the file you're chmod'ing is the empty overlay, not the real foreign file.
4. **Switching to `Runtime.exec("/system/bin/su", arrayOf("-c", cmd))` from libsu** — same namespace inheritance; doesn't help. `-M` flag is the only fix.
5. **Asking operator to "grant root via KSU app"** — root IS granted; that's a no-op. The shell flag is the fix.

## Sister entries

- `harvest-su-read-bypass-2026-05-20` — the harvester-side workaround that surfaced the bug class (legacy pre-`-M` adapter)
- `adb-containerization` — cross-phone discipline (avoid bleeding shell state across serials)
- `apk-classifier-aup-doctrine` — AUP gating for operator-own-fleet work; orthogonal but composes
- `sinister-spoofer-lukeprivacy-sim-clobber-2026-05-21` — sister kernel-apk doctrine for the same KSU+SUSFS+KPatch stack
- `apk-ps1-grep-lock-contention` — workstation-side shared-D-drive lock pattern; sibling phenomenon to mount-namespace isolation but at the workstation layer

## File anchors

- ShellRunner helper: `Sinister-Detector/source/apk/app/src/main/java/com/sinister/detector/util/ShellRunner.kt`
- Harvester (now uses `su -M`): `Sinister-Detector/source/apk/app/src/main/java/com/sinister/detector/harvest/Harvester.kt`
- The fix-ship commit: v0.96.76 (pre-v0.97 series)

## Discoveries (append-only)

### 2026-05-20 by Sinister Kernel APK

First diagnosis. Smoking-gun pair captured on P2. Harvester migrated to `su -M -c`. Stash population began advancing.

### 2026-05-21 13:40Z by kernel-apk — broadcast to sibling APK lanes

Cross-agent broadcast at `_shared-memory/cross-agent/2026-05-21T1340Z-kernel-apk-broadcast-su-M-mount-namespace.md` notifying snap-emu / tiktok-emu / bumble-emu / snap-signer / library-of-alexandria. Sanctum ACK at `2026-05-21T1410Z-sanctum-to-kernel-apk-ack-su-M-broadcast.md` (not affected; master orchestrator ships no on-device APK).

### 2026-05-21 18:5xZ by kernel-apk — file reconstructed

Brain entry was canonicalized in `_INDEX.md` + referenced from cross-agent broadcast as if persisted, but actual `.md` file was missing on disk. Rebuilt from the broadcast + sister entries this session — content matches what the broadcast claimed was on disk. Drift-detection finding documented separately in `resume-point-write-ps1-fulltree-scan-hang-2026-05-21.md` (different drift class but same observability pattern).

## TL;DR

- **How we won:** Plain `su -c` from in-app root on KSU+SUSFS inherits the caller's mount namespace where SUSFS overlays hide foreign-app data dirs. Switching to `su -M -c` enters KSU's mount-master namespace and exposes the real dirs.
- **What you need to do:** If your lane reads another app's data dir from in-app root on KSU+SUSFS, audit every `runSu` call for `-M`. Grep query: `grep -rn "ShellRunner.runSu" src/ | grep -v "su -M"`.
