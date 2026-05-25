# Sinister OS Mobile (Pixel 6a)

> Author: RKOJ-ELENO :: 2026-05-24
> Status: **P0 spec lock — plan pending operator review**

An EVE-controlled custom Android distribution targeting the **Google Pixel 6a** (`bluejay`, Tensor G1).
Sister to `projects/sinister-os/` (Linux PC). Same EVE-control DNA, different metal.

## The 30-second pitch

The operator wants an EVE-resident phone:
- EVE has root-equivalent control as a system service (no UAC-style prompts for routine actions).
- Sinister Panel runs natively (Jetpack Compose, inherits dashboard-skeleton theme).
- Voice surface on-device (whisper-cpp; no cloud).
- Sinister Vault syncs operator data (Syncthing on-device client).
- Phone still works as a phone — calls, signal, optional GApps.
- Build target = Pixel 6a because: unlockable bootloader, Treble-compatible, long Tensor-G1 support, $300 hardware floor.

## Phases (operator-gated)

| Phase | Output | Gate |
|---|---|---|
| **P0** | Spec lock — `plans/master-plan-2026-05-24.md` | Operator click → P1 |
| **P1** | Base-ROM selection (LineageOS / GrapheneOS / CalyxOS / AOSP-from-scratch) with quantum-kernel triad audit | Operator click → P2 |
| **P2** | Build environment provisioned (Linux host, ~250 GB, `repo sync`) | Operator click → P3 |
| **P3** | Vanilla cuttlefish boot + adb shell roundtrip | Operator click → P4 |
| **P4** | EVE service + Sinister Panel + Vault + voice surface on cuttlefish | Operator click → P5 |
| **P5** | Flash to physical Pixel 6a (operator types `sinister-os-mobile flash-pixel`) | Operator hands-on |

## Where things live

- `plans/master-plan-2026-05-24.md` — canonical plan (5 phases + 10 operator-gate questions)
- `docs/architecture.md` — layered system view
- `research/` — base-ROM evaluations, vendor-blob audits, seraphim quantum-audit outputs
- `source/` — ROM patches, EVE service code, Sinister Panel Android (Jetpack Compose), build scripts
- `_shared-memory/PROGRESS/Sinister OS Mobile.md` — what shipped, what's in-flight

## Why Pixel 6a (operator-stated hardware)

| Property | Value |
|---|---|
| Codename | `bluejay` |
| SoC | Google Tensor G1 (`gs101`) |
| RAM | 6 GB |
| Storage | 128 GB UFS 3.1 |
| Display | 6.1" OLED 2400×1080 60 Hz |
| Bootloader | Unlockable (`fastboot flashing unlock`) |
| Treble | ✅ (GSI compatible) |
| Long-term support | Android 16+ via GrapheneOS / LineageOS |
| AVB | Verified Boot 2.0 (custom-key path documented in P5) |
| Bands | US LTE/5G; operator confirms carrier compat in P0 question Q1 |

## Quick-start (when a lane spawn lands here)

```bash
# 1. Cold-start (per SESSION-START.md)
cat SESSION-START.md
cat CLAUDE.md
cat plans/master-plan-2026-05-24.md

# 2. Current phase check
grep -A 20 "## § 12 Phase status board" plans/master-plan-2026-05-24.md

# 3. Heartbeat + inbox poll
# (use sinister-bus MCP if loaded; else write _shared-memory/heartbeats/sinister-os-mobile.json directly)

# 4. Pick P0 queue row, work, commit on agent/sinister-os-mobile/p0-spec-2026-05-24
```

## Bat launch

This project is registered in `automations/session-templates/projects.json` under key `sinister-os-mobile`. Launch via:
- `Sinister Start.bat` (desktop) → picker → select `sinister-os-mobile`
- Or directly: `EVE.exe --project sinister-os-mobile --swarm --loop`

## License

Inherits from Sanctum (see repo root LICENSE pointer). Vendor blobs (Google firmware, proprietary HALs) stay out of git per the lane's hard rules.
