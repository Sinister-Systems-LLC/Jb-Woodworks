# PACKAGE-AUDIT-2026-05-24.md

> Author: RKOJ-ELENO :: 2026-05-24
> Scope: `projects/sinister-os/source/iso-build/packages.x86_64`
> Pre-audit line count (non-comment, non-empty): **88**
> Method: cross-checked each entry against current Arch `core` / `extra` / `multilib` package availability + known AUR-only packages.

## Legend

- **PRESENT** — already listed in `packages.x86_64` AND available from `core` / `extra` / `multilib`.
- **MISSING** — not listed; would need to be added if the build target requires it.
- **NEEDS-AUR** — not available in official repos; must be sourced via `yay` (AUR) at first-boot or via a `[chaotic-aur]` entry in `pacman.conf`. Cannot be pulled by `mkarchiso` directly.
- **NEEDS-MULTILIB-ENABLED** — depends on `[multilib]`; multilib IS enabled in current `pacman.conf` (verified). Flagged here only as a reminder.
- **NON-FOSS** — proprietary / closed-source component; listed in `docs/proprietary-blobs.md`.

---

## 1. Compositor / Wayland stack (Hyprland)

| Package | Status |
|---|---|
| hyprland | PRESENT |
| hyprlock | PRESENT |
| hypridle | PRESENT |
| hyprpicker | PRESENT |
| xdg-desktop-portal-hyprland | PRESENT |
| wayland | PRESENT |
| xorg-xwayland | PRESENT |
| waybar | PRESENT |
| wofi | PRESENT |
| swaybg | PRESENT |
| mako | PRESENT |
| **kitty** | **MISSING** — referenced as terminal fallback in `airootfs/etc/skel/.config/hypr/hyprland.conf` (`bind = $mod, Q, exec, kitty \|\| foot \|\| xterm`). Without it the hotkey falls through to `foot` (also missing) then `xterm` (also missing). Add `kitty` to guarantee a working terminal. |
| **foot** | **MISSING** — Wayland-native terminal; alternative to kitty. At least one of kitty/foot is required. |
| **xdg-desktop-portal** | **MISSING** — base portal (hyprland-portal is the impl, but the generic xdg-desktop-portal package is the umbrella). Often pulled as a dep, but should be explicit. |
| **qt5-wayland** | **MISSING** — needed because `hyprland.conf` sets `QT_QPA_PLATFORM=wayland`; Qt apps will crash without the platform plugin. |
| **qt6-wayland** | **MISSING** — same reason as qt5-wayland for Qt6 apps. |

---

## 2. Steam + 32-bit gaming (multilib)

| Package | Status |
|---|---|
| steam | PRESENT (NEEDS-MULTILIB-ENABLED, NON-FOSS) |
| lib32-mesa | PRESENT (NEEDS-MULTILIB-ENABLED) |
| lib32-vulkan-icd-loader | PRESENT (NEEDS-MULTILIB-ENABLED) |
| lib32-mangohud | PRESENT (NEEDS-MULTILIB-ENABLED) |
| lib32-gamemode | PRESENT (NEEDS-MULTILIB-ENABLED) |
| mangohud | PRESENT |
| gamemode | PRESENT |
| mesa | PRESENT |
| vulkan-icd-loader | PRESENT |
| vulkan-tools | PRESENT |
| wine-staging | PRESENT |
| winetricks | PRESENT |
| lutris | PRESENT |
| **steam-native-runtime** | **MISSING** — recommended for distros that ship newer glibc than the bundled Steam runtime can handle. Add for stability. |
| **proton-ge-custom** | **NEEDS-AUR** — operator wants Proton GE. AUR-only. Either: (a) install at first-boot via `yay`, (b) ship a tarball in `airootfs/srv/proton-ge/` and a one-shot script that drops it into `~/.steam/.../compatibilitytools.d/`, or (c) wire `[chaotic-aur]`. Recommend option (b) for live-ISO determinism. |

---

## 3. Communications (operator-requested)

| Package | Status |
|---|---|
| **discord** | **MISSING** (NON-FOSS) — official Discord client. Available in `multilib`. Add. |
| **telegram-desktop** | **MISSING** — `extra` repo. Add. |
| **spotify-launcher** | **MISSING** — `extra` repo (the AUR `spotify` is the older one; `spotify-launcher` is the official Arch-blessed launcher in `extra`). Add. |

---

## 4. Recording / streaming

