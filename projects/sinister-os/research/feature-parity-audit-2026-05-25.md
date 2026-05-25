# Feature parity audit — Windows operator workflow → Sinister OS

> Author: RKOJ-ELENO :: 2026-05-25
> Lane: sinister-os
> Composes with: `docs/no-function-loss-doctrine-2026-05-25.md`, `docs/rollout-doctrine-2026-05-25.md` (P0c gate), massive-expansion plan iter 13.

## Operator directive (verbatim, 2026-05-24T21:08Z)

> *"make sure i loose no function that i use on this pc"*

This audit is the **anchor reference** for the P0c gate. Every row that's still `BLOCKED` or `TBD` is a P0c blocker. Sinister OS does NOT advance to P0c until the BLOCKED list is empty OR each row carries an operator OK + rationale.

The list is derived from agent B's research run (massive-expansion plan iter 8) + operator's daily-driver observation from PROGRESS logs + workstation surveys at `_shared-memory/WORKSTATION.md`. Operator should append rows as he notices gaps; no row is closed without verification on the target Linux variant.

## Status legend

| Symbol | Meaning |
|---|---|
| ✅ COVERED | Verified working on Linux equivalent in a VM smoke. |
| 🟡 LIKELY | Standard Linux story; no smoke yet but no known blocker. |
| 🔴 BLOCKED | Known regression vs Windows; needs a workaround or an operator-OK to defer. |
| ⏳ TBD | Not yet investigated for this lane. |

## Daily-driver inventory

### A. Core development + agent fleet

| Windows feature | Linux replacement | Status | Notes |
|---|---|---|---|
| Claude Code CLI | Claude Code CLI (Linux x86_64 binary) | ✅ | Same binary, same flags including `--dangerously-skip-permissions`. |
| PowerShell 5.1 + 7.x | pwsh (PowerShell 7) | 🟡 | Most fleet scripts are pwsh-compatible. PS 5.1-only scripts (e.g. WMI cmdlets) need port. Audit pending: `automations/*.ps1` for `Get-WmiObject` / `Win32_*` usage. |
| Git Bash (git-for-windows mintty) | native bash / kitty / wezterm | ✅ | Better; bash is native. |
| VS Code + extensions | VS Code (official .deb / Flathub) | ✅ | Same UX. |
| Node + npm + bun | Same via nvm / asdf / pacman | ✅ | |
| Python 3.x (Microsoft Store) | Python 3.x (pacman / apt) | ✅ | |
| Docker Desktop | Podman + podman-compose OR Docker CE | 🟡 | Podman preferred (rootless); docker-compose.yml works as-is via podman-compose. |
| WSL2 | n/a — host IS Linux | ✅ | Strictly better. |

### B. Operator personal apps

| Windows feature | Linux replacement | Status | Notes |
|---|---|---|---|
| Discord (native) | Discord (.deb / Flatpak) | ✅ | |
| Steam + library | Steam (native) + Proton | 🟡 | Anti-cheat games are the risk; need per-game check. P0c spike. |
| Steam VR / Quest Link | ALVR / Steamcast / Monado | 🔴 | Quest Link officially Windows-only. Workaround: ALVR for wireless. Operator OK pending. |
| OBS Studio | OBS Studio | ✅ | |
| Spotify | Spotify (Flathub) | ✅ | |
| Browser (Chrome / Edge / Brave) | Same | ✅ | Profile sync via Firefox / Brave account; Edge has Linux build. |
| Adobe Photoshop / Illustrator | GIMP / Krita / Affinity-via-Wine | 🔴 | If operator depends on PS/AI: hard blocker. Mitigation = dual-boot Windows for these. |
| MS Office | LibreOffice / OnlyOffice / Office365 web | 🟡 | Web is fine for most workflows. |
| iMessage Bridge | iMessage Bridge (already a sister lane: `_shared-memory/inbox/sinister-os/2026-05-24T*-from-imessage-bridge-*.json`) | ✅ | Already targets Linux. |

### C. Operator infra integrations

