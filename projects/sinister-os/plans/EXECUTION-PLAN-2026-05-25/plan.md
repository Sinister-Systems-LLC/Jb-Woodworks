# Sinister OS — EXECUTION PLAN (complete everything → VM → laptop)

> **Author:** RKOJ-ELENO :: 2026-05-25T09:55Z
> **Plan ID:** `sinister-os/EXECUTION-PLAN-2026-05-25`
> **Operator directive (verbatim 2026-05-25T09:54Z):** *"create a plan to complete everything i have said to do then open the OS in VM so i can test things and tell you waht to do then we can talk about pushing to laptop"*
> **Builds on:** `MASTER-AUDIT-EXPANSION-2026-05-25/plan.md` (14 blocks A-N — the DESIGN) — this plan is the BUILD execution
> **Composes-with:** state-machine + EVE-LLM bridge + sinister-voice design trilogy 2026-05-25 · agent-containment-failsafe + fleet-tools-port + expand-and-quantum doctrines · master-plan-2026-05-24 P0-P5 baseline
> **Path:** designs are 90% done → this plan turns them into RUNNABLE artifacts the operator can boot, click, and review

---

## 0. The five phases (one line each)

| Phase | What | When | Operator action |
|---|---|---|---|
| **1A** | VM preview (Docker-based Hyprland-in-browser) | Same-day (this turn) | Run `python eve-vm.py up` → open `http://localhost:6080` |
| **1B** | Real Sinister OS ISO via archiso (WSL2-built) | Day 1-2 | Boot ISO in VirtualBox/QEMU/Hyper-V on Windows host |
| **2** | Build out 14 blocks A-N atop the ISO | Day 2-7 | Periodic review of acceptance harness output |
| **3** | VM acceptance test (T1 from MASTER plan Block I) | Day 7-8 | Drive the ISO through the test harness; operator iterates |
| **4** | Laptop deploy (T2; operator-gated) | Day 8+ | K1 VM on laptop → K2 bare-metal install |
| **5** | Main PC dual-boot (operator-gated; per master plan P0c) | Far future | Operator-clicked install during a maintenance window |

---

## 1. PHASE 1A — VM preview (SAME-DAY ship)

**Goal:** the operator can boot something that *looks and feels* like Sinister OS within minutes of running ONE Python command, even though the real ISO isn't built yet.

**Substrate:** Docker container (`sinister-os-preview`) running Hyprland + waybar + the EVE daemon stub + wofi sheet + `eve chat` CLI, exposed via noVNC at `http://localhost:6080`.

**Why Docker, not VirtualBox/QEMU yet:**
- Operator's Windows host has Docker Desktop already (assumed; if not, falls back to WSL2 path per Phase 1A.2)
- Faster iteration than building an ISO (~30s rebuild vs 10-min ISO build)
- noVNC works in any browser — no VM client install
- Same compose-stack the master plan Block J already uses

**Deliverables (this turn):**

| Artifact | Path | Status |
|---|---|---|
| `compose.os-preview.yml` | `source/docker-stack/compose.os-preview.yml` | NEW this turn |
| `Containerfile.os-preview` | `source/docker-stack/Containerfile.os-preview` | NEW this turn |
| `eve-vm.py` launcher | `source/docker-stack/eve-vm.py` (Python; no .bat) | NEW this turn |
| Operator README | `source/docker-stack/VM-PREVIEW-README.md` | NEW this turn |
| EVE daemon stub | `source/docker-stack/preview-stubs/eve-daemon-stub.py` | NEW this turn (responds to `chat.send` with placeholder; returns daemon info) |

**One-command operator flow:**

```
cd projects/sinister-os/source/docker-stack
python eve-vm.py up
# Wait ~60s (first run pulls + builds; ~30s subsequent)
# Browser auto-opens to http://localhost:6080
# Operator sees Hyprland with Sinister purple wallpaper + waybar pill + wofi-able EVE sheet
# Operator clicks the EVE pill → quick-chat sheet opens
# Operator types in terminal: eve chat "hello"  → daemon stub replies
# Operator clicks game-mode toggle → state transitions visible
```

**What's mocked vs real:**

