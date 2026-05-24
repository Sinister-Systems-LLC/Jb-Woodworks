# source/branding/

> **Author:** RKOJ-ELENO :: 2026-05-24
> **Phase:** P1/P2 (populates in lockstep with ISO build).

Sinister OS visual brand artifacts. Generated via `sinister-generator` brand-lock helpers + hand-tuning.

Layout when populated:

```
branding/
├── plymouth/                    (boot splash)
│   ├── sinister/                (theme dir)
│   └── README.md
├── grub-theme/                  (BIOS bootloader)
├── systemd-boot/                (UEFI bootloader logo)
├── sddm-theme/                  (login screen, QML)
├── wallpapers/                  (per-resolution generations)
│   ├── 3840x2160.png
│   ├── 2560x1440.png
│   └── 1920x1080.png
├── cursor-theme/                (Bibata fork, purple accent)
├── icon-theme/                  (Papirus fork)
├── sound-theme/                 (chime set replacing system bells)
└── README.md                    (this file)
```

Brand palette (locked in master plan § 5.2):
- Primary: `#7C3AED` (Sinister purple)
- Background: `#0A0A0F` (near-black void)
- Accent: `#A78BFA` (lighter purple for hovers)
- Text: `#F4F4F5` (off-white)
- Error: `#EF4444`
- Success: `#10B981`
