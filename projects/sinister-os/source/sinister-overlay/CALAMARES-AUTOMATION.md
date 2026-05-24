# Calamares full-auto preset

> Author: RKOJ-ELENO :: 2026-05-24
> Sibling: [README.md](README.md) — the broader sinister-overlay package this preset ships inside.

This doc explains the one-click Calamares automation that ships with the
sinister-overlay. When the operator boots a Sinister OS remastered ISO and
clicks "Install Sinister OS", Calamares walks through every install phase
autonomously using these presets — no questions, no clicks beyond the initial
"Install" button.

Operator directive (verbatim 2026-05-24): *"i want everything to install all
in one as well full auto to setup eevrything"*.

## What auto-installs

| Phase | Module config | What it does |
| --- | --- | --- |
| Welcome | (settings.conf) | Sinister branding + instant Next |
| Locale | `modules/locale.conf` | US English + UTC (no geoip) |
| Keyboard | `modules/keyboard.conf` | US `pc105` (carries over live session if changed) |
| Partition | `modules/partition.conf` | **Wipes first disk.** 1 GiB EFI (FAT32) + 100 GiB btrfs `/` + remainder btrfs `/home`. No swap (zram instead). No LUKS. |
| Users | `modules/users.conf` | Pre-creates `eve` / fullname `EVE Operator`, password `sinister`, autologin into the `autologin` group, sudo via `wheel` |
| Packages | `modules/packages.conf` | Installs Hyprland + Waybar + greetd + PipeWire + NetworkManager + Plymouth + EVE runtime deps + `paru` (try-install) |
| Bootloader | `modules/bootloader.conf` | systemd-boot, `efiBootloaderId: sinister`, 5s timeout, kernel params `quiet splash rd.udev.log_level=3 nowatchdog` |
| Display manager | `modules/displaymanager.conf` | greetd auto-launching Hyprland for `eve` |
| Hostname | `modules/hostname.conf` | `sinister-laptop` (operator can rename post-install) |
| Finished | `modules/finished.conf` | Auto-reboot via `systemctl -i reboot` with a 10s countdown |
| Cancel button | `settings.conf` | **Hidden entirely** (`disable-cancel: true` + `disable-cancel-during-exec: true`) |

## What it does NOT do (deliberate scope)

- **No LUKS / disk encryption.** First version ships unencrypted; operator can
  encrypt post-install once they understand the tradeoffs (key custody, snapshot
  size, boot flow).
- **No dual-boot.** The partition module is full-wipe single-disk.
- **No custom partitioning UI.** `allowManualPartitioning: false` hides the
  manual option entirely. Operator who wants custom layout uses the override
  (below).
- **No full system update during install.** `update_system: false` — operator
  runs `pacman -Syu` first thing post-install.
- **No telemetry / geoip.** `geoip` is commented out in `locale.conf`.
- **No password strength enforcement.** Default password is intentionally weak;
  operator MUST rotate on first login. The finished screen reminds them.

## Per-install override: kernel parameter

If the operator wants to do a custom install on a specific boot (multi-disk
preserve, dual-boot, custom partitions, LUKS, different user name, etc.), add
this to the kernel command line in the bootloader before booting the live ISO:

```
sinister.skip-auto=1
```

`apply-calamares-preset.sh` reads `/proc/cmdline` and short-circuits before
copying the preset files. Calamares then launches with its stock interactive
config and the operator gets every prompt they expect.

## How the preset gets onto the live ISO

`apply-calamares-preset.sh` (sibling to this doc) copies every file in
`etc/calamares/` into `/etc/calamares/` on the running live system. It runs as
part of the ISO build's first-boot path (added by `source/iso-remaster/` in
P2). For a manual test:

```bash
sudo bash apply-calamares-preset.sh
sudo calamares
```

The script is idempotent — safe to re-run. It honors `sinister.skip-auto=1` so
the operator's escape hatch works even if they re-run by accident.

## Operator action items (NOT automated)

These are the things the operator MUST do after the auto-install finishes —
the installer cannot or should not do them for security/safety reasons:

1. **Rotate the `eve` password.** First login: `passwd` (the shipped default is
   `sinister` and is publicly documented; any attacker who reads this doc has
   it).
2. **Rotate the root password.** `sudo passwd root` then store the new value
   in the operator's password manager.
3. **Run `pacman -Syu`** to pick up everything that landed in the upstream
   mirrors after the ISO snapshot.
4. **Configure NetworkManager** if not on DHCP-friendly Ethernet: `nmtui` for
   a TUI wizard.
5. **Enable LUKS** later if desired: full-disk encryption requires a re-install
   today; we will add LUKS-during-install as an opt-in toggle in P5.

## Verification of this preset (parse + smoke)

Before shipping a build:

```bash
# YAML parses cleanly
for f in source/sinister-overlay/etc/calamares/**/*.conf \
         source/sinister-overlay/etc/calamares/*.conf \
         source/sinister-overlay/etc/calamares/branding/sinister/branding.desc; do
  python -c "import yaml; yaml.safe_load(open('$f'))" || echo "PARSE FAIL: $f"
done

# apply script is shell-clean
bash -n source/sinister-overlay/apply-calamares-preset.sh

# inside a VM with the remastered ISO booted:
sudo bash apply-calamares-preset.sh
sudo calamares     # walks the install, reboots, EVE auto-logs in
```

## Reference

Schema verified against upstream Calamares source via WebFetch
2026-05-24:

- `settings.conf` — https://github.com/calamares/calamares/blob/calamares/settings.conf
- `branding.desc` — https://github.com/calamares/calamares/blob/calamares/src/branding/default/branding.desc
- `partition.conf` — https://github.com/calamares/calamares/blob/calamares/src/modules/partition/partition.conf
- `users.conf` — https://github.com/calamares/calamares/blob/calamares/src/modules/users/users.conf
- `packages.conf` — https://github.com/calamares/calamares/blob/calamares/src/modules/packages/packages.conf
- `bootloader.conf` — https://github.com/calamares/calamares/blob/calamares/src/modules/bootloader/bootloader.conf
- `displaymanager.conf` — https://github.com/calamares/calamares/blob/calamares/src/modules/displaymanager/displaymanager.conf
- `locale.conf` — https://github.com/calamares/calamares/blob/calamares/src/modules/locale/locale.conf
- `keyboard.conf` — https://github.com/calamares/calamares/blob/calamares/src/modules/keyboard/keyboard.conf
- `finished.conf` — https://github.com/calamares/calamares/blob/calamares/src/modules/finished/finished.conf
- CachyOS fork (compared for partition layout sanity) — https://github.com/CachyOS/cachyos-calamares
