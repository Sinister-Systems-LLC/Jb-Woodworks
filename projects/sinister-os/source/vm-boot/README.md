<!--
Author: RKOJ-ELENO :: 2026-05-24
Sinister OS :: vm-boot :: README
-->

# Sinister OS :: VM boot harness

Operator-facing harness for booting the Sinister OS ISO inside a display-capable virtual machine on the Windows workstation. Docker can't show a desktop — we need a real VM to see Hyprland, the Panel kiosk shell, Steam, wallpaper, EVE, etc.

The ISO itself is produced by the parallel `iso-build` lane at `source/iso-build/out/sinister-*.iso`. This harness only consumes ISOs; it does not build them.

---

## TL;DR — first time

```bash
# 1. Inspect what VM engines you already have (read-only, safe)
bash source/vm-boot/probe.sh

# 2. If none: install VirtualBox (the recommended first-time engine)
powershell -File source/vm-boot/install-helpers/install-virtualbox.ps1 -Yes

# 3. Boot the ISO (when iso-build lane has produced one)
powershell -File source/vm-boot/boot-virtualbox.ps1
```

That's it. The script creates the VM the first time, then just starts it on subsequent runs.

---

## Which engine to pick

| Engine            | Use it when                                       | Install                                                          |
|-------------------|---------------------------------------------------|------------------------------------------------------------------|
| **VirtualBox**    | Default. Best GUI, easiest daily testing.         | `winget install -e --id Oracle.VirtualBox`                       |
| **QEMU**          | Want CLI-only / scriptable / faster boot loops.   | `winget install -e --id qemu.qemu`                               |
| **Hyper-V**       | Already on Win Pro/Enterprise, no extra install.  | `Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V` (admin) |
| **VMware**        | Already licensed.                                 | (commercial; out of scope here)                                  |

Recommendation: **VirtualBox** for the first boot. The boot window pops open instantly and you can see the Sinister OS splash with zero CLI fuss.

---

## Scripts

### `probe.sh`

Read-only inspection. Prints which engines are installed + version. Safe to run any time.

```bash
bash source/vm-boot/probe.sh
```

Exit code: `0` if at least one engine is usable, `1` if none.

### `boot-virtualbox.ps1`

Creates (or reuses) a VM named `Sinister-OS-Test` and boots it.

```powershell
# Default: 4 GB RAM, 4 vCPUs, 60 GB disk, EFI, latest ISO from iso-build/out/
powershell -File source/vm-boot/boot-virtualbox.ps1

# Override the ISO path explicitly
powershell -File source/vm-boot/boot-virtualbox.ps1 -IsoPath D:\path\to\sinister.iso

# Dry-run — print the VBoxManage commands without executing
powershell -File source/vm-boot/boot-virtualbox.ps1 -DryRun

# Destroy and rebuild the VM from scratch (wipes the virtual disk)
powershell -File source/vm-boot/boot-virtualbox.ps1 -Recreate

# Headless (no display window) — useful for CI-style smoke tests
powershell -File source/vm-boot/boot-virtualbox.ps1 -Headless
```

Parameters:

| Param        | Default              | Meaning                                                          |
|--------------|----------------------|------------------------------------------------------------------|
| `-VmName`    | `Sinister-OS-Test`   | VirtualBox VM name. Won't touch your other VMs.                  |
| `-IsoPath`   | (auto)               | Path to a `.iso`. Auto-discovers latest in `iso-build/out/`.     |
| `-MemoryMB`  | `4096`               | RAM in MB.                                                       |
| `-Cpus`      | `4`                  | vCPUs.                                                           |
| `-DiskGB`    | `60`                 | Virtual disk size (sparse VDI; only grows when written to).      |
| `-DryRun`    | off                  | Print commands without running.                                  |
| `-Recreate`  | off                  | Unregister + delete the existing VM first.                       |
| `-Headless`  | off                  | Use `--type headless` instead of GUI.                            |

### `boot-qemu.sh`

