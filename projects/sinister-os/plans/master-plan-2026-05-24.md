# Sinister OS — Master Plan

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Plan ID:** `sinister-os/master-plan-2026-05-24`
> **Status:** P0 (spec lock) complete in this commit; P1-P5 await operator gate.
> **Audience:** every future EVE session opened on `projects/sinister-os/`; the operator (Ezekiel) on review.

---

## 0. Why we're doing this

Operator verbatim 2026-05-24:
> *"i need oyu to add to the sessions start and complie into a proejct folder with memory etc the sinister operating system we started that is like a linux based that i can use to replace the current operating system i have on my pc so that eve can have complete control with no nonsense. i can still play games etc and have all features i want because we will build them. complie all you need now and deep resaerch all this and make a super detailed plan for it and let me know once ready in the session start"*

Decoded into requirements:

| Op-stated need | Concrete requirement |
|---|---|
| "Linux-based" | We start from a real Linux distribution, not a fork-from-scratch hobby kernel. |
| "Replace the current operating system" | Sinister OS becomes the operator's daily driver. Windows 10 Home goes away after Phase 5. |
| "EVE has complete control with no nonsense" | EVE owns root via curated NOPASSWD sudoers + system-service-level MCP. No UAC-equivalent friction. No Microsoft telemetry, no forced reboot, no popups. |
| "I can still play games" | Steam + Proton-GE + Wine + Lutris + Bottles. NVIDIA proprietary driver if needed. Full anti-cheat support where Linux supports it (BattlEye + EAC on Proton). |
| "All features I want because we will build them" | Anything not on the FOSS shelf becomes a Sinister-built package shipped from our own repo. |

This document is the complete spec + phased delivery plan + operator-gate map.

---

## 1. Goals (numbered for traceability)

1. EVE controls the machine at the same layer Windows-Explorer + UAC + Task Scheduler would, with no per-action friction on the approved allowlist.
2. The operator can boot the machine, log in, and launch every game and every productivity app he uses today.
3. Zero telemetry leaving the machine without operator explicit opt-in (Steam telemetry stays because Steam, but distro-level telemetry = off).
4. The OS is fully reproducible — anyone with the build scripts in `source/iso-build/` can produce a bit-identical ISO.
5. Every Sinister project (Sanctum, RKOJ, Vault, Mind, Forge, Bots, EVE-personal) runs as a first-class system service on Sinister OS.
6. Recovery is one bootable USB away — every install ships a recovery image that re-flashes the operator's last-good snapshot.
7. The cutover from Windows is reversible until the moment the operator types `sinister-os finalize-cutover` (which wipes the Windows partition).

## 2. Non-goals (so we don't scope-creep)

- **Not** a from-scratch kernel. We use upstream Linux. Sanity > NIH.
- **Not** a public distribution. Sinister OS is the operator's machine + maybe Leo's machine eventually. We don't run a community.
- **Not** a phone OS. Phone work stays in `sinister-kernel-apk` lane.
- **Not** a server OS. This is the daily-driver workstation.
- **Not** a hardened-security distro (Qubes / Tails). Convenience-first; security boundaries are operator-tunable.

## 3. Base distro decision

### 3.1 Candidates

