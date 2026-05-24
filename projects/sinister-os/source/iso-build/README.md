# source/iso-build/

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P1 (scaffold landed 2026-05-24; smoke-build pending operator starting Docker Desktop).

Build environment for Sinister OS live ISOs. Driven by `archiso` inside a Docker container so the operator's Windows host does not need a Linux build VM.

## Layout

```
iso-build/
├── Dockerfile              archlinux base + archiso + build deps
├── profiledef.sh           archiso profile metadata
├── packages.x86_64         live ISO package list
├── pacman.conf             pacman repo config (core + extra + multilib)
├── build.sh                one-command builder: docker build + mkarchiso
├── bake-panel.sh           builds Sinister Panel Next.js standalone into airootfs
├── airootfs/               files overlaid onto the live root
│   ├── etc/
│   │   ├── skel/.config/hypr/hyprland.conf    compositor config (Sinister purple)
│   │   ├── sudoers.d/sinister                 NOPASSWD allowlist for eve user
│   │   └── systemd/system/sinister-first-boot.service
│   ├── usr/local/bin/
│   │   ├── sinister-first-boot.sh             one-shot init (NM, ollama, perms)
│   │   └── sinister-panel-kiosk.sh            launches Panel + Chromium kiosk
│   ├── srv/sinister-panel/                    Panel Next.js standalone bundle (baked)
│   └── root/.automated_script.sh              archiso live-tty1 auto-Hyprland
└── README.md
```

## Build procedure

Pre-reqs:
- Docker Desktop installed and running (currently 29.1.3 detected; daemon was DOWN at last check 2026-05-24T12:40Z)
- Node.js 20+ on the host (for `bake-panel.sh`)
- About 15 GB free disk

Steps (run from this directory):

```bash
# 1. Build the Panel Next.js bundle and stage it into airootfs
bash bake-panel.sh

# 2. Build the Docker image and run mkarchiso
bash build.sh

# Output: ../../build/sinister-os-0.1.0-alpha-<YYYYMMDD>-x86_64.iso
```

## Smoke-test the ISO

```bash
# In a Linux VM with KVM (or on a Linux laptop):
qemu-system-x86_64 \
  -enable-kvm \
  -m 8G -smp 4 \
  -cdrom ../../build/sinister-os-*-x86_64.iso \
  -device virtio-vga-gl \
  -display gtk,gl=on
```

Expected sequence:
1. GRUB Sinister-themed menu
2. Linux boots to tty1 as root
3. archiso auto-runs `/root/.automated_script.sh` -> enables NM + ollama + launches Hyprland
4. Hyprland autostart runs `sinister-panel-kiosk.sh`
5. Node server.js starts the Panel on 127.0.0.1:3080
6. Chromium kiosk loads `http://127.0.0.1:3080/` -> Sinister Panel overview

## What is NOT yet built (open for next turn)

- Calamares installer fork branded as `sinister-installer` (P1 row 1.4)
- Plymouth boot splash with Sinister sigil (P1 row 1.5)
- GRUB theme (P1 row 1.5)
- Backend services from `panel/backend/` baked in (currently only the dashboard frontend is bundled — Panel API calls will 404 against the rewrite target until backend is added)
- EVE daemon (`sinister-eve.service`) — P3 work
- Steam game library + Proton-GE — P4 work (packages are in the list but not configured)

## Doctrine

This folder follows the no-bullshit doctrine (`_shared-memory/knowledge/no-bullshit-tested-before-claimed-doctrine-2026-05-23.md`): every file in this scaffold is `parse-clean` (bash `-n` confirmed); none claim `smoke-tested` yet because the Docker daemon was down at scaffold time. First successful `bash build.sh` run promotes this scaffold to `smoke-tested`.
