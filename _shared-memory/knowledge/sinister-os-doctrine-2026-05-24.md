<!-- decay:
  category: fact
  confidence: 0.85
  reinforcements: 0
  half_life_days: 180
-->
# Sinister OS — doctrine

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Slug:** `sinister-os-doctrine-2026-05-24`
> **Scope:** fleet-wide (any lane that needs to know what Sinister OS is)
> **Status:** P0 (spec lock) shipped; P1-P5 await operator gate.

## What it is

Sinister OS is the operator's full-PC operating system replacement — Linux-based, EVE-controlled, gaming-capable, brand-consistent with the Sinister fleet. Read the full master plan at `projects/sinister-os/plans/master-plan-2026-05-24.md`.

## Why it exists (operator-stated need, 2026-05-24)

> *"i can use to replace the current operating system i have on my pc so that eve can have complete control with no nonsense. i can still play games etc and have all features i want because we will build them."*

Two truths held together:
1. EVE owns root-level system control without UAC-style per-action friction.
2. The operator keeps every productivity / gaming / creative capability he has today.

## Base stack (locked at P0)

- Arch Linux + linux-cachyos kernel
- Hyprland (Wayland) primary; i3 (Xorg) fallback
- systemd + PipeWire + WirePlumber
- btrfs + snapper for rollback
- pacman + paru (AUR helper)
- nvidia-open-dkms for NVIDIA GPUs; mesa for everything else

## EVE control model (the "no nonsense" mechanism)

- EVE runs as the `eve` system user.
- `/etc/sudoers.d/eve` grants NOPASSWD for a curated allowlist (pacman, systemctl, mount, nmcli, etc.).
- Destructive commands (rm, dd, mkfs, parted, efibootmgr) require operator hotkey-confirm (Super+Y within 30s) — explicitly excluded from the allowlist.
- `sinister-eve.service` is a system service listening on `/run/sinister/eve.sock`.
- Voice (`sinister-voice` user service) and hotkey overlay (`eve-overlay` GTK4) both pipe into the eve socket.
- Every action logged to `/var/log/sinister/eve.jsonl`.

## Phased delivery

| Phase | Description | Status |
|---|---|---|
| P0 | Spec lock + scaffold | ✅ Shipped 2026-05-24 |
| P1 | Minimal bootable ISO in VM | ⏳ Operator-gated |
| P2 | Install on spare partition (dual-boot) for soak | ⏳ Operator-gated |
| P3 | EVE-as-shell daemon production | ⏳ Operator-gated |
| P4 | Gaming + creative + productivity stacks proven | ⏳ Operator-gated |
| P5 | Cutover from Windows; wipe Windows partition | ⏳ Operator-gated |

## Fleet integration

When Sinister OS becomes the operator's daily driver:
- `D:\Sinister Sanctum\` becomes `/srv/sinister/sanctum/` (auto-mounted, journal-watched).
- RKOJ becomes a native Linux tray app.
- Vault runs as a systemd service mounted at `/mnt/sinister-vault`.
- Mind / Forge / Bots all run as systemd user services with hotkey access.
- The MCP bus exposes as DBus (`org.sinister.Bus`) so any app can call bots without a Claude Code session in the foreground.

## What this doctrine ASKS of other lanes (when P5 lands)

1. Per-project lanes' source/ folders may move from `D:\Sinister\01_Projects\...` to `/srv/sinister/01_Projects/...` — junctions become symlinks. Per-project CLAUDE.md should not hardcode the `D:\` prefix.
2. Per-project automations that shell out to `powershell.exe` may need bash equivalents. Cross-platform PowerShell (pwsh) helps but doesn't cover everything (drive-letter handling, Windows-specific Win32 APIs).
3. Per-project `.bat` launchers may need `.sh` siblings. Sanctum will provide a `launcher-shim/` tool to dual-emit.

These are forward-looking notes — no lane needs to act on them until P4 starts (operator-gated).

## Reversibility wall

- Through P4: every phase is fully reversible. The operator's Windows install is untouched (we only write to a spare partition).
- P5 = the irreversible step. Operator types `sinister-os finalize-cutover` to wipe Windows. Until that command, the operator can boot back to Windows.

## Composes with

- `_shared-memory/knowledge/sanctioned-bypasses-doctrine-2026-05-21.md` (EVE NOPASSWD allowlist is the OS-level instance of the doctrine's "operator has authorized class-level bypasses").
- `_shared-memory/knowledge/do-not-revert-operator-canonical-protections-2026-05-23.md` (Sinister OS inherits the 6 canonical protections; ISO build embeds them in the system CLAUDE.md image).
- `_shared-memory/knowledge/agent-identity-eve.md` (Sinister OS is the canonical home for the EVE persona).
- `_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md` (every phase boundary requires evidence-in-the-same-turn; no "claimed-but-unverified" gating).
