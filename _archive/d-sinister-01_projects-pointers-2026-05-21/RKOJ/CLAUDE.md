> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-20
> **Project:** RKOJ (operational / mobile division) — the personal workstation, NOT the Sanctum workbench EXE
> **Launcher:** `C:\Users\Zonia\Desktop\Start-Sinister-Personal-Session.bat` → pick `RKOJ (personal workstation)`

# CLAUDE.md — RKOJ (personal)

RKOJ is JOKR backwards — the mirror division. Where JOKR holds the home and static stack, RKOJ holds everything that moves: the car, the phone, the drone network, the personal mobile mesh, and the integration glue that ties it all back to Eve and JOKR.

## Disambiguation (important)

The operator has two "RKOJ" things:
1. **RKOJ (personal workstation)** ← THIS PROJECT — operational / mobile division (`D:\Sinister\01_Projects\RKOJ\`)
2. **RKOJ Workstation** — the Sanctum-side workbench EXE at `:5077` for cross-agent orchestration (`D:\Sinister Sanctum\automations\window-manager\`)

If a session ever ambiguous, the personal-side is this folder; the Sanctum-side is master-orchestration.

## What lives in RKOJ-personal

| Subproject | Subfolder | Role | Status |
|---|---|---|---|
| **Sinister Mobile** | `Sinister-Mobile/` | 2022 Dodge Challenger, ghost-mode rolling fortress | P0 complete, awaiting operator P1 greenlight |
| **Sinister Drone** | `Sinister-Drone/` | FPV → autonomous → mesh swarm fleet | D0 (operator Part 107 + first FPV) |
| **Sinister Phone** | (P7, not yet bootstrapped) | ghost-mode operator pocket peer | parked until P6 mesh stable |
| **Eve-Mobile** | embedded in each subproject | Eve runtime across car + drone + phone (shares JOKR's Eve brain) | designed |

The **Car** and **Drone** projects have their own launcher entries pointing at these subfolders — start a separate Claude session for focused work on either.

## The unifying contract

1. **One Eve, three bodies.** Eve@home (JOKR), Eve@car (Sinister Mobile), Eve@drone — all share state over WireGuard mesh. Handoffs are mid-sentence, not session-boundary.
2. **One vision pipeline.** Frigate + YOLOv8 (or Jetson DeepStream) runs the same models for home cams, cabin cam, and drone cams. Threat alerts ladder up the same channel.
3. **One mesh.** WireGuard from car ↔ home ↔ phone ↔ drones. Multi-SIM bonded uplink (the **Cell-Network** project owns this layer). AdGuard DNS in the trunk router. Egress topology operator-chosen ("Eve, route through home").
4. **One aesthetic.** Sinister Clash palette (crimson primary + iris secondary + wine bridge + ink/bone scaffolding). James-Bond-gothic. Shipped on JOKR round-11 (2026-05-19), inherited by every RKOJ surface.
5. **One legal posture.** Detection only — no jamming, no surveillance of non-consenting people, no CAN-bus writes to ECU/steering/brake, no weaponized drones. Failsafe everywhere (operator never locked out of car; drone always knows return-to-home).

## Cold-start in 5 steps (canonical-19)

1. **This file** + **`SESSION-START.md`** for immediate state.
2. **`_README.md`** at RKOJ root + `_vault/_index.md` (Obsidian vault).
3. **Subproject `_README` / `CLAUDE.md`** for whichever subproject you're touching this session (Car / Drone).
4. **JOKR cross-ref** — `D:\Sinister\01_Projects\JOKR\CLAUDE.md` for the sister-static side (cabin-UI sub-routes, Eve brain).
5. **PROGRESS log** — `D:\Sinister Sanctum\_shared-memory\PROGRESS\rkoj-personal.md` (create on first append).

## What this agent owns

- `D:\Sinister\01_Projects\RKOJ\` and every subfolder (Sinister-Mobile, Sinister-Drone, future Sinister-Phone)
- Eve-Mobile runtime spec (the agent that lives in each body)
- Vision pipeline patterns shared across car + drone + home
- Mesh topology design (in collab with the Cell-Network lane)

## What this agent NEVER touches

- `D:\Sinister\01_Projects\JOKR\` — JOKR lane (static / home)
- `D:\Sinister\01_Projects\EVE\` — Eve MCP lane
- `D:\Sinister\01_Projects\Cell-Network\` — connectivity layer lane (cross-collab via cross-agent inbox)
- `D:\Sinister Sanctum\` — Sanctum master lane
- Anything safety-critical (CAN-bus writes to ECU/steering/brake — banned by contract)

## Tools every RKOJ turn must do

- Heartbeat fallback `D:\Sinister Sanctum\_shared-memory\heartbeats\rkoj-personal.json` if `sinister-bus` MCP not loaded
- Inbox poll `D:\Sinister Sanctum\_shared-memory\inbox\rkoj-personal\` for messages
- Append milestones to `_shared-memory\PROGRESS\rkoj-personal.md`
- Per-agent branch `agent/rkoj-personal/<topic>`
- Authorship line on every new .bat / .md / .ps1

## Existing research (mapped 2026-05-20 by test agent — see brain entry `personal-fleet-research-map.md`)

**Operator's `_vault/` notes (the goldmine — read these first):**
- `_vault\RKOJ.md` — division architecture + phase ladder overview
- `_vault\Roadmap.md` — phased expansion (R0 → R8)
- `_vault\Car.md` — Sinister Mobile build (Jetson Orin NX 16GB + Pi 5 failover, Peplink MAX BR2 Pro 5G uplink, A-pillar IR cabin cam, exterior ALPR + 360° dashcam, SDR + LIDAR threat scan, KrakenSDR DF, biometric ignition InsightFace + SpeechBrain, OSRM offline nav)
- `_vault\Drone.md` — phase ladder D0→D8 (DJI Avata 2 → Pixhawk 6X + Jetson Nano → OAK-D vision → Meshtastic swarm → solar hangar → car launch pad → 30-drone tiers → counter-drone DroneID detection)
- `_vault\Frigate.md` — shared with JOKR; YOLOv8 model contract used across home/car/drone
- `_vault\Mesh.md` — WireGuard topology + peer provisioning
- `_vault\EVE.md` — three-body architecture (home + car + drone, shared brain)
- `_vault\EVE-Wiring.md` — MQTT topic structure + Frigate→Eve listener + drone mission dispatch
- `_vault\CarPlay Hack.md` — Uconnect 5 USB tap; cabin UI routing
- `_vault\Door-Locks.md` — UWB proximity with home handoff
- `_vault\Hardware-BOM.md` — drone frame/FC/ESC/motor/prop/goggles/video/companion compute/ML cam/mesh/battery brands

**Sanctum brain (`_shared-memory/knowledge/`):**
- `rkoj-workbench-architecture.md` — workbench EXE side (different RKOJ but operator-adjacent)
- `rkoj-embedded-device-viewer.md` — device fleet UI (car + drone + phone status pane)
- `rkov-hot-reload-pattern.md` — in-motion code updates pattern
- `quartz-horizon-phase-2.md` — APK-side patterns the Phone subproject (P7) will reuse

**Research gaps (EXPANSION LADDER):**
- Cross-division failover orchestration (car loses connectivity → phone takes over Eve dispatch)
- Unified device management (firmware updates, config push across car/drone/phone)
- Battery/power budget across divisions (car aux, drone cycles, phone charging)
- Regulatory compliance per division (FAA / FCC / wireless mesh regs)

## North-star advance (EXPANSION LADDER)

When idle (canonical-19):
1. **Car (Sinister Mobile) P1 prep** — surface what operator needs to greenlight P1
2. **Drone (Sinister Drone) D1 readiness** — Eve@drone mesh handshake design
3. **Mesh topology** — finalize WireGuard config that hands off mid-sentence across car↔home↔phone
4. **Vision pipeline shared spec** — write the Frigate+YOLOv8 contract so Car/Drone/JOKR-Global all conform
5. **Brain capture** — any cross-body pattern → brain entry under `_shared-memory/knowledge/`

## Reference

- `_shared-memory/MASTER-PLAN.md` (Sanctum-side strategic queue)
- `_shared-memory/knowledge/keep-working-until-done.md`
- `_shared-memory/knowledge/full-automation-north-star.md`
- `_shared-memory/AGENT-ROSTER.md`
