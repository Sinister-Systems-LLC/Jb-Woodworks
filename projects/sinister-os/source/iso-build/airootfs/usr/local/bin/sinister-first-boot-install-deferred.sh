#!/usr/bin/env bash
# sinister-first-boot-install-deferred.sh — first-boot installer for deferred packages
# Author: RKOJ-ELENO :: 2026-05-24
#
# Companion to packages.x86_64.slim. The slim base ISO ships ~85 lean packages;
# the heavier or operator-conditional 17 packages live here and install once,
# post-boot, after network is up and yay has been bootstrapped.
#
# Driven by /etc/sinister/first-boot-deferred.list (colon-separated repo:pkg
# rows; lines starting with # are comments). Idempotent: tracks completion via
# /var/lib/sinister/first-boot-deferred.done, and skips any package pacman
# reports as already installed.
#
# One bad package must NOT fail the whole run — we trap per-row failures and
# keep going so the operator gets the maximum yield from the first boot.

set -euo pipefail

LIST=/etc/sinister/first-boot-deferred.list
LOG=/var/log/sinister-first-boot-deferred.log
MARKER=/var/lib/sinister/first-boot-deferred.done
STATE_DIR=/var/lib/sinister

mkdir -p "$STATE_DIR"
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1

echo "[$(date --utc +%FT%TZ)] sinister-first-boot-install-deferred start"

# Idempotency: skip if marker exists
if [ -f "$MARKER" ]; then
    echo "[$(date --utc +%FT%TZ)] marker $MARKER exists, skipping"
    exit 0
fi

if [ ! -f "$LIST" ]; then
    echo "[$(date --utc +%FT%TZ)] FAILED: list $LIST not found"
    exit 1
fi

# Counters
TOTAL=0
INSTALLED=0
SKIPPED=0
FAILED=0

is_installed() {
    pacman -Qi "$1" >/dev/null 2>&1
}

install_pacman() {
    local pkg="$1"
    if is_installed "$pkg"; then
        echo "[$(date --utc +%FT%TZ)] SKIP pacman:$pkg already installed"
        SKIPPED=$((SKIPPED + 1))
        return 0
    fi
    echo "[$(date --utc +%FT%TZ)] pacman -S --noconfirm --needed $pkg"
    if sudo pacman -S --noconfirm --needed "$pkg"; then
        INSTALLED=$((INSTALLED + 1))
        return 0
    else
        echo "[$(date --utc +%FT%TZ)] FAIL pacman:$pkg"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

install_aur() {
    local pkg="$1"
    if is_installed "$pkg"; then
        echo "[$(date --utc +%FT%TZ)] SKIP aur:$pkg already installed"
        SKIPPED=$((SKIPPED + 1))
        return 0
    fi
    if ! command -v yay >/dev/null 2>&1; then
        echo "[$(date --utc +%FT%TZ)] FAIL aur:$pkg — yay not found (should be bootstrapped by sinister-first-boot-install-yay.sh)"
        FAILED=$((FAILED + 1))
        return 1
    fi
    echo "[$(date --utc +%FT%TZ)] yay -S --noconfirm --needed $pkg"
    if yay -S --noconfirm --needed "$pkg"; then
        INSTALLED=$((INSTALLED + 1))
        return 0
    else
        echo "[$(date --utc +%FT%TZ)] FAIL aur:$pkg"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Read list line by line; skip blanks/comments. Trap failures so one bad row
# does not abort the loop (set -e is in effect; || true catches the failure).
while IFS= read -r line || [ -n "$line" ]; do
    # Strip trailing CR (in case file has CRLF line endings from Windows edit)
    line="${line%$'\r'}"
    # Strip leading/trailing whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    # Skip blanks and comments
    [ -z "$line" ] && continue
    case "$line" in \#*) continue ;; esac

    TOTAL=$((TOTAL + 1))
    repo="${line%%:*}"
    pkg="${line#*:}"
    # Strip inline comments after pkg (e.g. "pacman:foo # comment")
    pkg="${pkg%%#*}"
    pkg="${pkg%"${pkg##*[![:space:]]}"}"

    if [ -z "$pkg" ] || [ "$repo" = "$line" ]; then
        echo "[$(date --utc +%FT%TZ)] SKIP malformed row: $line"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    case "$repo" in
        pacman) install_pacman "$pkg" || true ;;
        aur)    install_aur "$pkg" || true ;;
        *)
            echo "[$(date --utc +%FT%TZ)] SKIP unknown repo '$repo' for pkg '$pkg' (expected pacman|aur)"
            SKIPPED=$((SKIPPED + 1))
            ;;
    esac
done <"$LIST"

echo "[$(date --utc +%FT%TZ)] tally: total=$TOTAL installed=$INSTALLED skipped=$SKIPPED failed=$FAILED"

# Mark done even if some packages failed — re-running would just re-fail the
# same packages. Operator can manually retry from /var/log/sinister-first-boot-deferred.log.
touch "$MARKER"

echo "[$(date --utc +%FT%TZ)] sinister-first-boot-install-deferred done"
