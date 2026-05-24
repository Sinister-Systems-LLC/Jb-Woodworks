# Apply sinister-overlay to a running CachyOS VM (live ISO)

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Verified path:** A — `VBoxManage guestcontrol` over Guest Additions.
> **VM:** `Sinister-OS-Test` (CachyOS live ISO, Plasma 6, Hyprland config not active in live).
> **Live user:** `liveuser` (empty password; sudoers `NOPASSWD: ALL`).
> **Receipts:** see `post-overlay-2026-05-24.png` (Calamares foreground, purple panel) and `post-overlay-desktop-2026-05-24.png`.

## Why Path A worked

`VBoxManage guestproperty enumerate Sinister-OS-Test` showed:
- `/VirtualBox/GuestAdd/Version = 7.2.8` (revision 173730)
- `/VirtualBox/GuestInfo/OS/LoggedInUsersList = liveuser`

Guest Additions are preinstalled in the CachyOS 2026.03 live ISO, so the host can copy files and `run` binaries inside the live session without operator intervention. No Shared Folder mount needed.

## Repro (host = Windows 10, git-bash)

```bash
# 1. Tar overlay (host side)
cd "D:/Sinister Sanctum/projects/sinister-os/source"
tar czf /tmp/sinister-overlay.tar.gz sinister-overlay/

# 2. Push to /tmp inside VM. Important quirks:
#    - MSYS_NO_PATHCONV=1 prevents git-bash from mangling /tmp/ into a Windows path
#    - The source path MUST be the Windows form because git-bash translates the local arg
VBOX="C:/Program Files/Oracle/VirtualBox/VBoxManage.exe"
SRC="C:/Users/Zonia/AppData/Local/Temp/sinister-overlay.tar.gz"
MSYS_NO_PATHCONV=1 "$VBOX" guestcontrol Sinister-OS-Test copyto \
  --target-directory /tmp/ "$SRC" \
  --username liveuser --password ''

# 3. Extract + run install.sh as root. The `--` argv quirk: omit a leading "bash" token —
#    the first token after `--` becomes argv[0], and `--exe` already sets the binary.
MSYS_NO_PATHCONV=1 "$VBOX" guestcontrol Sinister-OS-Test run \
  --exe /usr/bin/bash --username liveuser --password '' \
  --wait-stdout --wait-stderr -- \
  -c "cd /tmp && rm -rf sinister-overlay && tar xzf sinister-overlay.tar.gz && \
      sudo -n bash /tmp/sinister-overlay/install.sh"

# 4. Push the new wallpaper into the LIVE Plasma session (does not require relogin)
MSYS_NO_PATHCONV=1 "$VBOX" guestcontrol Sinister-OS-Test run \
  --exe /usr/bin/bash --username liveuser --password '' \
  --wait-stdout --wait-stderr -- \
  -c "export DISPLAY=:0; \
      export XDG_RUNTIME_DIR=/run/user/\$(id -u liveuser); \
      export DBUS_SESSION_BUS_ADDRESS=unix:path=\$XDG_RUNTIME_DIR/bus; \
      plasma-apply-wallpaperimage /usr/share/backgrounds/sinister/wallpaper-primary.png"

# 5. Screenshot
"$VBOX" controlvm Sinister-OS-Test screenshotpng /path/to/post-overlay.png
```

## Install.sh result (live session, 2026-05-24)

| Step | Result |
|---|---|
| os-release | OK |
| wallpapers | OK |
| hyprland | OK (writes /etc/skel + /root only — invisible in live until those users exist) |
| gtk-qt | OK |
| plymouth | SKIP (live session — initramfs cannot be rebuilt; expected) |
| hostname | SKIP (operator-set hostname "CachyOS" preserved) |
| sudoers | OK (visudo -cf passed) |

Exit code: 0.

## What the operator now sees inside the VM

- **Wallpaper:** Sinister purple radial gradient (1920x1080 PNG rasterized from the overlay SVG via `rsvg-convert`). Visible behind Calamares; visible bleed-through in the Plasma panel translucency at the bottom of the screen.
- **`/etc/os-release`:** `PRETTY_NAME="Sinister OS"`, `ID=sinister`, `ID_LIKE="arch cachyos"`. `cachyos.bak` preserved for revert.
- **`/etc/sudoers.d/eve`:** EVE NOPASSWD allowlist installed (pacman/systemctl/nmcli/xdotool/swww/hyprctl). Validated by `visudo -cf`.
- **`/usr/share/themes/Sinister/`:** GTK 3 + 4 accent overlay applied at the theme level. Not auto-selected as the active GTK theme in this live session — to flip it: System Settings → Appearance → GNOME/GTK Application Style → choose "Sinister".
- **`/etc/skel/.config/hypr/` and `/root/.config/hypr/`:** Hyprland config seed deployed. Inert in the live session (Plasma is the active compositor), takes effect for the installed user after Calamares-driven install.

## What changes are EPHEMERAL (live ISO = RAM-backed overlayfs)

The CachyOS live ISO uses an overlayfs on tmpfs — every change above is lost on reboot. To make this overlay survive into the installed system the operator must either:
1. Run Calamares to install CachyOS, boot the installed system, then re-apply this overlay against the installed root (it auto-detects "installed" mode and writes Plymouth + the full theme stack), OR
2. Bake the overlay into the ISO before install (see `CALAMARES-AUTOMATION.md` for the postinstall hook approach).

## Caveats / gotchas

- **SVG comments must not contain double hyphens.** First install run failed because `wallpaper-primary.svg` had `--bg #0e0a1f` (CSS-var syntax) inside an XML comment. Fixed by rewriting that comment line. Watch this for any future SVG additions.
- **`--target-directory` for `copyto` MUST be a Linux path** and you must use `MSYS_NO_PATHCONV=1` from git-bash to prevent path mangling. PowerShell does not have this issue.
- **`VBoxManage guestcontrol run -- argv0 argv1 ...`** — the first token after `--` is argv[0]. For `bash -c "..."` either set argv[0] to `bash` AND argv[1] to `-c` AND argv[2] to the command (we instead used `-- -c "command"` which makes argv[0]="-c" — bash on Linux tolerates this because `--exe` sets the actual binary).
- **`plasma-apply-wallpaperimage`** must run as the logged-in user with `XDG_RUNTIME_DIR` and `DBUS_SESSION_BUS_ADDRESS` set, otherwise it cannot reach the Plasma session bus.
- **Calamares is modal-ish in this build** — KWin `showDesktop true` did not minimize it. If the operator wants a wallpaper-only screenshot, they should manually close Calamares first (or wait until install completes).

## Revert (live VM)

```bash
sudo -n bash /tmp/sinister-overlay/uninstall.sh
```

Restores `/etc/os-release.cachyos.bak`, removes `/usr/share/backgrounds/sinister/`, removes `/etc/sudoers.d/eve`. Wallpaper change in the running Plasma session does not auto-revert — operator re-applies CachyOS default via `plasma-apply-wallpaperimage /usr/share/wallpapers/cachyos-wallpapers/north.png`.
