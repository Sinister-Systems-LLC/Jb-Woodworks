# leak-audit.ps1 — Sinister Cast PC→Phone Leak Audit

> Author: RKOJ-ELENO :: 2026-05-24
> Lane: kernel-apk (EVE on Sinister Kernel APK)

Pre-flight scanner that measures whether PC-side ADB exposure is detectable from on-phone surfaces a fingerprinter (Snap, etc.) can read. **Not a fix tool** — it measures the state. Closures land in lukeprivacy KPM hide-targets + WiFi-ADB migration (Phase B.2 of the parent plan).

## Invocation

```powershell
# Live audit, attached phone (P1 = Pixel 6a; replace with `adb devices` serial)
.\leak-audit.ps1 -DeviceSerial 1A23B45C6D7E89

# Live audit + structured JSON output
.\leak-audit.ps1 -DeviceSerial 1A23B45C6D7E89 -Json

# Custom output directory
.\leak-audit.ps1 -DeviceSerial 1A23B45C6D7E89 -OutputDir D:\reports\leak-audit

# Dry-run — no adb calls, just preview commands + scaffold report (no phone needed; -DeviceSerial optional)
.\leak-audit.ps1 -DryRun -Json
```

## Surfaces audited (mirrors Phase B.1 of the parent plan)

| # | Surface | adb command |
|---|---|---|
| 1 | USB vendor/serial | `adb -s $S get-serialno` + `getprop ro.product.vendor.manufacturer` |
| 2 | sys.usb.config | `getprop sys.usb.config` |
| 3 | ADB_ENABLED | `settings get global adb_enabled` |
| 4 | /proc/bus/usb/devices | `cat /proc/bus/usb/devices` (root-only) |
| 5 | ADB_WIFI_ENABLED | `settings get global adb_wifi_enabled` |
| 6 | DEVELOPMENT_SETTINGS_ENABLED | `settings get global development_settings_enabled` |
| 7 | Wakelocks from com.android.adb | `dumpsys power \| grep -i adb` |
| 8 | dumpsys battery USB-state | `dumpsys battery \| grep -E 'powered\|USB\|AC'` |
| 9 | /proc/net/tcp port 9001 (hex 2351) | `cat /proc/net/tcp \| grep :2351` |

Each surface gets: raw output captured + risk verdict (LOW / MEDIUM / HIGH / UNKNOWN / ROOT-REQUIRED) + 1-line interpretation. Overall risk = max per-surface (concrete LOW/MEDIUM/HIGH outrank UNKNOWN/ROOT-REQUIRED).

## Output

Reports land in `-OutputDir` (default = script directory):

- `leak-audit-<serial>-<UTC>.md` — always written, human-readable
- `leak-audit-<serial>-<UTC>.json` — written only with `-Json`; schema = `sinister.leak-audit.v1`

JSON top-level: `{ schema, ts_utc, device_serial, mode, findings[], overall_risk }`.

## Composes with

- **Parent plan**: `D:\Sinister Sanctum\_shared-memory\plans\kernel-apk-adb-view-system-2026-05-24\plan.md` — Phase B.1 (surface inventory) + B.2 (closure work items).
- **Sibling tool**: `bridge.py` (next to this script in `tools/sinister-cast/`) — the SinisterCast PC-side WebSocket bridge daemon. Audit measures pre/post-state; bridge does the actual cast. They are intentionally separate so the audit can run on any phone, anytime, independent of whether SinisterCast is installed.

## Notes

- **Pre-flight only.** Phone-side fixes (lukeprivacy KPM hide-target additions, WiFi-ADB migration, com.snapchat.android battery/wakelock spoofing) are tracked under Phase B.2 of the parent plan and gated by source-tree restore (Phase D).
- **Root-required surfaces** (currently surface #4) report `ROOT-REQUIRED — skipped` rather than failing the whole audit if shell lacks root.
- **PowerShell 5.1 compatible.** No `&&`, no ternary, no null-coalescing.
- **Dry-run produces a representative markdown** for review when no phone is connected — every rubric returns `UNKNOWN` with a "DRY-RUN" interpretation.
