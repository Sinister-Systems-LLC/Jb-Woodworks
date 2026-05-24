# Dockerfile — Sinister OS ISO build host
# Author: RKOJ-ELENO :: 2026-05-24
#
# Purpose: a reproducible Arch Linux build environment that runs archiso
# without needing a Linux VM on the operator's Windows machine. Mount the
# iso-build/ directory and the output dir; run `mkarchiso` inside.
#
# Usage (driven by build.sh):
#   docker build -t sinister-os-builder .
#   docker run --rm --privileged \
#     -v "$PWD":/work \
#     -v "$PWD/../../build":/out \
#     sinister-os-builder \
#     mkarchiso -v -w /tmp/work -o /out /work
#
# --privileged is required because archiso uses loop devices + mount.

FROM archlinux:latest

# Refresh keyring + base tooling
RUN pacman-key --init && \
    pacman-key --populate archlinux && \
    pacman -Syu --noconfirm && \
    pacman -S --noconfirm --needed \
      archiso \
      git \
      base-devel \
      grub \
      mtools \
      dosfstools \
      libisoburn \
      squashfs-tools \
      arch-install-scripts \
      sudo \
      curl && \
    pacman -Scc --noconfirm

WORKDIR /work

# Default to dropping into bash so the operator can iterate
CMD ["bash"]
