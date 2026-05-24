> **Author:** RKOJ-ELENO :: 2026-05-24

# GitHub prior art for Sinister OS (Arch + Hyprland + gaming)

Operator directive (verbatim 2026-05-24): *"grab all you can from giuthub that already works to do all of this. jerry rig it together and improave all areas you can"*. This file is the catalog of mature, FOSS-permissive prior art the Sinister OS lane should lift from rather than reinvent. Every URL below was WebFetched on 2026-05-24 and confirmed alive (or marked archived / dead). Sister doc with the top-3 ranking lives at `research/recommended-bases.md`.

## Summary table

| # | Project | URL | Stars | License | Status | Verdict |
|---|---------|-----|-------|---------|--------|---------|
| 1 | CachyOS Live ISO | [CachyOS/CachyOS-Live-ISO](https://github.com/CachyOS/CachyOS-Live-ISO) | 80 | GPL-3.0 | Active | Fork as ISO-build base |
| 2 | CachyOS Settings | [CachyOS/CachyOS-Settings](https://github.com/CachyOS/CachyOS-Settings) | 380 | (org GPL-3.0) | Active | Lift kernel/perf tweaks |
| 3 | CachyOS Calamares | [CachyOS/cachyos-calamares](https://github.com/CachyOS/cachyos-calamares) | 53 | GPL-3.0 fork | Active | Lift installer fork |
| 4 | CachyOS Hyprland Settings | [CachyOS/cachyos-hyprland-settings](https://github.com/CachyOS/cachyos-hyprland-settings) | 125 | unspecified | Archived 2025-11 | Lift static configs only |
| 5 | proton-cachyos | [CachyOS/proton-cachyos](https://github.com/CachyOS/proton-cachyos) | 865 | (Wine LGPL) | Active | Lift Proton-GE wrapper |
| 6 | Garuda Tools | [garuda-linux/tools/garuda-tools](https://gitlab.com/garuda-linux/tools/garuda-tools) | n/a (GitLab) | GPL-3.0+ | Active (240 commits) | Lift gaming-stack package list |
| 7 | EndeavourOS ISO | [endeavouros-team/EndeavourOS-ISO](https://github.com/endeavouros-team/EndeavourOS-ISO) | 507 | GPL-3.0 | Active (699 commits) | Lift archiso skeleton + Calamares glue |
| 8 | ArcoLinuxL ISO | [arcolinux/arcolinuxl-iso](https://github.com/arcolinux/arcolinuxl-iso) | 89 | GPL-3.0 | Archived 2024-04 | Lift multi-bootloader pattern (GRUB + systemd-boot + rEFInd) |
| 9 | blendOS core | [blend-os/blendOS](https://github.com/blend-os/blendOS) | 787 | GPL-3.0 | Active (mirror; primary at git.blendos.co) | Steal container-app model only |
| 10 | blend-inst | [blend-os/blend-inst](https://github.com/blend-os/blend-inst) | 9 | GPL-3.0 | Active 2026-02 | Skip (low maturity) |
| 11 | HyDE (Hyprdots fork) | [Hyde-Project/Hyde](https://github.com/Hyde-Project/Hyde) | 9.1k | GPL-3.0 | Active 2026-03 | Lift Hyprland config + theme system |
| 12 | ML4W Dotfiles | [mylinuxforwork/dotfiles](https://github.com/mylinuxforwork/dotfiles) | 4.8k | GPL-3.0 | Active 2026-05 | Lift wallpaper-derived material theming |
| 13 | Hyprdots (original) | [prasanthrangan/hyprdots](https://github.com/prasanthrangan/hyprdots) | 8.5k | GPL-3.0 | Deprecated; use HyDE | Skip (use HyDE) |
| 14 | archiso (upstream) | [archlinux/archiso](https://github.com/archlinux/archiso) | 293 | GPL-3.0-or-later | Active | Build foundation (transitive) |
| 15 | Calamares (upstream) | [calamares/calamares](https://github.com/calamares/calamares) | 1.5k | REUSE/multi (LGPL/BSD/MIT) | Archived 2025-08; moved to Codeberg | Track via CachyOS fork |

All non-archived candidates are FOSS-permissive (GPL-3.0 family). One license caveat: `cachyos-hyprland-settings` (#4) ships no LICENSE file in-repo despite being a CachyOS-org GPL-3.0 project — we should treat it as GPL-3.0 by org convention but file an issue / cite the org policy before lifting verbatim. Two upstreams (Calamares #15, Hyprdots #13) have moved off GitHub; we follow the live forks (CachyOS fork for Calamares, HyDE for Hyprdots).

## Per-candidate writeup

### 1. CachyOS (the heavyweight — fork-base candidate)

[CachyOS](https://github.com/CachyOS) ships a full Arch derivative with a custom performance kernel ([linux-cachyos](https://github.com/CachyOS/linux-cachyos), 3.7k stars), pre-tuned settings, calamares installer, archiso ISO pipeline, Hyprland edition configs, and their own Proton fork for Steam. The Live ISO repo uses `archiso` with a `buildiso.sh` profile-driven entry point — clean enough to fork as our P1 ISO-build base. Their Hyprland settings repo was archived 2025-11 (the configs are still useful as static input; just don't depend on upstream updates). Their calamares fork (53 stars, GPL-3.0) is where the gaming/multilib/Proton-GE preselection logic lives — we lift this nearly intact. Avoid: heavy CachyOS branding in `airootfs/etc/skel/.config/`; their telemetry-free posture is fine but double-check `cachyos-rate-mirrors` doesn't phone home (it doesn't, per archlinux mirrorlist contract). One-line: **fork as base — strongest single source for installer + kernel + gaming**.

### 2. Garuda Linux

[garuda-tools on GitLab](https://gitlab.com/garuda-linux/tools/garuda-tools) (GPL-3.0+, 240 commits) is the ISO/image builder. Garuda's strength is the curated gaming meta-package (`garuda-gamer`) — pulls Steam, Lutris, MangoHud, GameMode, Wine-staging, Proton-GE, OBS in one shot. KDE Dragonized is heavily branded and not our target (we want Hyprland), so skip their DE work. License is permissive. Active but slow-moving (no tagged releases). One-line: **steal `garuda-gamer` package list + chaotic-aur opt-in pattern**.

### 3. EndeavourOS

[EndeavourOS-ISO](https://github.com/endeavouros-team/EndeavourOS-ISO) (507 stars, GPL-3.0, 699 commits, KDE live env) is the cleanest "thin layer over archiso" reference in the ecosystem. They explicitly call out using a "hugely modified" archiso + Calamares fork — the archiso modifications (systemd-boot + syslinux dual-boot, custom packages dir, naming convention) are exactly the pattern we want. EndeavourOS is famously light-touch (no telemetry, no enforced branding past first boot). One-line: **lift archiso skeleton + Calamares glue verbatim**.

### 4. ArcoLinux

[ArcoLinux org](https://github.com/arcolinux) has 477 repos — too many. The relevant one ([arcolinuxl-iso](https://github.com/arcolinux/arcolinuxl-iso), 89 stars, archived 2024-04) demonstrates GRUB + systemd-boot + rEFInd triple-bootloader support in one ISO, which is rare. Active development moved to [arconetpro](https://github.com/orgs/arconetpro/repositories). The [archlinux-tweak-tool](https://github.com/arcolinux/archlinux-tweak-tool) (184 stars, GPL-3.0, last update 2025-06) is a Python+Qt post-install settings panel we could borrow shape-of for EVE's OS-control GUI. One-line: **steal multi-bootloader recipe + tweak-tool UX pattern**.

### 5. Manjaro Hyprland

The github repo `manjaro-hyprland/manjaro-hyprland-settings` was a 404 in our probe and Manjaro Hyprland is community-maintained with shifting org names. Manjaro itself uses Calamares + their own `manjaro-tools` (not pure archiso). Not worth chasing — CachyOS Hyprland is the better-maintained drop-in. One-line: **skip**.

### 6. BlendOS

[blendOS](https://github.com/blend-os/blendOS) (787 stars, GPL-3.0) is an immutable Arch with container-based app delivery (you run a Fedora-app, Ubuntu-app, etc., side-by-side via `blend` package manager). GitHub is read-only mirror; primary dev at git.blendos.co. The container-app model is interesting for our P4 "stacks" goal (Steam in a container, OBS in a container) but the maturity is low (blend-inst at 9 stars) and immutable root conflicts with EVE's NOPASSWD sudo design. One-line: **steal container-app delivery model only — do NOT base on immutable root**.

### 7. HyDE (formerly Hyprdots)

[HyDE](https://github.com/Hyde-Project/Hyde) (9.1k stars, GPL-3.0, active 2026-03) is the maintained fork of [prasanthrangan/hyprdots](https://github.com/prasanthrangan/hyprdots) (8.5k stars, deprecated). Ships a full Hyprland desktop: Catppuccin/Tokyo Night/Gruvbox/Rose-Pine themes, themepatcher, wallbash dynamic color generation, Rofi launcher with 12+ styles, wlogout, game launcher, HyDEVM for testing in a VM. This is the single highest-impact lift in the catalog — it would take us months to build the equivalent. One-line: **lift the entire Hyprland config + theme system; reskin with Sinister purple accent**.

### 8. ML4W Dotfiles

[ML4W dotfiles](https://github.com/mylinuxforwork/dotfiles) (4.8k stars, GPL-3.0, v2.12.3 May 2026, ships a live ISO) is the wallpaper-derived material-color Hyprland setup. Adaptive theming from wallpaper is a polish feature HyDE also has via wallbash; choose one. ML4W also has a Lua config branch (rolling v2.13.0). One-line: **lift wallpaper-derived material theming as alternative to HyDE wallbash**.

## Upstream foundations (transitive)

[archiso](https://github.com/archlinux/archiso) (GPL-3.0-or-later, 293 stars, active) is the upstream build framework everyone else wraps. [Calamares](https://github.com/calamares/calamares) (1.5k stars, archived on GitHub 2025-08, primary on Codeberg) is the installer framework everyone else forks. We track these via the CachyOS forks rather than vendoring upstream directly — CachyOS keeps them current and gaming-ready.

Word count: ~1,050.
