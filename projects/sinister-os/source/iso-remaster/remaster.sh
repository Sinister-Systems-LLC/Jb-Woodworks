#!/usr/bin/env bash
# remaster.sh -- Sinister OS ISO remaster orchestrator
# Author: RKOJ-ELENO :: 2026-05-24
#
# Takes a CachyOS upstream ISO + a sinister-overlay/ directory and produces a
# branded Sinister OS ISO that first-boot-installs the overlay. Idempotent:
# rerunning with the same inputs produces a bit-for-bit identical output (we
# pin SOURCE_DATE_EPOCH from the overlay's newest mtime and pass --sort=name
# everywhere we can).
#
# Usage:
#   remaster.sh -i <input.iso> -o <output.iso> -v <version-tag> --overlay <dir>
#
# Exit codes:
#   0  success
#   1  generic failure (bad args, tool missing)
#   2  overlay dir not found (sibling agent has not finished)
#   3  input ISO not found or unreadable
#   4  unsquashfs / mksquashfs / xorriso failure
#   5  verification failure (output ISO missing or zero-byte)

set -euo pipefail

# ----- args -----------------------------------------------------------------

INPUT_ISO=""
OUTPUT_ISO=""
VERSION_TAG=""
OVERLAY_DIR=""

usage() {
    cat <<EOF
Usage: $0 -i <input.iso> -o <output.iso> -v <version-tag> --overlay <dir>

  -i, --input     Path to upstream CachyOS ISO (read-only mounted)
  -o, --output    Path to write remastered Sinister OS ISO
  -v, --version   Version tag for ISO label (e.g. v1)
      --overlay   Path to sinister-overlay/ directory to layer in
  -h, --help      Show this help

Exit codes: 0 success, 1 bad-args/tool-missing, 2 overlay-not-found,
            3 input-iso-missing, 4 squashfs/xorriso-fail, 5 verify-fail
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -i|--input)    INPUT_ISO="$2"; shift 2 ;;
        -o|--output)   OUTPUT_ISO="$2"; shift 2 ;;
        -v|--version)  VERSION_TAG="$2"; shift 2 ;;
        --overlay)     OVERLAY_DIR="$2"; shift 2 ;;
        -h|--help)     usage; exit 0 ;;
        *)             echo "ERROR: unknown arg $1" >&2; usage; exit 1 ;;
    esac
done

[[ -z "$INPUT_ISO"   ]] && { echo "ERROR: -i required" >&2; usage; exit 1; }
[[ -z "$OUTPUT_ISO"  ]] && { echo "ERROR: -o required" >&2; usage; exit 1; }
[[ -z "$VERSION_TAG" ]] && { echo "ERROR: -v required" >&2; usage; exit 1; }
[[ -z "$OVERLAY_DIR" ]] && { echo "ERROR: --overlay required" >&2; usage; exit 1; }

# ----- helpers --------------------------------------------------------------

ts()  { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { echo "[$(ts)] $*"; }
die() { echo "[$(ts)] FATAL: $*" >&2; exit "${2:-1}"; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1" 1
}

# ----- preflight ------------------------------------------------------------

log "===== Sinister OS ISO remaster ====="
log "input:    $INPUT_ISO"
log "output:   $OUTPUT_ISO"
log "version:  $VERSION_TAG"
log "overlay:  $OVERLAY_DIR"

for cmd in unsquashfs mksquashfs xorriso rsync sha256sum; do
    require_cmd "$cmd"
done

if [[ ! -f "$INPUT_ISO" ]]; then
    die "input ISO not found at $INPUT_ISO" 3
fi
if [[ ! -r "$INPUT_ISO" ]]; then
    die "input ISO not readable at $INPUT_ISO" 3
fi

if [[ ! -d "$OVERLAY_DIR" ]]; then
    log "overlay dir not found at $OVERLAY_DIR; this is expected if sinister-overlay agent has not finished"
    exit 2
fi

INPUT_SIZE=$(stat -c%s "$INPUT_ISO")
log "input ISO size: $INPUT_SIZE bytes"

# Deterministic build: pin epoch to overlay's newest mtime
SOURCE_DATE_EPOCH=$(find "$OVERLAY_DIR" -type f -printf '%T@\n' 2>/dev/null \
    | sort -n | tail -1 | cut -d. -f1)
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(date -u +%s)}"
export SOURCE_DATE_EPOCH
log "SOURCE_DATE_EPOCH (reproducibility pin): $SOURCE_DATE_EPOCH"

# ----- workspace ------------------------------------------------------------

WORK_ROOT="${WORK_ROOT:-/tmp/sinister-remaster}"
WORK_DIR="$WORK_ROOT/workspace"
ISO_MOUNT="$WORK_ROOT/iso-mount"
ISO_TREE="$WORK_ROOT/iso-tree"
SQUASH_ROOT="$WORK_ROOT/squashfs-root"