| Package | Status |
|---|---|
| **obs-studio** | **MISSING** — `extra` repo. Add. |

---

## 5. Browsers

| Package | Status |
|---|---|
| chromium | PRESENT |
| firefox | PRESENT |
| **brave-bin** | **NEEDS-AUR** — operator wants Brave. AUR-only (`brave-bin`). Install at first-boot via `yay` OR via `[chaotic-aur]`. |

---

## 6. Audio (PipeWire)

| Package | Status |
|---|---|
| pipewire | PRESENT |
| pipewire-pulse | PRESENT |
| pipewire-alsa | PRESENT |
| pipewire-jack | PRESENT |
| wireplumber | PRESENT |
| **pavucontrol** | **MISSING** — GUI mixer. Add for operator usability. |
| **alsa-utils** | **MISSING** — `alsamixer` + diagnostic tools. Add. |

---

## 7. GPU / graphics

| Package | Status |
|---|---|
| mesa | PRESENT |
| lib32-mesa | PRESENT |
| vulkan-icd-loader | PRESENT |
| lib32-vulkan-icd-loader | PRESENT |
| **nvidia** | **MISSING** (NON-FOSS) — operator's PC GPU vendor is not yet pinned in spec. Recommend NOT bundling NVIDIA in the live ISO; offer a post-install hook OR a second ISO variant. Flag in `proprietary-blobs.md`. |
| **nvidia-utils** | **MISSING** (NON-FOSS) — same as nvidia. |
| **lib32-nvidia-utils** | **MISSING** (NON-FOSS, NEEDS-MULTILIB-ENABLED) — same. |
| **vulkan-radeon** | **MISSING** — AMD Vulkan driver; cheap to include for hardware-agnostic live ISO. |
| **lib32-vulkan-radeon** | **MISSING** (NEEDS-MULTILIB-ENABLED) — same for 32-bit. |
| **vulkan-intel** | **MISSING** — Intel Vulkan driver. |
| **lib32-vulkan-intel** | **MISSING** (NEEDS-MULTILIB-ENABLED) — same for 32-bit. |
| **xf86-video-amdgpu** | **MISSING** — fallback X11 driver. |

---

## 8. Networking

| Package | Status |
|---|---|
| networkmanager | PRESENT |
| iwd | PRESENT |
| wpa_supplicant | PRESENT |
| openssh | PRESENT |
| dhcpcd | PRESENT |
| **network-manager-applet** | **MISSING** — `nm-applet` tray icon. Add. |
| **bluez** | **MISSING** — Bluetooth daemon. Add. |
| **bluez-utils** | **MISSING** — `bluetoothctl` + helpers. Add. |
| **blueman** | **MISSING** — GUI Bluetooth manager. Add. |

---

## 9. Filesystem

| Package | Status |
|---|---|
| btrfs-progs | PRESENT |
| snapper | PRESENT |
| e2fsprogs | PRESENT |
| dosfstools | PRESENT |
| exfatprogs | PRESENT |
| ntfs-3g | PRESENT |
| parted | PRESENT |
| gptfdisk | PRESENT |

All required filesystem tools present. No additions needed.

---

## 10. Bootloader

| Package | Status |
|---|---|
| syslinux | PRESENT |
| grub | PRESENT |
| edk2-shell | PRESENT |
| efibootmgr | PRESENT |
| memtest86+ | PRESENT |
| memtest86+-efi | PRESENT |

All required bootloader components present. Both BIOS (syslinux) and UEFI (grub) covered, consistent with `profiledef.sh bootmodes`.

---

## 11. Live ISO / installer tooling

| Package | Status |
|---|---|
| arch-install-scripts | PRESENT |
| archinstall | PRESENT |
| mkinitcpio | PRESENT |
| mkinitcpio-archiso | PRESENT |
| clonezilla | PRESENT |
| ddrescue | PRESENT |
| **calamares** | **NEEDS-AUR** — operator-friendly GUI installer (Arch deliberately keeps it out of official repos). Available via AUR as `calamares` + `calamares-tools`. Either: (a) bundle pre-built `.pkg.tar.zst` in `airootfs/var/cache/sinister-extras/` + install in first-boot, (b) wire `[chaotic-aur]`, (c) skip and rely on `archinstall` TUI (already PRESENT). Recommend (c) for the alpha; revisit for beta. |

---

## 12. Sudoers-allowlist consistency

