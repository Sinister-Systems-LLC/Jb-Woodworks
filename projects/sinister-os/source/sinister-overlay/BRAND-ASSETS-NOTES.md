# BRAND-ASSETS-NOTES — install.sh handoff

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Audience:** the sibling EVE working on `source/sinister-overlay/install.sh`

## Contract: PNG-or-SVG branding asset handling

The 2026-05-24T16:38Z generation run hit Gemini quota-depletion (429 RESOURCE_EXHAUSTED). All five branding assets ship as **SVG** in the overlay right now. When Gemini credit is restored, the driver at `projects/sinister-os/build/_work/gen-overlay-brand-assets.py` will produce **PNG** counterparts at the same paths.

`install.sh` MUST tolerate either extension at install-time. Suggested helper:

```bash
# install_brand_asset SRC_DIR DEST_DIR BASENAME
# Prefers SRC_DIR/BASENAME.png; falls back to SRC_DIR/BASENAME.svg.
# Writes the discovered file to DEST_DIR/BASENAME.<ext> with mode 644.
install_brand_asset() {
    local src_dir="$1" dest_dir="$2" basename="$3"
    local src
    if   [[ -s "$src_dir/$basename.png" ]]; then src="$src_dir/$basename.png"
    elif [[ -s "$src_dir/$basename.svg" ]]; then src="$src_dir/$basename.svg"
    else
        echo "WARN: no brand asset for $basename in $src_dir" >&2
        return 1
    fi
    install -Dm644 "$src" "$dest_dir/$(basename "$src")"
}
```

## Per-asset call sites

| Asset basename | Source dir (in overlay tree) | Destination dir (on target FS) | Notes |
|---|---|---|---|
| `wallpaper-primary`   | `usr/share/backgrounds/sinister/` | `/usr/share/backgrounds/sinister/` | Hyprland reads via `~/.config/hypr/hyprland.conf` → `hyprpaper`. |
| `wallpaper-lockscreen`| `usr/share/backgrounds/sinister/` | `/usr/share/backgrounds/sinister/` | `hyprlock` / SDDM theme reference. |
| `background`          | `usr/share/plymouth/themes/sinister/` | `/usr/share/plymouth/themes/sinister/` | Pair with the existing `sinister.plymouth` descriptor; central 200x200 region is intentionally blank for spinner overlay. |
| `show`                | `usr/share/calamares/branding/sinister/` | `/usr/share/calamares/branding/sinister/` | Calamares slideshow loop image. |
| `sinister-logo`       | `usr/share/icons/sinister/` | `/usr/share/icons/sinister/` | App-launcher icon + `/etc/os-release` `LOGO=` reference. If `LOGO` needs a `.png`, `rsvg-convert` it at install-time:<br>`rsvg-convert -w 512 -h 512 sinister-logo.svg -o sinister-logo.png` |

## Plymouth caveat

Plymouth's `script` plugin **prefers PNG**; some plugins (e.g. `two-step`) can read SVG via `rsvg-convert` at theme-install time. Safest path at install:

```bash
if [[ ! -s /usr/share/plymouth/themes/sinister/background.png \
     && -s /usr/share/plymouth/themes/sinister/background.svg ]]; then
    rsvg-convert -w 1920 -h 1080 \
        /usr/share/plymouth/themes/sinister/background.svg \
        -o /usr/share/plymouth/themes/sinister/background.png
fi
plymouth-set-default-theme -R sinister
```

`rsvg-convert` is provided by the `librsvg2-tools` package on Debian/Ubuntu / `librsvg` on Arch — add it to the ISO base package list if it isn't already.

## Palette source-of-truth

Every SVG references colors from `source/docker-stack/config/theme/sinister-theme-tokens.css`:
- `--bg` `#0e0a1f` — wallpaper / plymouth background
- `--accent` `#c084fc` — wordmark gradient top, logo top, status pills
- `--accent-strong` `#8b5cf6` — wordmark gradient bottom, plymouth wordmark, beam center
- `--text` `#e9d5ff` — high-contrast inset accents

Never inline a hex outside that palette without first adding it to the tokens file.