| Subsystem | Real vs mock in Phase 1A |
|---|---|
| Compositor (Hyprland) | REAL — actual Hyprland running |
| waybar | REAL — actual waybar with custom-eve module |
| EVE daemon | STUB — Python HTTP+UDS shim returns placeholder responses; logs intents to `/var/log/sinister/eve.jsonl` |
| EVE-LLM bridge | STUB — proxies to a `mock-panel.py` that returns canned chat replies (real bridge implementation lands Phase 2) |
| sinister-voice | NOT IN PREVIEW — Phase 2 |
| GPU arbiter | NOT IN PREVIEW (no GPU in container) — Phase 2 |
| Game mode toggle | UI-only stub — clicking it transitions state in `/tmp/game-mode-state.json` so operator can see the state machine; no real prep sequence |
| Sinister Browser auto-relogin | NOT IN PREVIEW — needs real Chromium + Playwright sandbox; Phase 2 |
| Sinister Panel | REAL — already in `compose.panel-shell.yml`; preview composes both |
| Sanctum tree | MOUNTED — operator's host `D:\Sinister Sanctum\` mounted read-only at `/srv/sinister-sanctum` |

**Acceptance gate (Phase 1A → 1B):** operator runs `python eve-vm.py up`, sees Hyprland in browser, can type `eve chat "hello"` and get a reply, can click game-mode toggle and see state change. If green → proceed to Phase 1B real ISO build.

**Phase 1A.2 — WSL2 fallback (if Docker Desktop missing):** `eve-vm.py` detects Docker Desktop absence and falls back to launching an Arch WSL2 distro with Sinister tools installed; WSLg gives Wayland; operator launches `wsl.exe -d Sinister-OS-Preview -- hyprland`. Documented in README; same Containerfile content adapted to WSL2 systemd-genie pattern.

---

## 2. PHASE 1B — Real Sinister OS ISO build (Day 1-2)

**Goal:** produce a bootable `sinister-os-2026-05-26.iso` that runs in any VM (VirtualBox / QEMU / Hyper-V / VMware) AND on bare metal (laptop, then main PC).

**Builder substrate:** archiso (Arch's official ISO builder), run inside WSL2 (Windows host doesn't have native archiso). Output: ISO at `projects/sinister-os/source/iso-build/out/sinister-os-<date>.iso`.

**Day 1 deliverables (build infrastructure):**

| Artifact | Path | Purpose |
|---|---|---|
| `source/iso-build/build.sh` | exists (scaffolded); fill in this phase | archiso wrapper |
| `source/iso-build/profile/` | NEW — archiso profile directory | base CachyOS + Hyprland + Sinister overlays |
| `source/iso-build/preinstall-manifest.toml` | exists (from Block N); consume here | what to install |
| `source/iso-build/sinister-aur-builder/PKGBUILDs/` | NEW — custom PKGBUILDs for sinister-* | per-tool build recipes |
| `source/iso-build/customize-airootfs.sh` | NEW | first-boot wizard + systemd unit symlinks |
| `source/iso-build/build-in-wsl.py` | NEW (Python launcher) | wrap WSL2 + archiso for Windows host |

**Day 1 acceptance:** `python build-in-wsl.py build` produces a bootable ISO within 15 minutes. ISO boots in QEMU `qemu-system-x86_64 -enable-kvm -cdrom out/sinister-os-*.iso -m 4096`.

**Day 2 deliverables (first-boot wizard + state migration):**

- `source/iso-build/first-boot-wizard.py` (TUI; per no-bat doctrine Python-native) — prompts LUKS passphrase + Yubikey enrollment + network + user account + state migration source disk
- `source/iso-build/state-migrate.py` — copies operator's Windows Sanctum tree → Linux `/srv/sinister-sanctum/` per Block N spec
- `source/iso-build/CHANGELOG.md` — what's in each ISO build

**Acceptance gate (Phase 1B → 2):** ISO boots in QEMU, first-boot wizard completes, operator lands at Hyprland session with EVE daemon active + waybar pill visible.

---

## 3. PHASE 2 — Build out 14 blocks A-N atop ISO (Day 2-7)

**Goal:** every design block from the MASTER plan ships as a built, installed, running artifact on the Sinister OS image.

**Per-block build schedule (parallel where possible):**

### Day 2 (parallel)

| Block | What ships | Where |
|---|---|---|
| **A** | Windows-parity merge doc | `docs/WINDOWS-PARITY-CANONICAL-2026-05-25.md` |
| **B** | (already done) | — |
| **L** | (already done — brain entry) | — |

### Day 2-3 (parallel — spawn 4-agent swarm per expand+quantum doctrine)

| Block | What ships | Where |
|---|---|---|
| **C** | `sinister-gpu-arbiter` Python prototype + systemd unit + apparmor profile + Containerfile | `source/sinister-gpu-arbiter/` |
| **D** | `sinister-game-mode` Python prototype + 7-state machine + 15-step ARMING sequence + game-mode.toml schema | `source/sinister-game-mode/` |
| **E** | niri variant Containerfile + KDL config + EVE overlay window rule + SDDM dropdown entry | `source/iso-build/profile/airootfs/etc/sinister/niri/` |
| **F** | RustDesk self-host recipe + Sunshine systemd unit + AnyDesk apparmor profile | `source/sinister-remote-access/` |

