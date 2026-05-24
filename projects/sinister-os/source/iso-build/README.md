# source/iso-build/

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P1 (gated — operator must say "P1 go" before EVE populates this folder).

This folder will hold the archiso profile for building bootable Sinister OS ISOs. Layout when populated (per master plan § 12.1):

```
iso-build/
├── profiledef.sh         (archiso profile)
├── packages.x86_64       (package list)
├── airootfs/             (overlay onto live root)
│   ├── etc/
│   ├── usr/
│   └── root/
├── pacman.conf           (custom repo includes for sinister AUR mirror)
├── syslinux/             (BIOS bootloader cfg)
├── efiboot/              (UEFI bootloader cfg)
├── grub/                 (theme)
└── README.md             (this file)
```

P1 acceptance criteria live in `plans/master-plan-2026-05-24.md § 12.1`.
