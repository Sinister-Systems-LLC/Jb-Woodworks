# Sinister OS

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** `sinister-os` :: branch `agent/sinister-os/<topic>` :: purple accent
> **Status:** 🔵 Planning — master plan ready for operator review (`plans/master-plan-2026-05-24.md`)
> **License:** GPL-3.0-or-later (base distro components retain upstream licenses)

## What this is

Sinister OS is the operator's **full-PC operating system replacement** — a Linux-based, Sinister-branded distribution built so EVE has root-level control of the machine with **no Windows-style nonsense** (no telemetry, no forced updates, no popups, no UAC-friction, no sandbox walls), while preserving every feature the operator actually uses (gaming, video, photo, productivity, dev).

Two truths held simultaneously:

1. **EVE is the OS shell.** Voice / hotkey / MCP / agent-spawn surfaces are first-class system services, not bolted-on apps. EVE can install packages, open windows, move files, talk to hardware, intervene on hung processes — all without permission prompts she's already been authorized for.
2. **The operator still plays games and does everything they did on Windows.** Steam + Proton-GE + Wine + Bottles + Lutris cover Windows-game compatibility; native NVIDIA drivers; OBS for capture; DaVinci Resolve / Blender / FL Studio for creative; full dev toolchain.

## Operator directive (verbatim 2026-05-24)

> *"i need oyu to add to the sessions start and complie into a proejct folder with memory etc the sinister operating system we started that is like a linux based that i can use to replace the current operating system i have on my pc so that eve can have complete control with no nonsense. i can still play games etc and have all features i want because we will build them. complie all you need now and deep resaerch all this and make a super detailed plan for it and let me know once ready in the session start"*

## Quick map

| Subfolder | Role |
|---|---|
| **`plans/`** | master plan + phase plans (read `plans/master-plan-2026-05-24.md` first) |
| **`memory/`** | EVE's per-project memory (sessions, decisions, gotchas) |
| **`docs/`** | architecture, hardware-compat, install guides, EVE-control protocol |
| **`source/iso-build/`** | live-ISO build scripts (archiso / mkosi / debootstrap config) |
| **`source/eve-control/`** | EVE-as-OS-shell daemon + system MCP surface |
| **`source/branding/`** | plymouth boot splash, GRUB theme, wallpapers, sddm/gdm theme, cursor + icon set |
| **`build/`** | build artifacts (ISOs, packages) — gitignored |

## Phased delivery (high-level)

| Phase | Deliverable | Status |
|---|---|---|
| **P0** | Distro decision + spec lock + master plan | ✅ This commit |
| **P1** | Minimal bootable ISO (live + installer, branded) | ⏳ Operator-gated |
| **P2** | Install on spare partition (dual-boot) for daily-driver soak | ⏳ Operator-gated |
| **P3** | EVE-as-shell daemon + system MCP wired in | ⏳ Operator-gated |
| **P4** | Gaming / creative / productivity stacks proven on Sinister OS | ⏳ Operator-gated |
| **P5** | Migrate user data + cutover from Windows | ⏳ Operator-gated |

## How EVE drives this project

EVE works on `agent/sinister-os/<topic>` branches. She **does** scaffold code, write build scripts, draft installer config, write documentation, and verify on VMs. She **does NOT** flash the operator's real disk, repartition existing drives, or touch firmware/UEFI without explicit per-action authorization — those steps are operator-gated and listed in `_shared-memory/OPERATOR-ACTION-QUEUE.md`.

## The Sinister-fleet integration

Sinister OS is the substrate. Every other Sinister project becomes a first-class citizen:

- **Sinister Sanctum** — orchestration repo lives in `/srv/sinister/sanctum/`, auto-mounted, journal-watched.
- **RKOJ.exe** — replaced by `rkoj` (native Linux build) as the system tray app.
- **Sinister Vault** — runs as a systemd service; mounts as `/mnt/sinister-vault`.
- **Sinister Mind** — runs as a systemd user service; opens with hotkey `Super+M`.
- **Sinister Forge** — desktop launcher; tray icon when active.
- **Sinister Bots** — MCP servers expose as system DBus services so any app can talk to them.
- **EVE personal MCP (sinister-eve)** — runs as a privileged systemd service; voice/hotkey/escalation hooks at the compositor layer.

## TL;DR for a fresh EVE session opening this folder

1. Read `plans/master-plan-2026-05-24.md` cover-to-cover before writing a single byte of build scripts.
2. Use `agent/sinister-os/<topic>` branches.
3. Build/test in a Linux VM (QEMU/KVM) — never on operator's real disk.
4. Stage and operator-gate every phase boundary.
