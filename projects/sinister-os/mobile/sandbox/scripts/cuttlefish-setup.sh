#!/usr/bin/env bash
# cuttlefish-setup.sh — one-shot Linux host bootstrap for the Sinister sandbox
# RKOJ-ELENO :: 2026-05-24 :: GPL-3.0-or-later
#
# Targets: Ubuntu 22.04 LTS / Debian 12 (other distros: substitute the apt block)
# Requires: x86_64 host with hardware virtualisation (vmx/svm), sudo, ~50 GB free disk
# Idempotent: rerun is safe.
#
# What it does:
#   1. Installs cuttlefish-base + cuttlefish-user packages from Google's PPA
#   2. Adds the invoking user to kvm/cvdnetwork/render groups
#   3. Verifies KVM is available
#   4. Downloads the latest cuttlefish-tools (cvd CLI)
#   5. Prepares the sandbox workdir at ~/sinister-cvd/
#   6. Prints the next-step command (does NOT auto-boot anything)
#
# What it does NOT do:
#   - Flash anything
#   - Pull any vendor firmware (operator does that interactively at P3)
#   - Touch any physical device
#
# Anti-brick: this script never runs `fastboot`, `adb sideload`, or `heimdall`.
# Grep gate in seven-green-gate.sh enforces that.

set -euo pipefail

WORKDIR="${SINISTER_CVD_HOME:-$HOME/sinister-cvd}"
LOG_PREFIX="[cuttlefish-setup]"

log()  { echo "${LOG_PREFIX} $*"; }
fail() { echo "${LOG_PREFIX} FAIL: $*" >&2; exit 1; }

# ----- Preflight ---------------------------------------------------------------

log "checking host arch + virtualisation support"
[[ "$(uname -m)" == "x86_64" ]] || fail "host arch is $(uname -m), need x86_64"
grep -qE '^(vmx|svm)$' <(grep -oE 'vmx|svm' /proc/cpuinfo | head -1) \
  || fail "no vmx/svm CPU flag — enable hardware virtualisation in BIOS"

if ! command -v sudo >/dev/null; then
  fail "sudo not present"
fi

# ----- Distro detection --------------------------------------------------------

if [[ -f /etc/os-release ]]; then
  . /etc/os-release
  log "distro: ${PRETTY_NAME:-unknown}"
else
  fail "/etc/os-release missing"
fi

case "${ID:-}" in
  ubuntu|debian) ;;
  *) log "WARNING: distro is ${ID:-unknown} — package install steps assume Debian/Ubuntu apt; substitute as needed" ;;
esac

# ----- Cuttlefish package install ---------------------------------------------

log "installing cuttlefish packages (requires sudo)"
sudo apt-get update -y
sudo apt-get install -y \
  cuttlefish-base \
  cuttlefish-user \
  android-platform-tools-base \
  qemu-system-x86 \
  qemu-utils \
  curl \
  jq \
  unzip \
  python3-pip \
  shellcheck \
  || fail "apt install failed"

# ----- Group membership --------------------------------------------------------

USER_NAME="${SUDO_USER:-$USER}"
for grp in kvm cvdnetwork render; do
  if getent group "$grp" >/dev/null; then
    sudo usermod -aG "$grp" "$USER_NAME"
    log "added $USER_NAME to $grp"
  else
    log "group $grp not present yet (will appear after first cvd start)"
  fi
done

# ----- Workdir -----------------------------------------------------------------

log "preparing workdir: $WORKDIR"
mkdir -p "$WORKDIR"/{images,builds,logs,fingerprints,seven-green}

# ----- Sanity check ------------------------------------------------------------

log "checking KVM accessibility"
if [[ -e /dev/kvm ]]; then
  ls -la /dev/kvm
else
  log "WARNING: /dev/kvm absent — cvd start will fail until you reboot or enable KVM"
fi

log "checking cvd binary"
if command -v cvd >/dev/null; then
  cvd --help 2>&1 | head -3 || true
else
  log "WARNING: cvd not on PATH after install — log out + back in to pick up group membership, then re-run"
fi

# ----- Verify rollback asset path placeholder ---------------------------------

ROLLBACK_DIR="$WORKDIR/rollback"
mkdir -p "$ROLLBACK_DIR"
if [[ ! -f "$ROLLBACK_DIR/bluejay-stock-boot.img" ]]; then
  cat > "$ROLLBACK_DIR/README-operator-fetch.md" <<'EOF'
# Rollback asset — operator-fetch required

This directory must contain `bluejay-stock-boot.img` (the signed Pixel 6a
factory boot.img) before any custom-kernel work begins.

Operator action:
  1. Visit flash.android.com/factoryimage (or use the operator's existing factory-image archive)
  2. Download the bluejay factory image matching the AOSP base build the kernel targets
  3. Unzip; extract `boot.img` to this directory as `bluejay-stock-boot.img`
  4. `sha256sum bluejay-stock-boot.img > bluejay-stock-boot.img.sha256`
  5. Confirm via `bash scripts/verify-rollback-asset.sh`

Why: per `docs/anti-brick-safety.md` Gate 4, the rollback asset is the
unbrick path for any soft-brick caused by a bad custom kernel.
EOF
  log "rollback asset placeholder + operator-fetch README written to $ROLLBACK_DIR"
fi

# ----- Next step ---------------------------------------------------------------

cat <<EOF
${LOG_PREFIX} ─────────────────────────────────────────────────────
${LOG_PREFIX} Bootstrap complete.
${LOG_PREFIX}
${LOG_PREFIX} Next:
${LOG_PREFIX}   1. log out + back in (or 'newgrp kvm' / 'newgrp cvdnetwork') so
${LOG_PREFIX}      group membership takes effect
${LOG_PREFIX}   2. operator drops bluejay-stock-boot.img into $ROLLBACK_DIR/
${LOG_PREFIX}      (see README-operator-fetch.md there)
${LOG_PREFIX}   3. bash scripts/kernel-build.sh        # builds the custom kernel
${LOG_PREFIX}   4. bash scripts/boot-cuttlefish.sh     # boots cvd with custom kernel
${LOG_PREFIX}   5. bash scripts/boot-check.sh          # smoke-tests + records 1/7
${LOG_PREFIX}   6. bash scripts/seven-green-gate.sh    # runs the 7-consecutive gate
${LOG_PREFIX} ─────────────────────────────────────────────────────
EOF
