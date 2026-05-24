# decisions.md — Sinister OS

> **Author:** RKOJ-ELENO :: 2026-05-24
> Append-only log of architectural decisions. Most-recent at top.

## 2026-05-24 :: D-001 :: Base distro = Arch Linux + linux-cachyos

**Decision:** Use Arch Linux as the base, with linux-cachyos as the default kernel.
**Alternatives considered:** NixOS (kept as Phase 6+ migration target), Ubuntu (rejected: Snap tax + GNOME default + slower packages), Fedora Bazzite (rejected: atomic model limits EVE's ad-hoc package writes), Gentoo (rejected: maintenance cost = entire project).
**Rationale:** Arch's PKGBUILD model + AUR + bleeding-edge packages + gaming community support + linux-cachyos scheduler tuning for desktop responsiveness.
**Reversible?** Phase boundaries are reversible. Switching base distro post-P4 is operator-gated and likely requires full rebuild.
**Reference:** master-plan-2026-05-24.md § 3.

## 2026-05-24 :: D-002 :: Compositor = Hyprland (Wayland) primary, i3 (Xorg) fallback

**Decision:** Hyprland is the default compositor; i3wm is preinstalled for Xorg fallback (NVIDIA Wayland HDR issues, etc.).
**Rationale:** Dynamic tiling matches operator's RKOJ workbench tab discipline. Hyprland has the best Wayland gaming support. Xorg fallback covers edge cases.
**Reversible?** Yes — toggle session at SDDM login.
**Reference:** master-plan-2026-05-24.md § 5.1.

## 2026-05-24 :: D-003 :: EVE control = sudoers NOPASSWD allowlist (no UAC equivalent)

**Decision:** EVE runs as the `eve` system user with `NOPASSWD` for a curated allowlist (pacman, systemctl, mount, etc.). Destructive commands (rm, dd, mkfs, parted) require operator hotkey-confirm.
**Rationale:** Operator's "no nonsense" requirement = no per-action UAC. But destructive commands always need a confirm to prevent EVE from wiping the operator's machine on a single hallucination.
**Reversible?** Yes — operator can edit `/etc/sudoers.d/eve` to widen/narrow.
**Reference:** master-plan-2026-05-24.md § 4.1.

## 2026-05-24 :: D-004 :: Filesystem = btrfs + snapper

**Decision:** Btrfs subvolumes for `/`, `/home`, `/var/log`, `/var/cache/pacman`, `/srv/sinister`. Snapper for snapshots. Snap-pac hook for pacman pre-snapshots.
**Rationale:** Atomic rollback to last-good state is the difference between "EVE made a mistake → operator reboots → fine" and "EVE made a mistake → operator reinstalls". Snapper + btrfs is the lowest-friction snapshot path.
**Reversible?** Operator can pick ext4 at install time; loses snapshot ability.
**Reference:** master-plan-2026-05-24.md § 9.

## 2026-05-24 :: D-005 :: Gaming primary = Steam + Proton-GE; secondary = Lutris + Heroic; non-gaming Windows apps = Bottles

**Decision:** Three-tier strategy for Windows compat.
**Rationale:** Each tool targets a use case. Steam = best for Steam library. Lutris/Heroic = best for non-Steam launchers. Bottles = best for ad-hoc Windows apps.
**Reversible?** Trivially — they coexist.
**Reference:** master-plan-2026-05-24.md § 6 + § 7.
