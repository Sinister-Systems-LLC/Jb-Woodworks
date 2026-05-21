> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-20
> **Project:** Sinister Drone — FPV → autonomous → mesh swarm fleet
> **Parent:** RKOJ (operational / mobile division)
> **Launcher:** `Start-Sinister-Personal-Session.bat` → pick `Sinister Drone`

# CLAUDE.md — Sinister Drone

The aerial layer of the RKOJ division. Currently at **D0** (operator has Part 107 + first FPV). The roadmap climbs: D1 FPV-with-Eve@drone, D2 autonomous waypoint, D3 mesh swarm.

## What this project covers

| Phase | Status | Notes |
|---|---|---|
| **D0** — Part 107 + first FPV | operator-side complete | manual flight only |
| **D1** — Eve@drone telemetry | designed | drone reports position / battery / camera state into the mesh |
| **D2** — autonomous waypoint | designed | flight plans sourced from Eve; operator-greenlight per mission |
| **D3** — mesh swarm | designed | multi-drone coordination; ROE-bounded |
| **Frigate + YOLOv8 on drone cam** | shared with home / car | same model registry, same alert ladder |

## The legal contract (non-negotiable)

- **No weaponization.** Sensor + comms platform only. Never an actuator.
- **No surveillance of non-consenting people.** Operator-designated public-space patterns only.
- **Always knows return-to-home.** Failsafe binding: GPS-loss → climb + RTL; comms-loss → RTL; battery-low → RTL.
- **No autonomous flight without operator greenlight per mission.** D2 ≠ "drone flies whenever it wants."
- **Visual line of sight when required** by FAA Part 107 unless operator has obtained explicit BVLOS waiver for that flight.

## Cold-start in 5 steps

1. **This file** + **`SESSION-START.md`**.
2. **Parent `RKOJ\CLAUDE.md`** for division contract.
3. **JOKR cross-ref** — threat-alert ladder lands at JOKR-Global; pipeline shared.
4. **Car cross-ref** — `..\Sinister-Mobile\CLAUDE.md` for the mesh handshake (same WireGuard topology).
5. **PROGRESS log** — `_shared-memory\PROGRESS\drone.md` (create on first append).

## What this agent owns

- All code/config under `D:\Sinister\01_Projects\RKOJ\Sinister-Drone\`
- Drone-side telemetry / vision / mesh-client provisioning
- Flight plan + mission validation logic (the "is this mission legal + safe?" gate)
- Drone cam model selection (shared with car/home; bumps coordinated via inbox)

## What this agent NEVER touches

- Parent RKOJ CLAUDE / contract (read-only)
- Car-side flight integration is symmetric — same mesh, coordinate via cross-agent ASK
- JOKR housing routes (consumer side)
- Anything that violates the legal contract above

## Tools every Drone turn must do

- Heartbeat fallback `_shared-memory\heartbeats\drone.json`
- Inbox poll `_shared-memory\inbox\drone\`
- Append milestones to `_shared-memory\PROGRESS\drone.md`
- Per-agent branch `agent/drone/<topic>`
- Authorship line on every new .bat / .md / .ps1

## North-star advance

EXPANSION LADDER:
1. **D1 prep** — Eve@drone telemetry contract (what fields, what cadence, what mesh path)
2. **Failsafe doc** — write the full RTL ladder + test scenarios (GPS-loss, comms-loss, battery-low)
3. **Mission validation gate** — formalize the "is this mission legal/safe?" decision tree
4. **Shared vision pipeline** — match Frigate + YOLOv8 contract with Car + JOKR
5. **Brain capture** — drone-specific patterns (GPS-denied nav, BVLOS prep, swarm coordination)

## Existing research (mapped 2026-05-20 by test agent)

**Operator's `_vault/` notes:**
- `..\_vault\Drone.md` — phase ladder D0→D8 (DJI Avata 2 FPV → Pixhawk 6X + Jetson Nano → mission orchestration → OAK-D YOLOv8 vision → Meshtastic swarm → solar charging hangar → car launch pad → 30-drone tiers → counter-drone RF + DroneID decode). Legal posture: FAA Part 107, Remote ID, 400 ft AGL, anti-jamming RX-only, state-by-state map.
- `..\_vault\Hardware-BOM.md` — frame, FC, ESC, motor, prop, goggles, video, companion compute, ML cam, mesh, battery brand picks
- `..\_vault\Frigate.md` — YOLOv8 model contract shared with home + car (vision autonomy D3+)
- `..\_vault\Mesh.md` — peer topology the drone-side telemetry rides on (Meshtastic + RFD900x in D4+)
- `..\_vault\EVE-Wiring.md` — drone mission dispatch over WireGuard mesh + Meshtastic; Eve@drone thin-client design
- `..\_vault\EVE.md` — three-body architecture (Eve@drone = Mission Planner client via mesh)

**Sanctum brain:**
- `_shared-memory\knowledge\quartz-horizon-phase-2.md` — phone-side OAK-D / vision patterns reusable on drone
- `_shared-memory\knowledge\keep-working-until-done.md` — canonical-19 doctrine

**Research gaps (EXPANSION LADDER):**
- D1 custom build detailed BOM + assembly guide (7" frame kits, Holybro wiring, battery placement)
- Jetson Nano thermal management during continuous inference (15-30 min flight)
- GPS waypoint geofencing logic (property boundary enforcement)
- Mission Planner / QGroundControl integration (cloud-free, local mesh dispatch)
- D4 swarm coordination algorithm (distributed object detection consensus, leader election)
- D5 inductive charging calibration (Wibotic / DIY Qi pad alignment, rain protection)
- D6 car roof-mount aerodynamics + quick-disconnect stress testing
- D8 DroneID sniffer (SDR setup, real-time spatial mapping)
- FAA waiver application strategy (BVLOS at D3, commercial ops at D7)

## Reference

- Parent: `..\CLAUDE.md` (RKOJ division)
- Sibling: `..\Sinister-Mobile\CLAUDE.md` (Car)
- `D:\Sinister\01_Projects\JOKR\CLAUDE.md` (threat-alert ladder consumer)
- `D:\Sinister\01_Projects\Cell-Network\CLAUDE.md` (uplink contract)
