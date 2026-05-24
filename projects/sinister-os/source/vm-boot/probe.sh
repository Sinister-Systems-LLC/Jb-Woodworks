#!/usr/bin/env bash
# Author: RKOJ-ELENO :: 2026-05-24
# Sinister OS :: vm-boot :: probe.sh
#
# Read-only inspection of which VM engines are installed on this Windows host.
# Safe to run any time. Prints a one-line verdict per engine, then a summary
# recommendation. Exits 0 if at least one engine is usable; 1 if none.
#
# Usage:
#   bash source/vm-boot/probe.sh
#
# Detection notes:
#   - VirtualBox: registry key HKLM\SOFTWARE\Oracle\VirtualBox or
#       C:\Program Files\Oracle\VirtualBox\VBoxManage.exe
#   - QEMU: qemu-system-x86_64 in PATH or C:\Program Files\qemu\
#   - Hyper-V: requires elevated PowerShell to query; we surface the cmdline.
#   - VMware: vmrun.exe in PATH or default install dirs.

set -u

PASS=0
FAIL=0

say() { printf '%s\n' "$*"; }
hr()  { printf -- '-%.0s' {1..60}; printf '\n'; }

VBOX_DEFAULT='/c/Program Files/Oracle/VirtualBox/VBoxManage.exe'
QEMU_DEFAULT='/c/Program Files/qemu/qemu-system-x86_64.exe'
VMRUN_DEFAULT='/c/Program Files (x86)/VMware/VMware Workstation/vmrun.exe'

say "Sinister OS :: VM engine probe :: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
hr

# --- VirtualBox ---
if command -v VBoxManage >/dev/null 2>&1; then
    VBOX_VER="$(VBoxManage --version 2>/dev/null || echo unknown)"
    say "VirtualBox  : INSTALLED (PATH)        version=${VBOX_VER}"
    PASS=$((PASS+1))
elif [ -x "$VBOX_DEFAULT" ]; then
    VBOX_VER="$("$VBOX_DEFAULT" --version 2>/dev/null || echo unknown)"
    say "VirtualBox  : INSTALLED (default dir) version=${VBOX_VER}"
    say "              path=${VBOX_DEFAULT}"
    say "              tip: add 'C:\\Program Files\\Oracle\\VirtualBox' to PATH for convenience"
    PASS=$((PASS+1))
else
    say "VirtualBox  : NOT FOUND"
    say "              install: see source/vm-boot/install-helpers/install-virtualbox.ps1"
    FAIL=$((FAIL+1))
fi

# --- QEMU ---
if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    QEMU_VER="$(qemu-system-x86_64 --version 2>/dev/null | head -n1 || echo unknown)"
    say "QEMU        : INSTALLED (PATH)        ${QEMU_VER}"
    PASS=$((PASS+1))
elif [ -x "$QEMU_DEFAULT" ]; then
    QEMU_VER="$("$QEMU_DEFAULT" --version 2>/dev/null | head -n1 || echo unknown)"
    say "QEMU        : INSTALLED (default dir) ${QEMU_VER}"
    say "              path=${QEMU_DEFAULT}"
    PASS=$((PASS+1))
else
    say "QEMU        : NOT FOUND"
    say "              install: winget install -e --id qemu.qemu  (or https://qemu.weilnetz.de/w64/)"
    FAIL=$((FAIL+1))
fi

# --- Hyper-V (requires elevation to query state) ---
say "Hyper-V     : check requires elevated PowerShell. Run from admin shell:"
say "              Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V"

# --- VMware Workstation ---
if command -v vmrun >/dev/null 2>&1; then
    VMRUN_VER="$(vmrun 2>&1 | head -n1 || echo unknown)"
    say "VMware      : INSTALLED (PATH)        ${VMRUN_VER}"
    PASS=$((PASS+1))
elif [ -x "$VMRUN_DEFAULT" ]; then
    say "VMware      : INSTALLED (default dir)"
    say "              path=${VMRUN_DEFAULT}"
    PASS=$((PASS+1))
else
    say "VMware      : NOT FOUND  (commercial; optional)"
fi

hr
say "Summary: usable engines detected = ${PASS}"

if [ "$PASS" -ge 1 ]; then
    say "Recommendation: use boot-virtualbox.ps1 (VirtualBox is simplest for daily testing)."
    say "                Fallback: boot-qemu.sh if QEMU is preferred."
    exit 0
else
    say "Recommendation: install VirtualBox first."
    say "                Run: powershell -File source/vm-boot/install-helpers/install-virtualbox.ps1"
    exit 1
fi
