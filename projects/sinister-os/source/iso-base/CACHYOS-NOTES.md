# CachyOS ISO — jerry-rig fast-path notes

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Lane:** `sinister-os`

## What we did

Downloaded CachyOS desktop ISO (Hyprland-capable; CachyOS unified all desktop editions into one ISO with installer-time DE selection — Hyprland is one of the choices), verified SHA256, booted in VirtualBox.

## Source

- **URL:** `https://mirror.cachyos.org/ISO/desktop/260426/cachyos-desktop-linux-260426.iso`
- **Build date:** 2026-04-26 (latest stable as of 2026-05-24)
- **Fetched:** 2026-05-24 12:09–12:27 UTC-ish (local Sanctum clock)
- **Local path:** `D:\Sinister Sanctum\projects\sinister-os\source\iso-base\cachyos-hyprland.iso`
- **Size:** 3,060,826,112 bytes (2,919 MB)
- **SHA256 (published):** `9a280d1e9732cfe50ab02db6a7e44ae0d9e6a10e6ea394f73192f7c14e263118`
- **SHA256 (computed):** `9a280d1e9732cfe50ab02db6a7e44ae0d9e6a10e6ea394f73192f7c14e263118` — **MATCH**

## Note on the URL

Per research/recommended-bases.md we wanted "CachyOS Hyprland edition ISO". CachyOS no longer publishes a separate Hyprland ISO — they consolidated to one `desktop/` ISO whose Calamares installer offers Hyprland as one of the desktop choices (alongside KDE, GNOME, Cosmic, etc.). The KDE-specific ISO and CLI ISO folders still exist for backward compat. Hyprland-only live boot still works: the live environment includes Hyprland session selectable from the greeter.

Mirrors checked: `mirror.cachyos.org` is Cloudflare-backed. Per-connection bandwidth was throttled to ~1 MB/s; the parallel-range downloader at `_parallel.py` got us through the last 261 MB at ~4.5 MB/s aggregate with 6 workers.

## Download artifacts kept here

- `_download.py` — single-stream downloader with auto-resume on truncated connection (first run hit a truncated response at 2.5 GB; second run resumed via HTTP Range)
- `_parallel.py` — parallel range completer (6 workers, used to finish the tail)
- `_download.log` / `_download2.log` / `_parallel.log` — invocation logs
- `cachyos-hyprland.iso` — the verified ISO

## Boot result

VirtualBox 7.2.4 VM `Sinister-OS-Test`:
- 4 GB RAM, 4 vCPUs, 60 GB sparse VDI, EFI64
- VMSVGA graphics (128 MB VRAM, 3D off for Hyprland live-boot stability)
- ISO attached via IDE controller, SATA hdd, NAT NIC, audio disabled
- Boot order: dvd → disk
- Started 2026-05-24 via `vm-boot/boot-virtualbox.ps1`
- VBoxManage reports `VMState=running` after `startvm`

Operator's existing VMs (`n8n - docker`, `simplexx`) untouched.

## Re-boot command (one-liner)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\Sinister Sanctum\projects\sinister-os\source\vm-boot\boot-virtualbox.ps1" -IsoPath "D:\Sinister Sanctum\projects\sinister-os\source\iso-base\cachyos-hyprland.iso"
```

The script is idempotent: if `Sinister-OS-Test` already exists it reuses the VM, hot-swaps the ISO if a fresh one is passed, and starts it. Pass `-Recreate` to wipe and rebuild.

## Power-off (clean shutdown from host)

```powershell
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" controlvm Sinister-OS-Test acpipowerbutton
```

## What's NEXT (operator-actionable, in order)

1. **Walk through Calamares to install to the 60 GB virtual disk.** Pick Hyprland edition in the DE selector. Use auto-partition (whole disk). After install completes, power off the VM, detach the ISO (or just let it boot-order to disk), boot fresh — you now have a persistent Hyprland install in the VM.
2. **Snapshot the freshly installed VM** before customizing:
   ```
   VBoxManage snapshot Sinister-OS-Test take cachyos-base-install --description "Vanilla CachyOS Hyprland post-Calamares"
   ```
3. **Layer Sinister branding on top.** Our `airootfs/` work in the parallel `iso-build/` lane becomes a post-install overlay script that:
   - swaps the wallpaper to Sinister purple (from `source/branding/`)
   - replaces `/etc/os-release` ID with `sinister-os` (keep `ID_LIKE=arch cachyos` so package mirrors still resolve)
   - drops the Sinister Panel kiosk config into `~/.config/`
   - installs `sinister-eve.service` + `/etc/sudoers.d/eve` (CLAUDE.md design constraint #1: root-equivalent EVE with curated NOPASSWD allowlist)
   - applies the HyDE Hyprland config tree from `recommended-bases.md` lift #2

## Where the Sinister-OS layer sits relative to CachyOS

```
CachyOS-Live-ISO (vanilla)                  <-- what we just booted
        |
        +-- Calamares install to /dev/sda  <-- next step (in VM)
        |
        +-- Sinister overlay scripts        <-- post-install, layered on top
        |     - branding swap
        |     - eve user + sudoers
        |     - hyprland config (HyDE-based)
        |     - panel kiosk drop-in
        |
        v
Sinister OS (CachyOS-based, Sinister-skinned, EVE-enabled)
```

Net effect: we get gaming-tuned Arch + Calamares + Hyprland + Steam for free, then layer the Sinister identity + EVE shell on top instead of building from `archiso` scratch. The parallel `iso-build/` lane's archiso work is NOT wasted — it becomes our Phase 1.5 "vanilla Sinister archiso" track that runs alongside the jerry-rig CachyOS-based track, giving us two paths to choose from in P4.

## Caveats

- Live ISO is 2.9 GB on disk; sparse VDI grew to ~3 GB after VM creation. Free space budget per VM = ~65 GB.
- Per-IP throttling on Cloudflare meant the download wasn't a one-shot curl — used Python urllib with HTTP Range + 6-worker parallel completion. For re-runs from same IP the throttle may differ; if it stalls again, re-run `python _parallel.py` (it picks up from current file size).
- VBoxManage's `createmedium` writes a progress bar to stderr; PowerShell wraps that as a "RemoteException" but exit code is 0 and the VM works. Cosmetic only.
- Live ISO boots an in-memory Hyprland (or KDE if you pick that in the boot menu). No persistence until you Calamares-install. The Phase boundary "P1 → P2" in plans/master-plan-2026-05-24.md remains operator-gated for the install step.
