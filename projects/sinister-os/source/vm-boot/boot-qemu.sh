#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-24
# Sinister OS :: vm-boot :: boot-qemu.sh
#
# Boot the Sinister OS ISO under QEMU on a Windows host.
#
# Windows-host quirks (read before running):
#   - KVM is Linux-only. On Windows you need an alternate accelerator:
#       * whpx  : Windows Hypervisor Platform (built-in Win10/11 Pro & Home,
#                 enable via "Turn Windows features on or off" -> WHPX).
#                 Conflicts with VirtualBox <6.1 if both want the hypervisor;
#                 fine on modern VirtualBox 7.x.
#       * haxm  : Intel HAXM (legacy, only Intel CPUs, deprecated).
#       * tcg   : pure software emulation. WORKS but ~10x slower; OK for smoke
#                 tests only.
#   - This script auto-prefers whpx, falls back to tcg.
#   - QEMU on Windows runs from C:\Program Files\qemu\ by default and is
#     usually NOT in PATH. We probe both.
#   - Use SDL or GTK display; this script uses the default (gtk on Windows
#     builds, falls back to sdl). For headless use, pass --headless.
#
# Usage:
#   bash source/vm-boot/boot-qemu.sh
#   bash source/vm-boot/boot-qemu.sh --iso /d/path/to/sinister.iso
#   bash source/vm-boot/boot-qemu.sh --dry-run
#   bash source/vm-boot/boot-qemu.sh --headless --novnc-port 5901
#
# Defaults:
#   - RAM       : 4096 MB
#   - vCPUs     : 4
#   - Disk      : 60 GB qcow2 (created on first run at out/sinister-os-test.qcow2)
#   - Firmware  : UEFI (OVMF) — auto-detected; falls back to BIOS if not found
#   - Network   : user-mode (NAT)
#   - Display   : default (gtk/sdl); --headless for VNC

set -eu

VM_RAM_MB=4096
VM_CPUS=4
VM_DISK_GB=60
ISO_OVERRIDE=''
DRY_RUN=0
HEADLESS=0
VNC_PORT=5901
RECREATE=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --iso)         ISO_OVERRIDE="$2"; shift 2 ;;
        --ram)         VM_RAM_MB="$2"; shift 2 ;;
        --cpus)        VM_CPUS="$2"; shift 2 ;;
        --disk)        VM_DISK_GB="$2"; shift 2 ;;
        --dry-run)     DRY_RUN=1; shift ;;
        --headless)    HEADLESS=1; shift ;;
        --novnc-port)  VNC_PORT="$2"; shift 2 ;;
        --recreate)    RECREATE=1; shift ;;
        -h|--help)
            sed -n '2,30p' "$0"
            exit 0 ;;
        *)             echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ISO_DIR="${SCRIPT_DIR}/../iso-build/out"
STATE_DIR="${SCRIPT_DIR}/state"
DISK_QCOW="${STATE_DIR}/sinister-os-test.qcow2"

mkdir -p "$STATE_DIR"

# --- Locate qemu-system-x86_64 ---
if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    QEMU="$(command -v qemu-system-x86_64)"
elif [ -x "/c/Program Files/qemu/qemu-system-x86_64.exe" ]; then
    QEMU="/c/Program Files/qemu/qemu-system-x86_64.exe"
else
    echo "ERROR: qemu-system-x86_64 not found. Install QEMU:" >&2
    echo "  winget install -e --id qemu.qemu" >&2
    echo "  or download: https://qemu.weilnetz.de/w64/" >&2
    exit 1
fi
echo "  using QEMU at: $QEMU"

# --- Locate qemu-img (sibling of qemu-system) ---
QEMU_IMG="$(dirname "$QEMU")/qemu-img"
if [ ! -x "$QEMU_IMG" ] && [ ! -x "${QEMU_IMG}.exe" ]; then
    QEMU_IMG="$(command -v qemu-img || true)"
fi
[ -z "$QEMU_IMG" ] && { echo "qemu-img not found alongside QEMU"; exit 1; }

