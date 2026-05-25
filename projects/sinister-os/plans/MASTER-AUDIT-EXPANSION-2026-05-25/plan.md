# Sinister OS — MASTER AUDIT + EXPANSION PLAN

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Plan ID:** `sinister-os/MASTER-AUDIT-EXPANSION-2026-05-25`
> **Operator directive (verbatim 2026-05-25 ~09:25Z):**
> *"create a plan to audit everything, expand things, test everything, complete everything that i said and all that shit and once you are ready for my viewing set it up on docker and we will test i will tell you what you change then you will put it live on my laptop. make sure it analyzes how much cpu, gpu to allocate in certain places. like on main pc i want to allow agents to use my gpu and its a intelligent system that balances its load with what it has to use based on what im using. then add a game mode toggle that i turn off when im ready to play a game then i wait like 5-10 minutes max for you to say safe to launch game. if you detect no activity or gaming for 30 minutes you can keep back to using what you need. think of many things like this and add everything that i use from my main pc and options you think i may want like the niri workstation. but def still want a desktop and a enhanced windows feel. hardened as fuck safe, anydesk, chat system all that shit from it. audit everything you need to do that we have planned to do and make sure its compiled all into one place. note in memory all agents can use expand tools and quantum tools as needed just be cautious on the seconds we use."*
> **Composes-with:** master-plan-2026-05-24.md (P0-P5 baseline) · mesh-os-master-plan-2026-05-24.md · sinister-os-massive-expansion-2026-05-24T2110Z (iters 8-15) · 3 design docs (state-machine + EVE-LLM bridge + sinister-voice 2026-05-25)
> **Operator-canonical compose:** "EVE-as-OS-shell" (CLAUDE.md sinister-os) · "I can still play games" · "hardened as fuck safe" · "no telemetry without opt-in" · "no gate questions, execute directly"

---

## 0. TL;DR

We have ~24 design/plan/doc artifacts across `plans/`, `docs/`, `docs/design/`, `research/`, `source/`. The system was designed across the baseline P0-P5 plan + the 2026-05-24 massive-expansion plan + last turn's design trilogy. This plan is the **one place** that audits all of it, decomposes the operator's 09:25Z directive into 12 work blocks (A-L), maps each block to existing artifacts vs new work, defines the Docker-test → laptop → main-PC rollout chain, and pins acceptance criteria.

**State summary:**
- **Design layer (P0-P3 docs):** ~90% complete. The trilogy from last turn (state-machine + EVE-LLM bridge + sinister-voice) locks the EVE control surfaces; we still need design docs for: GPU arbiter, game-mode subsystem, niri variant, RustDesk/Sunshine remote-access, hardening spec, hotkey-overlay GTK4 UX.
- **Build layer (iso-build / docker-stack / source):** ~25% complete. Docker overlays exist (8 compose files: dev / hardened / mesh / doh / wg-fallback / desktop / headless / panel-shell). ISO build scripts are scaffolded but not yet producing a bootable image.
- **Test layer:** docker-stack `validate-merge.sh` is the only smoke harness. No VM-boot test, no laptop test, no acceptance suite.
- **Rollout layer:** rollout-doctrine-2026-05-25.md defines P0a (docker) → P0b (laptop) → P0c (main PC) — but no execution receipts yet.

**Net:** the design is ready for Docker stand-up; build artifacts need the most work; tests need a harness; rollout needs receipts. The 12 work blocks below are ordered so the operator can review on Docker by **end of P0a** (~3 dev days of work), then iterate before laptop deploy.

---

## 1. AUDIT — every existing sinister-os artifact, classified

### 1.1 Plans (existing)

| Path | Date | Status | Notes |
|---|---|---|---|
| `plans/master-plan-2026-05-24.md` | 2026-05-24 | LOCKED (P0 done, P1-P5 awaits gate) | The canonical P0-P5 baseline. Sections 3-17 fully written. |
| `plans/mesh-os-master-plan-2026-05-24.md` | 2026-05-24 | LOCKED | Geo-mesh routing roadmap. Composes with `docs/geo-mesh-routing.md`. |
| `_shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md` | 2026-05-24 21:10Z | iters 8-15 SHIPPED to disk | The "operator interrupt 8-directive" plan. All 7 listed iters' files exist on disk. |
| `_shared-memory/plans/sinister-os-m5-expand-panel-shell-2026-05-24T2034Z/plan.md` | 2026-05-24 20:34Z | M5 SHIPPED | Panel-shell overlay (`compose.panel-shell.yml`) consumed. |
| THIS PLAN | 2026-05-25 | ACTIVE | The audit + expansion compile per operator 09:25Z. |

### 1.2 Docs (existing)

| Path | Status | Notes |
|---|---|---|
| `docs/architecture.md` | LOCKED | Layered system view (operator → compositor → eve daemon → kernel). |
| `docs/qol-features.md` | LOCKED | Hotkeys + niceties. Has slot for `Super+Shift+G` (game-mode) free. |
| `docs/proprietary-blobs.md` | LOCKED | NVIDIA / Steam / Proton / etc. AnyDesk row to be added (this plan). |
| `docs/ghost-server-hardening.md` | LOCKED | Hetzner panel hardening — translatable to OS workstation. |
| `docs/panel-as-os-shell.md` | LOCKED | Sinister-Panel as OS shell pattern. |
| `docs/geo-mesh-routing.md` | LOCKED | Layer-3 anonymity (`eve proxy`). |
| `docs/live-dev-workflow.md` | LOCKED | Dev-loop ergonomics. |
| `docs/pc-feature-audit.md` / `pc-feature-audit-2026-05-24-summary.md` | LOCKED | What the operator uses on Windows. **Critical input** for block A below. |
| `docs/variants-design-2026-05-24.md` | LOCKED | desktop / headless variants. Niri variant to be added (this plan). |
| `docs/rollout-doctrine-2026-05-24.md` + `-25.md` | LOCKED | P0a → P0b → P0c. |
| `docs/integration-phasing-2026-05-24.md` + `-25.md` | LOCKED | Bazzite / Hyprland / archiso / kiosk-linux integration. |
| `docs/no-function-loss-doctrine-2026-05-24.md` + `-25.md` | LOCKED | Every Windows feature → Linux replacement table. |
| `docs/design/sinister-eve-service-state-machine-2026-05-25.md` | LOCKED | EVE daemon typed-state-machine (iter 18). |

### 1.3 Designs landing THIS plan (research complete; docs to write below)

| Path (planned) | Lane (this plan block) | Source research |
|---|---|---|
| `docs/design/sinister-gpu-arbiter-2026-05-25.md` | Block C | sub-agent GPU research returned: cgroup.freeze + nvidia-smi -pl + MPS + gamemode D-Bus subscriber |
| `docs/design/game-mode-subsystem-2026-05-25.md` | Block D | sub-agent already wrote it (per agent return: ~1100 words at this path) — TO VERIFY ON DISK |
| `docs/design/niri-variant-2026-05-25.md` | Block E | sub-agent returned recommendation (b): parallel-installable second variant |
| `docs/design/remote-access-rustdesk-sunshine-2026-05-25.md` | Block F | sub-agent hardening research: RustDesk replaces AnyDesk by P5; Sunshine for gaming-stream-out |
| `docs/design/hardening-spec-2026-05-25.md` | Block G | sub-agent hardening research full spec: Secure Boot via sbctl, AppArmor (not SELinux), Flatpak Qubes-LITE, etc. |
| `docs/design/hotkey-overlay-gtk4-ux-2026-05-25.md` | Block H | covers wofi-style chat sheet + persona picker + system-status overlay from EVE-LLM bridge spec § 5.2 |
| `docs/design/windows-feel-desktop-2026-05-25.md` | Block I | "enhanced windows feel" — Cinnamon-like layout with KDE-Plasma if operator picks, or Hyprland-themed-to-feel-Windows |
| `docs/design/agent-cpu-budget-2026-05-25.md` | Block C2 | sister to GPU arbiter — cgroup CPU weights per agent slice |

### 1.4 Source code (existing skeletons)