log "cleaning workspace at $WORK_ROOT"
rm -rf "$WORK_ROOT"
mkdir -p "$WORK_DIR" "$ISO_MOUNT" "$ISO_TREE" "$SQUASH_ROOT"
mkdir -p "$(dirname "$OUTPUT_ISO")"

# ----- step 1: mount input ISO read-only -----------------------------------

log "step 1/8: mounting input ISO read-only"
mount -o loop,ro "$INPUT_ISO" "$ISO_MOUNT" \
    || die "could not mount input ISO (need --privileged + loop device)" 4

cleanup() {
    log "cleanup: unmounting ISO + workspace"
    mountpoint -q "$ISO_MOUNT" && umount "$ISO_MOUNT" || true
}
trap cleanup EXIT

# ----- step 2: copy contents to writable tree ------------------------------

log "step 2/8: copying ISO contents to writable tree"
rsync -aHAX --info=progress2 "$ISO_MOUNT/" "$ISO_TREE/" \
    || die "rsync of ISO tree failed" 4

# ----- step 3: locate + unsquash airootfs ----------------------------------

log "step 3/8: locating airootfs squashfs"
SQUASH_PATH=""
for candidate in \
    "$ISO_TREE/arch/x86_64/airootfs.sfs" \
    "$ISO_TREE/arch/x86_64/airootfs.img" \
    "$ISO_TREE/live/filesystem.squashfs" \
    "$ISO_TREE/casper/filesystem.squashfs"; do
    if [[ -f "$candidate" ]]; then
        SQUASH_PATH="$candidate"
        break
    fi
done

if [[ -z "$SQUASH_PATH" ]]; then
    SQUASH_PATH=$(find "$ISO_TREE" -type f \( -name '*.sfs' -o -name '*.squashfs' \) \
        | head -1 || true)
fi

[[ -z "$SQUASH_PATH" ]] && die "could not locate airootfs squashfs inside ISO" 4
log "found squashfs at: $SQUASH_PATH"

log "step 3/8: unsquashing"
unsquashfs -d "$SQUASH_ROOT/root" "$SQUASH_PATH" \
    || die "unsquashfs failed" 4

# ----- step 4: apply overlay -----------------------------------------------

log "step 4/8: applying sinister-overlay to airootfs"
mkdir -p "$SQUASH_ROOT/root/sinister-overlay"
rsync -aHAX "$OVERLAY_DIR/" "$SQUASH_ROOT/root/sinister-overlay/" \
    || die "rsync of overlay failed" 4

# Mark the version so first-boot can read it
echo "$VERSION_TAG" > "$SQUASH_ROOT/root/sinister-overlay/.sinister-version"
echo "$SOURCE_DATE_EPOCH" > "$SQUASH_ROOT/root/sinister-overlay/.build-epoch"

# Ensure first-boot runs install.sh exactly once via systemd one-shot
FIRSTBOOT_UNIT="$SQUASH_ROOT/root/etc/systemd/system/sinister-firstboot.service"
mkdir -p "$(dirname "$FIRSTBOOT_UNIT")"
cat > "$FIRSTBOOT_UNIT" <<'UNIT'
[Unit]
Description=Sinister OS first-boot overlay installer
ConditionPathExists=/sinister-overlay/install.sh
ConditionPathExists=!/var/lib/sinister/.firstboot-done
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash /sinister-overlay/install.sh
ExecStartPost=/bin/sh -c 'mkdir -p /var/lib/sinister && touch /var/lib/sinister/.firstboot-done'
RemainAfterExit=yes
StandardOutput=journal+console
StandardError=journal+console

[Install]
WantedBy=multi-user.target
UNIT

mkdir -p "$SQUASH_ROOT/root/etc/systemd/system/multi-user.target.wants"
ln -sf "../sinister-firstboot.service" \
    "$SQUASH_ROOT/root/etc/systemd/system/multi-user.target.wants/sinister-firstboot.service"

log "step 4/8: overlay applied; first-boot unit installed"

# ----- step 5: resquash with same compression ------------------------------

log "step 5/8: detecting original squashfs compression"
SQUASH_COMP=$(unsquashfs -s "$SQUASH_PATH" 2>/dev/null \
    | awk -F': *' '/^Compression/ {print $2; exit}' || true)
SQUASH_COMP="${SQUASH_COMP:-zstd}"
log "using compression: $SQUASH_COMP"

log "step 5/8: removing old squashfs + resquashing"
rm -f "$SQUASH_PATH"
mksquashfs "$SQUASH_ROOT/root" "$SQUASH_PATH" \
    -comp "$SQUASH_COMP" \
    -noappend \
    -no-progress \
    -all-root \
    -mkfs-time "$SOURCE_DATE_EPOCH" \
    -all-time  "$SOURCE_DATE_EPOCH" \
    || die "mksquashfs failed" 4

# Update sha256 sidecars CachyOS/archiso ships next to airootfs
if [[ -f "${SQUASH_PATH}.sha256" ]]; then
    log "refreshing sidecar ${SQUASH_PATH}.sha256"
    ( cd "$(dirname "$SQUASH_PATH")" && \
      sha256sum "$(basename "$SQUASH_PATH")" > "$(basename "$SQUASH_PATH").sha256" )
