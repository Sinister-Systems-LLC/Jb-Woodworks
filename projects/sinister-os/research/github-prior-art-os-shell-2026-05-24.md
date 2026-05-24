# GitHub Prior-Art Sweep — Sinister OS Shell Candidates

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** sinister-os
> **Trigger:** Operator utterance 2026-05-24T12:47:52Z verbatim *"review github and see what all you can compile from other repos."* Composes with cold-start step 9 (GitHub-first sourcing).
> **Sweep agent:** general-purpose sub-agent (gh search repos + WebSearch); see _shared-memory/plans/sinister-os-m5-expand-panel-shell-2026-05-24T2034Z/plan.md.

## Top-2 recommendations (prioritize integration)

1. **ublue-os/bazzite** (Apache-2.0, 8.4k stars) — production-tested gamescope-session + Steam Flatpak stack. Lift their `system_files/` shell scripts + systemd units for the Steam-on-Linux requirement (master-plan.md § 5). Distro-portable beyond their Fedora atomic base.
2. **hyprwm/Hyprland** (BSD-3-Clause) — canonical Wayland compositor with `exec-once` + kiosk-friendly single-window layout. Directly satisfies the "boot into Sinister Panel as shell" requirement (P3 in master-plan.md). Pin a release tag; vendor config rather than tracking main.

Pair Bazzite's gaming bits with Hyprland's compositor config and we cover ~70% of P1-P3 without writing original integration code.

## Full candidate table

| Repo | URL | License | Borrow | Risk |
|---|---|---|---|---|
| ublue-os/bazzite | https://github.com/ublue-os/bazzite | Apache-2.0 | SteamOS-clone OCI build with gamescope-session, Steam Flatpak, MangoHud ready-baked | Atomic image model differs from Arch direction; shell scripts/units are distro-portable |
| hyprwm/Hyprland | https://github.com/hyprwm/Hyprland | BSD-3-Clause | Wayland compositor for kiosk single-window + autolaunch via `exec-once` | Fast-moving upstream — pin release tag |
| holoiso-eol/holoiso | https://github.com/holoiso-eol/holoiso | Other (custom) | archiso `airootfs/` overlay pattern + first-boot session-select pattern | Custom license + EOL upstream — reference only, no vendoring |
| archlinux/archiso | https://github.com/archlinux/archiso | GPL-3.0 | `mkarchiso` + `profiles/releng` — canonical Arch ISO builder | GPL-3 on builder OK (not linked into output); learn-and-rewrite if non-GPL output needed |
| Fanaperana/tauri-kiosk | https://github.com/Fanaperana/tauri-kiosk | MIT | Bare Ubuntu → kiosk Tauri webview scripts (autologin + xinitrc) | Tiny (2★), unmaintained — snippet source only |
| LTBL-Studio/kiosk-linux | https://github.com/LTBL-Studio/kiosk-linux | MIT | chromium-kiosk autologin → fullscreen browser scripts | Low stars (3★), French docs — VM-verify before adopt |
| adi1090x/CustomArch | https://github.com/adi1090x/CustomArch | GPL-3.0 | Pre-customized archiso profiles + `airootfs/etc/skel/` theme injection pattern | GPL-3 builder OK; some bundled assets non-free — audit before pull |
| end-4/dots-hyprland | https://github.com/end-4/dots-hyprland | GPL-3.0 | High-polish Hyprland Quickshell-based bar + animation patterns | GPL-3 — must stay GPL-3-compatible if reshipped; heavyweight — strip-mine |
| noctalia-dev/noctalia-shell | https://github.com/noctalia-dev/noctalia-shell | MIT | MIT-licensed Wayland desktop shell — cleanest permissive alt to dots-hyprland | Newer project + Quickshell runtime weight |
| AvengeMedia/DankMaterialShell | https://github.com/AvengeMedia/DankMaterialShell | MIT | Multi-compositor abstraction (Hyprland/sway/niri) + Material 3 token system | MIT, healthy (6.4k★); Go + Quickshell runtime weight |

## Defect surfaced this sweep

`automations/github-prior-art.ps1` has a date-filter bug: its `>{today}` filter excludes everything; the `-AllowStale` flag does not appear to disable the filter cleanly. The sub-agent worked around via direct `gh search repos` calls. **Action:** queue a bug-fix row in OPERATOR-ACTION-QUEUE or hand off to the automations lane via cross-agent inbox.

## Integration phasing (proposed)

| Phase | Source | Deliverable |
|---|---|---|
| P1 (ISO build) | archlinux/archiso + adi1090x/CustomArch | Bootable Sinister ISO via `mkarchiso` with Sinister-purple airootfs theme |
| P2 (installer) | archiso releng + Calamares (already wired) | Spare-partition install flow with Sinister branding |
| P3 (EVE shell) | hyprwm/Hyprland + noctalia-shell or LTBL-Studio/kiosk-linux | Hyprland kiosk-mode booting into containerized Sinister Panel |
| P4 (gaming) | ublue-os/bazzite system_files | Steam + Proton-GE + gamescope-session systemd units |
| P5 (cutover) | (no new sources) | Operator-gated dual-boot → primary boot |

## Compose-with

- `_shared-memory/plans/sinister-os-m5-expand-panel-shell-2026-05-24T2034Z/plan.md` § ITER 5 (panel-as-shell scaffold).
- `projects/sinister-os/plans/master-plan-2026-05-24.md` (P0→P5 phase plan).
- `projects/sinister-os/source/docker-stack/PANEL-SHELL-DEPLOY.md` § "5. Review github and see what all you can compile from other repos" row of operator-gated next steps.
- Cold-start step 9 doctrine: `_shared-memory/knowledge/github-first-sourcing-doctrine-2026-05-24.md`.