QEMU equivalent. Auto-detects WHPX (Windows Hypervisor Platform) accelerator; falls back to TCG if unavailable.

```bash
# Default
bash source/vm-boot/boot-qemu.sh

# Override ISO
bash source/vm-boot/boot-qemu.sh --iso /d/path/to/sinister.iso

# Dry-run
bash source/vm-boot/boot-qemu.sh --dry-run

# Headless via VNC (connect with TightVNC / RealVNC viewer to localhost:5901)
bash source/vm-boot/boot-qemu.sh --headless --novnc-port 5901
```

Disk lives at `source/vm-boot/state/sinister-os-test.qcow2` (sparse qcow2, gitignored — see below).

### `install-helpers/install-virtualbox.ps1`

Operator-gated wrapper. Prints the `winget install` command. Pass `-Yes` to actually execute.

```powershell
# Just show what would happen
powershell -File source/vm-boot/install-helpers/install-virtualbox.ps1

# Actually install (UAC prompt + brief network blip)
powershell -File source/vm-boot/install-helpers/install-virtualbox.ps1 -Yes
```

---

## What to expect when the VM boots

1. **VirtualBox window opens** showing the firmware splash (EFI).
2. **GRUB / systemd-boot menu** appears with the Sinister OS boot entries.
3. **Live session boots into Hyprland** — purple Sinister wallpaper, Panel kiosk shell on the side.
4. From the live session you can either **try the desktop interactively** or **run the installer** to lay Sinister OS down on the 60 GB virtual disk.

On the first install: pick the virtual disk as the install target. Subsequent reboots will skip the live ISO and boot straight off the virtual disk (the `-Recreate` flag wipes both).

---

## Where the ISO comes from

A parallel agent on the `agent/sinister-os/iso-build-*` branch builds the ISO at:

```
source/iso-build/out/sinister-<date>-<arch>.iso
```

`boot-virtualbox.ps1` and `boot-qemu.sh` both auto-pick the most recent matching `sinister-*.iso`. If the build hasn't produced one yet, the scripts will create the VM shell but exit before attempting to boot.

---

## Troubleshooting

**No graphics / black window**
- VirtualBox: try `--graphicscontroller vboxsvga` instead of `vmsvga` (edit the script param). Some Hyprland configs prefer it.
- QEMU: try `-vga std` instead of `-vga virtio`.

**No network in the guest**
- Default config is NAT — guest has internet, host cannot reach guest. To SSH in, add a port-forward: `VBoxManage modifyvm Sinister-OS-Test --natpf1 "ssh,tcp,,2222,,22"` then `ssh -p 2222 user@localhost`.

**Very slow boot (QEMU)**
- The script fell back to TCG. Enable Windows Hypervisor Platform: `Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform` (admin shell) and reboot. Re-run; you'll see `accelerator: whpx`.

**"VBoxManage not found"**
- VirtualBox isn't on PATH. The script auto-detects `C:\Program Files\Oracle\VirtualBox\VBoxManage.exe`. If you installed elsewhere, edit `Resolve-VBoxManage` in `boot-virtualbox.ps1`.

**VirtualBox + Hyper-V conflict (older versions)**
- VirtualBox 7.x coexists with Hyper-V / WHPX on Windows 10/11. If you're on an old VirtualBox (<6.1) and have Hyper-V enabled, uninstall Hyper-V or upgrade VirtualBox.

**"Operator's existing VMs"**
- This harness only acts on a VM named `Sinister-OS-Test`. Other VMs (`n8n - docker`, `simplexx`, anything else) are untouched.

---

## State that lives here

| Path                                          | Purpose                              | gitignored? |
|-----------------------------------------------|--------------------------------------|-------------|
| `state/sinister-os-test.qcow2`                | QEMU virtual disk (sparse)           | yes         |
| `~/VirtualBox VMs/Sinister-OS-Test/`          | VirtualBox VM + VDI disk             | (outside repo) |

Add `state/` to `.gitignore` if it isn't already.
