# Proprietary blobs — Sinister OS

> Author: RKOJ-ELENO :: 2026-05-24
> Lane Rule reference: `projects/sinister-os/CLAUDE.md` § "Hard rules for this lane" item 4 — "No proprietary blobs without surfacing them."
> Companion: `source/iso-build/packages.x86_64` (entries marked NON-FOSS in the package audit).

## Purpose

Sinister OS is built on Arch Linux, which is FOSS-first but does not categorically refuse non-free software. The operator's PC is a daily-driver gaming + comms machine, so several proprietary components are intentional inclusions. This file is the durable inventory so the operator can see exactly what is bundled, what license each component carries, and where the source of trust lives.

Updated on every change to `packages.x86_64` that adds or removes a non-FOSS entry.

---

## Currently bundled in `packages.x86_64` (NON-FOSS)

| Package | Repo | License | Why bundled | Update channel |
|---|---|---|---|---|
| `steam` | `multilib` | Valve Steam Subscriber Agreement | Operator's primary gaming launcher; Phase 4 stack | `pacman -Syu` for the launcher; Steam self-updates for the runtime |
| `steam-native-runtime` | `multilib` | Valve SSA + bundled deps | glibc-current compatibility shim for Steam | tied to `steam` package |
| `discord` | `multilib` | Discord ToS (closed source) | Operator-requested comms (per audit request 2026-05-24) | `pacman -Syu`; client also self-updates |
| `spotify-launcher` | `extra` | FOSS launcher (MIT) → pulls proprietary Spotify client | Operator-requested music; the launcher is FOSS, the actual `spotify` binary downloaded on first run is proprietary | launcher via pacman; client via launcher |
| `intel-ucode` | `core` | Intel microcode license (redistributable binary blob) | CPU microcode for Intel chips; security-critical | `pacman -Syu` |
| `amd-ucode` | `core` | AMD microcode license (redistributable binary blob) | CPU microcode for AMD chips; security-critical | `pacman -Syu` |
| `linux-firmware` | `core` | mixed redistributable blobs (Realtek, Atheros, Intel WiFi, etc.) | Wireless / GPU / chipset firmware | `pacman -Syu` |
| `edk2-shell` | `extra` | BSD-style, but UEFI binary blob | UEFI shell for boot diagnostics | `pacman -Syu` |
| `b43-fwcutter` (transitive via linux-firmware) | `core` | Broadcom WiFi firmware extraction tool | only if Broadcom chip detected | `pacman -Syu` |

## Optional (commented out / NOT currently in packages.x86_64 — flagged for future decision)

| Package | Repo | License | Reason held back |
|---|---|---|---|
| `nvidia` | `extra` | NVIDIA proprietary EULA | GPU vendor not yet pinned in spec; a separate `sinister-os-nvidia` ISO variant is the cleaner option |
| `nvidia-utils` | `extra` | NVIDIA proprietary EULA | tied to `nvidia` |
| `lib32-nvidia-utils` | `multilib` | NVIDIA proprietary EULA | tied to `nvidia` |
| `nvidia-settings` | `extra` | NVIDIA proprietary EULA | tied to `nvidia` |
| `nvidia-dkms` | `extra` | NVIDIA proprietary EULA | for custom kernels — likely not needed |
| `vivaldi` | AUR | proprietary | alt browser, not requested |
| `zoom` | AUR | proprietary | not requested |
| `1password` | AUR | proprietary | not requested |

## AUR-deferred (will pull proprietary if installed)

| Package | Source | License | Install path |
|---|---|---|---|
| `proton-ge-custom` | AUR | mixed FOSS + Valve Proton (binary tarball) | Bundle tarball in airootfs OR first-boot via `yay` |
| `brave-bin` | AUR | MPL 2.0 (browser) + binary blobs (DRM widevine) | First-boot via `yay`; the binary tarball pulled from Brave's release server |
| Widevine CDM (transitive via brave-bin / chromium) | Google binary blob | Google CDM License | needed for Netflix / Spotify / Disney+ DRM playback in browser |

## Excluded by policy (will never auto-install)

- Closed-source kernel modules outside the curated list above
- Anything from `multilib-testing` or `testing` repos (instability)
- Any blob requiring online registration / phone-home telemetry that cannot be disabled
- Anything that requires the operator to accept an EULA via GUI on first boot (block boot)

## Trust + supply chain notes

- All `pacman` packages are signed; `pacman.conf` enforces `SigLevel = Required DatabaseOptional`.
- AUR packages are NOT signed by Arch; `yay` builds them locally from PKGBUILDs. Trust is on the AUR maintainer.
- `[chaotic-aur]` (if added per `PIPELINE-AUDIT-2026-05-24.md` § 5 option B) signs its rebuilt AUR packages, but introduces an additional third-party trust anchor (chaotic-aur maintainers).
- Steam, Discord, Spotify, and Brave all self-update at runtime — pacman tracks the launcher / installer, the actual binary running in user space may be newer than what pacman recorded.

## How to remove a blob

```
# Example: drop Discord
sudo pacman -Rns discord
# Also remove the line from packages.x86_64 and rebuild the ISO
```

For Steam (which has external data in `~/.local/share/Steam`), removing the package leaves user data intact; nuke the directory if a full purge is needed.

---

End of inventory.