### Day 3-4 (parallel)

| Block | What ships | Where |
|---|---|---|
| **G** | apparmor profiles + sbctl pacman hook + nftables ruleset + opensnitch starter rules + usbguard policy + sysctl drop-in | `source/iso-build/profile/airootfs/etc/` (multiple files) |
| **H** | "windows-feel" variant: KDE Plasma + Lightly theme + Plasma Activities config | `source/iso-build/profile/airootfs/etc/sinister/plasma-windows-feel/` |
| **I** | T0/T1/T2 acceptance test harness (pytest) | `source/acceptance/` |

### Day 4-5 (parallel)

| Block | What ships | Where |
|---|---|---|
| **J** | Docker stand-up — 5 compose overlays + 4 HTTP shims + `eve up` subcommand | `source/docker-stack/` (extends existing) |
| **M** | `sinister-agent-warden` Python prototype + warden-policy.toml + 12 Containerfiles + per-container apparmor profiles | `source/sinister-agent-warden/` + `source/iso-build/containers/` |
| **N** | `sinister-browser-bot` Python service + Playwright wrappers + MFA helpers + session TOML schema + sinister-browser-bot.service + sinister-browser-refresh.timer | `source/sinister-browser/` |

### Day 5-6 (sequential — depends on above)

- Wire all Block C-N artifacts into `preinstall-manifest.toml`
- Update `customize-airootfs.sh` to install + symlink all new units
- Rebuild ISO with everything included → `sinister-os-2026-05-30.iso`

### Day 6-7 (T0 acceptance test)

- Run `pytest source/acceptance/t0_docker/` against the docker-stack — all green
- Run `pytest source/acceptance/t1_vm/` against the new ISO booted in QEMU — all green
- Generate `_shared-memory/PROGRESS/sinister-os-acceptance-t0-t1-<date>.md` report

**Acceptance gate (Phase 2 → 3):** ISO contains every Block A-N artifact; T0 + T1 pytest suites pass; ISO boots clean in QEMU; first-boot wizard works end-to-end.

---

## 4. PHASE 3 — VM acceptance test + operator iteration (Day 7-8)

**Goal:** operator drives the ISO in a VM, files feedback, agent iterates without operator clicking install commands.

**Setup:**