| Path | Status | Lines / files | Notes |
|---|---|---|---|
| `source/docker-stack/` | SHIPPED, runnable | 9 compose overlays + `eve` CLI + `validate-merge.sh` + `smoke-test.sh` + `bake-panel.sh` | This is the Docker-test substrate per operator 09:25Z. |
| `source/eve-control/` | SCAFFOLDED (Rust target) | dir exists; no production code yet | Will host the Rust EVE daemon. |
| `source/eve-llm-bridge/SPEC-2026-05-25.md` | SHIPPED (design) | IPC contract | Iter 19 last turn. |
| `source/eve-os-integration/scaffold/sinister-eve-mcp-bridge.py` | SHIPPED (prototype) | ~500 LOC | Runnable on Linux dev VM. |
| `source/hot-reconfig/watcher/sinister-config-watcher.py` | SCAFFOLDED | ~120 LOC | Iter 10 of massive-expansion. |
| `source/iso-base/` + `source/iso-build/` + `source/iso-remaster/` | SCAFFOLDED | shell scripts | Not yet producing bootable ISO. |
| `source/sinister-control/` | SHIPPED (helpers) | `reboot-required.sh` + `reboot-banner-watch.sh` + `hot-reconfig-classifier.py` + README | Iter 10 of massive-expansion. |
| `source/sinister-lang/` | DESIGN-only | `DSL-DESIGN-2026-05-24.md` + `example.sin` | Janet+CUE deferred per agent A recommendation. |
| `source/sinister-overlay/` | SCAFFOLDED | dir exists | Reserved for hot-reconfig overlay output. |
| `source/branding/` | SCAFFOLDED | placeholder | Plymouth / SDDM / GRUB themes per master-plan § 5.2. |
| `source/vm-boot/` | SCAFFOLDED | placeholder | QEMU/KVM boot helpers. |

### 1.5 Research (returned this turn)

| Topic | Verdict | Where it lands |
|---|---|---|
| **niri compositor** | Ship as parallel-installable second variant (Hyprland stays default). Niri 26.04 in Arch `extra`, no HDR yet, NVIDIA "seems to work fine" with VRAM-quirk workaround, KDL config gives EVE clean parser. | Block E |
| **Intelligent GPU sharing** | Consumer RTX cards rule out MIG/DMEM cgroup/GOM. Practical path: cgroup.freeze + nvidia-smi -pl + MPS + gamemode D-Bus subscriber. Rust/Python daemon `sinister-gpu-arbiter.service`. ~600 LOC. | Block C |
| **Game-mode subsystem** | 7-state machine (DISARMED/ARMING/ARMED/GAMING/COOLDOWN/RESUMING/BLOCKED), 15-step prep sequence, 30s sustained convergence probe, 600s hard ceiling, per-game overrides in `/etc/sinister/game-mode.toml`. | Block D |
| **Hardened daily-driver** | Qubes-LITE via Flatpak/bwrap (not Xen/Qubes). sbctl Secure Boot + UKI + dm-verity-/usr (not /home) + AppArmor (not SELinux) + opensnitch + linux-cachyos lockdown=integrity + LUKS2-Argon2id+TPM2+YubiKey + nftables default-DROP + DoT + auditd + usbguard. **Drop AnyDesk for RustDesk by P5; add Sunshine+Moonlight for gaming-stream-out.** | Blocks F + G |

---

## 2. EXPANSION — operator's 09:25Z directive decomposed into 12 blocks (A-L)

| Block | Operator phrase → concrete deliverable | Owner | Phase |
|---|---|---|---|
| **A** | "everything that i use from my main pc" → Windows-feature parity gap-audit + completion plan | this plan + `pc-feature-audit*.md` + `no-function-loss-doctrine*.md` | P0 (audit) |
| **B** | "compiled all into one place" → THIS DOCUMENT is that one place. PROGRESS row + brain entry pin it. | this plan | P0 (compile) |
| **C** | "cpu / gpu to allocate" + "agents use my gpu" + "intelligent system that balances its load" → `sinister-gpu-arbiter.service` (research returned) + `agent-cpu-budget` cgroup slice | Block C design doc | P0a-P3 |
| **D** | "game mode toggle" + "5-10 min safe to launch" + "30 min idle resume" → `sinister-game-mode.service` (research returned) | Block D design doc | P0a-P3 |
| **E** | "options you think i may want like the niri workstation" → niri parallel variant | Block E design doc | P2 (variant ship) |
| **F** | "anydesk, chat system" → RustDesk (primary, FOSS), Sunshine+Moonlight (gaming-stream), AnyDesk retained until P5 then dropped. Chat system = EVE-LLM bridge (shipped iter 19) | Block F design doc | P2-P5 |
| **G** | "hardened as fuck safe" → sbctl + UKI + dm-verity-/usr + AppArmor + opensnitch + LUKS2+TPM2+YubiKey + nftables-DROP + DoT + auditd + usbguard (research returned) | Block G design doc | P1-P3 |
| **H** | "desktop and a enhanced windows feel" → `windows-feel-desktop` design (Cinnamon-as-default-pick OR Hyprland-themed-Windows-style); operator picks at SDDM | Block H design doc | P2 |
| **I** | "test everything" → P0a Docker acceptance harness (`source/docker-stack/acceptance/`) + P0b laptop VM smoke + P0c main-PC dual-boot smoke | Block I (test harness) | P0a-P0c |
| **J** | "set it up on docker and we will test" → run full stack via `docker compose ... up`, surface `https://localhost:8443/sinister-panel/` for operator review, expose `eve` CLI from inside container, expose all the new subsystems as compose services | Block J (Docker stand-up) | P0a |
| **K** | "put it live on my laptop" → P0b VM test on operator's laptop first; if green, sideload onto laptop bare metal via the existing `iso-build/` recovery USB path | Block K (laptop deploy) | P0b → laptop bare-metal |
| **L** | "all agents can use expand tools and quantum tools as needed just be cautious on the seconds we use" → brain entry + doctrine | Block L (brain entry) | P0 (memory write) |
| **M** | "agents have complete control of all things but we have failsafes ... all in containers. rate limit the agents if they do actions they should not" (operator utterance 09:36Z) → `sinister-agent-containment.service` + `sinister-agent-warden.service` + per-agent OCI containers + behavioral rate limiter + kill-switch | Block M (NEW design doc) | P1-P3 |
| **N** | "make sure all things like this come with us when we setup the OS and os installed and ready" (operator utterance 09:41Z) → every Sanctum fleet tool (Sinister Browser system / EVE.exe / eve-picker / sinister-term / panel / MCP bots / automation scripts / sinister-generator / sinister-memory / login-automation w/ auto-relogin + refresh + detection) ports to Sinister OS preinstalled. Includes operator state migration from Windows. | Block N (NEW design + manifest) | P1-P4 |

---

## 3. BLOCK-BY-BLOCK PLAN

### 3.1 Block A — Windows-parity gap audit (DEEP MERGE)

**Goal:** ensure operator loses no function he uses on Windows.

**Existing artifacts:**
- `docs/pc-feature-audit.md` (LOCKED)
- `docs/pc-feature-audit-2026-05-24-summary.md` (LOCKED)
- `docs/no-function-loss-doctrine-2026-05-24.md` + `-25.md` (LOCKED)
- `research/feature-parity-audit-2026-05-24.md` + `-25.md` (LOCKED)

**Gap to close THIS plan:** merge all 6 into a SINGLE canonical `docs/WINDOWS-PARITY-CANONICAL-2026-05-25.md`. Single-source-of-truth: every Windows feature/app/workflow → Linux replacement → status (PARITY / DEGRADED / GAP / N/A).

**This-plan deliverable:** Block A merge doc. ~150 rows.

### 3.2 Block B — One-place compile (THIS DOC)

**Goal:** operator can read ONE plan and know everything. PROGRESS row + brain entry pin THIS plan as the canonical entry-point for next 30 days of work.

**Deliverables:**
- THIS plan committed at `plans/MASTER-AUDIT-EXPANSION-2026-05-25/plan.md`
- PROGRESS row appended (most-recent at top)
- Brain entry: `_shared-memory/knowledge/sinister-os-master-audit-expansion-2026-05-25.md` + `_INDEX.md` row
- Next-30-days resume-points all point here.

### 3.3 Block C — `sinister-gpu-arbiter.service` (NEW design doc)

**Operator-canonical:** *"intelligent system that balances its load with what it has to use based on what im using"*

**Architecture** (from research returned):

```
sinister-gpu-arbiter.service (system, runs as eve user)
  UDS: /run/sinister/gpu-arbiter.sock (JSON-lines)

  Detectors (1Hz loop):
    - gamemode D-Bus subscriber  → state.foreground_gpu
    - nvidia-smi --query-compute-apps → state.client_pids[]
    - nvidia-smi --query-gpu=util,power → state.util_5s_avg
    - hypridle / loginctl IdleHint → state.user_idle_sec
    - pactl + hyprctl activewindow → state.call | fullscreen

  Policy engine (3 modes):
    YIELD   = foreground_gpu detected → freeze sinister-ai.slice + nvidia-smi -pl <low>
    HARVEST = idle 30min + util <5% → thaw slice + nvidia-smi -pl <max>
    SHARE   = default mixed-use → thaw slice + nvidia-smi -pl <mid>

  Client API (UDS):
    - request_gpu  { pid, vram_mb, priority }
    - release_gpu  { pid }
    - query_state  → { mode, util, foreground_gpu, ... }
    - subscribe    → push events on mode change
```

