# Sinister OS — Linux desktop integration (.desktop files)

> **Author:** RKOJ-ELENO :: 2026-05-25
> **Block:** N.9 (jcode-review-induced; addendum to fleet-tools-port doctrine)
> **Prior art reviewed:** `C:\Users\Zonia\Desktop\jcode-0.12.4\packaging\linux\jcode-desktop.desktop` (13 lines, single file — operator's "review this and other things like it" 2026-05-25T~10:00Z)

## What's here

Per Linux Desktop Entry spec (`freedesktop.org`), every user-facing Sinister GUI tool ships a `.desktop` file in `/usr/share/applications/` so it appears in:

- KDE Plasma's application launcher / KRunner
- GNOME Activities + Search
- Hyprland's wofi / fuzzel / rofi launchers
- niri's fuzzel
- xdg-open MIME handler chains
- Steam's "Add a Non-Steam Game" picker
- Plasma's "Open With…" menu
- Any DE's recent-apps list

| File | App | Categories | Launcher binary |
|---|---|---|---|
| `eve-desktop.desktop` | EVE Desktop (OS control center) | System;Settings;Utility | `eve-desktop` |
| `sinister-panel.desktop` | Sinister Panel (PWA wrapper) | Network;Development;System | `eve-launcher panel --pwa` |
| `sinister-term.desktop` | Sinister Term (themed kitty) | System;TerminalEmulator;Utility | `sinister-term-launcher` |

More to ship as their backing binaries land (Phase 2):

- `sinister-vault-ui.desktop` — vault browser
- `sinister-memory-ui.desktop` — brain/memory UI
- `sinister-generator.desktop` — AI image gen surface
- `sinister-overseer-ui.desktop` — overseer dashboard
- `sinister-browser.desktop` — auto-relogin browser status panel

## jcode-review findings (what we copy + what we improve)

**jcode pattern we copy:**
- Minimalist 10-13 line `.desktop` format
- `Type=Application` + `Terminal=false` + `StartupNotify=true` as defaults
- `Categories=Development;IDE;` for dev-flavored tools (we use the same for Sinister-Panel)
- `Keywords=` for search

**jcode patterns we deliberately improve on:**

| jcode does | Sinister does | Why |
|---|---|---|
| One `.desktop` file (jcode-desktop only) | Per-tool `.desktop` files for every GUI surface | Fleet has many user-facing surfaces; one-file pattern doesn't scale |
| No icon set | Ship multi-size icon set (16/22/24/32/48/64/128/256 + scalable SVG) | KDE/GNOME require sizes for HiDPI displays |
| No AppStream metadata | Ship `org.sinister.<app>.appdata.xml` | Surfaces in KDE Discover / GNOME Software with screenshots, version, license info |
| No `StartupWMClass` | Set `StartupWMClass=<app>` | Wayland window matching + better Hyprland window rules |
| No `X-GNOME-UsesNotifications` | Set on EVE Desktop + Panel | Native notification integration |
| Hardcoded `Icon=jcode` (single name) | Use freedesktop-spec icon-theme inheritance | Icon themes (Papirus, Adwaita, Bibata) can re-skin our app icons |
| No MIME scheme handler | `MimeType=x-scheme-handler/eve;` for EVE Desktop, `x-scheme-handler/sinisterpanel;` for Panel | Custom URL schemes — `eve://chat` opens EVE Desktop, `sinisterpanel://projects/sinister-os` opens Panel |
| `X-Sinister-*` custom keys (none) | Track lane + author + notes inline | Auditability — every `.desktop` file says which lane owns it |

## jcode build-pattern absorbed (separately, for our Rust daemons)

`C:\Users\Zonia\Desktop\jcode-0.12.4\scripts\build_linux_compat.sh` builds against the manylinux2014 / CentOS 7 / glibc 2.17 baseline inside a Docker container, producing a portable Linux binary + sibling `libssl.so` / `libcrypto.so` + wrapper that sets `LD_LIBRARY_PATH=<self_dir>` for runtime locality.

**We adopt this for the Sinister Rust daemons:** `sinister-eve`, `sinister-gpu-arbiter`, `sinister-game-mode`, `sinister-agent-warden`. Build once on CentOS 7 baseline → runs on Arch + Ubuntu + Debian + Fedora without per-distro repackaging. Cuts CI cost + makes Block N's preinstall-manifest portable across base distros if we ever stop pinning to Arch.

Build wrapper lands `source/iso-build/build-rust-portable.sh` in Phase 2 (Day 4-5 sequential after Rust daemons land). Adapts jcode's pattern verbatim with `cargo build --bin sinister-<tool>` per binary.

## How these get installed

Per Block N preinstall-manifest:

```toml
[tools.eve-desktop]
package = "sinister-eve-desktop"
desktop_file = "/usr/share/applications/eve-desktop.desktop"
icon_path = "/usr/share/icons/hicolor/<size>/apps/eve.png"
appdata = "/usr/share/metainfo/org.sinister.eve-desktop.appdata.xml"
```

The build.sh consumes the manifest + copies files into the airootfs at the right paths. `xdg-desktop-menu install --novendor` runs once on first-boot to refresh the application database.

## How operator launches

After install, operator opens KDE/GNOME/Hyprland launcher and types "EVE", "Sinister", or "Panel" — `.desktop` `Keywords=` field surfaces all three. Click → app opens. Same flow as Windows Start menu + search.

## Cross-references

- `projects/sinister-os/plans/EXECUTION-PLAN-2026-05-25/plan.md` § 4 (Phase 2 Day 4-5) — `.desktop` files install via Block N manifest
- `_shared-memory/knowledge/fleet-tools-port-to-sinister-os-doctrine-2026-05-25.md` — every NEW fleet tool ships `.desktop` + AppStream
- `_shared-memory/knowledge/we-have-the-source-read-it-doctrine-2026-05-25.md` — jcode source read directly, not RE'd
- freedesktop.org Desktop Entry spec: https://specifications.freedesktop.org/desktop-entry-spec/
- AppStream spec: https://www.freedesktop.org/software/appstream/docs/
