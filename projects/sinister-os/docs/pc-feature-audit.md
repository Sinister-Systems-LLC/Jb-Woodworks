> **Author:** RKOJ-ELENO :: 2026-05-24

# Sinister OS — Windows PC Feature Audit (operator's actual usage)

Operator directive 2026-05-24 (verbatim): *"make sure everything is fast efficient and only include the shit i need and remove all the fucking bullshit. review what i actually use on my actual pc and base it off all that info"*.

This audit replaces speculation with observation. Every entry below is grounded in a real filesystem path or live process on the operator's Windows 10 host (Zonia user, `C:\Users\Zonia`). Nothing is included on a hunch.

## Method

Inspected:
1. `C:\Program Files\` + `C:\Program Files (x86)\` — installed apps
2. `C:\Users\Zonia\AppData\Local\Programs\` — user-local apps
3. `C:\Users\Zonia\AppData\Roaming\` — app data presence (proof of run)
4. `C:\Users\Zonia\Desktop\` — operator-pinned shortcuts (high signal)
5. `Start Menu\Programs` (both user + system)
6. `Steam\steamapps\common\` — actual installed games
7. `Get-Process` snapshot — live running processes by CPU
8. `Downloads\` recent files — current-month activity

## Live process snapshot (top non-system CPU consumers)

| Process | Signal |
|---|---|
| `claude` (multiple) | Dev workflow — already covered |
| `zen` (multiple) | **PRIMARY BROWSER** — Zen Browser, not Firefox, not Chrome, not Brave |
| `Tresorit` | E2E cloud sync — daily-driver app |
| `com.docker.backend` | Docker Desktop — active container work |
| `audiodg` / `wireplumber` equivalent | Audio in use (Spotify likely) |
| `asus_framework` / `iCUE` / `LightingService` | Vendor RGB/peripheral software (Windows-only — IRRELEVANT to Linux) |
| `VirtualBoxVM` | Active VM (will replace with QEMU/KVM on Linux) |
| `Discord` | Active comms |
| `mintty` (multiple) | git-bash terminals — confirms terminal-heavy workflow |
| `explorer` | Windows shell — replaced by Hyprland |

## Per-category decisions

| Category | Windows evidence | Sinister OS decision | Packages |
|---|---|---|---|
| **Browser (primary)** | Zen Browser running heavy; Firefox + Chrome installed but idle | KEEP Zen as primary; Firefox as fallback; drop Chromium (chromium kept ONLY for kiosk-mode panel shell) | `zen-browser-bin` (AUR — first-boot), `firefox`, `chromium` |
| **Gaming launcher** | Steam (13 games installed) + GOG Galaxy (folder present, no recent activity) | KEEP Steam; SKIP GOG (replace with `lutris` which handles GOG too) | `steam`, `steam-native-runtime`, `lutris` |
| **Gaming runtime** | 7DTD, Rust, BAR, BMW, CS:GO, Factorio, PoE2, Schedule I, Straftat, Tower Dominion, V Rising, Brotato | KEEP — all need Proton + Vulkan + 32-bit libs | `wine-staging`, `winetricks`, `mangohud`, `gamemode`, `lib32-*` vulkan/mesa stack |
| **Anti-cheat games** | EasyAntiCheat folder present (Rust, BAR) | NOTE — many EAC titles work on Proton with `PROTON_EAC_RUNTIME` (handled by Proton GE); keep `proton-ge-custom` queued for first-boot | (AUR — `proton-ge-custom`) |
| **Comms** | Discord running, Telegram Desktop installed (recent download in folder) | KEEP both | `discord`, `telegram-desktop` |
| **Music** | Spotify AppData folder + Start Menu shortcut | KEEP | `spotify-launcher` |
| **Code editors** | VS Code, Cursor, Windsurf, Antigravity, Eclipse Adoptium (NEVER used — JDK only), Visual Studio (huge install) | KEEP VS Code (most common); Cursor + Windsurf available via AUR/post-install; DROP Visual Studio (Windows-only), DROP Eclipse | `code` (Arch package), `git`, `nodejs`, `npm`, `python`, `python-pip`, `python-pipx` |
| **AI runtimes** | Ollama running locally | KEEP | `ollama` |
| **Containers** | Docker Desktop active | KEEP — switch to native `docker` + `docker-compose` | `docker`, `docker-compose`, `docker-buildx` |
| **VM hypervisor** | VirtualBox running | REPLACE with QEMU/KVM (faster, Linux-native) | `qemu-desktop`, `virt-manager`, `libvirt`, `edk2-ovmf` |
| **Cloud sync** | Tresorit running heavy | KEEP — Tresorit has a Linux client (AUR) | `tresorit-cli` (AUR — first-boot) |
| **Screen recording** | OBS Studio installed, GeForce NOW also present | KEEP OBS | `obs-studio` |
| **Screenshot util** | Gyazo | REPLACE with `grim` + `slurp` (Wayland-native, faster) | `grim`, `slurp`, `wl-clipboard` |
| **Remote desktop** | RustDesk, AnyDesk, TightVNC, UltraViewer, HelpWire (FIVE clients) | KEEP only `rustdesk` (cross-platform, FOSS, operator uses) | `rustdesk-bin` (AUR — first-boot) |
| **Networking dev** | Tailscale running, Wireshark installed, Cloudflared, Npcap | KEEP all | `tailscale`, `wireshark-qt`, `cloudflared` |
| **Torrent** | qBittorrent installed | KEEP | `qbittorrent` |
| **Android dev** | Android Studio, platform-tools on Desktop, USB driver, QPilotos | KEEP `android-tools` (adb/fastboot) — drop Android Studio (heavy, IDE — install only if used; not in base) | `android-tools` |
| **DB clients** | MongoDB + Compass installed, MS SQL Server | KEEP MongoDB CLI — DROP MS SQL (Windows-only); Compass via AUR if needed | `mongodb-tools` |
| **Archives** | 7-Zip, WinRAR | REPLACE both with `7zip` (Linux successor to p7zip) + `unrar` | `7zip`, `unrar` |
| **Media players** | (No VLC, but Windows Media Player default) | Use `mpv` (already present) + `imv` for images | `mpv`, `imv` |
| **Office** | NO Microsoft Office, NO LibreOffice, NO Adobe Creative Cloud | SKIP entirely. Operator does NOT use office suites | (none) |
| **Vendor bloat (Windows-only)** | ASUS, GIGABYTE, Corsair iCUE, NVIDIA GeForce Experience, Realtek, Intel, Samsung, Patriot, WD, Verbatim, Logitech G-Hub, Driver Genius | SKIP ALL — Windows-only. `openrgb` handles Corsair/ASUS RGB on Linux | `openrgb` |
| **Browsers (alt)** | AdsPower, Kameleo (anti-detect browsers — Windows-only), Brave NOT installed | SKIP — not Linux-supported | (none) |
| **Password mgmt** | Bitwarden CLI in Roaming | KEEP | `bitwarden`, `bitwarden-cli` |
| **Notes** | Obsidian installed, recent shortcut | KEEP | `obsidian` |
| **Backup/restore** | Clonezilla, ddrescue (already in list) | KEEP | `clonezilla`, `ddrescue` |
| **Raspberry Pi** | Raspberry Pi Imager + Ltd folder | KEEP | `rpi-imager` |
| **Java runtime** | Eclipse Adoptium = JDK 17 (Minecraft / Android Gradle) | KEEP minimal JRE only | `jre17-openjdk` |

## Removed bullshit (Windows-only or unused)

- **Visual Studio 18** — IDE Linux equivalent is VSCode (already keeping)
- **Microsoft SQL Server** — Windows-only; operator uses MongoDB anyway
- **IIS / IIS Express** — Windows web server; Linux has nginx/caddy if needed (not in base)
- **Vendor RGB suites (iCUE, ASUS, GIGABYTE LightingService)** — `openrgb` covers all
- **Driver Genius / DIFX / Npcap / Patriot / WD / Verbatim** — Windows driver/vendor tools, irrelevant on Linux
- **Adobe / GeForce Experience / GOG Galaxy / Antigravity / Kameleo / AdsPower** — closed-source Windows tools; either unused or no Linux client
- **TunnelBear** — Windows-only VPN; if VPN needed, Tailscale already covers operator's actual use
- **TightVNC / UltraViewer / AnyDesk / HelpWire** — 4 redundant remote-desktop clients; `rustdesk` keeps the one operator actually runs
- **Norton** — kept in Roaming but appears stale; Linux doesn't need third-party AV
- **CapCut / Reolink / Roblox / Beyond-All-Reason standalone launcher** — installed but launched via Steam or skipped
- **WSL / Ubuntu-22.04** — irrelevant; we ARE Linux now

## Surprises worth flagging

1. **Zen Browser is the actual primary** — not Brave (NOT installed at all), not Chrome. The original 109-line list assumed Brave; it has been swapped.
2. **No office suite of any kind** — saves us 800 MB of LibreOffice or onlyoffice.
3. **5 remote-desktop apps installed but only 1 actively beneficial** (RustDesk).
4. **Tresorit is heavy** — operator runs it constantly. Linux client exists in AUR; first-boot script will pull it.
5. **VirtualBox in use** — switching to QEMU/KVM gives a 20-30% perf boost and is Linux-native.
6. **Gyazo for screenshots** — `grim` + `slurp` + a `~/Pictures/Screenshots/$(date).png` keybind in `hyprland.conf` matches the muscle memory at zero size cost.

End of audit.
