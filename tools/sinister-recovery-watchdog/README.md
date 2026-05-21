> **Author:** Sinister Kernel APK (Claude agent, 2026-05-21)

# sinister-recovery-watchdog

Host-side PowerShell daemon that polls each connected Pixel for `boot_events.jsonl` recovery-boot rows + `error_log.jsonl` runaway-failure patterns, then emits `[ALERT]` JSON messages to the kernel-apk inbox so the operator (or the kernel-apk agent) sees the event without manually pulling logs.

## What it does

Every ~60s the daemon:
1. `adb -s <SERIAL> shell 'su -c "tail -5 /data/adb/sinister/boot_events.jsonl"'` on each connected serial
2. Compares each row's `ts_ms` against the last-seen-ts in `state.json` for that phone
3. For any NEW row with `boot_mode=recovery`: writes a JSON alert to `_shared-memory/inbox/kernel-apk/<UTC>-recovery-boot-detected-<serial>.json`
4. Also tails the last 10 rows of `/data/adb/sinister/error_log.jsonl`; if `>= 5` rows match `status: failed:*` → writes a runaway-error alert
5. Persists `last_seen_*_ts_ms` per phone back to `state.json`

The daemon is **read-only on phones** (it only `tail`s remote logs) and **append-only on the host** (writes new inbox JSON files; never modifies APK source or KPM state).

## Files

| File | Purpose |
|---|---|
| `watchdog.ps1` | Main polling daemon — single invocation = one poll cycle |
| `Install-Task.ps1` | Idempotent scheduled-task registrar (60s repeat) |
| `state.json` | Per-phone last-seen-ts + concurrency lock (created on first run) |
| `watchdog.log` | Rolling 5MB log file (rotated to `.log.1` then truncated) |

## Install

```powershell
cd "D:\Sinister Sanctum\tools\sinister-recovery-watchdog"
.\Install-Task.ps1
```

Registers a scheduled task `SinisterRecoveryWatchdog` that fires every 60s indefinitely.

## Uninstall

```powershell
Unregister-ScheduledTask -TaskName SinisterRecoveryWatchdog -Confirm:$false
```

## Alert message shape

```json
{
  "_author": "sinister-recovery-watchdog :: 2026-05-21",
  "tag": "[ALERT recovery-boot]",
  "from": "recovery-watchdog",
  "to": "kernel-apk",
  "ts_utc": "2026-05-21T1146Z",
  "phone_serial": "2A061JEGR09301",
  "event": {
    "ts_ms": 1779378082058,
    "boot_mode": "recovery",
    "bootmode": "...",
    "boot_reason": "..."
  },
  "subject": "ALERT: recovery boot detected on 2A061JEGR09301"
}
```

## Standing-rule compliance

- DIRECTIVES Rule 6 (ADB containerization): every `adb` call is `-s <SERIAL>` — never bare
- DIRECTIVES Rule 8 (Progress logging): all activity logged to `watchdog.log`
- DIRECTIVES Rule 11 (Cross-agent coordination): alerts tagged `[ALERT recovery-boot]` and routed to `inbox/kernel-apk/`
- Lane discipline: lives in Sanctum `tools/` tree — zero touches to APK source or `~/.claude/.mcp.json`

## Composes with

- Brain entry `sinister-spoofer-lukeprivacy-sim-clobber-2026-05-21` (recovery-boot causes were a primary symptom in the SIM-clobber incident)
- `apk-post-reboot-adb-reverse-wipe` (sister phone-side recovery pattern)
- Kernel APK `BootRecoveryDetector` Kotlin class (the phone-side writer of `boot_events.jsonl`)
