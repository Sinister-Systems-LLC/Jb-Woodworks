# PIPELINE-AUDIT-2026-05-24.md

> Author: RKOJ-ELENO :: 2026-05-24
> Scope: `Dockerfile` + `build.sh` + `bake-panel.sh` + `profiledef.sh` + `pacman.conf` + `airootfs/` quick scan.
> Companion: `PACKAGE-AUDIT-2026-05-24.md` (per-package category breakdown).

## Status legend

- **GOOD** — file is correct; no patch required.
- **NEEDS-FIX** — file works but has a real gap; patch provided.
- **BLOCKER** — file will cause the actual mkarchiso run to fail or produce a broken ISO.

---

## 1. `Dockerfile` — **GOOD**

42 lines, single FROM `archlinux:latest`. Pulls `archiso` + standard mkarchiso prereqs (mtools, dosfstools, libisoburn, squashfs-tools, arch-install-scripts, grub) + `pacman -Scc` for image size. `--privileged` requirement is documented. No fix needed.

Minor note (not a NEEDS-FIX): `pacman -Syu` will pull whatever is latest at `docker build` time, so two builds days apart will not be byte-identical. If reproducibility becomes a goal, pin the Arch snapshot URL — defer to P2.

---

## 2. `build.sh` — **GOOD**

44 lines, set -euo pipefail, pre-flights the Panel `server.js` existence before launching the Docker build. Mounts `$PWD` read-only into `/work` (good — prevents the container from accidentally mutating profile inputs), separate writable `/tmp/work` for mkarchiso scratch, separate `/out` for the ISO artifact. `bash -n build.sh` → PASS.

No fix needed.

---

## 3. `bake-panel.sh` — **GOOD**

113 lines, set -euo pipefail. Has the recent (2026-05-24, RKOJ-ELENO) safety fixes for atomic DEST swap + cleanup trap + npm fetch-timeout bounds. `bash -n bake-panel.sh` → PASS.

No fix needed.

---

## 4. `profiledef.sh` — **NEEDS-FIX** (1 item)

40 lines. Branding is Sinister-aligned (`iso_name="sinister-os"`, `iso_label="SINISTER_OS_<YYYYMM>"`, `iso_publisher="Sinister Sanctum <https://github.com/z0nian>"`). Bootmodes covers BIOS (syslinux MBR + eltorito) and UEFI ia32/x64 (grub esp + eltorito) — correct for a hardware-agnostic live ISO.

**NEEDS-FIX 4a:** Missing `file_permissions` entry for `/etc/sudoers.d/eve` if/when an `eve`-specific sudoers file is added (currently the file is named `/etc/sudoers.d/sinister` and that IS covered — verified). However, if P1 splits the sudoers into two files (per CLAUDE.md lane "EVE-as-OS-shell design constraints" referencing `/etc/sudoers.d/eve`), this list will need a second entry. Track as a P1 to-do, not a current blocker.

Patch (defer until P1 actually creates the second file):
```
  ["/etc/sudoers.d/eve"]="0:0:440"
```

---

## 5. `pacman.conf` — **NEEDS-FIX** (1 item)

25 lines. `[core]` + `[extra]` + `[multilib]` all present and `Include = /etc/pacman.d/mirrorlist` correctly. Multilib enabled — Steam + lib32-* will resolve.

**NEEDS-FIX 5a:** No `[chaotic-aur]` repo and no other AUR-bridge. The `eve` sudoers allowlist whitelists `/usr/bin/yay` but `yay` is AUR-only — chicken-and-egg for the live ISO. Two acceptable resolutions:

**Patch option A (recommended for live-ISO determinism)** — pre-bundle the `yay-bin` `.pkg.tar.zst` in `airootfs/var/cache/sinister-extras/` and install it from the first-boot script. No pacman.conf change.

**Patch option B (faster but adds an external trust anchor)** — append to `pacman.conf`:
```
[chaotic-aur]
Include = /etc/pacman.d/chaotic-mirrorlist
```
Plus Dockerfile additions to import the chaotic-aur keyring + mirrorlist (`pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com && pacman-key --lsign-key 3056513887B78AEB && pacman -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst' 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst' --noconfirm`).

Recommendation: **Option A** for the alpha. Option B for the beta if calamares/brave-bin/proton-ge become recurring requirements.

---

## 6. `airootfs/` quick audit (depth 2) — **NEEDS-FIX** (3 items)

Tree found:
```
airootfs/
  etc/
    skel/.config/hypr/hyprland.conf      [PRESENT]
    sudoers.d/sinister                   [PRESENT]
    systemd/system/sinister-first-boot.service [PRESENT]
  root/.automated_script.sh              [PRESENT]
  srv/sinister-panel/server.js           [PRESENT — populated by bake-panel.sh]
  usr/local/bin/sinister-first-boot.sh   [PRESENT]
  usr/local/bin/sinister-panel-kiosk.sh  [PRESENT]
```

