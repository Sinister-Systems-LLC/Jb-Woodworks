# Sinister Mesh OS — Master Plan

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Plan ID:** `sinister-os/mesh-os-master-plan-2026-05-24`
> **Supersedes:** `master-plan-2026-05-24.md` (the single-machine OS plan). That plan's content is still valid for the per-host install layer; this document layers the **mesh** + **central FS** + **multi-dev collaboration** + **multi-account orchestration** + **dashboard** requirements on top.
> **Status:** P0 (spec) shipped this turn; foundational docker stack (P1.0) shipped this turn — verifiable via `docker compose up`.

---

## 0. Operator directives (verbatim 2026-05-24)

Two stacked directives:

> "I want a file system as well and a multi system approach to this so that the main OS will have a dashboard style management where i can see my other servers. see my agents phones connected per pc things like that. MAIN THING i need is the file system from sinister vault so that we can get off github and main goal is to have the agents be able to talk to each other and work as a mesh network between systems and have the ability to have 2 devs work on the project at once in similar areas and not over ride anything that each other do and the agents compound and build off each other etc. and all files are in a central self hosted location. make sure have this and all our system embedded. create a plan to complete all of this and get to work . install and open in docker for me. you have complete control"

> "i also need the multi claude account support and round robin system, etc. and the swarm and all memory we have etc. review all quantum tools and such and see what you can add from that"

## 1. The shape of Sinister Mesh OS

```
                     ╔════════════════════════════════════════════╗
                     ║         SINISTER MESH OVERLAY              ║
                     ║   (NATS pub/sub + Yjs CRDT + Tailscale)    ║
                     ╚════════════════════════════════════════════╝
                                    ▲     ▲     ▲
            ┌──────────────────────┘     │     └──────────────────────┐
            ▼                              ▼                              ▼
  ┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
  │   OPERATOR PC    │         │     LEO PC       │         │   PHONE (APK)    │
  │  (Sinister OS)   │         │  (Sinister OS    │         │  (sinister-eve   │
  │                  │         │   or Linux+vault)│         │   Android stub)  │
  ├──────────────────┤         ├──────────────────┤         ├──────────────────┤
  │ Panel (kiosk)    │         │ Panel (kiosk)    │         │ EVE app          │
  │ EVE daemon       │         │ EVE daemon       │         │ EVE socket relay │
  │ sinister-bus     │◄────────►│ sinister-bus    │◄────────►│ sinister-bus    │
  │ Vault node       │◄────────►│ Vault node      │◄────────►│ (read-only edge)│
  │ Ollama (local)   │         │ Ollama (local)   │         │ Mesh client only │
  │ Gitea            │         │ Gitea replica    │         │                  │
  │ Syncthing        │◄────────►│ Syncthing       │◄────────►│ Syncthing-Lite  │
  │ NATS node        │◄────────►│ NATS node       │◄────────►│ NATS client     │
  │ Yjs ws-server    │◄────────►│ Yjs ws-server   │         │                  │
  └──────────────────┘         └──────────────────┘         └──────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           ▼
                  ┌──────────────────┐
                  │  CENTRAL VAULT   │
                  │ (self-hosted, on │
                  │  operator's      │
                  │  always-on box)  │
                  │ Gitea = primary  │
                  │ Syncthing hub    │
                  │ Audit log writer │
                  │ Backup daemon    │
                  └──────────────────┘
```

**The five mesh services (run on every node):**

| Service | Tech | Purpose |
|---|---|---|
| **Vault filesystem** | Syncthing + Gitea + audit-daemon | Files replicated across all nodes; Gitea replaces GitHub for code repos; audit log captures every change |
| **Mesh bus** | NATS JetStream | Cross-node pub/sub for agent-to-agent messages, heartbeats, inbox routing |
| **CRDT relay** | Yjs websocket server | Two devs can edit the same file simultaneously; merge happens automatically without git conflict |
| **Local LLM** | Ollama | Every node runs its own model substrate so EVE works offline + cheap |
| **Mesh dashboard** | Sinister Panel | Each node renders the same dashboard; "Mesh" tab shows every connected node + their agents + their phones |

