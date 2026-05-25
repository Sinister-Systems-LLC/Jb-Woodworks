# upstream-bluejay-readonly

> Author: RKOJ-ELENO :: 2026-05-24

## What this is

Read-only clones of canonical Pixel 6a (`bluejay`) kernel sources for **grep-and-reference only**. NEVER patched here. Sinister patches land separately in `../patches/` (created when P3 fires).

Per CLAUDE.md hard rule 3 (no vendor binary leaks) + root `.gitignore` rule (`projects/*/source/`), nothing in this directory is tracked by git. The clones are local-machine only.

## What lives in here (populated by clone scripts)

| Subdir | Upstream URL | Purpose | Approx size |
|---|---|---|---|
| `bluejay/` | https://android.googlesource.com/kernel/private/devices/google/bluejay | Pixel 6a device kernel tree (DTS, board config, defconfig) | ~100-200 MB |
| `common-5.10/` | https://android.googlesource.com/kernel/common (branch `android13-5.10`) | Android Common Kernel (ACK) — the actual Linux 5.10 LTS base | ~3-4 GB |
| `google-modules/aoc/` | https://android.googlesource.com/kernel/google-modules/aoc | Always-on Compute driver (where hotword detection runs) | ~30 MB |
| `google-modules/edgetpu/` | https://android.googlesource.com/kernel/google-modules/edgetpu | TPU driver (on-device ML offload) | ~20 MB |
| `google-modules/power/` | https://android.googlesource.com/kernel/google-modules/power | Power HAL bindings (battery profile) | ~10 MB |
| `google-modules/display/` | https://android.googlesource.com/kernel/google-modules/display | Samsung S6E3FC3 panel driver (blur perf) | ~50 MB |

## Why clone individually instead of `repo`

`repo` (Google's manifest-based multi-tree tool) is a Python script that works on Linux/macOS. On the operator's Windows 10 workstation, individual `git clone` of the few repos we care about is more reliable. The full manifest fetch (`repo sync -c`) would be ~6-8 GB; this targeted subset is ~3.5-4.5 GB.

## How to use

```bash
# Grep for a kernel symbol
grep -r "device_initcall" bluejay/

# Find a defconfig entry
grep "CONFIG_SECURITY_SELINUX" bluejay/arch/arm64/configs/

# Reference upstream sepolicy hook
grep "TYPE_" common-5.10/security/selinux/*
```

When P3 fires (cuttlefish vanilla green), the build pipeline pulls fresh sources via `repo sync` on a Linux build host. THIS read-only mirror is for offline reference during P0-P2 spec work only.

## Rebuilding

If a clone gets corrupted, just `rm -rf <subdir>` and re-run the clone command. Nothing here is unique — everything is upstream-sourced.
