#!/usr/bin/env bash
# profiledef.sh — Sinister OS archiso profile
# Author: RKOJ-ELENO :: 2026-05-24
#
# Loaded by mkarchiso. Defines the ISO metadata + boot mode list + file
# permission overrides for the airootfs overlay.

# shellcheck disable=SC2034

iso_name="sinister-os"
iso_label="SINISTER_OS_$(date --utc +%Y%m)"
iso_publisher="Sinister Sanctum <https://github.com/z0nian>"
iso_application="Sinister OS Live/Install Medium"
iso_version="0.1.0-alpha-$(date --utc +%Y%m%d)"
install_dir="sinister"
buildmodes=('iso')
bootmodes=(
    'bios.syslinux.mbr'
    'bios.syslinux.eltorito'
    'uefi-ia32.grub.esp'
    'uefi-x64.grub.esp'
    'uefi-ia32.grub.eltorito'
    'uefi-x64.grub.eltorito'
)
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
bootstrap_tarball_compression=(zstd -c -T0 --auto-threads=logical --long -19)

file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:755"
  ["/usr/local/bin/sinister-first-boot.sh"]="0:0:755"
  ["/usr/local/bin/sinister-first-boot-install-yay.sh"]="0:0:755"
  ["/usr/local/bin/sinister-first-boot-install-deferred.sh"]="0:0:755"
  ["/usr/local/bin/sinister-panel-kiosk.sh"]="0:0:755"
  ["/etc/sudoers.d/sinister"]="0:0:440"
  ["/etc/sinister/first-boot-deferred.list"]="0:0:644"
)