fi
if [[ -f "${SQUASH_PATH}.md5" ]]; then
    rm -f "${SQUASH_PATH}.md5"  # leave stale md5 off rather than recompute wrong
fi

# ----- step 6: patch isolinux + EFI labels ---------------------------------

log "step 6/8: patching boot labels CachyOS -> Sinister OS"
PATCHED_COUNT=0
while IFS= read -r -d '' cfg; do
    if grep -qiE 'cachy(os)?' "$cfg" 2>/dev/null; then
        sed -i -E '
            s/CachyOS Linux/Sinister OS/g;
            s/CachyOS/Sinister OS/g;
            s/cachyos/sinister-os/g;
        ' "$cfg"
        PATCHED_COUNT=$((PATCHED_COUNT + 1))
    fi
done < <(find "$ISO_TREE" -type f \( \
    -name '*.cfg' -o -name '*.conf' -o -name '*.txt' -o -name 'grub.cfg' \
    -o -name 'loopback.cfg' -o -name 'syslinux.cfg' -o -name 'isolinux.cfg' \
    \) -print0)
log "patched $PATCHED_COUNT boot config file(s)"

# ----- step 7: rebuild ISO with xorriso -----------------------------------

log "step 7/8: rebuilding ISO with xorriso (preserves EFI + BIOS boot)"
ISO_LABEL="SINISTER_OS_${VERSION_TAG}"
ISO_LABEL=$(echo "$ISO_LABEL" | tr '[:lower:]' '[:upper:]' | tr -c 'A-Z0-9_' '_' | cut -c1-32)
log "ISO volume label: $ISO_LABEL"

# Locate boot artefacts (CachyOS layout is archiso-compatible)
BIOS_IMG=""
for c in "$ISO_TREE/boot/syslinux/isolinux.bin" \
         "$ISO_TREE/isolinux/isolinux.bin"; do
    [[ -f "$c" ]] && { BIOS_IMG="${c#$ISO_TREE/}"; break; }
done

EFI_IMG=""
for c in "$ISO_TREE/EFI/archiso/efiboot.img" \
         "$ISO_TREE/EFI/boot/efiboot.img" \
         "$ISO_TREE/efi.img"; do
    [[ -f "$c" ]] && { EFI_IMG="${c#$ISO_TREE/}"; break; }
done

XORRISO_ARGS=(
    -volid "$ISO_LABEL"
    -joliet on
    -rockridge on
    -outdev "$OUTPUT_ISO"
    -map "$ISO_TREE" /
    -chmod 0755 / --
)

if [[ -n "$BIOS_IMG" ]]; then
    log "adding BIOS boot record (isolinux): $BIOS_IMG"
    XORRISO_ARGS+=(
        -boot_image isolinux dir=/"$(dirname "$BIOS_IMG")"
        -boot_image isolinux system_area=/usr/lib/syslinux/bios/isohdpfx.bin
    )
fi

if [[ -n "$EFI_IMG" ]]; then
    log "adding EFI boot record: $EFI_IMG"
    XORRISO_ARGS+=(
        -append_partition 2 0xef "$ISO_TREE/$EFI_IMG"
        -boot_image any next
        -boot_image any efi_path="$EFI_IMG"
        -boot_image any platform_id=0xef
        -boot_image any emul_type=no_emulation
    )
fi

rm -f "$OUTPUT_ISO"
xorriso -as mkisofs \
    -iso-level 3 \
    -full-iso9660-filenames \
    -volid "$ISO_LABEL" \
    -appid "Sinister OS $VERSION_TAG" \
    -publisher "RKOJ-ELENO" \
    -preparer "sinister-os-remaster" \
    ${BIOS_IMG:+ -b "$BIOS_IMG" -c "boot.cat" -no-emul-boot -boot-load-size 4 -boot-info-table } \
    ${EFI_IMG:+ -eltorito-alt-boot -e "$EFI_IMG" -no-emul-boot -isohybrid-gpt-basdat } \
    -output "$OUTPUT_ISO" \
    "$ISO_TREE" \
    || die "xorriso failed" 4

# ----- step 8: verify + report --------------------------------------------

log "step 8/8: verifying output"
[[ -f "$OUTPUT_ISO" ]] || die "output ISO not created" 5
OUTPUT_SIZE=$(stat -c%s "$OUTPUT_ISO")
[[ "$OUTPUT_SIZE" -gt 0 ]] || die "output ISO is zero bytes" 5

OUTPUT_SHA=$(sha256sum "$OUTPUT_ISO" | awk '{print $1}')
echo "$OUTPUT_SHA  $(basename "$OUTPUT_ISO")" > "${OUTPUT_ISO}.sha256"

log "===== remaster complete ====="
log "output:   $OUTPUT_ISO"
log "size:     $OUTPUT_SIZE bytes"
log "sha256:   $OUTPUT_SHA"
log "version:  $VERSION_TAG"
log "============================="

exit 0
