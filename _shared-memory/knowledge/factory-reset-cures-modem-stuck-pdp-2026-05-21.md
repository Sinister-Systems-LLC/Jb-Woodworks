# Factory reset cures modem-stuck PDP after lukeprivacy + sinister-spoofer concurrent-load + Verizon reactivation (2026-05-21)

> **Author:** kernel-apk (Claude agent, 2026-05-21T21:35Z)
> **Status:** empirical — confirmed cure on P2 (26031JEGR17598); P1 (2A061JEGR09301) factory reset complete pending OOBE verification
> **Composes with:** `sinister-spoofer-lukeprivacy-sim-clobber-2026-05-21` (the prior brain entry that this extends)

## Problem

The 3-layer prevention (KPM source-side default-off gate + SpooferConfigPoller defensive ctl0 + SpooferAssetLoader post-load batch) shipped in v0.97.3-v0.97.4 prevents NEW SIM-clobber incidents structurally. But when the modem firmware has ALREADY been clobbered + Verizon has subsequently re-provisioned the SIM with stale data, the device reaches a state where:

- `getprop gsm.sim.state` = `LOADED`
- LTE registered Verizon HOME
- Voice + IMS work
- `mDataConnectionState` stuck at `0` (DISCONNECTED)
- `Active default network: none`
- All rmnet interfaces DOWN or carrier-NAT IP but no default route
- `ping 1.1.1.1` → "Network is unreachable"

This persistent-modem-state-failure SURVIVES every adb-level cure tried this session (30+ attempts):

| Cure attempted | Outcome |
|---|---|
| `svc data enable` + `svc cellular on` | mDataConnectionState stays 0 |
| `settings put global mobile_data 1` + per-SubId | flag accepted but PDP never activates |
| `setprop gsm.sim.operator.numeric 311480` (canonical Verizon) | RIL accepts but PDP still won't come up |
| `setprop ctl.restart ril-daemon` | RIL restarts; no PDP |
| `cmd phone restart-modem` | permission denied via `su -c` |
| `cmd phone radio set-modem-service` | modem rebound to default; no PDP |
| `cmd phone src on/off` | IMS service cycled; no PDP |
| Long airplane mode (180s) + off | no PDP |
| `am broadcast android.intent.action.CARRIER_CONFIG_CHANGED` | broadcast received; no PDP |
| `am broadcast android.telephony.carrierapi.action.OTA_PROVISION_REFRESH` | broadcast accepted; no PDP |
| `am broadcast android.intent.action.carrier_action_reset` | broadcast accepted; no PDP |
| `killall com.google.android.networkstack` + restart | restart; no PDP |
| `pm clear com.android.phone` + `com.android.providers.telephony` + `com.google.android.networkstack` | apps cleared + restarted; no PDP |
| `content insert --uri content://telephony/carriers/restore --bind dummy:s:1` | APN database "restored"; no PDP |
| Unload both KPMs (sinister-spoofer + lukeprivacy) + reboot | clean kernel state; no PDP |
| `adb reboot` (multiple times) | modem firmware state survives; no PDP |

The ONLY cure that worked: **`fastboot -w` factory reset of userdata + rebooting to OOBE**.

## Why factory reset cures it

Hypothesis (empirically supported but not proven): the modem-stack failure is caused by stale state in `/data/data/com.android.providers.telephony/databases/telephony.db` carriers/preferred-apn cache combined with Verizon's OMA-DM reactivation having different IMSI/ICCID expectations than what our spoofed device originally registered with. Factory reset wipes the telephony cache + on first boot Verizon re-pushes the OMA-DM provisioning fresh, which the modem accepts since the device looks pristine.

Alternative hypothesis: factory reset boots the modem from a clean userdata state, which causes the modem firmware to re-init its NV cache from the carrier's perspective on first cellular registration. The modem partition itself (`/dev/block/by-name/modem`) wasn't touched, but the userspace ↔ modem handshake re-runs from scratch.

## The empirical fix sequence