# --- Pick accelerator ---
ACCEL='tcg'
if "$QEMU" -accel help 2>/dev/null | grep -qi 'whpx'; then
    ACCEL='whpx'
elif "$QEMU" -accel help 2>/dev/null | grep -qi 'haxm'; then
    ACCEL='hax'
fi
echo "  accelerator: $ACCEL"
if [ "$ACCEL" = 'tcg' ]; then
    echo "  WARNING: falling back to TCG (software emulation). Enable Windows Hypervisor Platform for whpx." >&2
fi

# --- Resolve ISO ---
ISO=''
if [ -n "$ISO_OVERRIDE" ]; then
    [ -f "$ISO_OVERRIDE" ] || { echo "ISO not found at --iso: $ISO_OVERRIDE"; exit 1; }
    ISO="$ISO_OVERRIDE"
elif [ -d "$ISO_DIR" ]; then
    ISO="$(ls -t "$ISO_DIR"/sinister-*.iso 2>/dev/null | head -n1 || true)"
fi
if [ -z "$ISO" ]; then
    echo "  ISO: (none found — parallel iso-build lane has not produced one yet)"
    echo "  Will create disk + show planned cmdline, then exit."
fi

# --- Locate OVMF (UEFI firmware) ---
OVMF=''
for cand in \
    "$(dirname "$QEMU")/share/edk2-x86_64-code.fd" \
    "$(dirname "$QEMU")/share/OVMF.fd" \
    "/c/Program Files/qemu/share/edk2-x86_64-code.fd" \
    "/c/Program Files/qemu/share/OVMF.fd"
do
    [ -f "$cand" ] && { OVMF="$cand"; break; }
done

# --- Create disk if missing ---
if [ "$RECREATE" -eq 1 ] && [ -f "$DISK_QCOW" ]; then
    echo "  --recreate: removing existing disk"
    [ "$DRY_RUN" -eq 0 ] && rm -f "$DISK_QCOW"
fi
if [ ! -f "$DISK_QCOW" ]; then
    echo "  creating disk: $DISK_QCOW (${VM_DISK_GB}G sparse qcow2)"
    if [ "$DRY_RUN" -eq 0 ]; then
        "$QEMU_IMG" create -f qcow2 "$DISK_QCOW" "${VM_DISK_GB}G"
    else
        echo "  DRYRUN: $QEMU_IMG create -f qcow2 $DISK_QCOW ${VM_DISK_GB}G"
    fi
else
    echo "  reusing disk: $DISK_QCOW"
fi

# --- Build qemu cmdline ---
ARGS=(
    -name 'Sinister-OS-Test'
    -machine "type=q35,accel=${ACCEL}"
    -cpu max
    -smp "$VM_CPUS"
    -m "$VM_RAM_MB"
    -drive "file=${DISK_QCOW},format=qcow2,if=virtio"
    -netdev 'user,id=net0'
    -device 'virtio-net-pci,netdev=net0'
    -device 'virtio-balloon'
    -device 'qemu-xhci'
    -device 'usb-tablet'
    -rtc 'base=utc'
)

if [ -n "$OVMF" ]; then
    ARGS+=( -drive "if=pflash,format=raw,readonly=on,file=${OVMF}" )
    echo "  UEFI firmware: $OVMF"
else
    echo "  UEFI firmware not found — booting legacy BIOS."
fi

if [ -n "$ISO" ]; then
    ARGS+=( -cdrom "$ISO" -boot 'order=dc,menu=on' )
fi

if [ "$HEADLESS" -eq 1 ]; then
    ARGS+=( -display "vnc=:$((VNC_PORT-5900))" -vga virtio )
    echo "  headless: VNC on port ${VNC_PORT}"
else
    ARGS+=( -vga virtio )
fi

echo ""
echo "  full cmdline:"
printf '    %q ' "$QEMU" "${ARGS[@]}"; echo

if [ "$DRY_RUN" -eq 1 ]; then
    echo "  DRYRUN: not booting."
    exit 0
fi

if [ -z "$ISO" ]; then
    echo "  no ISO present — exiting without boot."
    exit 0
fi

echo ""
echo "  booting..."
exec "$QEMU" "${ARGS[@]}"
