# Sinister OS — Architecture

> **Author:** RKOJ-ELENO :: 2026-05-24
> Companion to `plans/master-plan-2026-05-24.md`. This file goes deeper on the system-layer view.

## Layer cake

```
L7  Operator                : keyboard, mouse, voice, hotkey
L6  Compositor              : Hyprland (Wayland) / i3 (Xorg fallback)
L5  EVE control surface     : sinister-eve.service + sinister-voice + eve-overlay
L4  Sinister fleet services : sinister-bus, sinister-vault, sanctum, rkoj, mind, forge
L3  System services         : systemd, pipewire, networkmanager, bluetooth, polkit, sddm
L2  Userland                : pacman/paru, glibc, coreutils, busybox, GNU stack
L1  Kernel                  : linux-cachyos + nvidia-open-dkms / mesa / vulkan
L0  Hardware                : operator's existing workstation (NVIDIA GPU + intel/amd CPU)
```

## How EVE crosses layers

| Operator intent | Layer crossed | Path |
|---|---|---|
| "Open Sinister Forge" | L7 → L6 → L5 → L4 → L3 | Voice/hotkey → eve-overlay → eve daemon → DBus to forge launcher → systemd-run user@.service |
| "Install OBS Studio" | L7 → L5 → L2 → L1 | Voice → eve daemon → sudoers allowlist → `pacman -S obs-studio` → kernel writes |
| "Snapshot before upgrade" | L7 → L5 → L3 → L2 | Voice → eve daemon → snapper create → btrfs subvol snapshot |
| "Restart NetworkManager" | L7 → L5 → L3 | Voice → eve daemon → `systemctl restart NetworkManager` (in allowlist) |
| "Wipe /home" | L7 → L5 → ⚠ stop | Voice → eve daemon → classified destructive → operator hotkey-confirm required |

## Where each Sinister project lives on disk

```
/                            (root subvol)
├── etc/
│   ├── sinister/
│   │   ├── eve.toml
│   │   ├── bus.toml
│   │   ├── theme.toml
│   │   └── allowlist.conf
│   └── sudoers.d/eve
├── srv/sinister/            (subvol @sinister, snapshotted hourly)
│   ├── sanctum/             (git clone of Sinister Sanctum)
│   ├── vault/               (sinister-vault data root)
│   └── shared/              (cross-project transient files)
├── opt/sinister/            (sinister-fleet binaries, managed via PKGBUILDs)
│   ├── bin/
│   │   ├── eve              (CLI)
│   │   ├── eve-overlay      (GTK4 prompt)
│   │   ├── rkoj             (workbench native build)
│   │   ├── sinister-forge   (forge launcher)
│   │   └── sinister-mind    (mind-graph)
│   └── lib/
│       └── eve_lib/         (shared python/rust libs)
├── run/sinister/            (sockets; created by systemd-tmpfiles)
│   ├── eve.sock
│   └── bus.sock
├── var/
│   ├── log/sinister/
│   │   ├── eve.jsonl
│   │   ├── bus.jsonl
│   │   └── installer.log
│   └── lib/sinister/
│       ├── proton-compat.json
│       └── operator-state.json
└── home/ezekiel/            (subvol @home)
    ├── sinister-sanctum/    (bind-mount or symlink to /srv/sinister/sanctum)
    └── .config/sinister/    (operator-specific overrides)
```

## Systemd unit summary

| Unit | Type | Role |
|---|---|---|
| `sinister-eve.service` | system | EVE control daemon |
| `sinister-bus.service` | system | MCP bus DBus surface |
| `sinister-vault.service` | system | Vault daemon (existing) |
| `sinister-voice.service` | user | Voice listener (per-session) |
| `sinister-mind.service` | user | Mind-graph server :5079 |
| `sinister-forge.service` | user | Forge background process |
| `sinister-autopush.timer` | system | 30-min auto-push to GitHub (existing daemon, ported) |
| `sinister-snapshot-pre-pacman.service` | system | Pacman hook → snapper pre-snap |

## DBus name reservations

```
org.sinister.Bus           — sinister-bus.service
org.sinister.Eve           — sinister-eve.service
org.sinister.Vault         — sinister-vault.service
org.sinister.Voice         — sinister-voice.service (user)
org.sinister.Mind          — sinister-mind.service (user)
```

## Boot sequence

```
UEFI → systemd-boot → linux-cachyos → systemd init
       (Sinister logo)  (Sinister plymouth)

systemd init starts:
  - sinister-bus.service           (early; other services depend)
  - sinister-eve.service           (early; needs bus)
  - sinister-vault.service         (after bus)
  - sinister-autopush.timer        (boot+30min, then every 30min)
  - sddm.service                   (login)

SDDM login → operator selects session (Hyprland default) → Hyprland starts:
  - hyprpaper                      (wallpaper)
  - waybar                         (status bar)
  - sinister-voice.service         (user, listens for wake word)
  - sinister-mind.service          (user, ready for hotkey)
  - sinister-forge.service         (user, tray icon)

Operator is now in EVE-controlled Sinister OS.
```

## What lives where for the OPERATOR (cheat sheet)

| If operator wants to … | Run this |
|---|---|
| Talk to EVE | Say "EVE" out loud, or press Super+E |
| Open Sanctum | `cd /srv/sinister/sanctum` then `claude` |
| Open RKOJ workbench | Super+R |
| Open Forge | Super+F |
| Open Mind | Super+M |
| Open Steam | Super+G |
| Snapshot before doing something risky | `eve snapshot before "<reason>"` |
| Roll back to last snapshot | Reboot → systemd-boot menu → pick snapshot |
| See what EVE did today | `eve list actions today` |
| Audit EVE | `journalctl -u sinister-eve` or `less /var/log/sinister/eve.jsonl` |
| Disable voice | `eve voice off` |
| Re-enable voice | `eve voice on` |
| Add a sudoers allowlist entry | `eve allowlist add <command>` (operator confirms) |