| Package | Status |
|---|---|
| **yay** | **NEEDS-AUR** — `/etc/sudoers.d/sinister` whitelists `/usr/bin/yay` for the eve user, but `yay` itself is AUR-only. Must be installed at first-boot via the standard `git clone https://aur.archlinux.org/yay.git && makepkg -si` flow OR bundled as a pre-built `.pkg.tar.zst`. Without it, the sudoers entry is a dangling reference (not harmful, but misleading). Recommend pre-bundling. |

---

## Summary counts

- **PRESENT (verified in repos):** 88
- **MISSING (high priority — referenced by configs or operator-requested):** kitty, foot, qt5-wayland, qt6-wayland, xdg-desktop-portal, steam-native-runtime, discord, telegram-desktop, spotify-launcher, obs-studio, pavucontrol, alsa-utils, network-manager-applet, bluez, bluez-utils, blueman, vulkan-radeon, lib32-vulkan-radeon, vulkan-intel, lib32-vulkan-intel, xf86-video-amdgpu = **21**
- **NEEDS-AUR (cannot land in initial mkarchiso pass):** proton-ge-custom, brave-bin, calamares, yay = **4**
- **NON-FOSS (flag in proprietary-blobs.md):** steam, discord, spotify-launcher (launcher is FOSS but pulls proprietary Spotify client), nvidia/nvidia-utils (if added later) = **4–5**

## Recommended in-place additions to `packages.x86_64`

Add the following 21 lines (each annotated per CLAUDE.md authorship rule). Do NOT remove existing entries. See actual patch applied below the audit table in commit.

```
kitty                          # Added 2026-05-24 (RKOJ-ELENO): hyprland.conf binds Super+Q to kitty fallback chain
foot                           # Added 2026-05-24 (RKOJ-ELENO): wayland-native terminal, secondary fallback
qt5-wayland                    # Added 2026-05-24 (RKOJ-ELENO): hyprland.conf sets QT_QPA_PLATFORM=wayland
qt6-wayland                    # Added 2026-05-24 (RKOJ-ELENO): same as qt5-wayland for Qt6 apps
xdg-desktop-portal             # Added 2026-05-24 (RKOJ-ELENO): umbrella portal package
steam-native-runtime           # Added 2026-05-24 (RKOJ-ELENO): glibc compatibility for Steam
discord                        # Added 2026-05-24 (RKOJ-ELENO): operator-requested comms (NON-FOSS, see proprietary-blobs.md)
telegram-desktop               # Added 2026-05-24 (RKOJ-ELENO): operator-requested comms
spotify-launcher               # Added 2026-05-24 (RKOJ-ELENO): operator-requested music (launcher FOSS, client NON-FOSS)
obs-studio                     # Added 2026-05-24 (RKOJ-ELENO): operator-requested recording
pavucontrol                    # Added 2026-05-24 (RKOJ-ELENO): GUI audio mixer
alsa-utils                     # Added 2026-05-24 (RKOJ-ELENO): alsamixer + diagnostics
network-manager-applet         # Added 2026-05-24 (RKOJ-ELENO): nm-applet tray icon
bluez                          # Added 2026-05-24 (RKOJ-ELENO): bluetooth daemon
bluez-utils                    # Added 2026-05-24 (RKOJ-ELENO): bluetoothctl + helpers
blueman                        # Added 2026-05-24 (RKOJ-ELENO): GUI bluetooth manager
vulkan-radeon                  # Added 2026-05-24 (RKOJ-ELENO): AMD vulkan driver
lib32-vulkan-radeon            # Added 2026-05-24 (RKOJ-ELENO): AMD vulkan 32-bit
vulkan-intel                   # Added 2026-05-24 (RKOJ-ELENO): Intel vulkan driver
lib32-vulkan-intel             # Added 2026-05-24 (RKOJ-ELENO): Intel vulkan 32-bit
xf86-video-amdgpu              # Added 2026-05-24 (RKOJ-ELENO): AMD X11 fallback driver
```

Post-audit projected line count: **88 + 21 = 109**.

## AUR-deferred items (handled in first-boot or P2)

- `proton-ge-custom` — bundle tarball in airootfs OR install via `yay` in first-boot
- `brave-bin` — install via `yay` in first-boot
- `calamares` — skip for alpha (archinstall suffices); revisit for beta
- `yay` — pre-bundle .pkg.tar.zst in airootfs OR install via makepkg in first-boot (chicken-and-egg without it)

---

End of audit.
