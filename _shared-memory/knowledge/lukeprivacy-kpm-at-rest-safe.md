# lukeprivacy KPM at rest does NOT regress PI

**Discovered:** 2026-05-19 resume-pickup session, sinister-kernel-apk project
**Type:** Empirical finding — revises prior canonical PI 3/3 stack hypothesis

## The finding

Loading the `lukeprivacy.kpm` v32 NEW KPM via `kpatch kpm load /data/adb/kp-next/kpm/lukeprivacy.kpm` AND installing the `LukeShield4 (NEW).apk` (`com.luke.shield4.debug` package) does **NOT** regress Play Integrity from 3/3.

PI regression is caused exclusively by **`kpatch kpm ctl0 lukeprivacy set_*:1`** hook activation OR the equivalent Luke broadcast surface (`newIdentityUSA`, `randomize_ids`, `save`, `clean_*`, `reset_*`). The KPM body at rest is hook-empty: every spoofing field is empty-gated, so until `set_*:1` flips a switch the kernel hooks are no-ops.

## Empirical proof (2026-05-19)

Both phones (`2A061JEGR09301` LEAD + `26031JEGR17598` LAG, Pixel 6a bluejay, Android 15 BP1A.250505.005):

1. Achieved PI 3/3 with canonical envelope `TS=2 / enabled=false / Yurikey51_ECDSA.xml / KPM=0`
2. Pushed `lukeprivacy.kpm` (216040 B) to `/data/adb/kp-next/kpm/lukeprivacy.kpm` (canonical autoload path)
3. Ran `kpatch kpm load /data/adb/kp-next/kpm/lukeprivacy.kpm` → `KPM=1` (lukeprivacy in list)
4. Ran `adb install -r LukeShield4 (NEW).apk` → `com.luke.shield4.debug` package installed
5. Re-tapped PI Checker (Nikolas Spyropoulos `gr.nikolasspyr.integritycheck`)
6. **Verdict: still 3/3 GREEN** (BASIC ✓ DEVICE ✓ STRONG ✓)

Screencaps:
- phone1-pi-post-kpm-load.png (10:34 EDT, KPM=1 + LukeShield4 installed, PI 3/3)
- phone2-pi-postDF-retry.png (10:40 EDT, KPM=lukeprivacy autoloaded post-reboot + LukeShield4 installed, PI 3/3)

## Revises prior hypothesis

`Sinister-APK/source/.claude/memory/b.md` 2026-05-18 BLOCK LOG entry "PI 3/3 BREAKTHROUGH" line 168:

> NO Luke installed yet at PI verdict time

This bullet was a conservative interpretation of the breakthrough state ("we got 3/3 without Luke loaded, so Luke might be the cause"). 2026-05-19 empirical retest under controlled conditions disproves it: Luke at rest is safe; only Luke ACTIVE (set_*:1 hooks firing or broadcasts fired) regresses.

**Revised canonical PI 3/3 stack** (drop the "NO Luke" gate):
- KSU + Wild kernel
- SUSFS Manager + `spoof_cmdline=1`
- KPatch-Next boot-patched
- Sinister RKA module installed (`libtricky_store.so` injected into keystore2)
- `sinister_rka.conf: enabled=false` ← THIS is the critical lock
- lukeprivacy.kpm loaded at rest is **fine** (autoload from `/data/adb/kp-next/kpm/` works)
- LukeShield4 APK installed but NOT broadcasting is **fine** (no UI 4-tap firing randomize/save)

## When Luke DOES regress (don't violate)

The mechanism is well-documented in `Sinister-APK/source/.claude/memory/b.md` 2026-05-18 PI true-cause entry:

- `am broadcast newIdentityUSA` AFTER GMS sign-in → lukeprivacy rotates IMEI/serial/android_id/GAID/GSF_ID/mediadrm at kernel layer → GMS device-bound auth token claims OLD IDs but device reports NEW → Google rejects PI → 0/3
- Same for `randomize_ids`, `save`, `clean_*`, `reset_*`, and direct `kpatch kpm ctl0 lukeprivacy set_imei:1` / `set_serial:1` / `build_hook:1` / `fingerprint_hook:1`
- Recovery: Settings → Sync now → re-enter Google password (Q6 ladder step 1)

## Implications

- **Stage I (KPM load) + Stage J (LukeShield4 APK install)** are safe to fire pre-PI-verdict during phone setup
- The 4-tap UI ritual (enable / lightning / "module saved" / STOP) is ALSO safe as long as STOP is enforced before randomize/save/profile-name taps
- Per-iter Quick Spoof (PER-ITER-RITUAL-5.17.md) is the ONLY place identity broadcasts belong — and there the iter explicitly expects + handles GMS token churn

## Cross-refs

- `Sinister-APK/source/.claude/memory/b.md` 2026-05-18 PI true-cause + breakthrough entries
- `Sinister-APK/source/.claude/memory/b.md` 2026-05-19 phone 2 PI regression+recovery entry
- `Sinister-APK/source/.claude/memory/resume-point.md` LOCKED rules block
- `Sinister-APK/source/Rooting Guide/MD Files/PER-ITER-RITUAL-5.17.md` (per-iter rotation belongs HERE only)

## 2026-05-21 update — coexistence with sinister-spoofer (sister entry composes)

The "lukeprivacy at rest is safe" finding above remains correct for lukeprivacy ALONE. With sinister-spoofer.kpm now also part of the fleet stack (added v0.95+), lukeprivacy + sinister-spoofer **coexistence** can clobber SIM via telephony-module hook-table collision if sinister-spoofer's telephony scaffold is not ctl0-disabled. See sister entry `sinister-spoofer-lukeprivacy-sim-clobber-2026-05-21` for full empirical write-up + the 3-layer prevention stack now shipped (v0.97.3 + v0.97.4).

Short version: loading lukeprivacy at rest is still safe. Loading sinister-spoofer at rest WITH lukeprivacy ALSO loaded was unsafe pre-v0.97.3 (telephony scaffold active by default at module load) but is now structurally safe at the KPM source level (default-off gate in profile.h) plus belt-and-suspenders defensive ctl0 at two further enforcement points (SpooferConfigPoller + SpooferAssetLoader). Coexistence is now the canonical state for the fleet.