**NEEDS-FIX 6a (BLOCKER for the "kiosk auto-launches" claim):** `hyprland.conf` lives at `airootfs/etc/skel/.config/hypr/hyprland.conf` — that's the right path for the **default user's home**. But the live ISO boots as `root` (or as the archiso default `liveuser`) and `/etc/skel` is only used for NEW user creation. The kiosk will NOT auto-launch on first boot of the live ISO unless either (a) a user is auto-created from `/etc/skel` at boot, or (b) the config is also placed at `/root/.config/hypr/hyprland.conf`. Patch: copy `hyprland.conf` to `/root/.config/hypr/` AND have `sinister-first-boot.sh` create the `eve` user from the skel template before exiting.

Patch (add to `sinister-first-boot.sh` before the `touch /var/lib/sinister/.first-boot-done` line):
```
# Create eve user from /etc/skel and add to wheel for full sudo
useradd -m -G wheel,audio,video,input,network -s /bin/bash eve 2>/dev/null || true
# Auto-login eve via greetd
cat >/etc/greetd/config.toml <<'EOF'
[terminal]
vt = 1
[default_session]
command = "Hyprland"
user = "eve"
EOF
systemctl enable greetd.service || true
```

**NEEDS-FIX 6b:** No wallpaper file anywhere in `airootfs/`. `hyprland.conf` does NOT reference one (no `exec-once = swaybg -i ...` line), so this is not a hard block, but the Sinister-branded boot experience expects one. Add `airootfs/usr/share/sinister/wallpaper.png` (purple Sinister motif) AND a `swaybg` autostart line in `hyprland.conf`. Defer to P2 — tracked as a polish item, not a blocker.

**NEEDS-FIX 6c:** `sinister-first-boot.sh` line 28-29 has the `touch` BEFORE the `mkdir -p /var/lib/sinister` which will fail (touch creates parent? No, it does not). Reorder:
```
mkdir -p /var/lib/sinister
chmod 700 /var/lib/sinister
touch /var/lib/sinister/.first-boot-done
```
(Current code does the chmod and touch in the wrong order — the touch will fail on first run because `/var/lib/sinister` doesn't exist yet, and the `set -euo pipefail` will abort the script. This is a **BLOCKER** for first-boot completion.)

---

## 7. `airootfs/etc/sudoers.d/sinister` — **NEEDS-FIX** (1 item)

24 lines, mode 0440 enforced by `profiledef.sh`. Whitelist covers pacman/yay/systemctl/journalctl/nmcli/mount/umount/snapper + the two sinister-* scripts. The `%wheel ALL=(ALL:ALL) ALL` line provides conventional fallback.

**NEEDS-FIX 7a:** `eve ALL=(root) NOPASSWD: /usr/bin/yay` references `yay` which is not pre-installed (AUR-only). See `pacman.conf` NEEDS-FIX 5a — same root cause. Will resolve when yay is pre-bundled OR installed via first-boot. No file change needed here.

---

## Summary table

| File | Status | Patches needed |
|---|---|---|
| Dockerfile | GOOD | none |
| build.sh | GOOD | none |
| bake-panel.sh | GOOD | none |
| profiledef.sh | NEEDS-FIX | 1 (deferred to P1 when sudoers/eve is added) |
| pacman.conf | NEEDS-FIX | 1 (yay bootstrap — recommend pre-bundle, no file change) |
| airootfs/etc/skel/.config/hypr/hyprland.conf | NEEDS-FIX | 1 (also place at /root or create eve user from skel) |
| airootfs/usr/local/bin/sinister-first-boot.sh | **BLOCKER** | 1 (mkdir before touch — file currently reorders the calls fatally) |
| airootfs/etc/sudoers.d/sinister | NEEDS-FIX | 0 (resolves with yay bootstrap) |
| wallpaper | MISSING | deferred to P2 |

## Top 3 BLOCKERS

1. **`sinister-first-boot.sh` orders `touch` before `mkdir`** → first-boot script fails with `set -e` before completing. Reorder lines.
2. **Kiosk Hyprland config only at `/etc/skel/`** → live ISO boots as root/liveuser, no Hyprland session starts, kiosk never launches. Either copy config to `/root/.config/hypr/` OR create eve user from skel in first-boot.
3. **`yay` whitelisted in sudoers but not installed** → first invocation of `yay` (intended path for brave-bin / proton-ge / calamares) fails with `command not found`. Pre-bundle `yay-bin` `.pkg.tar.zst` in airootfs OR add bootstrap step.

---

End of audit.
