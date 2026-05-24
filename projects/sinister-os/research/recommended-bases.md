> **Author:** RKOJ-ELENO :: 2026-05-24

# Recommended bases — top 3 ranked

Companion to `research/github-prior-art-2026-05-24.md`. These are the three repos to clone first for Sinister OS P1 (ISO build) through P3 (Hyprland EVE shell). Every recommendation cites the specific subset we lift, not a wholesale fork.

## 1. CachyOS (fork as base) — primary distro skeleton

URL: [CachyOS/CachyOS-Live-ISO](https://github.com/CachyOS/CachyOS-Live-ISO) (GPL-3.0, 80 stars, active) + [CachyOS/cachyos-calamares](https://github.com/CachyOS/cachyos-calamares) (GPL-3.0, 53 stars, active) + [CachyOS/CachyOS-Settings](https://github.com/CachyOS/CachyOS-Settings) (380 stars).

LIFT:
- `buildiso.sh` profile-driven archiso runner + `airootfs/` skeleton from Live-ISO (rename `cachyos-*` → `sinister-*`).
- Calamares fork with gaming/multilib/Proton-GE preselection logic (modules under `src/modules/`).
- CachyOS-Settings sysctl/udev/cpufreq tunings — keep verbatim, drop `cachyos-` package deps that pull branding.

DO NOT TAKE: CachyOS branding in `etc/skel`, calamares-branding repo, `cachyos-hello` welcome app, plymouth theme.

## 2. HyDE (Hyprdots fork) — Hyprland desktop

URL: [Hyde-Project/Hyde](https://github.com/Hyde-Project/Hyde) (GPL-3.0, 9.1k stars, active 2026-03).

LIFT:
- Entire `Configs/.config/hypr/` + `Configs/.config/waybar/` + `Configs/.config/rofi/` tree.
- `themepatcher` + `wallbash` dynamic-color engine (this is months of work we get for free).
- HyDEVM test pattern (we already require VM testing per lane rules — slot HyDEVM in).
- Rofi + wlogout + game-launcher menus, restyled with Sinister purple.

DO NOT TAKE: HyDE branding splash, default catppuccin selection (we ship Sinister-purple as default with HyDE themes as alternates).

## 3. EndeavourOS ISO — archiso recipe reference

URL: [endeavouros-team/EndeavourOS-ISO](https://github.com/endeavouros-team/EndeavourOS-ISO) (GPL-3.0, 507 stars, 699 commits, active).

LIFT:
- Dual systemd-boot + syslinux bootloader entries (BIOS + UEFI in one ISO).
- `airootfs/root/packages` local-package mechanism (lets us inject Sinister-specific PKGBUILDs without a separate repo at first).
- ISO naming convention `SinisterOS_<codename>-YYYY.MM.DD.iso`.
- Their Calamares-fork glue (online + offline install modes).

DO NOT TAKE: EndeavourOS KDE live env (we ship Hyprland live), EndeavourOS welcome app.

## Composition strategy

P1 = fork CachyOS-Live-ISO as `sinister-os-iso`, rename, swap in HyDE Hyprland configs into `airootfs/etc/skel/.config/`, borrow EndeavourOS's bootloader entries and local-packages mechanism. P2 = fork cachyos-calamares as `sinister-installer`. P3 = HyDE configs become the user-default Hyprland config; EVE's hotkeys layer on top via Hyprland `bind` directives.

Garuda's `garuda-gamer` meta-package list (research file #6) is the source-of-truth for the gaming package set we preselect in the calamares fork — not a base, just a reference list.

Word count: ~310.
