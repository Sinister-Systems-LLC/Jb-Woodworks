# Author: RKOJ-ELENO :: 2026-05-21

# Sinister Panel — 1:1 UI spec for RKOJ.exe PyQt6 port
# Created at 2026-05-21T23:03Z

Pixel-precise translation reference. Source-of-truth = `projects/sinister-panel/source/Andrew Panel/`.

## 1. Color tokens (Panel iOS-themed dark palette)

| Token | Hex | Usage |
|---|---|---|
| Brand-primary | `#BF5AF2` | Sidebar active text, page-title color, primary glow |
| Brand-accent | `#A06EFF` | KPI tile borders, chip-active fill, button fill |
| Brand-deep | `#7A3DD4` | Sidebar active background |
| Brand-halo | `#C39DFF` | Hover wash, soft accents |
| Page bg | `#0a0a0c` | Top-level surface |
| Panel bg | `#0E0A14` | Body container |
| Card bg | `#15131A` | KPI tiles, agent cards, chip background |
| Card-2 bg | `#1C1626` | Inner-card nested surface, terminal |
| Border | `#2c2c2e` | Hairline divider |
| Border-2 | `#3A2A55` | Glass border (chip outlines) |
| Glow | `#2A1F3D` | Scrollbar handle, soft glow |
| Text-primary | `#E8D6FF` | Default text |
| Text-soft | `#8e8e93` | Muted text |
| Text-dim | `#6E6E84` | Disabled |
| Success | `#30D158` | Status dot online |
| Danger | `#FF453A` | Close hover, error |
| Warning | `#FF9F0A` | Status dot busy |
| Info | `#0A84FF` | Info status |

## 2. Sidebar (240px wide, full-height)

- Width: **240px** (Panel default; we use 220 in current code → bump to 240)
- Bg: `#0a0a0c` (matches page bg, with right-edge 1px `#2c2c2e` divider)
- Mascot block: 96px tall, mascot SVG 64x64 centered, no subtitle
- Nav-item: 36px tall, `padding: 8px 12px`, gap-3 (`12px`) between icon + label, 13px font, 500 weight, 10px border-radius
- Active state: bg `#7A3DD4`, color `white`, font-weight 600, border 1px `#A06EFF`
- Hover state: bg `rgba(255,255,255,0.05)`, color `white`
- Section header (when sections present): 11px uppercase, 700 weight, color `#8e8e93`, letter-spacing 1.5px, padding `12px 16px 6px 16px`

## 3. Header — Row 1 (Sheets-style menu strip, 32px tall)

- Bg: `#0a0a0c`, bottom border 1px `#2c2c2e`
- Brand mascot label: `EVE`, 11px / 800 weight / letter-spacing 2px / color `#BF5AF2`, padding-left 14px
- Menu item: text-only, 11px / 500 weight / color `#8e8e93`, padding `4px 10px`, hover bg `#1C1626` + color white + radius 4px
- Window controls right-side: 32x24 round buttons, SVG glyph 14px, close-hover `#FF453A` bg

## 4. Header — Row 2 (Page bar, 64px tall)

- Bg: `#0a0a0c`, bottom border 1px `#2c2c2e`
- Content margins: `28px left, 12px top/bottom, 16px right`, gap 12px
- **Page title** ("Agents" / "Devices"): font-size **26px** (Panel `text-[26px]`), font-weight 700 (bold), letter-spacing -0.5px, color `#BF5AF2`
- Chip tabs (Agents/Devices):
  - Pill shape: border-radius **16px** (Panel `rounded-full`)
  - Height: **32px** (Panel `h-8`), min 26px-30px
  - Padding: `4px 14px` (Panel `px-4`)
  - Font: 13px / 600 weight
  - Inactive: bg `#15131A`, color `#8e8e93`, border 1px `#2c2c2e`
  - Hover: color white, border 1px `#7A3DD4`
  - Active: bg `#7A3DD4`, color white, border 1px `#A06EFF`
  - Icon size: 14px SVG glyph, gap 7px to label
- Round action icons (alerts/inbox/search/settings):
  - 32x32 round, border-radius 16px
  - Default: transparent bg + transparent border, color `#8e8e93`
  - Hover: bg `#15131A`, color white, border 1px `#2c2c2e`
  - Icon size: 15px
- Primary "+ Create Agent" button:
  - Bg `#A06EFF`, color white, border 1px `#A06EFF`, radius 6px
  - Padding `6px 12px`, font 13px / 600 weight
  - Hover: bg `#C39DFF`, color `#0E0A14`
  - Plus-icon 12px to left of label, gap 6px
- Health pill: `5/5 healthy ●` style — green dot SVG + color text, bg `#15131A`, border `#2c2c2e`, radius 12px, padding `4px 10px`, font 11px / 600
- Clock: mono font 12px, color `#8e8e93`, padding 0 8px

## 5. Folder tab row (above body, 40px tall)

