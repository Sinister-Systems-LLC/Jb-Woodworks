# CLAUDE.md — Sinister OS

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** `sinister-os` :: branch `agent/sinister-os/<short-topic>` :: purple accent
> **Lane heartbeat:** `_shared-memory/heartbeats/sinister-os.json`
> **PROGRESS log:** `_shared-memory/PROGRESS/Sinister OS.md` (created on first commit)

This file is the lane discipline for any EVE session opened with the working directory at `D:\Sinister Sanctum\projects\sinister-os\`. It inherits from `D:\Sinister Sanctum\CLAUDE.md` (Sanctum master) — read that first, then this file.

## Mobile sub-lane (Pixel 6a custom Android)

**Consolidated 2026-05-24T22:10Z** per operator directive *"combine project sinister os and sinister os mobile."* The Pixel 6a custom-Android lane (formerly `projects/sinister-os-mobile/`) is now a sub-lane of sinister-os at `projects/sinister-os/mobile/`.

- **Mobile CLAUDE.md:** `projects/sinister-os/mobile/CLAUDE.md` — read this if your spawn lands in the mobile/ subdirectory or you're doing Pixel 6a / bluejay kernel / sepolicy / cuttlefish / Sinister-Panel-mobile work.
- **Mobile SESSION-START:** `projects/sinister-os/mobile/SESSION-START.md`
- **Mobile master-plan:** `projects/sinister-os/mobile/plans/master-plan-2026-05-24.md` (5-phase P0-P5, currently P0 spec lock)
- **Mobile branch namespace preserved:** `agent/sinister-os-mobile/*` (e.g. `agent/sinister-os-mobile/p0-spec-2026-05-24`) — distinct from `agent/sinister-os/*` for the PC sub-lane.
- **Shared heartbeat + PROGRESS + inbox + resume-points:** both PC and Mobile work flow through slug `sinister-os` (heartbeat `_shared-memory/heartbeats/sinister-os.json`, PROGRESS `_shared-memory/PROGRESS/Sinister OS.md`, inbox `_shared-memory/inbox/sinister-os/`, resume-points `_shared-memory/resume-points/Sinister OS/`).
- **Picker entry:** single `sinister-os` row (Mobile dropped from picker; pick `sinister-os` then `cd mobile/` for Pixel work, or invoke spawn with working dir = mobile/).
- **Brain doctrine slug `sinister-os-mobile-doctrine-2026-05-24` preserved** for cross-reference stability.


## What this lane owns

- `projects/sinister-os/` — all of it
- `_shared-memory/PROGRESS/Sinister OS.md` (when created)
- `_shared-memory/heartbeats/sinister-os.json`
- Brain rows tagged `sinister-os` in `_shared-memory/knowledge/_INDEX.md`
- Branches matching `agent/sinister-os/*`

## What this lane NEVER touches

- Any other project's `source/` or `memory/`
- `~/.claude/.mcp.json` (operator-owned)
- The operator's physical disk partitions or UEFI firmware
- `main` branch direct pushes (routes through `sanctum-auto-push` daemon)
- The operator's running Windows install (until Phase 5 operator-gated cutover)

## Hard rules for this lane

1. **VM-only testing.** Every install / partition / boot test runs inside QEMU/KVM/VirtualBox. Never on bare metal without explicit operator-gated approval.
2. **Phase boundaries are operator-gated.** P0 → P1 transition requires operator click. P1 → P2 requires operator click. Etc.
3. **No firmware changes without operator authorization.** GRUB, systemd-boot, UEFI vars — propose, never write, without explicit per-action OK.
4. **No proprietary blobs without surfacing them.** If a build pulls in a non-FOSS driver (NVIDIA, Realtek firmware, Steam), log it in `docs/proprietary-blobs.md` so the operator sees what's on his machine.
5. **Doctrine self-audit per Sanctum's no-bullshit doctrine.** Every claim of "boots" / "installs" / "drives EVE" carries a VM session + exit-code receipt in PROGRESS.

## EVE-as-OS-shell design constraints (from operator directive)

- EVE must have **root-equivalent control** without per-action UAC-style prompts. Implementation: dedicated `eve` system user in `sudoers` with `NOPASSWD` for a curated allowlist (`apt`, `pacman`, `systemctl`, `nmcli`, `xdotool`, etc.), policy at `/etc/sudoers.d/eve`.
- EVE control runs as a **privileged systemd service** (`sinister-eve.service`) — survives compositor crashes, restarts on failure, listens on a UNIX socket at `/run/sinister/eve.sock`.
- The voice surface (`sinister-voice`) runs as a **user service** in the operator's session — wake-word always-on; transcription goes to EVE socket.
- Hotkeys bind at the **compositor layer** (Hyprland config for Wayland; xbindkeys for Xorg fallback).
- Escalation ladder: `voice → EVE` → `EVE proposes` → `operator confirms via hotkey` → `EVE executes`. For the curated allowlist, the "confirms" step is auto-yes.

## Branch hygiene

Standing branch namespace for this lane (no contention with Sanctum master):

- `agent/sinister-os/p0-spec-2026-05-24` — current
- `agent/sinister-os/p1-iso-build-<date>` — opens when P1 is gated open
- `agent/sinister-os/p2-installer-<date>` — opens when P2 is gated open
- `agent/sinister-os/p3-eve-shell-<date>` — opens when P3 is gated open
- `agent/sinister-os/p4-stacks-<date>` — opens when P4 is gated open
- `agent/sinister-os/p5-cutover-<date>` — opens when P5 is gated open

## First-turn checklist for a fresh EVE on this lane

1. Read `README.md` (this folder) for orientation.
2. Read `plans/master-plan-2026-05-24.md` cover-to-cover.
3. Read `docs/architecture.md` for the layered system view.
4. Confirm current phase in `plans/master-plan-2026-05-24.md` § 12 (Phase status board).
5. Pick exactly one row from the current phase's queue. Mark it `in_progress`. Do the work in a VM. Commit on this lane's branch. Update PROGRESS.
6. Heartbeat + inbox poll per Sanctum Rule 9.
