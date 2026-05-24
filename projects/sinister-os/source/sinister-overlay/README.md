# sinister-overlay

> Author: RKOJ-ELENO :: 2026-05-24
> Lane: `sinister-os` :: phase P2 (overlay for CachyOS live/installed bases)

## What this is

A self-contained overlay package that converts a vanilla CachyOS system (live ISO OR an installed
disk) into Sinister OS by stamping our branding on every operator-facing surface: `/etc/os-release`,
desktop wallpaper, Hyprland window-manager theme, Waybar status bar, GTK 3/4 accent, Plymouth boot
splash, hostname seed, and the EVE NOPASSWD sudoers policy.

It is **idempotent** and **safe to re-run**. It does NOT install Sinister Panel — that ships as a
separate `sinister-panel-kiosk` package.

Operator directive (verbatim 2026-05-24): *"everything we make needs to have our branding"*.

## Companion: Calamares full-auto preset

Sibling doc [CALAMARES-AUTOMATION.md](CALAMARES-AUTOMATION.md) describes the
one-click installer preset shipped in `etc/calamares/` and applied by
`apply-calamares-preset.sh`. When the operator boots the Sinister OS remastered
ISO and clicks "Install Sinister OS", Calamares walks every install phase
autonomously — disk auto-partitioned, `eve` user pre-created, branding pre-applied,
packages installed, auto-reboot into Hyprland. Per-install override: kernel
parameter `sinister.skip-auto=1`.

## Apply on a booted live CachyOS ISO

```bash
curl -L https://vault.sinister.systems/sinister-overlay.tar.gz | tar xz
cd sinister-overlay
sudo bash install.sh
```

The installer auto-detects the live session (read-only `/usr` + airootfs/cow mounts) and skips
Plymouth (initramfs cannot be rebuilt on a live ISO). All other branding applies in-memory until
reboot — useful for screenshots + UX validation.

## Apply post-install (real disk)

```bash
git clone https://github.com/<org>/sinister-overlay.git
cd sinister-overlay
sudo bash install.sh
```

Full overlay including Plymouth. Log out + back in (or reboot) for every surface to pick up the
theme. The installer prints a summary table at the end (`STEP | RESULT`) showing what landed and
what was skipped.

Useful flags:

| Flag             | Effect                                                                 |
| ---------------- | ---------------------------------------------------------------------- |
| `--dry-run`      | Print every action without executing — preview before commit.          |
| `--no-plymouth`  | Force-skip Plymouth even on an installed system (no initramfs rebuild).|

## What gets stamped

| Surface                                | File / target                                                                |
| -------------------------------------- | ---------------------------------------------------------------------------- |
| `/etc/os-release`                      | `NAME="Sinister OS"`, `ID=sinister`, `LOGO=sinister`. Original backed up to `/etc/os-release.cachyos.bak`. |
| Desktop wallpaper                      | `/usr/share/backgrounds/sinister/wallpaper-primary.{svg,png}` (PNG rendered via `rsvg-convert` if installed). |
| Lockscreen wallpaper                   | `/usr/share/backgrounds/sinister/wallpaper-lockscreen.{svg,png}`             |
| Hyprland (system skel + root)          | `/etc/skel/.config/hypr/hyprland.conf`, `/root/.config/hypr/hyprland.conf`. Sinister purple borders (`#c084fc → #8b5cf6` 45 deg), Waybar autostart, SUPER keybindings. |
| Waybar                                 | `/etc/skel/.config/waybar/{config.jsonc,style.css}` + `/root/.config/waybar/...` |
| GTK 3                                  | `/usr/share/themes/Sinister/gtk-3.0/gtk.css` — Adwaita-dark + Sinister accent override. |
| GTK 4 / libadwaita                     | `/usr/share/themes/Sinister/gtk-4.0/gtk.css` — same accent via `@define-color`. |
| Plymouth boot splash                   | `/usr/share/plymouth/themes/sinister/` + `plymouth-set-default-theme -R sinister`. Installed-system only. |
| Hostname seed                          | `/etc/hostname` set to `sinister-laptop` ONLY if it was empty or `cachyos`. Operator-set names are preserved. |
| EVE sudoers                            | `/etc/sudoers.d/eve` (mode 0440) — NOPASSWD on `pacman`, `systemctl`, `nmcli`, `xdotool`, `swww`, `hyprctl`. |

## What this overlay does NOT do

- Does NOT install `sinister-panel-kiosk` (Sinister Panel runs in its own package).
- Does NOT install Hyprland / Waybar / swww / rsvg-convert — assumes a CachyOS desktop ISO has them
  or that the operator `pacman -S`'s them post-install.
- Does NOT change the kernel or pull in proprietary blobs (per `docs/proprietary-blobs.md` doctrine).
- Does NOT push to bare metal — testing is VM-only until the operator-gated P5 cutover.

## Idempotency

Every step is overwrite-by-design (`install -m ... source dest`). The `/etc/os-release.cachyos.bak`
backup is created only if missing, so re-runs do not chain backups of already-Sinister files. The
hostname step refuses to clobber an operator-set hostname.

## Source single-source-of-truth

All colors derive from `D:/Sinister Sanctum/projects/sinister-os/source/docker-stack/config/theme/sinister-theme-tokens.css`:

| Token                | Value      | Where it lands                                       |
| -------------------- | ---------- | ---------------------------------------------------- |
| `--accent`           | `#c084fc`  | Hyprland active border, Waybar active workspace, GTK accent, Plymouth wordmark. |
| `--accent-strong`    | `#8b5cf6`  | Hyprland border gradient stop, Plymouth core glow.   |
| `--bg`               | `#0e0a1f`  | Wallpaper base, Hyprland background, GTK window bg.  |
| `--bg-2`             | `#1a1330`  | Waybar bg, GTK headerbar, Hyprland inactive border.  |
| `--text`             | `#e9d5ff`  | Waybar text, GTK fg.                                 |

## Uninstall

```bash
sudo bash uninstall.sh
```

Restores `/etc/os-release.cachyos.bak`, removes our wallpaper / theme / Hyprland / Waybar / Plymouth
files, drops `/etc/sudoers.d/eve`. The hostname is reset to `cachyos` only if it is still our
`sinister-laptop` seed; otherwise it is preserved.

## File tree

```
sinister-overlay/
├── install.sh
├── uninstall.sh
├── README.md
├── etc/
│   ├── hostname.sinister
│   ├── os-release.sinister
│   ├── skel/.config/{hypr,waybar}/...
│   └── sudoers.d/eve
├── root/.config/{hypr,waybar}/...
└── usr/share/
    ├── backgrounds/sinister/{wallpaper-primary,wallpaper-lockscreen}.svg
    ├── plymouth/themes/sinister/{sinister.plymouth,sinister.script,background.svg}
    └── themes/Sinister/{index.theme,gtk-3.0/gtk.css,gtk-4.0/gtk.css}
```

## Verification (run before shipping a new build)

```bash
bash -n install.sh && echo "install.sh parse OK"
bash -n uninstall.sh && echo "uninstall.sh parse OK"
grep -rE '#c084fc|#8b5cf6|var\(--accent' .  # confirm Sinister tokens referenced everywhere
```
