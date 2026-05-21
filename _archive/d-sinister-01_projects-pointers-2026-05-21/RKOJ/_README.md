# RKOJ — Operational / Mobile Division

**RKOJ** is JOKR backwards — the mirror division. Where JOKR holds the home and static stack, RKOJ holds everything that moves: the car, the phone, the drone network, the personal mobile mesh, and the integration glue that ties it all back to Eve and JOKR.

## What lives in RKOJ

| Project | Role | Memory shard | Status |
|---|---|---|---|
| **Sinister Mobile** | 2022 Dodge Challenger, ghost-mode rolling fortress | `01_MEMORY/sinister-mobile/` | P0 complete, awaiting operator P1 greenlight |
| **Sinister Drone** | FPV → autonomous → mesh swarm fleet | `01_MEMORY/sinister-drone/` | D0 (operator Part 107 + first FPV) |
| **Sinister Phone** | Ghost-mode operator pocket peer | (P7, not yet bootstrapped) | parked until P6 mesh stable |
| **Eve-Mobile** | Eve runtime across car + drone + phone (shares JOKR's Eve brain) | embedded in each project | designed |

## The unifying contract

1. **One Eve, three bodies.** Eve@home (JOKR), Eve@car (Sinister Mobile), Eve@drone — all share state over WireGuard mesh. Handoffs are mid-sentence, not session-boundary.
2. **One vision pipeline.** Frigate + YOLOv8 (or Jetson DeepStream) runs the same models for home cams, cabin cam, and drone cams. Threat alerts ladder up the same channel.
3. **One mesh.** WireGuard from car ↔ home ↔ phone ↔ drones. Multi-SIM bonded uplink. AdGuard DNS in the trunk router. Egress topology operator-chosen ("Eve, route through home").
4. **One aesthetic.** Sinister Clash palette (crimson primary + iris secondary + wine bridge + ink/bone scaffolding). James-Bond-gothic. Shipped on JOKR round-11 (2026-05-19), inherited by every RKOJ surface.
5. **One legal posture.** Detection only — no jamming, no surveillance of non-consenting people, no CAN-bus writes to ECU/steering/brake, no weaponized drones. Failsafe everywhere (operator never locked out of car; drone always knows return-to-home).

## Obsidian vault

`_vault/` — open `_index.md` first.

The vault is the operator's mental map of the division. Per-project memory shards (in `D:\Sinister\Sinister Skills\01_MEMORY\<project>\`) are the agent's working memory — independent + scriptable. The Obsidian vault is operator-facing, prose-first, hand-edited.

Both layers stay in sync via `refresh.ps1` (hub-level) and per-project session logs.

## Cross-project links

- **JOKR Global** — home/static parent. `C:\Users\Zonia\Desktop\JOKR-Global\`. Cabin UI sub-routes at `app/housing/<vehicle-id>/cabin/`. Theme + Eve + auth come from here.
- **Sinister Skills hub** — `D:\Sinister\Sinister Skills\`. Hub-level memory + MCP inventory + master plan.
- **Library of Alexandria** — `D:\Sinister\`. The drive itself.
- **Kernel-SU-Setup / Sinister-Detector** — phone-side ghost-mode patterns to carry into Sinister Phone (P7).