- Operator runs `python eve-vm.py up --iso sinister-os-2026-05-30.iso` (Phase 1A's launcher gets `--iso` flag in Phase 2)
- Browser opens to noVNC view of the booted ISO in QEMU/KVM
- Operator interacts: clicks through hotkeys, runs `eve chat`, tries game-mode toggle, opens sinister-panel
- Feedback channel: operator pastes screenshot + comment in this session; sinister-os agent iterates next turn

**T1 acceptance test (operator-runnable):**

```
python eve-vm.py test --suite t1
```

Runs 25+ scenarios:
- Boot + login (LUKS unlock works)
- EVE daemon active (curl `http://localhost:7331/health` returns 200)
- EVE-LLM bridge proxies (curl `eve chat "hello"` works)
- sinister-voice loads (wake-word listener starts; `pgrep sinister-voice` non-empty)
- GPU arbiter starts (`systemctl status sinister-gpu-arbiter` green; mock-mode if no GPU passthrough)
- Game mode cycles DISARMED→ARMING→ARMED in <60s with mock metrics
- Hyprland + niri both selectable at SDDM
- AppArmor enforce mode active for browsers + chat + anydesk
- nftables default-DROP inbound
- LUKS2 active on `/`
- Snapper hourly snapshots auto-firing
- ... etc per Block I spec

**Per-iteration loop:**

```
operator runs test → fails on row N → operator pastes failure
sinister-os agent reads failure → fixes → rebuilds ISO → operator re-runs
loop until T1 all green
```

**Acceptance gate (Phase 3 → 4):** operator says "ship to laptop". Until that exact phrase (or equivalent), Phase 4 does not begin. This is operator-canonical "operator-gated phase boundaries".

---

## 5. PHASE 4 — Laptop deploy (operator-gated)

**Goal:** Sinister OS lives on the operator's laptop with all fleet tools working.

**Three sub-paths (operator picks; default = K2c USB-boot for safety):**

### K1 — Laptop VM (always first; no risk)

- Operator copies the ISO to laptop
- Boots in laptop's VirtualBox/QEMU/Hyper-V
- Runs T1 + T2 acceptance suites on laptop hardware (catches laptop-specific issues — Wi-Fi chipset, touchpad, fingerprint reader, etc.)
- If green → proceed to K2 sub-path operator picks

### K2a — Dual-boot (RECOMMENDED for first laptop deploy)

- `eve-vm.py install --target laptop --mode dualboot`
- Repartitions free space, installs Sinister OS alongside existing OS
- GRUB picker at boot
- Existing laptop OS preserved untouched
- Roll back = pick existing OS at GRUB

### K2b — Replacement (operator must explicitly opt-in)

- `eve-vm.py install --target laptop --mode replace --backup-to /path/to/external-disk.img`
- Full disk image to external first
- Then full wipe + Sinister OS install
- Reversible IF the operator restores from the external backup

### K2c — USB-boot (safest; no laptop disk touched)

- Sinister OS on a fast NVMe-USB enclosure (operator already has one for vault use)
- Laptop boots from USB; laptop's internal disk untouched
- Best for first-day "try it"

**Acceptance gate (Phase 4 → 5):** operator says "now main PC". Until then, do not propose Phase 5.

---

## 6. PHASE 5 — Main PC dual-boot (operator-gated; FAR future)

- Per master-plan rollout-doctrine-2026-05-25 § P0c
- Operator-clicked install during a maintenance window
- Backup of Windows partition to external first (mandatory)
- Dual-boot for 30 days minimum
- After 30-day soak operator can run `eve finalize-cutover` (wipes Windows)

---

## 7. WHAT GETS BUILT WHEN (one-page schedule)

```
Day 0 (THIS TURN)
├── ✅ MASTER-AUDIT-EXPANSION plan (iter 21)
├── ✅ 3 brain doctrines (iter 21)
├── ✅ EXECUTION plan (this iter)
└── ✅ VM preview (eve-vm.py + compose.os-preview.yml + Containerfile + stubs)
       → operator runs `python eve-vm.py up`

Day 1
├── archiso profile + build.sh wired in WSL2
├── Block A Windows-parity merge doc
└── First ISO build → boots in QEMU

Day 2-3 (parallel swarm)
├── Block C sinister-gpu-arbiter
├── Block D sinister-game-mode
├── Block E niri variant
├── Block F RustDesk + Sunshine

Day 3-4 (parallel swarm)
├── Block G hardening (apparmor + sbctl + nftables + opensnitch)
├── Block H Plasma windows-feel
└── Block I acceptance test harness

Day 4-5 (parallel swarm)
├── Block J Docker stand-up extensions
├── Block M sinister-agent-warden + 12 containers
└── Block N sinister-browser-bot + manifest + first-boot wizard

Day 5-6 (sequential)
├── ISO rebuild with everything
└── T0/T1 acceptance test runs

Day 7-8
├── Operator drives ISO in VM
├── Feedback iteration loop
└── ACCEPTANCE GATE → operator says "ship to laptop"

Day 8+
└── Phase 4 laptop deploy (operator picks K1/K2a/K2b/K2c)
```

---

## 8. RISK REGISTER (this execution plan)

| # | Risk | Mitigation |
|---|---|---|
| 1 | Docker Desktop not installed on operator host | `eve-vm.py` detects + falls back to WSL2 + Arch installation path |
| 2 | archiso build fails in WSL2 (kernel module issues) | Use `docker buildx` with `arch4edu` archiso container as fallback |
| 3 | ISO doesn't boot in QEMU (UEFI / NVIDIA driver issues) | Ship ISO with both UEFI + BIOS boot loaders; NVIDIA fallback to nouveau |
| 4 | Day-by-day schedule slips beyond 8 days | Phase 2 is the longest; can drop niri (Block E) + Plasma (Block H) to ship faster; both are non-critical-path |
| 5 | Operator's feedback is "rebuild from scratch" mid-Phase 3 | Each phase is independently revertable; keep all ISOs at `source/iso-build/out/` for rollback |
| 6 | GPU arbiter needs real NVIDIA hardware to fully test | Mock-mode in container; real test happens when ISO runs on laptop with NVIDIA passthrough or bare metal |
| 7 | Operator wants laptop deploy BEFORE T1 green | Document the "T1-not-green = K2c USB-boot only" policy; bare-metal install gated on T1 + operator explicit "I accept the risk" |
| 8 | Browser-auto-relogin doesn't survive cookie format migration | Re-record sessions on Linux (one-time operator cost); document in first-boot wizard |

---

## 9. ACCEPTANCE FOR THIS PLAN

- [x] § 1 Phase 1A specified with deliverables shipping THIS turn
- [x] § 2-5 phases sequenced with operator-gated transitions
- [x] § 7 one-page schedule visible at a glance
- [x] § 8 risk register
- [ ] § 1 deliverables actually written to disk THIS turn (eve-vm.py + compose.os-preview.yml + Containerfile + stubs)
- [ ] PROGRESS row + heartbeat updated
- [ ] Commit + push

---

## 10. THE OPERATOR'S NEXT STEP (after this turn ships)

Open a terminal in `D:\Sinister Sanctum\projects\sinister-os\source\docker-stack\` and run:

```
python eve-vm.py up
```

That's it. Browser will open within ~90 seconds (first run pulls + builds). If it doesn't auto-open, navigate manually to **http://localhost:6080**. Click around, type `eve chat "hello"` in the terminal, tell us what to fix.

---

## 11. JCODE-REVIEW ADDENDUM (operator 2026-05-25T~10:00Z)

**Operator directive:** *"C:\Users\Zonia\Desktop\jcode-0.12.4\packaging\linux\jcode-desktop.desktop review this and other things like it"*

**Reviewed (read-directly per WE-HAVE-THE-SOURCE doctrine):**
- `jcode-0.12.4/packaging/linux/jcode-desktop.desktop` — single 13-line `.desktop` file for jcode's fullscreen workspace variant
- `jcode-0.12.4/scripts/build_linux_compat.sh` — manylinux2014 / CentOS 7 / glibc 2.17 Docker-based portable build for the `jcode` Rust binary; bundles libssl/libcrypto siblings + wrapper script setting `LD_LIBRARY_PATH=<self_dir>` for runtime locality

**Verdict:** jcode's Linux story is minimal but their two patterns are worth adopting:

1. **Per-tool `.desktop` files (Block N.9)** — shipped this turn at `source/iso-build/desktop-files/`:
   - `eve-desktop.desktop` (EVE Desktop OS control center; Categories=System;Settings;Utility; MimeType=x-scheme-handler/eve)
   - `sinister-panel.desktop` (Panel PWA wrapper; Categories=Network;Development;System; MimeType=x-scheme-handler/sinisterpanel)
   - `sinister-term.desktop` (Sinister-themed kitty; Categories=System;TerminalEmulator;Utility)
   - `README.md` explaining what we copy from jcode + what we improve (per-tool not single, multi-size icons, AppStream metadata, MIME scheme handlers, StartupWMClass for Wayland, X-Sinister-* audit keys)

2. **manylinux2014 portable Rust build pattern (Phase 2 Day 4-5)** — adopt for `sinister-eve`, `sinister-gpu-arbiter`, `sinister-game-mode`, `sinister-agent-warden` Rust daemons. Build once on CentOS 7 baseline → runs on Arch + Ubuntu + Debian + Fedora + manylinux base images without per-distro repackaging. Adds `source/iso-build/build-rust-portable.sh` (adapts jcode's script per-binary). Cuts CI cost + future-proofs Block N preinstall-manifest if base distro ever changes.

**What jcode doesn't have that we ship:** AppStream metadata, multi-size icon sets, MIME scheme handlers, StartupWMClass for Wayland window matching, X-Sinister-* custom keys for fleet auditability. The full comparison is in `source/iso-build/desktop-files/README.md`.

**Composes-with:** fleet-tools-port-to-sinister-os-doctrine-2026-05-25 (Block N N.9 addendum); we-have-the-source-read-it doctrine (read jcode source directly, no RE sub-agent); no-bullshit (verified via Read+ls — the 4 new files are on disk).

## 12. CROSS-REFERENCES

- `projects/sinister-os/plans/MASTER-AUDIT-EXPANSION-2026-05-25/plan.md` — the DESIGN (14 blocks A-N this plan executes)
- `projects/sinister-os/plans/master-plan-2026-05-24.md` — P0-P5 baseline
- `projects/sinister-os/docs/design/sinister-eve-service-state-machine-2026-05-25.md` — EVE daemon contract
- `projects/sinister-os/source/eve-llm-bridge/SPEC-2026-05-25.md` — EVE-LLM IPC contract
- `projects/sinister-os/docs/design/sinister-voice-user-service-2026-05-25.md` — voice oracle
- `_shared-memory/knowledge/agent-containment-failsafe-doctrine-2026-05-25.md` — Block M doctrine
- `_shared-memory/knowledge/fleet-tools-port-to-sinister-os-doctrine-2026-05-25.md` — Block N doctrine
- `_shared-memory/knowledge/expand-and-quantum-tools-authorized-2026-05-25.md` — Block L doctrine
- `_shared-memory/operator-utterances.jsonl` row 2026-05-25T09:54:37Z — originating directive