| Windows feature | Linux replacement | Status | Notes |
|---|---|---|---|
| Sinister Vault (D:\sinister-vault\) | sinister-vault (Linux daemon, port 5078) | ✅ | Already cross-platform. |
| EVE.exe / Sinister Start.bat | EVE (Linux binary, same source) | ⏳ | PyInstaller spec needs Linux target stanza; not yet built/tested. P0b blocker. |
| Tailscale | Tailscale (native, better) | ✅ | |
| GitHub Desktop | gh CLI / lazygit / VS Code git | ✅ | Better via gh + lazygit. |
| RKOJ workbench (Qt) | Same Qt (PySide6) — cross-platform | 🟡 | Build needs verification on Wayland (XCB fallback). |
| Sinister Panel (Next.js) | Same (Next.js is Linux-first) | ✅ | |

### D. Hardware

| Windows feature | Linux replacement | Status | Notes |
|---|---|---|---|
| NVIDIA driver | nvidia-dkms (proprietary) or nouveau | 🟡 | Proprietary: log in `docs/proprietary-blobs.md` per CLAUDE.md rule 4. |
| Audio (DAC + bluetooth) | Pipewire + Wireplumber + bluez | 🟡 | Default for Hyprland-class stacks. |
| Multi-monitor + 144Hz | Hyprland (Wayland) | 🟡 | Per-monitor refresh works on Wayland; need verification. |
| Game controllers (Xbox / DualShock) | xpadneo / ds4drv | ✅ | |
| Webcam | uvcvideo (built-in) | ✅ | |
| Yurikey 50/51/52 hardware security keys | libfido2 + udev rules | ⏳ | Signing-oracle lane (kernel-apk, snap-emu) needs the udev rules ported. Not P0b/P0c blocker since signing happens off-the-OS, but flag for P5. |
| Pixel 6a USB (adb / fastboot) | adb / fastboot (Linux native) | ✅ | Already better-supported on Linux. |
| UEFI / TPM 2.0 | systemd-boot / sbctl + tpm2-tools | 🟡 | btrfs snapper requires care with TPM-sealed disk encryption. |

### E. Operator-private workflows

| Windows feature | Linux replacement | Status | Notes |
|---|---|---|---|
| Desktop shortcuts to .bat files | systemd user units OR .desktop launchers OR EVE workflows (`.janet`) | 🟡 | Hyprland .desktop is standard; .janet workflows are an upgrade (see DSL-DESIGN-2026-05-24.md). |
| Operator-style purple accent | Skeleton CSS token `--accent: #c084fc` | ✅ | Already wired through `dashboard-skeleton`. |
| Auto-startup background apps (Sinister Vault, Tailscale, etc.) | systemd user units | ✅ | Strictly better than HKLM\Run; auditable. |
| One-click Start-Sinister-Session.bat | Hyprland keybind → `start-sinister-session.sh` (port pending) | ⏳ | PS1 → bash port needed. P0b blocker. |

## P0c gate — required-to-be-COVERED-or-OK-deferred

The following MUST be COVERED before P0c green:

- EVE Linux binary (build + smoke test)
- start-sinister-session.sh (PS1 → bash port)
- Operator's daily-driver app list (Discord / browser / VS Code / Steam-non-anti-cheat / Spotify / OBS) all run for 7-day operator-self-test
- Yurikey signing path WORKS (even if off-host) — verify operator can sign + ship from sinister-os
- NVIDIA proprietary driver path documented in `docs/proprietary-blobs.md` + signed off

The following CAN defer to P5 with operator OK:

- Adobe PS/AI (Wine attempt or accept dual-boot)
- Quest Link (ALVR or accept loss)
- PowerShell 5.1-only scripts (port to pwsh 7)

## Append-only operator surface

Operator should add rows here as he notices gaps. Format:

```
- [Windows feature] — current usage frequency (daily/weekly/monthly) — operator notes
```

(empty; populated by operator during P0b laptop self-test)

## Risk register

1. **Underestimated app list.** Operator may have apps not in this audit. Mitigation: P0b is operator-driven; new rows appended freely.
2. **Anti-cheat games.** Some Steam games refuse Proton. Mitigation: keep dual-boot through P0c; only at P5 cutover gate is Windows removed.
3. **Driver regression.** Linux NVIDIA driver matrix vs game compatibility. Mitigation: log every install in `docs/proprietary-blobs.md`; rollback via btrfs snapper if a driver bump breaks.
4. **Operator workflow muscle memory.** Win+R, alt-tab behavior, etc. Mitigation: Hyprland binds can mimic; document deltas in `docs/operator-workflow-deltas.md` (P0c sub-task).