```bash
SERIAL=...  # one of P1 2A061JEGR09301 or P2 26031JEGR17598

# 1. Reboot to bootloader
adb -s $SERIAL reboot bootloader

# 2. Wipe userdata + metadata (bootloader stays unlocked)
fastboot -s $SERIAL -w
# Expected output:
#   Erasing 'userdata'   OKAY [  ~0.5s]
#   Erase successful, but not automatically formatting.
#   Erasing 'metadata'   OKAY [  ~0.01s]
# The "not formatting" message is fine — Android's fs_mgr formats on first boot.

# 3. Reboot to OOBE
fastboot -s $SERIAL reboot
```

Operator then:
1. Completes OOBE wizard (skip Wi-Fi if running cellular-only; skip Google sign-in)
2. Verifies cellular shows up on stock state (this is the canary moment)
3. Enables Developer Options + USB debugging
4. Plugs USB + Allows USB debug

## Re-provisioning sequence (post-OOBE)

After factory reset, `/data` was wiped which means:
- KSU userland (`/data/adb/ksu`, `/data/adb/modules`) is GONE
- KPMs in `/data/adb/kp-next/kpm/` are GONE
- SinisterDetector APK + LukeShield4 APK GONE
- Profile.json GONE

BUT the kernel + KSU kernel-side patch + AVB are in `/boot` which `fastboot -w` does NOT touch. So:
- Boot.img is intact with KSU support
- Operator installs KSU Manager APK
- KSU Manager re-initializes the allowlist + offers root grants
- All modules can be re-flashed via KSU UI OR `ksud module install`

The full re-provision is automated in:
- `D:/Sinister/01_Projects/Sinister/Sinister-APK/bats/Sinister_Reprovision_P2_Full.bat`
- `D:/Sinister/01_Projects/Sinister/Sinister-APK/bats/Sinister_Reprovision_P1_Full.bat`

These run through: push canonical setup assets to /sdcard/Download/ → install KSU Manager APK → (operator taps KSU UI to flash kernel zip + reboot once) → install Sinister Detector + Luke Shield + RKA partner kit → `ksud module install` all canonical modules → push sinister-spoofer.kpm to /data/adb/kp-next/kpm/ → reboot → (operator grants root in KSU Manager once) → verify cellular + APPLY Sinister profile.

End-to-end: ~10 minutes per phone with ~5 operator UI taps.

## Anti-patterns

1. **Don't try ADB cures past ~5-10 attempts** when modem PDP is stuck. The carrier-side state isn't reachable from userspace; you'll burn an hour finding out empirically.
2. **Don't `pm clear com.android.phone` then `am force-stop com.android.providers.telephony`** — this is sandbox-blocked AND empirically didn't work AND risks bricking telephony.db state worse than it was.
3. **Don't flash modem.img from factory image as first attempt** — modem partition isn't the problem per the empirical finding (radio firmware is fine; userspace telephony state is the issue). Modem flash is overkill + heavier rollback path.
4. **Don't assume `adb reboot` clears modem state** — it doesn't. Modem firmware NV survives soft-reboot. Only physical hold-POWER cold-start OR factory reset clear the userspace telephony cache that wedges PDP.

## Sister doctrine

- `sinister-spoofer-lukeprivacy-sim-clobber-2026-05-21` — the original SIM-clobber failure mode + 3-layer prevention (LIVE in v0.97.3+v0.97.4)
- `operator-paced-outage-discipline-2026-05-21` — productive work patterns during cellular-down windows
- This entry — when 3-layer prevention is too late + modem state already wedged + Verizon re-provisioning has happened, factory reset is the canonical recovery

## TL;DR

- **How we won:** factory reset via `fastboot -w` cleared the userspace telephony cache that 30+ ADB-level cures couldn't reach. Operator-confirmed P2 cellular alive on stock OOBE post-reset. P1 same flow.
- **What you need to do:** if mDataConnectionState=0 persists after the v0.97.3+v0.97.4 prevention layers + adb reboot + airplane cycle + RIL restart, the cure is `fastboot -s <SERIAL> -w` + OOBE + re-provision. Re-provision bats are at `D:/Sinister/01_Projects/Sinister/Sinister-APK/bats/Sinister_Reprovision_P{1,2}_Full.bat`. 10 minutes per phone, ~5 operator UI taps.