**Why this works on consumer RTX:**
- MIG / DMEM cgroup / GOM are enterprise-only (A100/H100). Skip.
- `cgroup.freeze` (cgroup v2) is kernel-supervised, <10ms, atomic. **PRIMARY throttle.**
- `nvidia-smi -pl <watts>` (root, survives until reboot). **SECONDARY** for graceful yield.
- MPS `CUDA_MPS_ACTIVE_THREAD_PERCENTAGE` for AI-only clients that opt in.
- `gamemoded` D-Bus signal (already exists in Arch) is the gold-standard "operator is gaming" trigger.

**systemd plumbing:**
- `sinister-ai.slice` (Delegate=cpu,memory,freezer)
- Every AI agent runs as `Slice=sinister-ai.slice` (ollama, sinister-generator-worker, whisper-local, eve-llm-bridge daemon, etc.)
- Polkit rule for `eve` to write `nvidia-smi -pl` (already in master-plan § 4.1)
- Hotkey `Super+Shift+G` toggles manual YIELD override (operator can force-yield when gamemode doesn't fire — e.g. video calls).

**Implementation:** Rust binary `sinister-gpu-arbiter` (~600 LOC). Python prototype first (`source/sinister-gpu-arbiter/prototype/`) so operator can boot CachyOS VM and curl-test before greenlighting Rust.

**Acceptance (P3):** `ollama run` at 100% util; launch Proton game via Steam → arbiter freezes slice within 500ms → game shows no frame dips beyond baseline → on game exit + 30min keyboard idle → slice thaws → inference resumes → `dmesg` zero CUDA "context lost".

### 3.4 Block D — `sinister-game-mode.service` (NEW design doc)

**Operator-canonical:** *"game mode toggle that i turn off when im ready to play a game then i wait like 5-10 minutes max for you to say safe to launch game ... if you detect no activity or gaming for 30 minutes you can keep back to using what you need"*

**State machine (7 states):**

```
                    operator toggle / voice / waybar
   DISARMED ─────────────────────────────────────────┐
       │                                             │
       │ operator: ARM                               │
       ▼                                             │
   ARMING (max 600s) ──────────► BLOCKED (failure surfaces blocker)
       │                                             │
       │ all 4 metrics converged 30s                 │
       ▼                                             │
   ARMED (waiting for game launch up to 4h)          │
       │                                             │
       │ game pid detected OR operator launch        │
       ▼                                             │
   GAMING (until exit + cooldown)                    │
       │                                             │
       │ game exit                                   │
       ▼                                             │
   COOLDOWN (3 min before resume detection starts)   │
       │                                             │
       │ resume conditions met                       │
       ▼                                             │
   RESUMING (gradual thaw)                           │
       │                                             │
       └──────────────► DISARMED ───────────────────┘
```

**15-step ARMING prep sequence** (each idempotent + reversible + receipt-logged):

1. Pause agent workloads via GPU arbiter `request_release` (block C)
2. Freeze `sinister-ai.slice` (cgroup.freeze=1) + freeze `sinister-utility.slice`
3. `sync; echo 3 > /proc/sys/vm/drop_caches`
4. Disable cron + at jobs for next 4h (`systemctl --now stop cronie atd`)
5. Stop background indexers: baloo / mlocate / file-watchers
6. Stop system-update daemons: pamac-daemon / packagekit
7. CPU governor → `performance` (all cores)
8. NVIDIA power state → P0 (`nvidia-smi -pm 1`, `-lgc`)
9. Disable compositor frame-pacing battery-saver
10. Set NVIDIA MSI mode + Game Mode via `__GL_*` driver knobs
11. Stop opt-out background services: Tailscale tray polling / OneDrive / AnyDesk listener (operator-listable in `game-mode.toml`)
12. PreEmpt kernel scheduler → game-friendly defaults
13. Auto-snapshot via snapper (rollback target if game CTDs the system)
14. Final convergence probe: GPU util <5% AND RAM free >8GB AND disk IO <5MB/s AND net RX/TX <1Mbps — sustained 30s
15. Emit `safe_to_launch` signal → TTS + waybar green + notification + audio chime

**While GAMING — guardrails:**
- No subprocess spawns from agents > N watts predicted GPU load
- No `eve` system control intents that touch active windows
- Voice surface auto-mutes (sinister-voice already wires this)
- No notifications except CRITICAL
- AnyDesk/RustDesk connections rejected until game exits (operator override available)

**30-min idle → RESUMING detection (composes with block C HARVEST):**
- All 3 conditions held for full 30 min: Steam not running OR no game in foreground + GPU util <5% sustained 30min + operator input present but in non-game window (`xdotool getactivewindow` WM_CLASS != game-list)
- Operator can `hold_until_unix` flag to STAY in game mode indefinitely.

**Failure modes (BLOCKED state):**
- ARMING didn't converge in 600s → surface specific blocker ("OBS recording, can't drop GPU"; "background pacman upgrade running")
- Operator can `force_launch` with polkit prompt — proceeds with degraded ARMED state.

**Config:** `/etc/sinister/game-mode.toml` — per-game overrides via `[games.overrides]` (e.g. CS2 = relax net for matchmaking; Factorio = unlock CPU-bound by not pinning GPU clocks).

**Implementation:** Python prototype (so operator can poke at it on Day 1), Rust production. Composes with `sinister-eve.service` typed-state-machine (uses `subscribe` topic + `denied` result code with new `reason` strings `game_mode_gpu_budget` / `game_mode_window_lock`).

**Acceptance:** 10 tests in VM with NVIDIA passthrough/vGPU stub; full reverse-symmetry diff (test #10) to prove DISARM restores prior state byte-for-byte.

### 3.5 Block E — niri variant (NEW design doc)

**Operator-canonical:** *"options you think i may want like the niri workstation"*

**Recommendation:** **parallel-installable second variant**, NOT default replacement.

**Rationale (from research):**
- Cost is low — both compositors share 90% of stack (waybar, mako, fuzzel, portals, PipeWire, xwayland-satellite, gamescope).
- Scrollable tiling fits agent-fleet / research / dashboard work the operator does daily — some sessions will want it.
- HDR gap matters for media/gaming → Hyprland stays for those.
- KDL config gives EVE a clean parser (vs Hyprland regex-patching).

**Concrete additions:**
- New § 5.1.5 in master-plan: "Alternate compositor: niri"
- `niri` + `xwayland-satellite` added to P2 package list
- `/usr/share/wayland-sessions/niri.desktop` from upstream
- `/etc/sinister/eve-overlay-niri.kdl` (niri-flavored `eve-overlay` window rule)
- SDDM dropdown: "Sinister OS (Hyprland)" / "Sinister OS (niri)"

**EVE shell integration:** ~50-100 LOC compositor-specific glue per variant. `hyprctl` calls become `niri msg` calls in a small wrapper. Waybar pill + wofi sheet + `eve chat` CLI work unchanged.

**Block E design doc captures:** install spec, KDL `binds {}` block, window rules for EVE overlay, niri-specific `mute_watch` event subscriptions for sinister-voice, gamescope integration recipe, NVIDIA workaround (`50-limit-free-buffer-pool-in-wayland-compositors.json`).

### 3.6 Block F — Remote access: RustDesk + Sunshine, drop AnyDesk by P5

**Operator-canonical:** *"anydesk, chat system all that shit from it"*

**Verdict (from hardening research):** ship all three initially; AnyDesk is closed-source with a 2024 incident — keep only until RustDesk + Sunshine are validated.

| Tool | Role | Phase | Notes |
|---|---|---|---|
| **RustDesk** | PRIMARY remote desktop | P3 (alongside AnyDesk) → P5 (drop AnyDesk) | FOSS, MIT, self-host relay (`hbbs` + `hbbr`) on Sanctum VPS, P2P fallback |
| **Sunshine + Moonlight** | PRIMARY gaming-stream-out (laptop → desktop) | P3 | NVENC, sub-frame latency, perfect for "play desktop games from laptop" |
| **Apache Guacamole** | Browser-access tier | already in ghost-server overlay | Operator-only browser remote |
| **AnyDesk** | LEGACY — operator-known habit | P3 → drop P5 | Closed-source; opensnitch monitors outbound and alerts on unknown ASNs |
| **xrdp** | SKIP | — | Wayland support poor, NVIDIA flicker |

**Chat system:** EVE-LLM bridge (shipped iter 19) IS the chat system. SPEC-2026-05-25.md § 4 defines `chat.send` / `chat.history` / `persona.list` / `persona.tweak` / `events.subscribe` JSON-RPC contract. UI surfaces (waybar pill / wofi sheet / `eve chat` CLI / mobile Compose tile) are spec'd; implementation lands at P3.

**Block F design doc:** RustDesk self-host recipe (hbbs/hbbr on Sanctum VPS at `rustdesk.sinijkr.com:21115-21119`), Sunshine systemd unit + Hyprland integration (gamescope nested for streaming), AnyDesk sunset checklist (apparmor profile lockdown, opensnitch outbound monitoring with ASN allowlist).

### 3.7 Block G — "hardened as fuck safe" spec (NEW design doc)

**Pattern:** **Qubes-LITE via Flatpak/bwrap.** NOT Xen/Qubes (operator vetoed; breaks GPU passthrough).

**Layered hardening (from research):**

1. **Boot integrity:** Secure Boot via sbctl with self-enrolled keys (`-m` keeps MS keys for dual-boot/Windows-VM firmware compat); UKI mandatory; auto-sign DKMS NVIDIA module via `/etc/dkms/sign_helper.sh` pacman hook.
2. **dm-verity:** `/usr` only (read-only root pattern). `/home` stays R/W (Steam writes constantly). A/B verity image swap on `pacman -Syu`.
3. **MAC:** AppArmor (NOT SELinux — breaks Steam/Proton/AUR). Profiles for `anydesk` / `discord` / `steam` (complain mode) / `firefox` (upstream).
4. **Sandboxing:** Default-sandbox Discord / Slack / Telegram / Signal / Element / Spotify / OBS / Chromium-stealth / AnyDesk via Flatpak (bwrap). Steam stays native (Proton+DXVK+GPU break under bwrap).
5. **Network:** nftables default-DROP inbound (except mDNS / DHCP / Tailscale / opt SSH). DNS-over-TLS via systemd-resolved → Quad9 + Cloudflare. Tailscale ACL with `tag:operator` / `tag:vault` / `tag:leo`. opensnitch per-app outbound prompts, pre-approved at install for Steam/Discord/Slack/AnyDesk/Tailscale/pacman.
6. **Anti-exfil:** auditd rules for `/usr` writes + `/tmp` execve + `/etc/sinister` changes. cliphist for Wayland clipboard (no X11 leak). xdg-desktop-portal-hyprland for screenshot/screencast chooser. usbguard default-block for mass-storage class (`08:*`).
7. **Kernel:** linux-cachyos WINS (hardened patches conflict with NVIDIA proprietary). `lockdown=integrity` (NOT `confidentiality` — kills `nvidia-smi`). sysctls: `kernel.kexec_load_disabled=1`, `kernel.yama.ptrace_scope=2`, `net.ipv4.tcp_syncookies=1`. KEEP `kernel.unprivileged_userns_clone=1` (Flatpak needs it).
8. **Disk:** LUKS2 + Argon2id (`--memory 1048576 --iter-time 5000`). TPM2 auto-unlock via `systemd-cryptenroll --tpm2-device=auto --tpm2-pwk-pcrs=0+7` (Secure Boot breach voids unlock). YubiKey FIDO2 second factor for operator-only tier (`/srv/sinister-vault-cold`). Auto-lock on suspend via hyprlock.
9. **Browser:** Firefox + arkenfox user.js; override `media.peerconnection.enabled=true` for WebRTC compat with AnyDesk-in-browser.
10. **Drop list (max-hardening minus gaming reality):** drop `lockdown=confidentiality`, drop `unprivileged_userns_clone=0`, drop full-system firejail, drop Wayland-only (keep Xorg fallback for AnyDesk).

**Block G design doc:** full apparmor profile files in `source/iso-build/apparmor-profiles/{anydesk,discord,steam-complain,firefox}.profile`, sbctl pacman hook, nftables ruleset template, opensnitch starter rules, usbguard policy.

### 3.8 Block H — "enhanced windows feel" desktop (NEW design doc)

**Operator-canonical:** *"def still want a desktop and a enhanced windows feel"*

**Interpretation:** familiar Windows-style ergonomics (taskbar at bottom, start menu, system tray, window snap to halves/quarters, alt-tab carousel) but on Linux compositor.

**Two options (operator picks at SDDM):**

| Variant | Compositor | Theme | Notes |
|---|---|---|---|
| **Sinister Hyprland (default)** | Hyprland | Default Sinister purple tiling | Power-user default |
| **Sinister niri** | niri | Scrollable tiling, Sinister purple | Research/multi-pane sessions |
| **Sinister Windows-Feel** | Cinnamon OR KDE Plasma (operator pick) | Windows 11-inspired but Sinister purple accent | "Enhanced Windows feel" — taskbar/start/tray/snap/alt-tab |

**Block H design doc:** recommend KDE Plasma over Cinnamon (better Wayland support, better HDR, better NVIDIA, Plasma Activities = Windows virtual desktops done right, Plasma's "Application Style" can faithfully clone Windows 11 chrome via `Lightly` theme). Cinnamon kept as fallback for the Mint-familiarity case.

**Composes:** all three variants share the same `eve-overlay` GTK4 hotkey window, same waybar/plasma-panel pill, same EVE socket. Variant choice doesn't change EVE control surface.

### 3.9 Block I — Test harness (NEW)

**Goal:** "test everything" → a runnable acceptance suite that proves each subsystem works without operator clicks.

**Three tiers:**

| Tier | Where it runs | What it tests | Pass criterion |
|---|---|---|---|
| **T0 — Docker** | `source/docker-stack/acceptance/` (NEW) | All overlays merge clean; `eve` CLI socket reachable; EVE-LLM bridge proxies to mock panel; sinister-control hot-reconfig classifies sample diffs; sinister-eve.service typed-state-machine transitions via mock triggers | green = operator can review Docker stack at `http://localhost:8443/` |
| **T1 — VM** | `source/vm-boot/acceptance/` (NEW) | Full ISO boots in QEMU/KVM; EVE daemon active; voice surface registers; GPU arbiter loads (mock NVIDIA via `nvidia-mock`); game-mode toggle cycles DISARMED→ARMING→ARMED in <60s with mock metrics | green = laptop deploy candidate |
| **T2 — Laptop bare-metal** | live USB recovery flow | First-boot completes; LUKS2 unlocks; Hyprland session loads; `eve chat "hello"` returns reply; Steam launches; AnyDesk + RustDesk both reachable from operator's main PC | green = main-PC dual-boot candidate |

**Block I design doc:** acceptance harness layout, pytest-style test runners (Python), pass/fail CI matrix, mock-NVIDIA + mock-panel shim files.

### 3.10 Block J — Docker stand-up for operator review (the "set it up on docker" deliverable)

**Goal:** by end of P0a (~3 dev days), operator can run ONE command and see the full Sinister OS stack in Docker for review.

**One-command entrypoint:** `cd projects/sinister-os/source/docker-stack && ./eve up` (existing `eve` CLI gets `up` subcommand)

**Stack composition** (existing overlays + new from this plan):

```
base: docker-compose.yml          (existing)
+ compose.dev.yml                  (existing — dev tools)
+ compose.hardened.yml             (existing — apparmor + opensnitch mocks)
+ compose.panel-shell.yml          (existing — Sinister-Panel UI)
+ compose.desktop.yml              (existing — desktop variant)
+ compose.eve-llm-bridge.yml       (NEW — EVE-LLM bridge daemon)
+ compose.gpu-arbiter.yml          (NEW — GPU arbiter w/ nvidia-mock)
+ compose.game-mode.yml            (NEW — game-mode subsystem w/ mock metrics)
+ compose.remote-access.yml        (NEW — RustDesk hbbs/hbbr + Sunshine mock)
+ compose.acceptance.yml           (NEW — T0 acceptance harness runner)
```

**Review surfaces** (operator opens browser):

- `https://localhost:8443/sinister-panel/` — main UI (existing)
- `http://localhost:8081/eve-status/` — EVE daemon status page (NEW shim)
- `http://localhost:8082/gpu-arbiter/` — GPU arbiter mode + metrics (NEW shim)
- `http://localhost:8083/game-mode/` — game-mode state machine + history (NEW shim)
- `http://localhost:8084/chat-bridge/` — EVE-LLM bridge status + recent chats (NEW shim)

**Block J deliverable:** the 5 new compose overlays + the 4 new shim HTTP services + the `eve up` subcommand + a one-page `source/docker-stack/REVIEW.md` operator-facing checklist.

### 3.11 Block K — Laptop deploy path

**Goal:** "put it live on my laptop" → after operator review in Docker.

**Two-stage rollout:**

**Stage K1 — Laptop VM (P0b):** operator boots `sinister-os-recovery.iso` in QEMU/KVM/VirtualBox on the laptop. Runs T1 acceptance. If green: proceed.

**Stage K2 — Laptop bare-metal:** operator-clicked. Three sub-paths:
- **K2a (RECOMMENDED):** dual-boot — install Sinister OS alongside existing laptop OS via `iso-build/` installer. Operator picks at GRUB.
- **K2b:** full replacement — wipe laptop, install Sinister OS. Backup → recovery USB first. NOT done without operator explicit "wipe it" intent.
- **K2c:** USB-boot only — Sinister OS on a fast NVMe-USB enclosure; laptop boots from USB. No disk touched. Best for first-day try.

**Block K deliverable:** the recovery ISO build target works end-to-end; first-boot setup wizard prompts for LUKS passphrase + YubiKey enrollment + network + user account; first-login lands in Hyprland session with EVE daemon active.

### 3.12 Block L — Brain entry: expand + quantum tools authorized

**Operator-canonical:** *"all agents can use expand tools and quantum tools as needed just be cautious on the seconds we use"*

**Brain entry:** `_shared-memory/knowledge/expand-and-quantum-tools-authorized-2026-05-25.md`

**Content:** "Fleet agents are AUTHORIZED to use expand-tier and quantum-tier tools when the work warrants it. Cautious posture: each invocation should be budgeted in seconds — prefer shorter focused queries over wide scans. Doctrine cross-references: forever-improve-review-doctrine (review-driven expansion bias), safe-quality-loops (12 guardrails), sanctum-scope-discipline (don't expand outside lane), no-bullshit-tested-before-claimed (verify before claiming)."

**Composes with:** existing tool-reach doctrine, loop-relentless doctrine rule 10.

### 3.13 Block M — Agent containment + failsafes + rate limits + all-in-containers

**Operator-canonical (verbatim 2026-05-25T09:36Z):** *"make sure our agents have complete control of all things but we have failsafes in place to prevent ai's going rogue and its all in containers. rate limit the agents if they do actions they should not"*

**Three-tier model — complete control + failsafes + containment:**

#### M.1 — Every agent in a container

Each agent class runs in its OWN OCI container (podman, rootless where possible, root for system agents that need it). NO agents run on the host PID 1 namespace.

| Agent class | Container | Cgroup slice | Network | FS access |
|---|---|---|---|---|
| **EVE control daemon** (`sinister-eve`) | `quay.io/sinister/eve-control:latest` (host networking; privileged) | `sinister-control.slice` | host (needs `/run/sinister/eve.sock`) | RW `/var/log/sinister`, RW `/run/sinister`, RO `/etc/sinister`, RW selective sudoers allowlist via host-exec bridge |
| **EVE-LLM bridge** | `quay.io/sinister/eve-llm-bridge:latest` | `sinister-control.slice` | private bridge (egress only to Hetzner panel) | RW `/var/lib/sinister/eve-llm`, RO `/etc/sinister/secrets/snap-chatter.key` |
| **sinister-voice user-service** | `quay.io/sinister/sinister-voice:latest` | `sinister-user.slice` (user@.service) | private (no egress; sends text intents to host socket) | RO mic device (mediated by PipeWire portal) |
| **GPU arbiter** | runs on HOST (needs raw `nvidia-smi` + cgroup writes) | `sinister-control.slice` | none | RW `/sys/fs/cgroup/sinister-ai.slice/cgroup.freeze`, exec `nvidia-smi` |
| **AI agents** (Ollama, local LLM workers, sinister-generator, whisper-local) | `quay.io/sinister/ollama:latest` etc. | `sinister-ai.slice` (DELEGATE freezer) | private bridge (egress only to allowlisted endpoints) | RW per-agent volume only; NO host filesystem |
| **MCP bots** (sinister-bus, brain, vault) | `quay.io/sinister/sinister-bus:latest` etc. | `sinister-mcp.slice` | UDS to host `/run/sinister/bus.sock` only | RW per-bot volume only |
| **Claude Code sessions** | one container per agent slug, podman rootless | `sinister-user.slice` | bridge to host MCP UDS only; allowlisted egress (api.anthropic.com, github.com, mesh nodes) | per-session volume mounted to scoped project directory (e.g. `/projects/sinister-os/`) — NO other project visible |

**Container ground rules:**
- Default `--security-opt=no-new-privileges`, `--cap-drop=ALL`, `--read-only` rootfs with tmpfs overlay
- All containers seccomp-confined to a baseline profile + per-agent additions (e.g. AI agents get `madvise`/`mmap` for tensor loads; MCP bots get `connect`/`bind` for IPC only)
- AppArmor profile per container class (`sinister-eve`, `sinister-ai`, `sinister-mcp`, `sinister-claude-session`)
- All container images self-built from a Sinister-controlled registry (`registry.sinister.local:5000`); no Docker Hub pulls
- Image signing via cosign; podman verifies signature on pull

#### M.2 — `sinister-agent-warden.service` (the failsafe enforcer)

System daemon that watches every agent container + every agent process. Anomaly detection + behavioral rate limiting + kill-switch.

```
sinister-agent-warden.service (system, runs as warden user, no agent can spawn it)
  UDS: /run/sinister/warden.sock (read-only query API; write via privileged operator socket)

  Subscriptions:
    - cgroup memory.events / cpu.stat (per-agent slice)
    - podman events stream (container start/stop/exec/exit)
    - auditd /etc/sinister write events
    - opensnitch egress decisions per agent container
    - eve.sock action log (every intent dispatched)
    - filesystem watch on /home/operator (writes outside agent's allowed scope = ALERT)

  Detectors:
    1. Action rate limiter (per agent slug, sliding 60s window)
       - default: 30 actions/min sustained; 90 actions/min burst (10s)
       - exceed → THROTTLE (cgroup CPU weight halved)
       - sustain throttle 5min → QUARANTINE (cgroup.freeze=1 + operator notification)
    2. Egress allowlist enforcement
       - per agent class, allowlist of (domain, port) pairs
       - unknown egress attempt → LOG + DENY (default-deny nftables in container netns)
       - 3+ denied attempts in 10min → QUARANTINE
    3. Filesystem escape detection
       - agent writes outside its volume → IMMEDIATE QUARANTINE (no warning)
       - operator notified, action log captured
    4. Sudoers allowlist drift
       - agent attempts sudo command NOT in allowlist → DENY + QUARANTINE
    5. Behavioral fingerprint
       - per-agent JSONL of last 1000 actions
       - simple z-score on (actions/min, avg action latency, action diversity)
       - 3σ deviation from rolling 24h baseline → SOFT-WARN (logged); 5σ → QUARANTINE
    6. Self-modification detection
       - agent writes to its own container image, its own systemd unit, its own apparmor profile → IMMEDIATE QUARANTINE
       - agent attempts to disable warden / GPU arbiter / eve daemon → IMMEDIATE QUARANTINE + emergency operator notification (TTS + waybar red + LED if available)

  Enforcement primitives:
    - THROTTLE: cgroup CPUWeight halve (recoverable)
    - QUARANTINE: cgroup.freeze=1 (instant, recoverable on operator unfreeze)
    - KILL: podman kill + cgroup.kill (irreversible for the run)
    - PANIC: kill ALL sinister-ai.slice + sinister-mcp.slice + send "operator panic" signal to EVE daemon (which surfaces a full-screen modal "WARDEN PANIC: agent <slug> escalated; all AI frozen; operator action required")

  Operator API (privileged socket /run/sinister/warden-priv.sock, polkit-gated):
    - warden status                           → human-readable agent state list
    - warden unfreeze <slug>                  → recover from QUARANTINE
    - warden raise-limit <slug> --duration 1h → temporary rate limit raise (audit logged)
    - warden panic                            → trigger emergency freeze of all AI
    - warden tail-log <slug>                  → live agent action log
```

#### M.3 — Per-agent rate limit policy (`/etc/sinister/warden-policy.toml`)

```toml
[defaults]
actions_per_minute = 30
actions_per_minute_burst = 90
burst_window_sec = 10
sustained_violation_throttle_sec = 300
denied_egress_quarantine_threshold = 3
denied_egress_window_sec = 600

[slug.sinister-os]
actions_per_minute = 60               # this lane spawns many file reads
egress_allowlist = ["github.com:443", "api.anthropic.com:443", "registry.sinister.local:5000"]

[slug.ollama]
actions_per_minute = 200              # inference produces many GPU calls/sec
egress_allowlist = []                 # ZERO egress; model files mounted local

[slug.sinister-generator]
actions_per_minute = 100
egress_allowlist = ["api.fal.ai:443", "api.together.ai:443"]
gpu_arbiter_priority = "low"          # always yields to game-mode + operator GPU use

[slug.sinister-bus]
actions_per_minute = 500              # high-volume IPC dispatcher
egress_allowlist = []

[slug.eve-llm-bridge]
actions_per_minute = 120
egress_allowlist = ["snap.sinijkr.com:443"]
```

#### M.4 — Failsafe layer summary (defense in depth)

| Layer | Mechanism | Recoverable? |
|---|---|---|
| 1. OCI container | seccomp + cap-drop + read-only rootfs | container restart |
| 2. AppArmor | per-agent-class profile | profile reload |
| 3. cgroup v2 | CPU/memory/io limits, freezer | freeze→unfreeze |
| 4. Network namespace + nftables | default-DENY egress, per-agent allowlist | rule reload |
| 5. opensnitch | per-rule logging, anomaly alerting | rule update |
| 6. sudoers allowlist | NOPASSWD allowed list only, deny-list explicit | edit /etc/sudoers.d/eve |
| 7. EVE daemon escalation ladder | informational < observable < mutating < destructive | per-action |
| 8. **WARDEN action rate limit** | sliding-window throttle + quarantine | unfreeze |
| 9. **WARDEN egress anomaly** | allowlist + quarantine | unfreeze |
| 10. **WARDEN filesystem escape** | immediate quarantine | unfreeze + investigate |
| 11. **WARDEN self-modification** | immediate quarantine + operator alert | operator-only unfreeze |
| 12. **WARDEN PANIC** | freeze all AI slices, EVE modal | operator-only recovery |

#### M.5 — "Complete control" preserved despite containment

The operator-canonical "EVE has complete control" is NOT a contradiction with containment. EVE control daemon runs in a **privileged container with host PID + host networking** (M.1 row 1) — it CAN do everything sudoers allows. What's contained is:
- AI agents (Ollama, generators, workers) — they can use the GPU and CPU but cannot reach the host filesystem or change system state
- MCP bots — they can talk to the EVE daemon socket but cannot exec system commands directly
- Claude Code sessions — they can edit files in their assigned project directory but cannot reach other projects or system files

EVE (the daemon) is the privileged executor. Agents propose; EVE executes (within sudoers allowlist). Warden polices agent behavior. This is the **Bell-LaPadula-like** pattern: agents have READ access to the world but WRITE access only via EVE daemon, which is independently audited by Warden.

#### M.6 — Block M deliverables

- `docs/design/agent-containment-failsafe-2026-05-25.md` — full design doc (this section expanded to per-container Containerfile + per-agent Compose unit + warden-policy.toml + warden Rust code architecture + 10 acceptance tests)
- `source/sinister-agent-warden/` — warden daemon Rust scaffold (Python prototype first)
- `source/iso-build/containers/` — Containerfiles for eve-control, eve-llm-bridge, sinister-voice, ollama, sinister-bus, sinister-claude-session
- `source/iso-build/apparmor-profiles/` — per-container apparmor profiles
- `/etc/sinister/warden-policy.toml` — runtime policy template
- Brain entry: `_shared-memory/knowledge/agent-containment-failsafe-doctrine-2026-05-25.md` — fleet-wide doctrine (this pattern applies to every Sanctum agent slug, not just sinister-os)

#### M.7 — Acceptance criteria

10 tests in CachyOS VM with podman + nftables + cgroup v2:

1. EVE daemon container can write to `/etc/sinister/*.toml`; ollama container CANNOT.
2. Ollama container at 100% GPU util — game-mode ARMING freezes it within 500ms; unfreezes after 30min idle.
3. Ollama container attempts egress to `api.openai.com:443` — DENIED + logged.
4. Sinister-bus container attempts to exec `/usr/bin/pacman` — DENIED + logged (no sudo allowlist match).
5. Claude session container in `agent/sinister-os/*` attempts to read `projects/sinister-chatbot/` — DENIED (volume not mounted).
6. Action rate limit: synthetic spam of 1000 actions/sec from test agent — THROTTLED within 1s, QUARANTINED within 5min sustained.
7. Filesystem escape: agent writes to `/home/operator/.ssh/` — IMMEDIATE QUARANTINE within 100ms, operator notified.
8. Self-modification: agent attempts to edit own systemd unit — IMMEDIATE QUARANTINE + WARDEN PANIC signal raised.
9. Warden PANIC drill: operator runs `warden panic` — all AI slices freeze within 500ms, EVE modal appears, no false-positive on EVE daemon itself.
10. Operator unfreeze: `warden unfreeze ollama` — container resumes, no data loss, inference completes the in-flight request.

#### M.8 — Risks specific to Block M

| # | Risk | Mitigation |
|---|---|---|
| M-1 | Warden itself becomes a single point of failure | Warden runs in its OWN container with restart=always; secondary "warden-watchdog" minimal daemon on host pings warden every 5s; on miss, raises EVE modal |
| M-2 | Overly aggressive rate limits break legitimate work | Per-slug override + operator `warden raise-limit` + behavioral fingerprint baselines learned over 24h before enforcement |
| M-3 | Quarantine cascade (one agent freezes, dependents pile up requests) | Backpressure: when sinister-ai.slice frozen, EVE daemon returns `dependency_unavailable` to dependent clients instead of queuing infinitely |
| M-4 | Container escape via kernel CVE | Defense in depth: AppArmor + seccomp + read-only rootfs + cap-drop + no-new-privileges; kernel = linux-cachyos with hardening patches included |
| M-5 | Operator gets warden-fatigue from false positives | 7-day soak: log only, no quarantine; after 7d operator reviews + tunes baselines; then enforce |
| M-6 | Privileged EVE container itself goes rogue | EVE daemon source is operator-readable Rust; every action logged to `/var/log/sinister/eve.jsonl`; warden subscribes to that log and applies same anomaly detection to EVE — but EVE quarantine requires DUAL operator confirm (chord + voice) since killing EVE means losing all control surfaces |

### 3.14 Block N — Fleet tools port to Sinister OS preinstalled

**Operator-canonical (verbatim 2026-05-25T09:41Z):** *"make sure all things like this come with us when we setup the OS and os installed and ready"*

**Operator prior context (screenshot reference):** *"make this entire login process actually work and be fully automated and add refresh and detection for auto relogin all things like that use our sinister browser system"* — i.e. the Sinister Browser System (cookie capture + session record/replay + template apply + auto-relogin) and similar fleet automation tools MUST work on Sinister OS day-one.

#### N.1 — Fleet tool inventory + port strategy

Audit of Sanctum tools currently on the operator's Windows workstation, with per-tool port classification:

| Tool | Current state on Windows | Port strategy for Sinister OS | Phase |
|---|---|---|---|
| **Sinister Browser System** (Ruflo MCP: `browser_cookie_use` / `browser_session_record` / `browser_session_replay` / `browser_session_end` / `browser_template_apply`) | Ruflo MCP server, Python, calls Chromium via Playwright/Selenium | **Native Linux port** — Playwright + Chromium-flatpak; same MCP surface; cookie store on encrypted Sinister Vault | P2 |
| **Login automation + auto-relogin + refresh+detect** | Sinister Browser System patterns | **Native Linux port** — same code; runs as `sinister-browser-bot.service` (user service); per-domain session profile in `/var/lib/sinister/browser-sessions/`; auto-detect 401/403/login-redirect → fire replay; refresh on TTL expiry | P2 |
| **EVE.exe** (Windows PyQt picker/launcher binary) | PyInstaller bundle, Win32 | **Re-implement as `eve-desktop`** GTK4 app (Linux-native) — same picker UX, same key bindings, same accounts panel, same health view. NOT WINE-wrapped (Win32 deps too tangled). | P3 |
| **eve-picker / main_menu.py** | Python module behind EVE.exe | **Port directly** — Python is portable; reskin via gtk4-layer-shell or Tk for terminal-mode fallback | P3 |
| **sinister-term** | Windows terminal wrapper | **Drop on Linux** — kitty/foot/wezterm cover all features natively; ship `sinister-term-launcher` Python script that wraps kitty with Sinister theming + status line | P2 |
| **Sinister Panel** | Bun + React web app served on Hetzner | **No port needed** — it's already web; ships as local PWA pinned to Hyprland; `eve panel` CLI opens it | P2 |
| **MCP bots** (sinister-bus, brain, vault, ruflo, memory) | Python servers on Windows | **Port directly** — Python is portable; ship as systemd units under `sinister-mcp.slice`; per-bot containers per Block M | P2 |
| **automation scripts** (`automations/*.py` + ~250 legacy `*.ps1`) | Python + PowerShell on Windows | **Python ports first** (operator hard-canonical NO .ps1); legacy `*.ps1` migrated per "no-bat-no-ps1" doctrine on next touch; equivalents in Bash where Python isn't natural | P2-P4 |
| **sinister-generator** (nano-banana wrapper for AI image gen) | Python, calls fal.ai/together.ai | **Port directly** — Python is portable; ship as `sinister-generator.service` under `sinister-ai.slice` | P2 |
| **sinister-memory** (unified memory CLI + Ruflo MCP semantic store) | Python CLI + SQLite FTS5 + BM25 | **Port directly** — Python+SQLite are portable; `forge-memory recall` CLI works as-is | P2 |
| **sinister-vault** | Python daemon on port 5078 | **Port directly** — Python; ship as `sinister-vault.service`; vault data dir at `/srv/sinister-vault` (already in master plan filesystem) | P2 |
| **sinister-overseer** | Python meta-agent | **Port directly** — Python; ship as `sinister-overseer.service` | P2 |
| **EVE.exe single-instance guard + watchdog + auto-restart** | Windows-specific (mutex, schtask) | **Re-implement** — systemd `RestartSec` + `Restart=on-failure` is the native replacement; user-service unit for each fleet component | P2 |
| **claude-accounts.ps1 + OAuth rotation** | PowerShell | **Python rewrite** as `sinister-accounts.py` CLI; account creds in encrypted Vault; round-robin iterator + health check | P2 |
| **fleet-update.ps1 / mesh-coordinator.ps1 / agent-poke.ps1** | PowerShell IPC over JSON files | **Python rewrites** under `automations/`; same JSON-file contract (cross-platform); legacy `.ps1` left in place for Windows transitional | P2 |
| **RKOJ workbench (window manager)** | Windows Qt | **Linux re-implementation** as `rkoj-workbench` (PyQt6 — same Qt, native Linux) OR drop entirely (Hyprland workspace + scratchpad replicates the UX) | P3 (decision deferred) |
| **OperatorPickerForge / picker variants** | Python+Qt on Windows | **Port directly** — PyQt6 is cross-platform | P3 |
| **Schtask-based heartbeat watchdog** | Windows schtasks | **systemd timer units** — `sinister-heartbeat-watchdog.timer` (15-min cadence) | P2 |

#### N.2 — Login automation deep dive (the screenshot ask)

The screenshot operator phrase *"login process actually work and be fully automated and add refresh and detection for auto relogin all things like that use our sinister browser system"* decomposes into:

1. **Bootstrap login** — operator runs first-time login for each service (snap, lets-text panel, jokr, github, anthropic console, etc.) ONCE. Ruflo `browser_session_record` captures the full flow (URL, form fills, MFA token entry, redirect chain, post-login cookies + localStorage + sessionStorage).
2. **Session replay** — when the cookies expire OR a 401/403 fires OR the operator-detected "login-redirect" pattern hits, `browser_session_replay` re-runs the recorded flow without operator intervention. Headless Chromium, optionally with `--debug` flag opening visible browser for operator inspection.
3. **TTL-based refresh** — per-domain TTL stored in `/var/lib/sinister/browser-sessions/<domain>.toml`. Background `sinister-browser-refresh.timer` (15-min) checks every active session; if `now > expiry - refresh_buffer`, fires session replay proactively.
4. **Auto-detect** — `sinister-browser-bot.service` monitors each open session via a Playwright "context heartbeat" — a tiny periodic `GET /me` or equivalent that confirms session is live. On HTTP 401/403/302-to-login, fires auto-relogin.
5. **MFA flows** — TOTP secrets stored in encrypted Vault; Ruflo session replay auto-fills the OTP at the right step. Yubikey OTP flows route through the operator's connected Yubikey via `pyhidapi`.
6. **Quarantine on repeat failures** — 3 consecutive failed relogins in 30 min → operator notification (TTS + waybar amber + email/SMS) + flag session as `manual-intervention-required`.

**Deliverable in Block N:**
- `source/sinister-browser/` — Python service + Playwright wrappers + MFA helpers + per-domain session TOML schema
- `source/sinister-browser/systemd/sinister-browser-bot.service` + `sinister-browser-refresh.timer`
- `source/sinister-browser/docs/session-profiles.md` — per-domain template format
- `/var/lib/sinister/browser-sessions/` — runtime dir (chmod 0700, owned by `eve`)
- `/etc/sinister/browser-policy.toml` — global policy (max sessions, retry counts, MFA routing)

#### N.3 — Preinstall manifest (baked into ISO)

Every tool above ships in `source/iso-build/preinstall-manifest.toml`:

```toml
[manifest]
sanctum_root = "/srv/sinister-sanctum"   # operator's Sanctum tree mounts here on first boot
first_boot_setup_wizard = true
operator_user = "ezekiel"
operator_groups = ["wheel", "eve", "video", "audio", "input", "render"]

[tools.eve-desktop]
package = "sinister-eve-desktop"
service = "sinister-eve-desktop.service"
user_service = true
auto_start = true

[tools.sinister-browser]
package = "sinister-browser-bot"
service = "sinister-browser-bot.service"
user_service = true
auto_start = true
mfa_vault_path = "/srv/sinister-vault/secrets/mfa/"
session_dir = "/var/lib/sinister/browser-sessions/"

[tools.sinister-bus]
package = "sinister-bus-mcp"
service = "sinister-bus.service"
user_service = false
slice = "sinister-mcp.slice"
auto_start = true

[tools.sinister-vault]
package = "sinister-vault"
service = "sinister-vault.service"
port = 5078
data_dir = "/srv/sinister-vault"

[tools.sinister-memory]
package = "sinister-memory-cli"
cli_only = true              # no daemon; CLI on PATH for all users

[tools.sinister-generator]
package = "sinister-generator"
service = "sinister-generator.service"
user_service = true
slice = "sinister-ai.slice"
gpu_arbiter_priority = "low"

# ... and so on for every fleet tool
```

This manifest is consumed by `source/iso-build/build.sh` to write the packagelist + systemd unit symlinks + first-boot setup wizard config.

#### N.4 — Operator state migration (Windows → Linux)

The operator's current Windows workstation has years of state in:

- `D:\Sinister Sanctum\` — the Sanctum tree (this repo)
- `D:\sinister-vault\` — the Vault data
- `D:\LetsText\` — LetsText project
- `C:\Users\Zonia\.claude\` — Claude Code session state
- `C:\Users\Zonia\AppData\Local\` — various app states

On first-boot of Sinister OS, the **state-migration wizard**:

1. Asks operator to plug in the source disk (USB enclosure or temporary mount).
2. Migration script (`source/iso-build/state-migrate.py`) maps:
   - `D:\Sinister Sanctum\` → `/srv/sinister-sanctum/` (full sync; preserves git state)
   - `D:\sinister-vault\` → `/srv/sinister-vault/`
   - `D:\LetsText\` → `/srv/sinister-projects/letstext/`
   - `~/.claude/` → `~/.claude/` (settings.json + accounts cache)
   - Browser sessions → `/var/lib/sinister/browser-sessions/` (re-recorded; cookies don't survive cross-OS in many cases)
3. Operator verifies via `eve verify migration --since <timestamp>` — runs sanity checks (git status clean? vault daemon starts? sanctum CLAUDE.md readable? heartbeat directory writable?).
4. After 7-day soak on Sinister OS with no issues, operator can wipe the Windows partition via `eve finalize-cutover` (per master plan § 7).

#### N.5 — Build chain (how tools get into the ISO)

```
source/iso-build/
├── preinstall-manifest.toml      # what to install
├── build.sh                      # archiso wrapper
├── packagelist.txt               # generated from manifest
├── customize-airootfs.sh         # systemd unit symlinks + first-boot wizard
├── sinister-aur-builder/         # custom PKGBUILDs for Sanctum tools (sinister-*)
│   ├── sinister-eve-desktop/
│   ├── sinister-browser-bot/
│   ├── sinister-bus-mcp/
│   ├── sinister-vault/
│   ├── sinister-memory-cli/
│   ├── sinister-generator/
│   └── ...
├── containers/                   # Containerfiles per Block M
└── apparmor-profiles/            # per Block G + Block M
```

PKGBUILDs build `.pkg.tar.zst` from this repo's `projects/*/source/` directories. Pacman repository at `repo.sinister.local:8080` (or built into the ISO directly for offline install).

#### N.6 — Block N deliverables

- Add this § 3.14 to MASTER-AUDIT-EXPANSION plan (THIS edit)
- `docs/design/fleet-tools-port-2026-05-25.md` — full per-tool port spec (Day 1-2)
- `source/iso-build/preinstall-manifest.toml` — manifest schema + initial rows (Day 1-2)
- `source/sinister-browser/` — Linux Python port skeleton (Day 2-3)
- Brain entry: `_shared-memory/knowledge/fleet-tools-port-to-sinister-os-doctrine-2026-05-25.md` — every NEW fleet tool ships Linux-port plan from day one (Day 0 this turn)
- Updated PROGRESS row + heartbeat

#### N.7 — Acceptance criteria

After Sinister OS install + state migration:

1. `eve picker` opens — same 11 projects visible.
2. `eve chat "hello"` → EVE-LLM bridge replies via local UDS → Hetzner panel (or direct on initial reach).
3. `sinister-browser-bot status` shows all configured sessions live + healthy.
4. Operator's `snap.sinijkr.com` session — operator triggers an action; bot auto-relogins if expired; action completes.
5. `forge-memory recall "sinister-os"` returns recent rows from Sanctum brain.
6. `sinister-generator` produces a test image (with operator GPU + Sinister API key).
7. `sinister-vault` daemon serving on `localhost:5078`.
8. `sinister-bus` MCP active; `sinister-bus.inbox_poll` returns operator inbox.
9. Every fleet tool runs in its container per Block M; Warden allowlists already populated for known agents.
10. `eve migration verify` returns green for git state, vault state, claude state, sanctum CLAUDE.md.

#### N.8 — Risks specific to Block N

| # | Risk | Mitigation |
|---|---|---|
| N-1 | Some browser sessions don't survive cookie format conversion | Re-record sessions on Sinister OS (one-time operator cost); document in migration wizard |
| N-2 | EVE.exe rewrite (PyQt → GTK4) takes longer than expected | Ship a Tk fallback as MVP; full GTK4 polish in P4 |
| N-3 | Operator's Windows AppData state lost | Pre-migration disk imaging via `dd if=/dev/sdX of=/srv/backups/windows-preimage.img.zst` (operator-clicked once) |
| N-4 | Some legacy PowerShell scripts have Windows-only deps | Per "no-bat-no-ps1" doctrine, rewrite in Python on next touch; transitional Wine wrapping for short tail |
| N-5 | MFA secrets in Windows → Linux Vault migration | Operator re-enrolls TOTP secrets (security best practice anyway); Vault migration script audit-logs the count moved |

## 4. EXECUTION PHASING (Docker → Laptop → Main PC)

```
THIS PLAN (P0 audit + compile)            ─┐
   ↓                                       │
Block L brain entry (memory write)         │  Day 0 (this turn)
Block B PROGRESS row                       │
   ↓                                       │
Block A Windows-parity merge doc           ─┘  Day 0-1

Block C GPU-arbiter design doc             ─┐
Block D game-mode design doc               │  Day 1
Block E niri-variant design doc            │  (parallel writes; 4 docs)
Block F remote-access design doc           ─┘

Block G hardening-spec design doc          ─┐
Block H windows-feel-desktop design doc    │  Day 1-2
Block I test-harness design doc            │
Block M agent-containment-failsafe doc     ─┘  (+ brain entry)

Block J Docker stand-up                    ─┐
  - 5 new compose overlays                 │  Day 2-3
  - 4 new HTTP shims                       │
  - eve up subcommand                      │
  - REVIEW.md operator checklist           │
   ↓                                       │
OPERATOR REVIEW IN DOCKER                  ─┘  ← gate
   ↓
operator edits / iteration cycles
   ↓
Block K1 Laptop VM (T1 acceptance)         ─┐
   ↓                                       │  Operator-gated
Block K2 Laptop bare-metal                 ─┘
   ↓
Block K2 Main-PC dual-boot                 (P0c per rollout-doctrine; far-future)
```

**Realistic estimate:** ~3 dev days for Docker stand-up. The 4 research returns + this plan + brain entry = Day 0 ship.

---

## 5. DOCTRINE COMPLIANCE (no-bullshit + scope + push-policy)

- **No-bullshit rule 1 (precise verbs):** every deliverable in this plan is marked `shipped` / `design-only` / `queued` / `unverified`. Docker stand-up itself is `queued`; the plan to build it is `shipped`.
- **Sanctum scope discipline:** every deliverable lives in `projects/sinister-os/**` or this plan / brain entry. Zero cross-lane edits.
- **Single-repo push policy:** branch `agent/sinister-os/master-audit-expansion-2026-05-25` will commit + push to Sinister-Sanctum (push blocked at GitHub by historical fleet-updates.jsonl until operator filters; commits durable locally).
- **No gate questions:** this plan EXECUTES — it doesn't ask "should we?" anywhere.
- **Forever-improve degradation signals:** brain row count, PROGRESS size, plans active — all within green after this plan (brain +1, PROGRESS +1 row, plans +1 active). No degradation triggered.

---

## 6. RISK REGISTER

| # | Risk | Mitigation |
|---|---|---|
| 1 | Operator's GitHub push blocked by 494MB fleet-updates.jsonl in branch ancestry | Local commits durable; sanctum-auto-push retries; operator may eventually need git-filter-repo (destructive — operator-scope). |
| 2 | Gitea on localhost:3000 down | Same as #1 — local durable, auto-push retries. |
| 3 | Auto-branch-router moves commits to wrong branch (e.g. routing "chatbot" filenames to overseer) | Cherry-pick back to correct branch each commit. Tracked in iter 19 PROGRESS row. |
| 4 | Docker stack pulls 10+ GB images on first `eve up` | Pre-bake images via `bake-panel.sh` pattern; document size budget in REVIEW.md |
| 5 | NVIDIA proprietary driver instability on niri | Document `50-limit-free-buffer-pool-in-wayland-compositors.json` workaround; gate niri variant ship on VM-test pass |
| 6 | AnyDesk supply-chain risk while we keep it transitionally | Block F: apparmor profile + opensnitch ASN allowlist + audit log; sunset by P5 |
| 7 | Game-mode ARMING never converges (e.g. background pacman upgrade) | 600s hard ceiling + BLOCKED state + force_launch escape hatch + specific blocker surfaces in failure mode |
| 8 | Scope explosion (operator dumped many features) | This plan is the single compile point; brain entry pins it; subsequent operator interrupts amend this plan rather than spawn new |

---

## 7. ACCEPTANCE FOR THIS PLAN

This plan is `shipped` when:

- [x] Document committed at `plans/MASTER-AUDIT-EXPANSION-2026-05-25/plan.md`
- [x] Audit § 1 covers every existing artifact (24+ rows)
- [x] Expansion § 2 covers every operator phrase (12 blocks A-L)
- [x] Block-by-block § 3 maps each block to concrete deliverables + composes-with refs
- [x] Phasing § 4 makes the Docker-first → laptop → main-PC chain explicit
- [x] PROGRESS row appended (Block B)
- [ ] Brain entry written (Block L) — next deliverable this turn
- [ ] Block A Windows-parity merge doc — Day 0-1
- [ ] Block C-H design docs — Day 1-2
- [ ] Block I-J Docker stand-up — Day 2-3
- [ ] Block M agent-containment-failsafe design doc + warden Rust scaffold + brain entry — Day 1-2
- [ ] Block K laptop deploy — operator-gated

Pre-flight tracking via TaskList in this lane.

## 8. CROSS-REFERENCES

- `projects/sinister-os/plans/master-plan-2026-05-24.md` — P0-P5 baseline
- `projects/sinister-os/plans/mesh-os-master-plan-2026-05-24.md` — mesh routing
- `_shared-memory/plans/sinister-os-massive-expansion-2026-05-24T2110Z/plan.md` — prior expansion (iters 8-15 SHIPPED)
- `projects/sinister-os/docs/design/sinister-eve-service-state-machine-2026-05-25.md` — EVE daemon state machine (iter 18)
- `projects/sinister-os/source/eve-llm-bridge/SPEC-2026-05-25.md` — EVE-LLM bridge IPC (iter 19)
- `projects/sinister-os/docs/design/sinister-voice-user-service-2026-05-25.md` — voice oracle (iter 20)
- `_shared-memory/knowledge/expand-and-quantum-tools-authorized-2026-05-25.md` — Block L brain entry
- `D:\Sinister Sanctum\CLAUDE.md` — operator hard-canonicals (no-gate-questions, no-bat-no-ps1, loop-relentless, single-repo-push, etc.)
- `_shared-memory/operator-utterances.jsonl` row 2026-05-25T09:26:13Z — first originating directive (12 blocks A-L)
- `_shared-memory/operator-utterances.jsonl` row 2026-05-25T09:36:15Z — second originating directive (Block M)
- `_shared-memory/knowledge/agent-containment-failsafe-doctrine-2026-05-25.md` — Block M brain entry (fleet-wide doctrine)
- `_shared-memory/knowledge/expand-and-quantum-tools-authorized-2026-05-25.md` — Block L brain entry
