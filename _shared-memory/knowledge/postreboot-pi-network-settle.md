<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Post-reboot PI tap needs ~30s network settle, even when ping works

**Discovered:** 2026-05-19 resume-pickup session, sinister-kernel-apk project
**Type:** Phone-side gotcha — distinct from adb-reverse-wipe pattern

## The finding

Immediately after a phone reboot (Pixel 6a bluejay, cellular 5G/LTE), the Play Integrity API Checker (Nikolas Spyropoulos `gr.nikolasspyr.integritycheck`) returns **`NETWORK_ERROR (-3)`** ("No available network is found. Check your connection.") **even when basic network connectivity is fully restored** — `ping 8.8.8.8` returns 0% loss at 100-400ms RTT, and the mobile data carrier-assigned IP (e.g., `rmnet1 10.x.x.x/32`) is bound.

The PI API specifically needs full **GMS push channel / GCM connectivity** to establish, which lags basic IP routing by ~20-30 seconds on cellular. Until GMS is fully connected, the PI request can't reach Google's verifier.

## Empirical proof (2026-05-19)

Phone 2 `26031JEGR17598` after `adb reboot` at 10:25 EDT:

| Time | Action | Result |
|---|---|---|
| 10:25:10 | `adb reboot` fired | — |
| 10:25:20 | `adb wait-for-device` returns | online |
| 10:25:41 | `getprop sys.boot_completed` = 1 | boot complete |
| 10:25:45 | adb reverse 59347/8/9 restored | OK |
| 10:26:00 | PI tap | **NETWORK_ERROR (-3)** |
| 10:26:15 | Network diagnostic: `ping 8.8.8.8 -c 4` | 0% loss, 115-376 ms RTT |
| 10:26:15 | `ip addr` shows `rmnet1 10.210.100.198/32` | mobile data IP bound |
| 10:28:00 | PI tap retry | 3/3 GREEN ✓ |

So between 10:26 (NETWORK_ERROR despite ping OK) and 10:28 (PI 3/3 GREEN), the ~2-minute gap was GMS push channel handshake completing. The phone went from "network up but GMS not connected" to "GMS connected and PI verdict served".

## Permanent rule

After any phone reboot:

1. `adb wait-for-device` (returns when ADB transport up — too early for PI)
2. Poll `sys.boot_completed = 1` (returns when init done — still too early)
3. Restore `adb reverse 59347/8/9` (immediate, no wait needed)
4. **Wait additional 30-45s** before tapping PI Checker
5. **OR** poll `ping 8.8.8.8` + a Google domain DNS lookup until both succeed for ~10 sec consecutively
6. Then tap PI Checker

If a PI tap returns NETWORK_ERROR(-3), **wait 30s and retry** — don't escalate to keybox swap / RKA daemon restart / module reload until ≥2 NETWORK_ERROR returns ≥60s apart.

## PS1 helper pattern

In `SinisterAPK_RunMe.ps1` `Invoke-PiRetap` helper, after the post-reboot adb wait, add:

```powershell
# Wait for GMS push channel (PI API needs this, not just basic IP)
Start-Sleep -Seconds 30
$pingOk = $false
for ($i = 0; $i -lt 5; $i++) {
    $ping = adb -s $Serial shell "ping -c 2 -W 2 8.8.8.8" 2>&1
    if ($ping -match "0% packet loss") { $pingOk = $true; break }
    Start-Sleep -Seconds 5
}
if (-not $pingOk) { Write-PhaseLog "WARN: ping never succeeded; PI tap may NETWORK_ERROR" }
# Now safe to tap PI
```

## Related gotchas

- **adb reverse wipes on reboot**: see `apk-post-reboot-adb-reverse-wipe.md`. The reverse mappings AND the PI network settle are BOTH post-reboot consequences; one is fixable in 1 second, the other needs 30s wait.
- **Lockscreen blocks monkey-launched PI tap**: if phone has secure lock, `monkey -p gr.nikolasspyr.integritycheck` may put the app behind the lockscreen → CHECK tap doesn't register. Unlock first via `input keyevent KEYCODE_WAKEUP` + `input swipe 500 1500 500 500 200`.

## Cross-refs

- `Sinister-APK/source/.claude/memory/b.md` 2026-05-19 phone 2 PI regression+recovery entry (permanent_rule field documents this)
- Sister entry: `apk-post-reboot-adb-reverse-wipe.md`
- PS1 helper: `Sinister-APK/source/_runme/scripts/SinisterAPK_RunMe.ps1` `Invoke-PiRetap`