## 2. The "two devs can't override each other" problem

Git is wrong for live collaboration. Two devs editing the same file produces a merge conflict the loser has to resolve manually. CRDT (Conflict-free Replicated Data Type) is the right answer.

**Approach:**

- **Source files** stay in Gitea (git semantics for branching, releases, history). Two devs working on *different* files = git is fine.
- **Live collaborative areas** (PROGRESS files, design docs, inbox messages, plans, brain entries, the `_shared-memory/` tree) are mirrored into a **Yjs document** that the panel's editor opens via websocket. Yjs handles concurrent edits at character-resolution.
- **Sync direction**: when a Yjs doc is `quiesced` (no edits for 30 s), the Yjs daemon writes the merged state back to the file on disk and commits to Gitea with author = whoever was editing most recently.
- **Source-code editing** (TypeScript, Rust, Python, etc.) stays in editor + git; CRDT is for markdown + JSONL + the operator-visible coordination surface.

**This solves operator's exact problem:** Leo and Zonia can both type into `_shared-memory/PROGRESS/Sinister Sanctum.md` at the same time; their edits merge in real-time inside the Panel; the daemon commits once they're both done.

## 3. The "agents compound and build off each other" problem

Three things have to be true for agents to compound:

1. **Shared memory across machines.** An agent on Leo's PC needs to know what the operator's RKOJ lane just shipped. Solution: Syncthing replicates `_shared-memory/` between every Vault node. Reads are instant from local disk; writes propagate within ~1-5 s.
2. **Cross-machine inbox routing.** When Sanctum on operator's PC writes `inbox/forge/<msg>.json`, the forge agent on operator's PC reads it directly. When Sanctum writes `inbox/leo-rkoj/<msg>.json`, the message has to land on Leo's machine. Solution: NATS subject `sinister.inbox.<lane>.*` published on any node; subscribers on the target node pick up.
3. **Lane discipline across machines.** Two agents in the same lane on different machines could race. Solution: NATS distributed lock (`sinister.lane.<name>.holder`) — first to claim wins, others queue. Extends existing local lane discipline (canonical-10).

## 4. Multi Claude account support + round-robin

**Already exists:** `_shared-memory/claude-accounts.json` (v2, 4-slot, round-robin strategy, max_concurrent_global = 8). Currently per-machine.

**Mesh extension:**

- Account state (`current_sessions`, `last_spawn_at_utc`, `rate_limited_until_utc`) lives in the central Vault as `vault/state/claude-accounts.json`.
- Each node holds a read replica; writes go through a NATS request-reply pattern (`sinister.accounts.claim` → returns which account to use).
- Round-robin happens at the mesh level: an operator-PC spawn + a Leo-PC spawn + a phone spawn all share the same per-account quota and don't double-claim.
- Per-account credentials stay on each operator's machine (NEVER replicated; lane discipline). The mesh only coordinates "which account this spawn should use", not the secrets.

**New tool to ship:** `tools/sinister-mesh-accounts/` — Python module + MCP exposing `claim()` / `release()` / `status()` over NATS.

## 5. Swarm mode + all memory integration

**Existing swarm:** `tools/sinister-swarm/` + `/loop` mode. Per-machine.

**Mesh extension:**

- Swarm coordinator promotes one node to "swarm leader" via NATS Raft election (or simpler: lowest mesh-node-id wins).
- Leader holds the task queue; workers across all nodes pull from `sinister.swarm.tasks.*`.
- Memory shared: brain (`_shared-memory/knowledge/`), resume-points, PROGRESS, inbox all replicate via Syncthing.
- Brain-recall is a NATS request-reply: `sinister.brain.recall` → returns top-K from local Vault's brain index (every node maintains the same index via Syncthing).

## 6. Phased delivery for the mesh layer

