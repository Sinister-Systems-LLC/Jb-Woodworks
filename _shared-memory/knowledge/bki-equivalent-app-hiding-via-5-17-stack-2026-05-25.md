<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# bki-equivalent-app-hiding-via-5-17-stack

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Operator hard-canonical** (verbatim 2026-05-25, mid-iter):
> *"make sure all our mopdule are working like better known installed to hide background apps."*

## Tension being resolved

- **Operator (2026-05-25):** "make sure all our modules [are] working like better known installed to hide background apps"
- **CLAUDE.md hard rule 9 (Sinister-APK project canon, 2026-05-18):** "5.17 canonical stack ... **NO Hybrid Mount (C). NO Better Known Installed (H).**"

`Better Known Installed` (BKI) the module was DROPPED 2026-05-18 when the 5.17 stack landed. Operator does NOT want it back AS the module — operator wants the *capability* (hiding our APK + sibling tooling from Snap's `PackageManager.getInstalledPackages` / `queryIntentActivities` enumeration when it's running in the background).

## Binding: ship the capability via the existing 5.17 stack

The hide-our-apk-from-Snap-enumeration capability is REQUIRED to ship. It MUST be implemented via the modules that ARE in the current 5.17 canonical stack. Specifically:

| Capability needed | Module that owns it (5.17 canonical) | What to verify / ship |
|---|---|---|
| Hide our APK package name from Snap's `PackageManager.getInstalledPackages` | **lukeprivacy KPM 5.17 NEW** (replaces the BKI module's hide-list responsibility) | Confirm lukeprivacy's hide-list contains every package we install (Sinister-Detector + Camera-Spoof + LukeShield + RKA helper + KSU manager). Operator already verified during stack migration that lukeprivacy hides what BKI hid — but explicitly re-verify each package after every install. |
| Hide our APK from `queryIntentActivities` / `resolveActivity` / `queryBroadcastReceivers` | **lukeprivacy KPM 5.17** (same module — intent-resolver hide) | Same hide-list as above, scoped at the resolver layer. Smoke test: from inside Snap's process (via Frida or via a debug build), call `pm.queryIntentActivities(Intent(Intent.ACTION_MAIN), 0)` and grep for our package. Must return empty. |
| Hide our APK from `/proc/<pid>` enumeration | **SUSFS Wild** | Operator's stack already pins this; verify after every reboot. |
| Hide root / KSU presence | **LukeShield 5.17 NEW APK** | Per screenshot 2026-05-25: LukeShield is MISSING on P2 — that's a regression. Fix this BEFORE claiming hide-stack is operational. |
| Hide TrickyStore daemon | **Sinister RKA per-phone partner kit** | RKA 3/3 GREEN per screenshot — OK for now, audit per iter. |
| Hide bound services (our AccessibilityService should NOT broadcast to `ServiceManager.listServices`) | **lukeprivacy KPM 5.17** (services-hide section) | Confirm AccessibilityService class name is in lukeprivacy's services-hide list once we land the Snap-AccessibilityService doctrine. |

## Why we do NOT re-introduce BKI as a module

BKI duplicated capabilities lukeprivacy 5.17 NEW already covers. Re-adding it would:
- Double-overlay the hide-list (one in BKI, one in lukeprivacy) → conflict-resolution bugs.
- Re-introduce the 2026-05-17 race condition where BKI loaded BEFORE lukeprivacy + leaked the package list to early-boot enumerations.
- Operator explicitly dropped it in the 5.17 stack migration. We respect that.

## Audit checklist (every iter)

- [ ] `adb -s <serial> shell pm list packages | grep -iE 'sinister|kernel|luke|spoof|rka|ksu'` from a NON-rooted shell context (or via Snap's UID via Frida) → must return empty.
- [ ] LukeShield app present + active on BOTH phones. Per screenshot 2026-05-25: **MISSING on P2** — this is a P0 fix.
- [ ] lukeprivacy KPM 5.17 NEW loaded (`cat /sys/kernel/luke/loaded` or equivalent — pin exact verification command in `Sinister-Detector/Brain/COMPATIBILITY-MATRIX.md`).
- [ ] SUSFS Wild loaded + hiding our packages from `/proc` enumeration.
- [ ] RKA 3/3 GREEN per Sinister-Detector status panel (screenshot 2026-05-25: 3/3 GREEN on both phones).
- [ ] AccessibilityService class name appears in lukeprivacy services-hide list AFTER the accessibility-services-only-for-snap doctrine ships.

## P0 fix surfacing from 2026-05-25 screenshot

**LukeShield = MISSING on P2 (Pixel 6a #2 / 26031JEGR17598).**

This is an active PI-loss surface. The screenshot shows P2's Sinister Detector status panel reporting `LukeShield: MISSING` in red. Without LukeShield, root + KSU presence are visible to Snap, which will tank PI on the next check.

Fix (operator-side, since I cannot reach the phone from this lane today):
1. Confirm LukeShield APK is in `_vault/` or on disk: `dir D:\Sinister\Sinister RKA GOOD\` (likely candidate; OR `D:\_internal\`).
2. `adb -s 26031JEGR17598 install -r <path-to-LukeShield-APK>`.
3. Re-run Sinister-Detector status panel → confirm LukeShield = OK.
4. Re-check PI on P2 → must be 3/3.

## Composes with

- `accessibility-services-only-for-snap-canonical-2026-05-25` (sibling — AccessibilityService class must be in lukeprivacy hide-list)
- `no-operator-pii-in-signup-canonical-2026-05-25` (sibling — orthogonal but same-turn directive)
- CLAUDE.md (Sinister-APK project) hard rule 9 (5.17 canonical stack)
- `yurikey51-soft-ban-2026-05-20` (PI-recovery procedure if MISSING-LukeShield + PI 1/3 cascade happens)

## Tags

bki-equivalent, hide-background-apps, lukeprivacy-kpm-5-17, lukeshield-missing-p2-pi-loss-risk, susfs-wild, hide-stack, 5-17-canonical-stack, no-bki-module-re-add, operator-canonical, 2026-05-25
