# Dockerfile -- Sinister OS ISO remaster host
# Author: RKOJ-ELENO :: 2026-05-24
#
# Purpose: a reproducible Arch Linux container that takes a CachyOS upstream
# ISO + a sinister-overlay/ directory and produces a branded Sinister OS ISO.
# Sibling to source/iso-build/Dockerfile (the from-scratch path). This is the
# REMASTER path -- faster, riding CachyOS's curated package set + Hyprland config.
#
# Usage (driven by remaster.sh + Makefile):
#   docker build -t sinister-iso-remaster .
#   docker run --rm --privileged \
#     -v "$PWD/..":/sinister-os \
#     -v "$PWD/out":/out \
#     sinister-iso-remaster \
#     /sinister-os/iso-remaster/remaster.sh \
#       -i /sinister-os/iso-base/cachyos-hyprland.iso \
#       -o /out/sinister-os-$(date -u +%Y%m%dT%H%M%SZ).iso \
#       -v v1 \
#       --overlay /sinister-os/sinister-overlay
#
# --privileged is required for unsquashfs loop-device handling.

FROM archlinux:latest

# Refresh keyring + remaster tooling. Kept minimal vs iso-build/ since we are
# not running mkarchiso here -- just unsquash / squash / xorriso.
RUN pacman-key --init && \
    pacman-key --populate archlinux && \
    pacman -Syu --noconfirm && \
    pacman -S --noconfirm --needed \
      archiso \
      squashfs-tools \
      libisoburn \
      mtools \
      dosfstools \
      rsync \
      coreutils \
      grep \
      sed \
      gawk \
      bash \
      file \
      which && \
    pacman -Scc --noconfirm

WORKDIR /work

# Default to bash so operator can drop in and inspect mid-remaster
CMD ["bash"]