| Phase | Deliverable | Status |
|---|---|---|
| **M0** | Spec + docker stack scaffold (this plan + docker-compose.yml) | ✅ Shipped 2026-05-24 |
| **M1** | Docker stack runs locally on operator's PC; all 5 services healthy | 🟡 Shipping this turn (smoke-test in progress) |
| **M2** | Single-node Mesh OS ISO builds with all 5 services systemd-enabled | ⏳ Operator-gated; opens after M1 verified |
| **M3** | Second node added (Leo's PC); Syncthing pairs; Gitea mirrors; NATS clustered | ⏳ Operator-gated |
| **M4** | CRDT (Yjs) editing live in Panel; two browsers on same file = real-time merge | ⏳ Operator-gated |
| **M5** | Phone (sinister-kernel-apk) joins as edge node (read-only Vault, NATS subscriber, EVE socket relay) | ⏳ Operator-gated |
| **M6** | Multi-account round-robin extended to mesh; quota arbitrage across nodes | ⏳ Operator-gated |
| **M7** | Swarm leader election + cross-node task dispatch | ⏳ Operator-gated |
| **M8** | Cut over from GitHub: all repos mirrored to mesh Gitea; GitHub becomes archive-only | ⏳ Operator-gated |

## 7. Docker stack composition (M1 — shipping this turn)

```yaml
services:
  gitea:         # self-hosted git, replaces GitHub
  syncthing:     # file replication
  nats:          # mesh pub/sub
  yjs:           # CRDT websocket
  ollama:        # local LLM
  panel:         # Next.js dashboard kiosk surface
  vault-api:     # HTTP wrapper around the file tree (existing sinister-vault daemon)
```

Stack lives at `projects/sinister-os/source/docker-stack/docker-compose.yml`. One command brings it up: `docker compose up -d`.

## 8. Dashboard "Mesh" tab spec

A new top-level Panel route `/mesh` that shows:

| Section | Source |
|---|---|
| **Connected nodes** | NATS subject `sinister.mesh.heartbeat` (every node beats every 10 s) |
| **Per-node agents** | NATS subject `sinister.agent.heartbeat` (every agent beats every 60 s) |
| **Per-node phones** | sinister-kernel-apk publishes to `sinister.device.phone.heartbeat` |
| **Live activity feed** | NATS subject `sinister.activity.*` (cards similar to existing Panel "Live activity") |
| **File-tree latency** | Syncthing API: per-folder out-of-sync byte count |
| **Account quota** | `sinister.accounts.status` request-reply |
| **Inbox routing** | Per-lane inbox depth from local Vault read |

**Wiring:** Panel adds a Next.js API route `/api/mesh/status` that hits the local NATS + Vault + Syncthing APIs and returns JSON; React component renders.

## 9. Embedded fleet systems checklist

Every existing Sinister system that becomes a first-class mesh citizen:

| System | Integration |
|---|---|
| Sinister Sanctum | The mesh root; ships as `/srv/sinister/sanctum/` on every node, Syncthing-replicated |
| Sinister Vault | The mesh filesystem layer (this plan = the answer to "make it the FS") |
| Sinister Bus (MCP) | Already the local message bus; NATS extends it across nodes |
| Sinister Bots (13 MCPs) | Run per-node as systemd services; brain index Syncthing-replicated |
| Sinister Panel | The dashboard rendered as the OS shell on every node |
| Sinister Forge | Desktop launcher; tray on every node |
| Sinister Mind | Per-operator service; not mesh-replicated |
| Sinister Generator | Per-node image gen (cost cap); shared output dir in Vault |
| Sinister Kernel APK | Phone client; subscribes to NATS as edge node |
| Sinister Term | Per-node terminal multiplexer |
| Sinister Snap/TikTok/Bumble emulators | Per-node services; outputs land in shared Vault |
| Sinister Letstext | Branded UI variant for OS-shell rebrand |
| Sinister JOKR | Per-operator app; mesh sees activity, not creds |
| Sinister Freeze (Joe) | External-collaborator lane on its own node |
| Sinister Mesh (NEW) | The mesh control plane shipped by this plan |

## 10. Open questions for operator (mesh review)

| # | Question | Default |
|---|---|---|
| M-Q1 | Central Vault host — operator's main PC, or a dedicated always-on machine (mini-PC, NAS, Pi)? | Main PC for M1-M2; dedicated always-on box for M3+ |
| M-Q2 | Tailscale or self-hosted WireGuard for the mesh overlay network? | Tailscale (zero config, free for personal) |
| M-Q3 | Gitea or Forgejo (Gitea fork)? | Gitea (more battle-tested) |
| M-Q4 | Push existing GitHub repos to mesh Gitea as M0 sanity check, or wait until M3? | Wait until M3 (avoid double-push window) |
| M-Q5 | Per-phone agent or one shared phone EVE? | Per-phone (each phone has its own EVE identity) |
| M-Q6 | Backup strategy: local snapper + offsite restic to operator's backup target? | Yes, both |
| M-Q7 | Encryption at rest for Vault? | Yes (LUKS2 on the Vault disk) |
| M-Q8 | Make M2 ISO available to Leo before M3? | Yes — Leo can build single-node OS while operator does the mesh setup |

## 11. Risks

| Risk | Mitigation |
|---|---|
| Gitea is now the single point of code-loss if Vault disk dies | Syncthing replicates Gitea data dir to every other Vault node + restic offsite |
| NATS jetstream cluster split-brain | Run NATS with cluster=3+ nodes; require quorum for writes |
| Yjs CRDT can't represent every file format (binary, lockfile) | CRDT applied only to markdown/text/JSONL; binaries stay in Gitea |
| Tailscale auth-key rotation | Mesh-bootstrap script handles rotation; doc at `docs/tailscale-bootstrap.md` (P-M3) |
| Operator's existing GitHub workflows break after M8 | Keep GitHub as read-only mirror; CI continues to work |

## 11.5 Extended scope (operator directive 2026-05-24 mid-turn)

Operator added during the M1 build:

> "review everything i use and would need in the custom os. like folder system with viewer like this the niri workstation thing. everything we need. i also need our communications systems baked in so i can self host that and talk between servers etc. i want our own things like anydesk so i can login to server from anywhere and i want the sinister mobile app so i can use that for chatting to people and to login to servers from and talk to my claude agents from my phone fully. complete all of this test it and let me know once ready. all needs to have the exact sinister panel theme"

Decoded into modules:

| Module | What | How (concrete tech) | Phase |
|---|---|---|---|
| **M-Files** | File system viewer (NIRI-workstation style) inside the Panel | `filebrowser` container at :8090 (added M1), embedded as iframe in Panel `/files` tab. Sinister-themed CSS overlay added M2. | M1 (ships); M2 themes |
| **M-Chat** | Self-hosted comms between operator + Leo + future collaborators | Rocket.Chat at :8050 (added M1) federated across mesh Vault nodes; mobile via Rocket.Chat React Native client; Panel `/chat` tab embeds. | M1 (ships); M3 federates |
| **M-Remote** | "Sinister AnyDesk" — login to server from anywhere | Apache Guacamole at :8060 (added M1): RDP/SSH/VNC through the browser, no client install. Plus WireGuard tunnel for raw SSH from phone. | M1 (ships); M5 phone-side |
| **M-Mobile** | Sinister mobile app: chat people + login servers + talk to EVE | Built on existing `projects/sinister-kernel-apk/` Android stub. Adds: Rocket.Chat client embed, Guacamole webview, Claude API client tied to fleet account round-robin. | M5 |
| **M-Workspace** | NIRI workstation feel — scrollable workspaces, column tiling | Hyprland on the OS already provides; M2 adds the Panel-as-shell `/desktop` view with workspace switcher matching NIRI's scroll-tile UX | M2 |

### Operator's full daily-driver feature inventory (audit for OS readiness)

Based on the workstation's current usage + the inferred Windows feature list:

| Feature | Sinister OS path | Status |
|---|---|---|
| Web browser | Chromium + LibreWolf in packages.x86_64 | ✅ baked |
| Steam + games | `steam` `gamemode` `mangohud` `wine-staging` `lutris` in packages.x86_64 | ✅ packages baked; runtime verification = P4 |
| Discord-equivalent | Rocket.Chat M-Chat | ✅ M1 |
| File explorer | Filebrowser M-Files + Hyprland file mgr `nautilus` (add to packages.x86_64 P2) | ✅ M1 web + P2 native |
| Remote desktop | Guacamole M-Remote | ✅ M1 |
| Video player | `mpv` in packages.x86_64 | ✅ baked |
| Image viewer | `imv` in packages.x86_64 | ✅ baked |
| OBS / capture | `obs-studio` add P2 | ⏳ P2 |
| DaVinci Resolve / video edit | `kdenlive` (native) + DaVinci via Wine (operator confirms?) | ⏳ P2 |
| FL Studio / DAW | Existing FL via Wine + native `ardour` / `bitwig-studio` (purchase) | ⏳ P2 + operator |
| Photo edit | `gimp` + `darktable` add P2 | ⏳ P2 |
| Office docs | `libreoffice-fresh` add P2 | ⏳ P2 |
| Dev IDE | `code` (VS Code), `neovim`, `git`, full toolchain — neovim+git baked, `code` add P2 | 🟡 partial |
| Container dev | Docker (already used to build the ISO), `podman`, `lazydocker` add P2 | ⏳ P2 |
| Local LLM | `ollama` baked + containerized | ✅ M1 + baked |
| Voice control | `tools/sinister-voice` (existing) + Whisper local | ⏳ P3 (EVE daemon) |
| Hotkey overlay | `eve-overlay` GTK4 | ⏳ P3 |
| Password manager | `keepassxc` add P2 | ⏳ P2 |
| Vault sync (this device's files visible everywhere) | Syncthing baked | ✅ M1 |
| Self-hosted git | Gitea baked | ✅ M1 |
| Calendar / mail | `thunderbird` add P2 | ⏳ P2 |
| Music | `spotify-launcher` (AUR) + `mpd` + `ncmpcpp` add P2 | ⏳ P2 |
| Screenshot + screen-record | `grim` `slurp` `wf-recorder` for Wayland; add P2 | ⏳ P2 |
| Clipboard manager | `cliphist` add P2 | ⏳ P2 |
| System monitor | `btop` + Panel `/system` tab | ⏳ P2 |

### Sinister theme compliance

Every web-facing service in this stack must render in Sinister purple (`#0e0a1f` background / `#c084fc` accent / `#e9d5ff` text). Strategy:

- **Panel** (Next.js + Tailwind 4) — already correct, the operator's screenshot is the canon.
- **Filebrowser** — supports custom CSS via `branding.files` config; M2 adds `config/filebrowser/sinister.css`.
- **Rocket.Chat** — admin > Layout > Custom CSS; M2 ships `config/rocketchat/sinister.css`.
- **Guacamole** — themable via `guacamole.properties` + custom skin JAR; M2 ships skin.
- **Gitea** — theme via `app.ini` + custom CSS; M2 ships `config/gitea/templates/sinister.css`.
- **Syncthing** — limited theme support; M2 either reverse-proxies behind a Sinister-styled wrapper or accepts default chrome (low-frequency UI).

All theming work scheduled as one consolidated M2 task: `docs/sinister-theme-pack.md`.

## 12. Done-criteria for THIS turn (M0 + M1 scaffold)

- ✅ This plan committed.
- ✅ `source/docker-stack/docker-compose.yml` written and parse-clean (`docker compose config` exits 0).
- 🟡 `docker compose up -d` brings up all 7 services; `docker compose ps` shows each healthy.
- 🟡 `curl http://127.0.0.1:3000` (Gitea) returns 200.
- 🟡 `curl http://127.0.0.1:8384` (Syncthing) returns 200.
- 🟡 `curl http://127.0.0.1:8222` (NATS monitor) returns 200.
- 🟡 `curl http://127.0.0.1:1234` (Yjs) returns websocket-upgrade.
- 🟡 `curl http://127.0.0.1:11434` (Ollama) returns 200.

Promoted to ✅ on successful smoke-test.