| Distro | Pros | Cons | Score |
|---|---|---|---|
| **Arch Linux** | Bleeding-edge packages, AUR covers ~all FOSS, simple PKGBUILD format, rolling release fits "always current", massive gaming-on-Linux community | Rolling means breakage risk; no installer (we'd ship our own) | **9 / 10** |
| **NixOS** | Atomic upgrades, reproducible by design, declarative config (perfect for "EVE writes the system"), rollback on bad upgrade, flakes | Steep learning curve, gaming setup is fiddlier than Arch, Nix language friction for ad-hoc EVE-write-this-package moments | **8 / 10** |
| **Ubuntu 24.04 LTS** | Largest hardware compat, Steam supports it first-class, easy installer to crib from | Snap-forced, slower package updates (kills bleeding-edge gaming features), GNOME default | **6 / 10** |
| **Debian 12** | Stable, predictable, smallest attack surface, systemd-correct | Too slow for gaming-edge; older kernels miss newer GPU support | **6 / 10** |
| **Fedora 41 / Bazzite** | Bleeding-ish, good gaming defaults (Bazzite is gaming-flavored Fedora Atomic), SELinux | RPM/dnf less universal than pacman; Bazzite atomic model less flexible for system-level EVE control | **7 / 10** |
| **Gentoo / LFS** | Maximum control | Maintenance cost is the entire project | **3 / 10** |
| **CachyOS** (Arch-based) | Arch-bleeding + gaming-tuned kernels (BORE/EEVDF schedulers) + good defaults | Smaller ecosystem than mainline Arch; adds CachyOS layer to debug | **8 / 10** |

### 3.2 Decision

**Base: Arch Linux + linux-cachyos kernel + custom installer.**

Rationale:
- Arch's PKGBUILD model gives EVE the simplest "write a package" path (~10 lines of bash for a typical wrapper).
- AUR + arch4edu + chaotic-aur cover ~everything we'd otherwise have to build.
- Steam, Proton-GE, Wine, Lutris, Bottles, Heroic, anti-cheat — all are well-supported on Arch (Steam Deck runs Arch under the hood).
- We avoid the Snap tax (Ubuntu) and the RPM-monoculture (Fedora).
- linux-cachyos kernel gives us BORE-EEVDF scheduler + transparent hugepages + zen-tuned for desktop responsiveness without losing kernel mainline support.
- We ship our own installer (Calamares fork, branded) so the operator experience is Sinister, not Arch wiki.

Runner-up: **NixOS** — kept as the eventual migration target for Phase 6+ when we want fully declarative system state. Out of scope for this plan.

### 3.3 Snapshot of the base stack

```
Linux kernel:        linux-cachyos 6.13+
Init / service mgr:  systemd 257+
Display server:      Wayland (Hyprland compositor) primary; Xorg (i3) fallback
Audio:               PipeWire + WirePlumber
Display manager:     SDDM (themed)
Sound theme:         pipewire + custom Sinister chime set
Package manager:     pacman + paru (AUR helper)
Filesystem:          btrfs (root + home subvolumes, snapper for snapshots)
                     ext4 fallback for /boot
Bootloader:          systemd-boot (UEFI primary) + GRUB (BIOS fallback)
GPU:                 nvidia-open-dkms (operator has NVIDIA) — fallback nouveau
Firewall:            nftables + opensnitch (per-app prompts the operator can pre-approve)
Sandbox:             flatpak for risky GUI apps; bubblewrap available
```

## 4. Architecture (system layers)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Operator layer                                                       │
│   keyboard / voice / hotkey / mouse → input events                   │
└────────────────┬──────────────────┬──────────────────────────────────┘
                 │                  │
                 ▼                  ▼
┌──────────────────────┐  ┌──────────────────────────────────────────┐
│ Compositor (Hyprland)│  │ sinister-voice user service              │
│   - keybinding fires │  │   wake-word always-on; transcription     │
│     "Super+E" → EVE  │  │   PCM → text → EVE socket                │
└────────┬─────────────┘  └────────────────┬─────────────────────────┘
         │                                 │
         └─────────────┬───────────────────┘
                       ▼
       ┌─────────────────────────────────────────────────────────┐
       │ sinister-eve.service (system, runs as eve user)        │
       │   UNIX socket: /run/sinister/eve.sock                  │
       │   - command routing                                    │
       │   - intent recognition                                 │
       │   - escalation ladder (auto-yes for allowlist)         │
       │   - logs every action to /var/log/sinister/eve.jsonl   │
       └────────┬───────────────┬───────────────────┬───────────┘
                │               │                   │
                ▼               ▼                   ▼
       ┌─────────────┐ ┌─────────────────┐ ┌─────────────────────┐
       │ MCP bridge  │ │ system action   │ │ app launcher        │
       │ (DBus +     │ │ executor        │ │ (xdg-open, wlrctl,  │
       │  HTTP)      │ │ (sudo allow-    │ │  ydotool, hyprctl)  │
       │             │ │  list runner)   │ │                     │
       └─────┬───────┘ └────────┬────────┘ └──────────┬──────────┘
             │                  │                      │
             ▼                  ▼                      ▼
       ┌──────────────────────────────────────────────────────────┐
       │ Linux kernel + systemd + pacman + filesystem + hardware  │
       └──────────────────────────────────────────────────────────┘
```

### 4.1 The sudoers allowlist (the "no nonsense" mechanism)

`/etc/sudoers.d/eve` (drafted; reviewed by operator before install):

```
# Sinister OS :: EVE NOPASSWD allowlist
# Author: RKOJ-ELENO :: 2026-05-24
# Audited by: <operator-name> on <install-date>
eve ALL=(ALL) NOPASSWD: \
    /usr/bin/pacman, \
    /usr/bin/paru, \
    /usr/bin/systemctl, \
    /usr/bin/journalctl, \
    /usr/bin/nmcli, \
    /usr/bin/timedatectl, \
    /usr/bin/hostnamectl, \
    /usr/bin/mount, \
    /usr/bin/umount, \
    /usr/bin/btrfs, \
    /usr/bin/snapper, \
    /usr/bin/dmesg, \
    /usr/bin/lsblk, \
    /usr/bin/lspci, \
    /usr/bin/lsusb, \
    /usr/bin/iwctl, \
    /usr/bin/bluetoothctl, \
    /usr/bin/cp, \
    /usr/bin/mv, \
    /usr/bin/install
# Explicitly NOT included (require operator interactive confirm):
#   - rm, dd, mkfs, parted, fdisk, cfdisk, sfdisk
#   - efibootmgr, bootctl install, grub-install
#   - passwd, useradd, userdel, chsh
#   - chmod 777 (any wide-permission flips)
#   - shell-quoting that EVE could weaponize (no ALL: /bin/bash)
```

The deny-list is the safety net. Destructive commands always require the operator hotkey-confirm (Super+Y) inside a 30-second window, with EVE printing "About to run: <command> (operator confirm with Super+Y / cancel with Super+N)".

### 4.2 System MCP

Sinister Sanctum's MCP bots become **system DBus services** on Sinister OS — so any app (terminal, IDE, browser via extension) can talk to them without a Claude Code session in the foreground:

```
DBus interface: org.sinister.Bus
  Methods:
    Heartbeat(slug, display) → ack
    InboxPoll(slug) → message_list
    InboxSend(to_slug, from_slug, body, tags) → message_id
    BrainSearch(query) → row_list
    BrainAdd(slug, title, body) → row_id
    SpawnAgent(project, mode) → window_id
    Heartbeat(slug, display) → ack
  Signals:
    InboxMessage(slug, message)
    HeartbeatStale(slug)
    BrainRow75Approaching()
```

Implementation: thin shim around existing `bots/agents/sinister-bus/server.py` that publishes the same surface on DBus.

## 5. Desktop environment + branding

### 5.1 Compositor: Hyprland (Wayland)

- Dynamic tiling (operator preference; matches RKOJ workbench tab discipline).
- GPU-accelerated blur + animations.
- Wallpaper: `hyprpaper` with Sinister purple/black gradient + faint sigil.
- Hotkeys (operator-tunable):
  - `Super+Return` → terminal (kitty)
  - `Super+B` → browser (LibreWolf default; Brave + Firefox installed)
  - `Super+E` → EVE prompt overlay (floating, 60% screen, accepts text or voice)
  - `Super+M` → Sinister Mind (open mind-graph)
  - `Super+R` → RKOJ workbench
  - `Super+F` → Sinister Forge
  - `Super+G` → Steam Big Picture
  - `Super+Y` / `Super+N` → confirm / cancel EVE destructive prompt
  - `Super+space` → wofi launcher
  - `Super+1..9` → workspaces
- Fallback Xorg session: i3wm with same hotkey map.

### 5.2 Branding deliverables (live in `source/branding/`)

| Artifact | Format | Notes |
|---|---|---|
| Plymouth boot splash | `.plymouth` + PNG sequence | Sinister sigil pulse on black, ~3s |
| GRUB theme | GRUB theme dir | Used only on BIOS fallback path |
| systemd-boot logo | BMP | UEFI primary boot path |
| SDDM theme | QML | Login screen — purple accent, EVE waveform idle |
| Hyprland wallpaper | PNG @ operator's resolution | Generated via sinister-generator brand-lock |
| Cursor theme | Custom Bibata fork | Purple accent |
| Icon theme | Papirus fork | Tweaked accent colors |
| Sound theme | `freedesktop` overlay | Custom chime set replaces system bells |
| Terminal prompt | starship.toml | Purple + Sinister glyph |

### 5.3 Apps preinstalled

- **Browser**: LibreWolf (default) + Brave + Firefox + Chromium (for stealth-browser bot)
- **Terminal**: kitty (primary) + foot (Wayland-native fallback)
- **Editor**: VSCodium + Helix + Neovim
- **Files**: Nautilus or Dolphin (operator pick)
- **Office**: LibreOffice + OnlyOffice (compat with `.docx`)
- **Media**: mpv + VLC + OBS Studio
- **Image**: GIMP + Krita + ImageMagick + sinister-generator wrapper
- **Audio**: Audacity + Ardour + REAPER (paid, install if licensed)
- **Video**: DaVinci Resolve (free tier) + Kdenlive
- **Comms**: Discord, Slack, Telegram, Signal, Element (via flatpak)
- **Dev**: git, gh, nodejs, python, rustup, go, docker, podman, claude-code CLI
- **Gaming**: see § 6

## 6. Gaming stack (Op's "I still play games" requirement)

### 6.1 Core

- **Steam** (`steam` from multilib repo) + Proton + Proton-GE-Custom (`proton-ge-custom-bin` from AUR).
- **Lutris** for non-Steam launchers (Epic, GOG, Battle.net).
- **Heroic Games Launcher** as Lutris alternative for Epic / GOG / Amazon.
- **Bottles** for ad-hoc Wine prefixes (Windows-only apps that aren't games).
- **MangoHud** (FPS + frametime overlay) + **goverlay** GUI.
- **Gamemode** (auto CPU governor switch + IO priority for game processes).

### 6.2 Anti-cheat

| Anti-cheat | Linux status | Strategy |
|---|---|---|
| BattlEye (BE) | Devs must opt-in via Proton flag | Enabled for opted-in titles via Proton-GE; surface "not supported" warning for non-opted titles |
| Easy Anti-Cheat (EAC) | Same — dev opt-in | Same |
| Vanguard (Riot) | **Not supported on Linux** (kernel-mode). | Warn the operator; Valorant won't work. Document the title list. |
| Roblox Hyperion | **Not supported on Linux** as of 2024. | Same warn pattern. |
| Punkbuster | Legacy; works under Wine | Just works |

EVE surfaces the compat status when the operator launches a game (via ProtonDB scrape + cached title→status table at `/var/lib/sinister/proton-compat.json`).

### 6.3 GPU

- NVIDIA: `nvidia-open-dkms` (open kernel module variant) + `nvidia-utils` + `lib32-nvidia-utils` for 32-bit titles.
- AMD: `mesa` + `vulkan-radeon` + `lib32-vulkan-radeon` (no setup; works OOTB).
- Intel: `mesa` + `vulkan-intel`.
- HDR support: gamescope + Wayland HDR protocol once Hyprland ships it.
- Wayland VRR (variable refresh / G-Sync / FreeSync): supported via Hyprland config.

### 6.4 Controller support

- Steam Input handles 99% (Xbox / DualShock / DualSense / generic).
- For non-Steam apps: `xpadneo` (Xbox via Bluetooth), `xone` (Xbox via dongle/USB), `dualsensectl` (PS5 features).

### 6.5 Streaming / capture

- **OBS Studio** with NVENC + Pipewire screen capture.
- **GameStream replacement**: Sunshine (host) + Moonlight (client) for in-house streaming to the operator's other devices.

## 7. Productivity / creative compat

Mapping operator-likely Windows apps to Linux replacements:

| Windows app | Sinister OS path |
|---|---|
| Office 365 | LibreOffice + OnlyOffice + Office365 web via browser |
| Photoshop | GIMP + Krita; or Photoshop via Bottles (CC 2021 works on Wine, newer is iffy) |
| Premiere | DaVinci Resolve (native Linux) + Kdenlive |
| Illustrator | Inkscape (native) or Affinity Designer via Bottles (works) |
| AutoCAD | LibreCAD / FreeCAD native, or AutoCAD via Wine (mixed) |
| FL Studio | Native Linux build (since FL 21) — operator's audio path |
| Visual Studio | VSCodium native + Rider native; full VS via Wine (don't bother) |
| Notion | Native Linux app via flatpak |
| Discord/Slack/Teams | All native or flatpak |
| Excel power-user | LibreOffice Calc + Excel web via browser; gnumeric for scripting |

## 8. EVE control surface (the centerpiece)

### 8.1 Daemon spec

`sinister-eve.service` — system service running as the `eve` user, started at boot, listens on `/run/sinister/eve.sock` (filtered by polkit to `wheel` group → operator).

Daemon flow:
1. Receive command on socket (from voice, hotkey overlay, MCP DBus, or `eve` CLI).
2. Classify intent (informational / observable-action / mutating-action / destructive-action).
3. Informational → answer inline, no permission needed.
4. Observable-action (open file, open URL, run lint) → execute, no permission needed.
5. Mutating-action (install package, change setting, mount drive) → check sudoers allowlist; auto-execute if covered; else queue for operator confirm.
6. Destructive-action (delete, partition, format, system reset) → always operator-confirm via hotkey overlay.
7. Log every action with timestamp + intent class + command + exit code to `/var/log/sinister/eve.jsonl`.

### 8.2 Configuration

`/etc/sinister/eve.toml`:

```toml
[identity]
agent_name = "EVE"
operator_name = "Ezekiel"
voice_wake_word = "EVE"

[escalation]
confirm_hotkey = "Super+Y"
cancel_hotkey  = "Super+N"
confirm_timeout_sec = 30
auto_yes_for_allowlist = true

[mcp]
bus_url = "unix:///run/sinister/bus.sock"
sanctum_root = "/home/ezekiel/sinister-sanctum"
brain_root = "/home/ezekiel/sinister-sanctum/_shared-memory/knowledge"

[voice]
enabled = true
provider = "local"   # or "openai-whisper" / "deepgram" — operator picks
language = "en-US"

[logging]
journal = true
file = "/var/log/sinister/eve.jsonl"
retention_days = 90
```

### 8.3 EVE CLI

`eve` is a thin client wrapping the socket. Operator runs:

```
eve open project sinister-forge
eve install package obs-studio
eve snapshot before "system upgrade"
eve revert to last-good
eve list actions today
eve why did pipewire restart at 14:32
eve voice off
```

### 8.4 Voice surface (uses existing tools/sinister-voice/)

- Always-on wake-word ("EVE") via `openWakeWord` (FOSS, runs locally on CPU).
- On wake: 4-second recording window (operator can extend via "EVE longer").
- Audio → local Whisper (or operator-configured cloud provider).
- Text → eve socket as command.
- Response → text overlay + optional TTS (`piper-tts`, local, fast).

### 8.5 Hotkey overlay

Hyprland binds `Super+E` → spawn `eve-overlay` (a tiny GTK4 window):
- Text input at the top.
- Bottom strip shows last 5 EVE actions.
- Esc closes; Enter sends command.
- Floating, 60% width, centered.
- Theme: Sinister purple, blurred background.

## 9. Filesystem layout

Btrfs root with subvolumes (snapper-managed):

```
/                  → subvol @root        (snapshotted nightly)
/home              → subvol @home        (snapshotted hourly during workday, daily otherwise)
/var/log           → subvol @log         (excluded from root snapshots)
/var/cache/pacman  → subvol @pkgcache    (excluded; we don't want to snapshot package cache)
/srv/sinister      → subvol @sinister    (Sanctum + projects live here, snapshotted hourly)
/mnt/games         → ext4 mount          (Steam library on separate partition for size)
/mnt/sinister-vault → vault daemon mount (separate disk if available)
```

Snapshots: snapper rotates 30 dailies + 7 weeklies + 6 monthlies + 2 yearlies. Boot menu (systemd-boot) shows snapshots as alternate boot entries via `snap-pac` hook.

## 10. Recovery + rollback

- **Live recovery USB**: each ISO build emits a `sinister-os-recovery.iso` flavor with btrfs tools, snapper, GParted, the operator's network creds (encrypted), and an `eve-recover` CLI that walks the operator through "boot last-good snapshot" / "reinstall preserving home" / "factory reset preserving home" flows.
- **Auto-snapshot before risk**: any `pacman -Syu` triggers pre-snapshot; any destructive `eve` action triggers pre-snapshot.
- **Snapshot retention**: tunable in `/etc/snapper/configs/`.

## 11. Security model

- Firewall: nftables default-deny inbound except `dhcp`, `mdns`, `ssh` (key-only).
- Opensnitch app-level firewall (per-app outbound prompts, operator can pre-approve).
- AppArmor profiles for browsers + Discord + Steam (loose enough to not break gaming).
- LUKS2 disk encryption (operator can decline at install time if they prefer).
- Secure boot: operator-gated. If enabled, we MOK-enroll our signed kernels.
- SSH: key-only, root-login=no, fail2ban (operator can disable for LAN-only setups).
- Telemetry: zero distro-level telemetry. Steam telemetry stays (it's Steam). Surface a notice during install.

## 12. Phase status board

| Phase | Description | Status | Operator gate |
|---|---|---|---|
| **P0** | Spec lock + master plan + project scaffold | ✅ DONE 2026-05-24 | n/a |
| **P1** | Build a minimal bootable ISO (live + installer) in VM. No EVE, no apps — just proves the build system. | ⏳ Awaiting operator OK | Operator: "P1 go" |
| **P2** | Add Hyprland + branding + base apps + EVE skeleton. Install to spare partition (dual-boot). Soak for 7 days as secondary. | ⏳ Blocked on P1 | Operator: "P2 go" |
| **P3** | EVE-as-shell daemon production-ready. Voice, hotkeys, MCP DBus, sudoers allowlist, polkit policies. | ⏳ Blocked on P2 | Operator: "P3 go" |
| **P4** | Gaming stack proven on real titles. Creative stack tested. Productivity tested. Operator does a "Sinister OS only" week. | ⏳ Blocked on P3 | Operator: "P4 go" |
| **P5** | Migrate user data from Windows. Cutover. Wipe Windows partition. | ⏳ Blocked on P4 | Operator: "P5 cutover go" (explicit, can't be misheard) |

### 12.1 P1 detail (next phase EVE can execute on operator OK)

| # | Row | Acceptance |
|---|---|---|
| 1.1 | Choose ISO build tool: `mkosi` vs `archiso` | Decision committed to `docs/iso-build-tool.md`. **Pick: archiso** (more battle-tested, operator-mode familiar). |
| 1.2 | Write `source/iso-build/profiledef.sh` + `packages.x86_64` for minimal flavor | `mkarchiso -v` builds without error in VM. |
| 1.3 | Verify ISO boots in QEMU/KVM with `qemu-system-x86_64 -enable-kvm -m 4G -cdrom build/sinister-os.iso` | Boot to login prompt; `root` login works; `pacman -Syu` runs. |
| 1.4 | Add `sinister-installer` Calamares fork | Installer flow walks through: language → keyboard → disk → user → install. |
| 1.5 | Add Sinister branding (plymouth + GRUB) | Boot splash shows Sinister sigil. |
| 1.6 | Build matrix doc | `docs/p1-build-matrix.md` lists every tested combo + which work. |
| 1.7 | Operator review gate | Operator boots ISO in VM themselves; signs off. |

### 12.2 P2 detail (preview)

- Add Hyprland + SDDM + base apps from § 5.3.
- Add btrfs subvol layout + snapper.
- Add operator user with `wheel` group.
- Install on spare partition (operator picks which drive/partition).
- Set up dual-boot via systemd-boot.
- 7-day soak as secondary OS.

### 12.3 P3 detail (preview)

- Build `sinister-eve.service` (Rust binary for speed + memory safety).
- Build `eve-overlay` (GTK4).
- Build DBus bus wrapper.
- Wire `tools/sinister-voice` into the daemon.
- Operator hotkey overlay.
- Sudoers + polkit policies installed.

### 12.4 P4 detail (preview)

- Steam + Proton-GE install + verify on operator's owned titles.
- Lutris + Heroic for Epic/GOG titles.
- OBS test (NVENC + Pipewire capture).
- DaVinci Resolve install + verify.
- 7-day "Sinister OS only" challenge.

### 12.5 P5 detail (preview)

- Mount Windows partition read-only from Sinister OS.
- Migrate `C:\Users\Zonia\Documents`, Desktop, Downloads, AppData (for relevant apps) via `rsync`.
- Migrate browser profiles (Chromium/Firefox/Brave) via their import paths.
- Migrate Steam library (already on `/mnt/games` if separate disk; else `rsync`).
- Migrate `D:\Sinister Sanctum` (it's already on D:; just remount as ext4 or migrate to btrfs).
- Operator types `sinister-os finalize-cutover`. Confirm prompt. Wipe Windows. Reclaim C: as btrfs subvol.

## 13. Build / dev workflow (for EVE)

```
# In a Linux VM (Arch host preferred for build symmetry):
git clone D:/Sinister Sanctum/projects/sinister-os/source ~/sinister-os
cd ~/sinister-os/iso-build
sudo mkarchiso -v -w /tmp/sinister-work -o /tmp/sinister-out .
qemu-system-x86_64 -enable-kvm -m 4G -smp 4 -cdrom /tmp/sinister-out/sinister-os-*.iso
```

EVE iterates: edit packages list / config → rebuild → re-test in QEMU.

## 14. Open questions for operator (P0 review)

| # | Question | Why it matters | Recommended default |
|---|---|---|---|
| Q1 | Arch + linux-cachyos OK as base? Or NixOS instead? | Locks the entire build path. | Arch + linux-cachyos. |
| Q2 | Hyprland (Wayland) primary OK? Or KDE Plasma 6 / GNOME / XFCE? | Defines desktop UX. | Hyprland. |
| Q3 | Browser default: LibreWolf? Brave? Firefox? Chromium? | Default for `xdg-open` URLs. | LibreWolf. |
| Q4 | Voice transcription: local Whisper (free, slower, private) or cloud (faster, costs)? | Affects voice latency + privacy posture. | Local Whisper. |
| Q5 | Install LUKS2 disk encryption? | Loss of password = loss of data. | Yes, but operator-tunable. |
| Q6 | Secure Boot enabled? | Adds MOK enrollment step; some games + nvidia DKMS need re-enroll on kernel updates. | Off (simpler). |
| Q7 | Dual-boot during P2-P4 soak? Or jump straight to single-boot? | Recovery posture. | Dual-boot. |
| Q8 | Spare partition for P2 install — which drive? | Need to know before P2. | Operator picks; usually D: or a new SSD. |
| Q9 | Anti-cheat games operator cares about (Valorant? Vanguard-protected?) | Determines if we need a Windows fallback for Q10. | Operator answers. |
| Q10 | If Q9 has Vanguard-protected titles, keep Windows VM via VFIO GPU passthrough? | Lets operator play those titles on Sinister OS via a Windows VM with the second GPU. | Decide post-Q9. |

## 15. Open risks / known unknowns

| Risk | Mitigation |
|---|---|
| Wayland HDR not yet stable on NVIDIA proprietary | Hold X11 fallback; revisit Q4 2026 |
| NVIDIA driver regressions on bleeding-edge kernel | Pin known-good driver version; snapshot before each upgrade |
| Operator workflow has a Windows-only app we haven't catalogued | P2 soak surfaces it; either Wine-it or VM-it |
| Voice transcription latency on CPU-only Whisper feels slow | Provide cloud fallback toggle; or quantized Whisper model |
| Operator gets locked out of EVE during a failed update | Recovery USB boots into last-good snapshot |
| Build cost (image bandwidth, disk space) | ISOs are ~2GB; we keep last 3 versioned in `build/` |
| EVE makes a mistake on a NOPASSWD command | Audit log; rollback via snapper; operator can grep `/var/log/sinister/eve.jsonl` |

## 16. References (reading list for EVE)

- Arch Wiki: https://wiki.archlinux.org/title/Installation_guide
- archiso: https://gitlab.archlinux.org/archlinux/archiso
- linux-cachyos: https://github.com/CachyOS/linux-cachyos
- Hyprland: https://wiki.hyprland.org/
- Proton-GE: https://github.com/GloriousEggroll/proton-ge-custom
- ProtonDB: https://www.protondb.com/
- snapper: http://snapper.io/
- nftables: https://wiki.nftables.org/
- openWakeWord: https://github.com/dscripka/openWakeWord
- Whisper: https://github.com/openai/whisper
- piper-tts: https://github.com/rhasspy/piper

## 17. End-of-plan acceptance (P0 done-criteria)

This plan is "P0 complete" when:

- [x] Project folder exists at `D:/Sinister Sanctum/projects/sinister-os/`.
- [x] `README.md`, `CLAUDE.md`, this `plans/master-plan-2026-05-24.md` exist and read coherently end-to-end.
- [x] SESSION-START surfaces the plan in `05-PROJECT-OVERVIEW.md` and adds a pointer paragraph in `README.md`.
- [x] Brain doctrine row exists in `_shared-memory/knowledge/_INDEX.md`.
- [x] PROGRESS log entry created.
- [x] Committed + pushed.
- [ ] Operator answered Q1-Q10 (P1 gate).

When operator answers Q1-Q10, P0 transitions to P1 and a new branch `agent/sinister-os/p1-iso-build-<date>` opens.
