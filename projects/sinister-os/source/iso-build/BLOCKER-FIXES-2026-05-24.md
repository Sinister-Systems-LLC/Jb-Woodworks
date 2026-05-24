# BLOCKER-FIXES-2026-05-24.md

> Author: RKOJ-ELENO :: 2026-05-24
> Companion: `PIPELINE-AUDIT-2026-05-24.md` (audit that identified these BLOCKERs).
> Scope: minimum-viable patches so the from-scratch ISO produces a bootable image.

## Patch log

### BLOCKER #1 — `sinister-first-boot.sh` ordered `touch` before `mkdir`

- **File:** `airootfs/usr/local/bin/sinister-first-boot.sh` (lines 27-31)
- **Before:** `touch /var/lib/sinister/.first-boot-done` ran before `mkdir -p /var/lib/sinister`. Under `set -euo pipefail` the `touch` aborts the whole first-boot script because the parent dir does not exist yet.
- **After:** Reordered to `mkdir -p` → `chmod 700` → `touch`. The marker file lands correctly and the script can continue.
- **Why:** Fatal under strict-mode shell. The `ConditionPathExists=!/var/lib/sinister/.first-boot-done` guard on the systemd unit means a half-executed first boot would re-trigger on every reboot, never converging.

### BLOCKER #2 — Hyprland kiosk config never loaded at first boot

- **File:** `airootfs/usr/local/bin/sinister-first-boot.sh` (new block, lines 33-37)
- **Before:** `hyprland.conf` only at `airootfs/etc/skel/.config/hypr/hyprland.conf`. The archiso live environment boots as `root` (or `liveuser`) — `/etc/skel` is consulted only at user creation, so the kiosk autostart line never fires.
- **After:** First-boot script `mkdir -p /root/.config/hypr` then `cp -f /etc/skel/.config/hypr/hyprland.conf /root/.config/hypr/hyprland.conf`. On next compositor launch Hyprland reads from the root user's home and the `exec-once = /usr/local/bin/sinister-panel-kiosk.sh` line fires.
- **Why simpler option:** Per audit's two-option recommendation, the copy-to-/root path is one mkdir + one cp inside the existing first-boot script. The greetd auto-login of a dedicated `eve` user (audit's alternative) requires creating the user, configuring greetd, enabling the unit, and re-testing the wheel-group sudo path — strictly more surface for the alpha. Comment in the script flags greetd as the M2 long-term work.

### BLOCKER #3 — `yay` whitelisted in sudoers but not installed

- **File:** `airootfs/usr/local/bin/sinister-first-boot-install-yay.sh` (new, 56 lines) + invocation from `sinister-first-boot.sh` line 40
- **Before:** `/etc/sudoers.d/sinister` whitelists `/usr/bin/yay` but yay is AUR-only and is not in `packages.x86_64`. First invocation: `command not found`. brave-bin / proton-ge / calamares install paths all break.
- **After:** New oneshot bootstrap script. Idempotent guard (`command -v yay` short-circuit), pulls `git` + `base-devel` via pacman, creates a transient `yaybuild` user (makepkg refuses root), grants it transient passwordless pacman via `/etc/sudoers.d/yaybuild-transient`, clones `https://aur.archlinux.org/yay-bin.git`, runs `makepkg -si --noconfirm`, then tears down the transient user and sudoers entry. Logs to `/var/log/sinister/yay-bootstrap.log`.
- **Why first-boot bootstrap over pre-bundling .pkg.tar.zst:** Bundling pins a version, requires per-rebuild refresh of the `.pkg.tar.zst`, and adds a binary blob to the airootfs that needs a checksum-or-signature story. First-boot bootstrap pulls a fresh build from the canonical AUR repo and adds no airootfs binary weight; downside is requiring network on first boot (acceptable — first-boot already enables NetworkManager and pulls Ollama models on demand).
- **Invocation:** Trailing `|| true` so a yay bootstrap failure does not abort first-boot completion (the marker file is touched immediately before, so first-boot is considered done even if yay bootstrap fails — the marker can be deleted manually to retry).

## Files changed

| Path | Change |
|---|---|
| `airootfs/usr/local/bin/sinister-first-boot.sh` | Edit: reorder + add BLOCKER #2 + BLOCKER #3 invocation |
| `airootfs/usr/local/bin/sinister-first-boot-install-yay.sh` | New: yay bootstrap |
| `BLOCKER-FIXES-2026-05-24.md` | New: this log |

## Verification

```
$ bash -n airootfs/usr/local/bin/sinister-first-boot.sh             ; echo $?
0
$ bash -n airootfs/usr/local/bin/sinister-first-boot-install-yay.sh ; echo $?
0
```

Both scripts parse-clean under bash strict-mode. Acceptance test (boots in QEMU, first-boot service runs to completion, marker file present, `/root/.config/hypr/hyprland.conf` exists, `command -v yay` resolves) is deferred — the from-scratch ISO build is still in flight in another agent. This patch is `smoke-tested` (parse-clean) but NOT `acceptance-tested` until the ISO actually boots in QEMU.

## Caveats

- The yay bootstrap requires network on first boot; if the live ISO is booted offline, `command -v yay` will still fail. Acceptable for the alpha (online assumption matches Ollama-pull behavior already present).
- Reordering of touch-vs-mkdir does not change the systemd unit's `ConditionPathExists` semantics, but means the marker now lands BEFORE the BLOCKER #2 + BLOCKER #3 work. If yay bootstrap fails, first-boot is still considered done. Trade-off: avoid re-running the heavy bootstrap on every reboot; acceptable because the bootstrap is idempotent and can be re-run manually.
- `chown -R eve:eve /var/log/sinister` on line 25 references the `eve` user which is NOT created yet on the alpha live ISO. The `|| true` guard prevents abort. When greetd auto-login of `eve` lands in M2, this becomes a real chown; until then it is a no-op that documents intent.
