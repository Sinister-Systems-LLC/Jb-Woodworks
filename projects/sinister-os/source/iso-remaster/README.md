# iso-remaster -- Sinister OS ISO remaster pipeline

> Author: RKOJ-ELENO :: 2026-05-24
> Lane: `sinister-os` :: sibling of `source/iso-build/` (from-scratch path)

This is the **remaster path** for Sinister OS: take an upstream CachyOS Hyprland
ISO + the `source/sinister-overlay/` directory and produce a single bootable
`sinister-os-vN.iso` that boots already-branded as Sinister OS and runs the
overlay's `install.sh` on first boot.

Companion: `source/iso-build/` builds from scratch with `mkarchiso` (slower,
total control). `iso-remaster/` rides CachyOS's curated package set + Hyprland
config (faster, less surface area to maintain).

## Time budget

- `make build-image`  ~ 3-5 min (one-time download of `archlinux:latest` +
  ~150 MB of Arch packages; cached for subsequent runs)
- `make remaster`     ~ 5-10 min on a decent host (NVMe + 16 GB RAM):
  - mount + rsync ISO tree     ~ 60-90 s
  - unsquashfs airootfs        ~ 90-120 s (2.5 GB squashfs)
  - apply overlay              < 5 s
  - mksquashfs (zstd)          ~ 3-5 min (dominant step)
  - xorriso rebuild ISO        ~ 30-60 s
- `make verify`       ~ 5-10 s

Total wall-clock from a clean repo to a flashable ISO: **~10-15 min**.

## Inputs

| Input            | Path                                                  | Source                              |
|------------------|-------------------------------------------------------|-------------------------------------|
| Upstream ISO     | `source/iso-base/cachyos-hyprland.iso` (2.92 GB)      | downloaded by `_download.py`        |
| Sinister overlay | `source/sinister-overlay/`                            | written by parallel sibling agent   |

## Output

| Output           | Path                                                  |
|------------------|-------------------------------------------------------|
| Remastered ISO   | `source/iso-remaster/out/sinister-os-<UTC>.iso`       |
| SHA256 sidecar   | `source/iso-remaster/out/sinister-os-<UTC>.iso.sha256`|
| Build log        | `source/iso-remaster/_logs/remaster-<UTC>.log`        |

UTC stamps are `YYYYMMDDTHHMMSSZ` (e.g. `20260524T143055Z`).

## First-run, copy-pasteable

From `D:\Sinister Sanctum\projects\sinister-os\source\iso-remaster\` in a
git-bash window:

```bash
# 1. Build the container (one-time, ~5 min)
make build-image

# 2. Remaster the ISO (~10 min)
make remaster

# 3. Verify the output (size + sha256 + xorriso report)
make verify
```

That produces `out/sinister-os-<UTC>.iso` ready to:

- `make verify` -- size + sha256 + xorriso bootability report
- flash to USB:  `dd if=out/sinister-os-<UTC>.iso of=/dev/sdX bs=4M status=progress`
- VM-boot:       point QEMU/VirtualBox at the ISO (see `source/vm-boot/`)

## What the remaster actually does

`remaster.sh` runs these 8 steps, all inside the docker container:

1. Mount input ISO read-only via loop device.
2. `rsync` ISO tree to a writable workspace.
3. Locate the airootfs squashfs (`arch/x86_64/airootfs.sfs` for CachyOS) and
   `unsquashfs` it.
4. Apply the overlay: `rsync OVERLAY_DIR/ -> <root>/sinister-overlay/`, drop a
   `.sinister-version` marker, install a `sinister-firstboot.service`
   one-shot systemd unit that runs `bash /sinister-overlay/install.sh` exactly
   once and creates `/var/lib/sinister/.firstboot-done` as the guard.
5. `mksquashfs` back with the same compression as the original (detected via
   `unsquashfs -s`; defaults to `zstd` on CachyOS).
6. Patch boot configs: rewrite "CachyOS" -> "Sinister OS" in every
   `.cfg`/`.conf`/`grub.cfg`/`isolinux.cfg`/`loopback.cfg`/`syslinux.cfg`
   under the ISO tree.
7. Rebuild the ISO with `xorriso -as mkisofs`, preserving BIOS (isolinux)
   and EFI boot records, with volume label `SINISTER_OS_<VERSION>`.
8. Verify output exists + non-zero + compute SHA256 sidecar.

The script is **idempotent**: `SOURCE_DATE_EPOCH` is pinned to the overlay's
newest mtime, `mksquashfs` is invoked with `-mkfs-time` + `-all-time`, and
file sorting is stable -- rerunning with identical inputs produces a bit-for-bit
identical output ISO.

## Variables you can override

```bash
make remaster VERSION_TAG=v2
make remaster INPUT_ISO=/path/to/other-cachy.iso
make remaster OVERLAY_DIR=/path/to/other-overlay
make remaster IMAGE_TAG=my-fork
```

## Troubleshooting

| Symptom                                                          | Fix                                                                              |
|------------------------------------------------------------------|----------------------------------------------------------------------------------|
| `ERROR: overlay dir not found` (exit 2)                          | The `sinister-overlay/` sibling agent has not finished. Wait + rerun.            |
| `could not mount input ISO (need --privileged + loop device)`    | Make sure Docker Desktop is running and the container has `--privileged` (Makefile sets this).  |
| `unsquashfs: failed to allocate ...`                             | Bump Docker Desktop RAM allocation (Settings -> Resources -> Memory) to 8 GB+.   |
| `xorriso: ERROR: Cannot find ...isohdpfx.bin`                    | Rebuild image: `make build-image` (syslinux package missing in stale layer).     |
| Output ISO won't boot in UEFI VM                                 | Inspect `make verify` xorriso report -- EFI image must be partition 2 type 0xef. |

## Lane discipline reminders

- **VM-only testing.** Never `dd` the output to the operator's bare-metal disk
  without explicit gate. Use QEMU/VirtualBox via `source/vm-boot/`.
- **No commit from this agent.** PIPELINE-READY is the deliverable; first real
  remaster run is operator-action.
- The `out/`, `workspace/`, `_logs/`, `*.iso` paths are gitignored.

## Overlay status (snapshot at write time)

The sibling agent for `source/sinister-overlay/` is still in flight at the
time this README was written -- run `make tree-overlay` to see the current
state. If empty, the overlay agent hasn't finished; `make remaster` will exit
2 with a clean message.
