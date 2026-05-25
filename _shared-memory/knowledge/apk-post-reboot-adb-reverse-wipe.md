<!-- decay:
  category: preference
  confidence: 0.9
  reinforcements: 0
  half_life_days: 180
-->
---
updated: 2026-05-19
audience: claude (all Sinister-APK agents)
format: prose
purpose: canonical reference for re-establishing adb reverse 59347/8/9 after every phone reboot - read on cold-start when "Connection refused", "reverse", "fetch_keybox.log", "RKA unreachable from phone" surfaces in any log
rotates-at: never (workaround doc)
---

> **Author:** tiktok-emu agent (Claude) :: 2026-05-19 (cross-zone, operator-authorized)

# APK post-reboot adb-reverse wipe - mandatory re-establish after every reboot

**Slug:** apk-post-reboot-adb-reverse-wipe
**Status:** workaround (recurring; protocol-enforced)
**Tags:** apk, adb, reverse, reboot, rka, fetch_keybox, connection-refused
**First discovered:** 2026-05-17 (recurring; documented multiple PROGRESS entries)
**Last updated:** 2026-05-19 by tiktok-emu agent (cross-zone fix)

## Problem

After any `adb reboot` on either phone, the local RKA server at `:59347` (host) becomes unreachable from the phone. Phone-side logs show:

```
fetch_keybox.log: Connection refused
fetch_keybox.log: Connection refused
sinister_rka.conf: enabled=false  (but server IS alive on host)
```

This always presents as "RKA broken" but the RKA server is fine - only the adb reverse port-forward got wiped.

## Why it happens

`adb reverse` mappings are NON-PERSISTENT. Phone reboot kills the USB FFS gadget config which includes reverse port-forwards. The mapping needs to be re-established on every cold-start of the USB stack (phone reboot OR adb daemon restart OR USB cable replug).

This is by-design Android behavior (per AOSP `adb` source code). There's no "persistent reverse" flag.

## Fix / workaround

**After every phone reboot, re-establish the 3 ports:**

```bash
for S in 2A061JEGR09301 26031JEGR17598; do
  for P in 59347 59348 59349; do
    adb -s $S reverse tcp:$P tcp:$P
  done
done
```

Port roles:
- **59347:** RKA keybox server (Yurikey51_ECDSA.xml; java pid rotates; primary; required for PI 3/3)
- **59348:** RKA secondary (auth-token registry; required for panel-bound flows)
- **59349:** RKA command_server (panel-driven commands; Hetzner-only feature; not blocking Quick Spoof - phone-2 was observed missing this without functional impact 2026-05-19 07:40)

**Verify post-establish:**

```bash
for S in 2A061JEGR09301 26031JEGR17598; do
  adb -s $S reverse --list
done
# expect 3 UsbFfs entries per phone (or 2 for phones without 59349)
```

**Built into the bridge:**

- `SinisterAPK_RunMe.bat P-A1` (pre-flight) runs the re-establish loop + verifies via `--list`.
- `SinisterAPK_RunMe.bat 7` (post-reboot unlock; tiktok-emu cross-zone seeded) waits for boot_completed, dismisses keyguard, then re-establishes reverse.

## Caveats

- **Port collision with TT-EMU.** TT-EMU also uses :59347 for its RKA server BUT via cvd-2's direct localhost (no adb reverse needed - cvd-2 IS the localhost from the agent's WSL2 viewpoint). The two agents don't actually conflict because the phones use adb-reverse (forwarding host's 59347 into phone-localhost's 59347) while cvd-2 uses direct localhost. Single host process listening on :59347 serves both.
- **USB cable replug also wipes reverse.** If operator unplugs + replugs a phone, re-establish needed - same as reboot.
- **`adb usb` / `adb tcpip` mode switch wipes reverse.** Don't switch modes mid-session.
- **`adb kill-server` / `adb start-server` wipes reverse fleet-wide.** Forbidden anyway (host-shared lifecycle - PARALLEL-AGENT-POLICY § 4.1).

## Detection

If `fetch_keybox.log` is the first sign:

```bash
adb -s <serial> shell "su -c 'tail -5 /data/adb/modules/tricky_store/fetch_keybox.log'"
```

If output shows `Connection refused` recently, run the re-establish loop above. Then re-poll fetch_keybox.log; should show successful 200 + md5 verification within 30s.

Alternative detection (host-side):

```bash
adb -s <serial> reverse --list
# if output is empty OR < 2 entries, re-establish needed
```

## Cross-refs

- Project: `D:\Sinister\01_Projects\Sinister\Sinister-APK\source\living-mds\GOTCHAS.md` - operator-facing surface.
- PROGRESS: `D:\Sinister Sanctum\_shared-memory\PROGRESS\Sinister Kernel APK.md` - multiple entries reference this (2026-05-19 07:40, 07:45, 08:05, 13:38, 13:55).
- PS1 phase: `SinisterAPK_RunMe.ps1` Invoke-PhaseA1 (verify) + Invoke-PhaseA2 (PI re-tap; runs re-establish first).
- Cross-fleet: TT-EMU uses cvd-2 + WSL2, doesn't hit this. Snap-EMU same. ONLY phone-stack agents (APK + future ones) need this.

## Discoveries (append-only - most-recent at top)

### 2026-05-19 by tiktok-emu agent (cross-zone)

First brain entry. Recurring issue documented multiple times in PROGRESS without a brain-entry capture; this consolidates. Cross-zone authored under operator directive 2026-05-19 LATE ("not get blocked"). Pairs with `apk-classifier-aup-doctrine.md` + `apk-ps1-grep-lock-contention.md` (also this session).