- Pills: `h-5 px-3` style
- Height ~20px, padding `3px 12px`, font-size 11px / 600 weight, border-radius 12px
- Inactive: bg `#15131A`, color `#8e8e93`, border 1px `#3A2A55`
- Hover: color white, border 1px `#7A3DD4`
- Active: bg `#A06EFF`, color white, border 1px `#A06EFF`

## 6. Niri-scroll body — Agent grid

- Container: 20px horizontal padding, 8px top, 12px bottom, gap 12px between cards
- Cards: full width (minus margins), min-height 280px (current `220` doctrine ceiling), max-height auto
- Group divider: 1px `#7A3DD4` thin rule between project-groups
- Scrollbar: 10px wide vertical, handle bg `#2A1F3D`, radius 5px, hover bg `#7A3DD4`

## 7. Agent card

- Bg `#15131A`, border 1px `#2c2c2e`, radius 12px, padding `12px 8px`
- Card header strip (40px):
  - Status dot 12x12 round (color per state)
  - Project label: 10px / 700 weight uppercase, color `#C39DFF`, letter-spacing 1.2px
  - Agent title: 13px / 700 weight, color white
  - Mode pill: 10px / 600 weight, color `#C39DFF`, bg `#1C1626`, border `#3A2A55`, radius 10px, padding `2px 9px`
  - Close button (right): 22x22 round, hover bg `#FF453A`, color white
- Awaiting-input glow: border 1px `#A06EFF` + `QGraphicsDropShadowEffect` 20px blur 50% alpha purple, NO offset
- Terminal: bg `#0E0A14`, color `#E8D6FF`, border `#2c2c2e`, radius 6px, font Cascadia Mono 12px, padding 6px, selection bg `#7A3DD4`
- Input: bg `#1C1626`, color white, border `#2c2c2e`, radius 6px, padding `6px 10px`, font mono 12px, focus border `#A06EFF`
- Send button: bg `#A06EFF`, color white, radius 6px, padding `6px 14px`, 600 weight, hover bg `#C39DFF` color `#0E0A14`

## 8. Typography stack

- UI: `Segoe UI, Inter, -apple-system, BlinkMacSystemFont, "SF Pro Display", system-ui, sans-serif`
- Mono: `Cascadia Mono, "Cascadia Code", "JetBrains Mono", "Fira Code", "SF Mono", ui-monospace, Consolas, monospace`
- Default size: 13px
- Tabular-nums on numeric KPI/count surfaces

## 9. Spacing scale (Panel — Tailwind-aligned)

| Token | px | Usage |
|---|---|---|
| xs | 4 | Mid-pill padding, label gaps |
| sm | 8 | Default gap, padding-y |
| md | 12 | Section margins, gap-3 |
| lg | 16 | Outer margin, container padding |
| xl | 24 | Section break gap |

## 10. Border radii scale

| Token | px | Usage |
|---|---|---|
| sm | 6 | Buttons, inputs |
| md | 10 | Nav items |
| lg | 12 | Folder tabs, cards |
| xl | 14 | Window outer shell |
| pill | 16 | Chip tabs (rounded-full) |
| dot | 6 (half of 12) | Status dot |

## 11. Animations + transitions

- Awaiting-input glow: blur-radius pulse 24 → 36 → 24 px, 2s loop, QPropertyAnimation
- Chip-tab swap: instant (no transition by default; can add 200ms ease later)
- Hover transitions: 150ms ease on bg + border + color
- Folder-tab add/remove: 200ms fade

## 12. Translation status — what's already correct in current QSS

- ✓ Color palette tokens (theme.py lines 64-81)
- ✓ Sidebar nav-item hover/active mapping (theme.py 140-160)
- ✓ Header row 1 menu strip (theme.py 162-187)
- ✓ Header row 2 page bar (theme.py 189-271)
- ✓ Chip tabs (theme.py 202-221)
- ✓ Header round action icons (theme.py 224-239)
- ✓ Create Agent button (theme.py 242-255)
- ✓ Folder tab strip (theme.py 293-311)
- ✓ Agent card + terminal + input (theme.py 314-385)
- ✓ Awaiting-input glow border (theme.py 319-321)
- ✓ Card close + send buttons (theme.py 376-399)
- ✓ Scrollbar styling (theme.py 438-462)
- ✗ Sidebar width should be **240** not 220 — patch needed
- ✗ Page title font-size should be **26px** not 24 — patch needed
- ✗ Chip tab height should be **32px** min — patch needed (currently 26)

## 13. Patch list (apply in re-skin pass)

1. `theme.py::SIDEBAR_WIDTH = 240`
2. `theme.py::QLabel#PageTitle { font-size: 26px; }`
3. `theme.py::QPushButton#ChipTab { min-height: 30px; padding: 6px 16px; }`
4. Verify `nav-eve-ai.svg` icon exists for Agents tab — confirmed in assets/panel-icons/
5. Verify `nav-phones.svg` icon exists for Devices tab — confirmed in assets/panel-icons/

---

End of spec.
