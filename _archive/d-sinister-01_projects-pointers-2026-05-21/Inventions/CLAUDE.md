> **Author:** Sinister Sanctum master agent (test, Claude) :: 2026-05-20
> **Project:** Inventions — master view across operator's invention buildouts
> **Launcher:** `C:\Users\Zonia\Desktop\Start-Sinister-Personal-Session.bat` → pick `Inventions` (default)

# CLAUDE.md — Inventions (master view)

The Inventions hub is the **single Claude session** that owns the operator's five active invention buildouts as one coordinated portfolio. Per operator 2026-05-20: *"combine all things into inventions, eve, car etc will all be in inventions setcion"*. This hub does NOT duplicate project files — it is the **navigation + cross-cutting doctrine** layer. Each invention keeps its own folder + CLAUDE.md + SESSION-START.md for focused work.

## The five inventions

| Invention | Folder | Role | Focused doc |
|---|---|---|---|
| **Eve** | `D:\Sinister\01_Projects\EVE\` | operator personal-assistant MCP (eve-mcp; 51 tools — memory / schedule / watch / alerts; runs across home + car + drone bodies) | `D:\Sinister\01_Projects\EVE\CLAUDE.md` |
| **Car (Sinister Mobile)** | `D:\Sinister\01_Projects\RKOJ\Sinister-Mobile\` | 2022 Dodge Challenger ghost-mode platform — Jetson Orin NX + Pi 5 failover; cabin cam (Frigate+YOLOv8); Peplink bonded uplink; SDR + LIDAR + KrakenSDR threat scan; InsightFace + SpeechBrain biometric ignition | `D:\Sinister\01_Projects\RKOJ\Sinister-Mobile\CLAUDE.md` |
| **Drone (Sinister Drone)** | `D:\Sinister\01_Projects\RKOJ\Sinister-Drone\` | D0→D8 phase ladder — DJI Avata 2 FPV → Pixhawk + Jetson Nano → OAK-D YOLOv8 vision → Meshtastic swarm → solar hangar → car launch pad → 30-drone tiers → DroneID counter-drone detection | `D:\Sinister\01_Projects\RKOJ\Sinister-Drone\CLAUDE.md` |
| **RKOJ-personal** | `D:\Sinister\01_Projects\RKOJ\` | the operational / mobile division parent — contract layer that ties Car + Drone + future Phone (P7) + Eve into one mesh + one vision pipeline + one aesthetic + one legal posture | `D:\Sinister\01_Projects\RKOJ\CLAUDE.md` |
| **Cell-Network** | `D:\Sinister\01_Projects\Cell-Network\` | multi-SIM bonded uplink (Peplink MAX BR2 Pro 5G) + AdGuard DNS + WireGuard mesh — the connectivity layer every body rides on | `D:\Sinister\01_Projects\Cell-Network\CLAUDE.md` |

## Why this hub exists

The five inventions ARE one system at runtime — Eve@home talks to Eve@car talks to Eve@drone over the WireGuard mesh that Cell-Network manages, all sharing the same Frigate+YOLOv8 model registry, all bound by the same legal posture. Treating them as 5 separate Claude sessions led to context fragmentation. One session that knows ALL five = the master view operator asked for.

## When to spawn a focused session instead

The hub is the default. Spawn a focused per-invention session from the picker (multi-select on first screen, e.g. type the project number) when:
- The work is deeply within ONE invention (e.g. Drone D1 build BOM iteration)
- The blast radius is invention-local (e.g. Eve memory-schema refactor)
- The operator explicitly says "focus on X"

Otherwise: stay in the Inventions hub. Switch contexts by changing your TaskList in_progress entry, not by spawning new sessions.

## Cold-start in 7 steps (canonical-19 keep-working-until-done)

1. **This file** + **`SESSION-START.md`** for the current cross-invention state.
2. **`_shared-memory/knowledge/personal-fleet-research-map.md`** — the canonical research index across all 5 inventions (operator `_vault/*.md` paths + cross-project shared contracts).
3. **`_shared-memory/knowledge/agents-never-stop-no-bat-deferral.md`** — the 4-contract doctrine for never-stop + no-bat-deferral.
4. **Per-invention CLAUDE.md files** — read whichever inventions you're going to touch this session.
5. **Operator's `_vault/` notes** (HIGHEST SIGNAL — Obsidian-curated):
   - `D:\Sinister\01_Projects\RKOJ\_vault\Car.md` · `Drone.md` · `EVE.md` · `EVE-Wiring.md` · `Mesh.md` · `Frigate.md` · `Hardware-BOM.md` · `RKOJ.md` · `Roadmap.md` · `Home-Stack.md` · `CarPlay Hack.md` · `Door-Locks.md`
6. **PROGRESS log** — `D:\Sinister Sanctum\_shared-memory\PROGRESS\inventions.md` (create on first append).
7. **MASTER-PLAN.md** Sanctum-side for any cross-fleet directives.

## The shared contracts (what binds the 5 inventions together)

These contracts are the reason the hub exists. Changes to any contract impact multiple inventions; coordinate cross-invention before editing.

| Contract | Producer | Consumers |
|---|---|---|
| **Frigate + YOLOv8 model registry** | JOKR (home; out of Inventions but tightly coupled) | Eve@home, Car cabin_car, Drone OAK-D |
| **WireGuard mesh topology** | RKOJ-personal (designer) | Car / Drone / Phone-P7 peers; Cell-Network is the transport |
| **MQTT topic structure** | Eve (`EVE-Wiring.md`) | every invention produces + consumes |
| **Threat-tier 5-ladder** | JOKR `Frigate.md` | Eve@home (escalation), Eve@car (voice alert + SDR scan), Eve@drone (hangar auto-launch) |
| **Egress topology selector** (`Eve, route through home`) | Eve dispatch | Cell-Network (executes route swap) |
| **51-tool MCP surface** | Eve (eve-mcp) | every body |
| **Legal posture** (detection-only + no surveillance of non-consenting + no weaponization + always-RTH) | Operator policy | every invention — non-negotiable |

## What this agent owns (Inventions hub)

- This hub folder + CLAUDE.md + SESSION-START.md
- Cross-invention coordination (contract changes, shared model updates, mesh topology revisions)
- The portfolio-level EXPANSION LADDER below

## What this agent NEVER touches

- JOKR (home / static stack) — separate session lane via the launcher's `JOKR` picker entry
- LetsText — separate session lane via `LetsText` picker entry
- `D:\Sinister Sanctum\` master-lane code — Sanctum master owns
- `~/.claude/.mcp.json` — operator-owned trust root
- Anything that violates the legal posture (no weaponization, no non-consenting surveillance, no CAN-bus writes, no autonomous-flight-without-greenlight)

## Tools every Inventions turn must do (canonical-9)

- Heartbeat fallback `D:\Sinister Sanctum\_shared-memory\heartbeats\inventions.json`
- Inbox poll `D:\Sinister Sanctum\_shared-memory\inbox\inventions\`
- Append milestones to `D:\Sinister Sanctum\_shared-memory\PROGRESS\inventions.md`
- Per-agent branch `agent/inventions/<topic>`
- Authorship line on every new .bat / .md / .ps1

## North-star advance (EXPANSION LADDER — portfolio level)

When idle (canonical-19 says idle = bug), the cross-invention slices in priority:

1. **Mesh + uplink ready** (Cell-Network) — pick the travel router model + SIM matrix; nothing downstream can finalize without this concrete reference
2. **Eve@body bootstrap spec** — write the per-body onboarding flow (Eve@car cold-start, Eve@drone cold-start) — unblocks both Car P1 and Drone D1
3. **Shared vision pipeline contract** — formalize Frigate+YOLOv8 model contract so JOKR + Car + Drone all conform (model registry, version bumps, alert ladder)
4. **Failsafe + RTH formal spec** — Drone-side full RTL ladder + Car-side override priority — non-negotiable safety layer
5. **Eve memory persistence across bodies** — home → car → phone → home session continuity (the "one Eve, three bodies" promise)
6. **Threat-tier 5-ladder formalization** — uniform escalation across cam streams (home / cabin / drone) → Eve → alert channel
7. **Brain capture** — patterns from one invention that other inventions could reuse → write a brain entry under `_shared-memory/knowledge/`

When all 7 portfolio slices are covered: drop into the invention-specific EXPANSION LADDERs in each per-invention CLAUDE.md.

## Reference

- `D:\Sinister Sanctum\_shared-memory\knowledge\personal-fleet-research-map.md` — the canonical research index
- `D:\Sinister Sanctum\_shared-memory\knowledge\agents-never-stop-no-bat-deferral.md` — the 4-contract doctrine
- `D:\Sinister Sanctum\_shared-memory\knowledge\keep-working-until-done.md` — canonical-19
- `D:\Sinister Sanctum\_shared-memory\knowledge\full-automation-north-star.md` — the goal
- `D:\Sinister Sanctum\_shared-memory\AGENT-ROSTER.md` — fleet map (who owns what)
- Sister lanes: `D:\Sinister\01_Projects\JOKR\CLAUDE.md` (home) · `D:\LetsText\CLAUDE.md` (compliance SMS)
