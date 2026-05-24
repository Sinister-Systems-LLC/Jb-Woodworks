# SLIM-WIRING-2026-05-24

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Driver:** operator hard-canonical 2026-05-24: *"make sure everything is fast efficient and only include the shit i need"*.

## Summary

`build.sh` now defaults to the lean **85-package** list (`packages.x86_64.slim`) instead of the legacy 109-line `packages.x86_64`. The 17 packages the audit moved off the base ISO install once, automatically, on first boot — after the network is up and `yay` has been bootstrapped from AUR.

## Override matrix

| Env var | Behavior |
|---|---|
| (unset) | default — feeds `packages.x86_64.slim` to mkarchiso |
| `SINISTER_PACKAGES=slim` | explicit slim (same as default) |
| `SINISTER_PACKAGES=fat` | reverts to the legacy 109-line `packages.x86_64` |
| `SINISTER_PACKAGES=auto` | prefer `.slim` if present, else fall back to `packages.x86_64` |

Examples:

```bash
./build.sh                          # slim (default)
SINISTER_PACKAGES=fat ./build.sh    # full 109-pkg legacy build
SINISTER_PACKAGES=auto ./build.sh   # let the script pick
```

The script never mutates the source tree. It stages a writable build context under `../../build/_stage`, copies the chosen list in as `packages.x86_64` (the only filename `mkarchiso` reads), and mounts that staged dir read-only into the builder container.

## First-boot deferred installer

Three files cooperate:

1. `airootfs/etc/sinister/first-boot-deferred.list` — 17 rows, format `<repo>:<pkg>` (`pacman:` or `aur:`).
2. `airootfs/usr/local/bin/sinister-first-boot-install-deferred.sh` — reads the list, installs each row, idempotent via `/var/lib/sinister/first-boot-deferred.done`, per-package failure trap so one bad row never aborts the run.
3. `airootfs/etc/systemd/system/sinister-first-boot.service` — gained `ExecStartPost=-/usr/local/bin/sinister-first-boot-install-deferred.sh`. Runs only after `sinister-first-boot.sh` (which bootstraps yay) succeeds. Leading `-` makes the unit ignore non-zero exit so the first-boot state still finalizes.

Service ordering also tightened: `After=network-online.target` + `Wants=network-online.target` (was `network.target`) so the deferred pacman/yay calls have routable internet, not just a link-local interface.

The 17 packages:

```
pacman: discord, obs-studio, spotify-launcher, lutris,
        qemu-desktop, virt-manager, libvirt, edk2-ovmf,
        docker, docker-compose, android-tools
aur:    zen-browser-bin, rustdesk-bin, tresorit-cli,
        proton-ge-custom, obsidian, openrgb
```

## Size estimate

| Phase | Size |
|---|---|
| Slim base ISO (out of mkarchiso) | ~1.8 GB |
| First-boot pull (17 deferred pkgs + transitive AUR deps) | ~500 MB |
| Cumulative on-disk after first boot | ~2.3 GB |
| Reference: legacy 109-pkg ISO (everything in image) | ~2.9 GB |

Net win: 600 MB smaller ISO download, 600 MB smaller install-media write, and the ~500 MB of deferred pulls happen in the background on first boot instead of bloating every distribution copy.
