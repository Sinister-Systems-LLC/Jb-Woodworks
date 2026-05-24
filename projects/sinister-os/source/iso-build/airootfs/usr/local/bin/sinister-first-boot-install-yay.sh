#!/usr/bin/env bash
# sinister-first-boot-install-yay.sh — bootstrap yay (AUR helper) on first boot
# Author: RKOJ-ELENO :: 2026-05-24
#
# Safety fix 2026-05-24 (RKOJ-ELENO): BLOCKER #3 from PIPELINE-AUDIT-2026-05-24.md.
# /etc/sudoers.d/sinister whitelists /usr/bin/yay but yay is AUR-only and is NOT
# pre-installed on the live ISO. First invocation would fail "command not found".
# This script installs yay-bin from the official AUR source on first boot.
# Idempotent — exits 0 quickly if yay already present.

set -euo pipefail

LOG=/var/log/sinister/yay-bootstrap.log
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1

echo "[$(date --utc +%FT%TZ)] yay bootstrap start"

# Safety fix 2026-05-24 (RKOJ-ELENO): idempotency guard — skip if yay already present
if command -v yay >/dev/null 2>&1; then
    echo "[$(date --utc +%FT%TZ)] yay already installed, skipping bootstrap"
    exit 0
fi

# Safety fix 2026-05-24 (RKOJ-ELENO): need git + base-devel to build AUR pkg
pacman -Sy --noconfirm --needed git base-devel || {
    echo "[$(date --utc +%FT%TZ)] FAILED: pacman could not install git/base-devel"
    exit 1
}

# Build directory in /tmp (tmpfs on live ISO — wiped on reboot, no cleanup needed)
BUILD_DIR=$(mktemp -d -t yay-bootstrap-XXXXXX)
# Safety fix 2026-05-24 (RKOJ-ELENO): makepkg refuses to run as root — use a transient build user
BUILD_USER=yaybuild
if ! id "$BUILD_USER" >/dev/null 2>&1; then
    useradd -m -s /bin/bash "$BUILD_USER"
    # Allow this user passwordless pacman for the duration of bootstrap
    echo "$BUILD_USER ALL=(root) NOPASSWD: /usr/bin/pacman" >/etc/sudoers.d/yaybuild-transient
    chmod 0440 /etc/sudoers.d/yaybuild-transient
fi
chown -R "$BUILD_USER:$BUILD_USER" "$BUILD_DIR"

# Clone + build + install as the build user
sudo -u "$BUILD_USER" bash -c "
    set -euo pipefail
    cd '$BUILD_DIR'
    git clone https://aur.archlinux.org/yay-bin.git
    cd yay-bin
    makepkg -si --noconfirm
"

# Safety fix 2026-05-24 (RKOJ-ELENO): clean up the transient sudoers + build user
rm -f /etc/sudoers.d/yaybuild-transient
userdel -r "$BUILD_USER" 2>/dev/null || true
rm -rf "$BUILD_DIR"

echo "[$(date --utc +%FT%TZ)] yay bootstrap done"
