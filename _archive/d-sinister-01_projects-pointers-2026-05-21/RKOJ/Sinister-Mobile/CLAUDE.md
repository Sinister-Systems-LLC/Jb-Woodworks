> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-20
> **Project:** Sinister Mobile (Car) — 2022 Dodge Challenger, ghost-mode rolling fortress
> **Parent:** RKOJ (operational / mobile division) at `D:\Sinister\01_Projects\RKOJ\`
> **Launcher:** `Start-Sinister-Personal-Session.bat` → pick `Sinister Mobile (Car)`

# CLAUDE.md — Sinister Mobile (Car)

The vehicle integration layer of the RKOJ division. Operator's 2022 Dodge Challenger as a rolling sensor + compute + comms platform that hands off seamlessly to JOKR (home) and the Drone fleet.

## What this project covers

| Layer | Status | Notes |
|---|---|---|
| **Cabin compute** | P0 complete | small-form-factor box wired; awaiting P1 greenlight |
| **Cabin UI** | designed | sub-routes at `JOKR-Global/app/housing/<vehicle-id>/cabin/` — owned by JOKR lane; this project plugs in |
| **Cabin cam** | designed | Frigate + YOLOv8 driver-attention + threat alerts; shares pipeline contract with JOKR home cams |
| **Multi-SIM bonded uplink** | designed | owned by the **Cell-Network** lane; this project consumes |
| **AdGuard DNS in trunk router** | designed | trunk-mounted travel router; egress policy operator-controlled |
| **WireGuard mesh** | designed | car ↔ home ↔ drones; designed by parent RKOJ lane |
| **Eve@car** | designed | shares state with Eve@home + Eve@drone (mid-sentence handoff via mesh) |

## The legal contract (non-negotiable)

- **No CAN-bus writes** to ECU / steering / brake. Read-only telemetry, never actuate.
- **No surveillance of non-consenting people** — cabin cam = driver only; outward cams = public-space only (no zoom into neighboring vehicles' cabins).
- **Failsafe everywhere** — operator must always retain manual override; no software lockout of vehicle controls.
- **Detection only** — same posture as JOKR / Drone. Alert + log; never engage.

## Cold-start in 5 steps

1. **This file** + **`SESSION-START.md`** for immediate state.
2. **Parent `RKOJ\CLAUDE.md`** for division-level contract (one Eve / one mesh / one pipeline).
3. **JOKR cross-ref** — cabin-UI routes live in JOKR's `app/housing/<vehicle-id>/cabin/`; coordinate via cross-agent inbox.
4. **Cell-Network cross-ref** — uplink design lives in `D:\Sinister\01_Projects\Cell-Network\CLAUDE.md`.
5. **PROGRESS log** — `D:\Sinister Sanctum\_shared-memory\PROGRESS\car.md` (create on first append).

## What this agent owns

- All code/config under `D:\Sinister\01_Projects\RKOJ\Sinister-Mobile\`
- Cabin compute provisioning + boot scripts
- Vehicle-side service definitions (Frigate, Eve@car, mesh client)
- Cabin cam model selection + threshold tuning

## What this agent NEVER touches

- Parent RKOJ CLAUDE / contract (read-only reference)
- JOKR's housing/cabin sub-route source (consumer side; coordinate via inbox)
- Cell-Network's uplink bonding config (consumer side)
- Eve MCP source (`D:\Sinister\01_Projects\EVE\`)
- Anything that violates the legal contract above (any CAN-bus write, any zoom-into-neighbor logic)

## Tools every Car turn must do

- Heartbeat fallback `_shared-memory\heartbeats\car.json`
- Inbox poll `_shared-memory\inbox\car\`
- Append milestones to `_shared-memory\PROGRESS\car.md`
- Per-agent branch `agent/car/<topic>`
- Authorship line on every new .bat / .md / .ps1

## North-star advance

EXPANSION LADDER when idle:
1. **P1 unblock** — surface what operator needs to greenlight P1 (install cabin cam, configure mesh client, calibrate Frigate model)
2. **Cabin-UI contract** — write the JOKR-side route spec so JOKR lane can pre-stage
3. **Cell-Network handshake** — write the contract Car expects from Cell-Network (SIM bonding, AdGuard rules)
4. **Threat-alert ladder** — define the cabin-cam → mesh → Eve@home alert escalation
5. **Brain capture** — patterns useful for Drone or other moving bodies

## Existing research (mapped 2026-05-20 by test agent)

**Operator's `_vault/` notes (read these first):**
- `..\_vault\Car.md` — full Sinister Mobile spec: 2022 Dodge Challenger; trunk-mounted Jetson Orin NX 16GB + Pi 5 failover; Peplink MAX BR2 Pro 5G bonded uplink; A-pillar IR cabin cam; exterior front/rear ALPR + 360° dashcam; SDR scanner (K/Ka radar + IMSI catchers); LIDAR detection; KrakenSDR direction-finding; biometric ignition (InsightFace + SpeechBrain); WireGuard mesh peer; OSRM offline nav + Navidrome music
- `..\_vault\CarPlay Hack.md` — Uconnect 5 CarPlay USB tap; EVE cabin UI routing
- `..\_vault\Door-Locks.md` — UWB proximity with home handoff
- `..\_vault\Frigate.md` — cabin_car YOLOv8 model contract (shares with home + drone)
- `..\_vault\Mesh.md` — WireGuard peer topology this project consumes
- `..\_vault\EVE-Wiring.md` — Eve@car command relay architecture (MQTT topics, car-control tools)

**Sanctum brain:**
- `_shared-memory\knowledge\rkoj-embedded-device-viewer.md` — car status pane (live video, GPS, threat feed)
- `_shared-memory\knowledge\rkov-hot-reload-pattern.md` — code updates while in motion
- `_shared-memory\knowledge\keep-working-until-done.md` — canonical-19 doctrine

**Research gaps (EXPANSION LADDER):**
- Jetson Orin power + thermal budget at highway speed
- InsightFace + SpeechBrain enrollment / re-enroll cadence + spoofing test protocol
- Jetson Orin → Pi 5 hot failover timing
- ALPR plate watchlist real-time distribution from JOKR
- In-motion OBD-II telemetry streaming (read-only) into JOKR fleet telemetry
- SDR + LIDAR threat-scan accuracy at 80 mph (false-positive minimization)
- Cabin audio recording legal/consent protocol (single-party state map)

## Reference

- Parent: `..\CLAUDE.md` (RKOJ division)
- Sibling: `..\Sinister-Drone\CLAUDE.md` (Drone)
- `D:\Sinister\01_Projects\JOKR\CLAUDE.md` (housing routes consumer)
- `D:\Sinister\01_Projects\Cell-Network\CLAUDE.md` (uplink contract)
