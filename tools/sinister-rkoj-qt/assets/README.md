# RKOJ Sanctum brand-asset kit

> **Author:** RKOJ-ELENO :: 2026-05-21
> **License:** AGPL-3.0
> **Consumed by:** PyQt6 desktop (`tools/sinister-rkoj-qt`), React Native mobile (`projects/sinister-claw`), future Sanctum products.

Single source of truth for the Sanctum-purple, devil-mascot, EVE-branded visual identity. Matches the snap.sinijkr.com Sinister Panel feel (operator screenshots 13 / 14 / 16).

## Files

| File | Purpose | Format | Size |
|---|---|---|---|
| `mascot.svg` | Devil mascot, Sanctum-purple gradient (`#7A3DD4 -> #A06EFF -> #C39DFF` vertical), transparent bg. | SVG | 60x60 viewBox |
| `logo.svg` | RKOJ wordmark in light-purple (`#E8D6FF -> #C39DFF`), transparent bg. | SVG | 200x40 viewBox |
| `icon-32.png` ... `icon-512.png` | Raster mascot exports at 32 / 64 / 128 / 256 / 512 px. Transparent bg. | PNG | square |
| `splash-1290x2796.png` | iOS splash screen — mascot top-center, RKOJ wordmark center, "Sinister Sanctum" subtitle, "EVE - RKOJ-ELENO" accent, radial Sanctum-purple bg. | PNG | 1290x2796 |
| `palette.json` | Machine-readable Sanctum palette tokens. | JSON | — |
| `_build_rasters.py` | One-shot regen script: draws the mascot directly in Pillow (no cairosvg dep) and composes the splash. | Python | — |
| `requirements.txt` | Optional deps for `_build_rasters.py` (Pillow required, cairosvg listed for future use). | text | — |

## Re-building rasters

```bash
pip install -r requirements.txt   # Pillow required; cairosvg optional (unused today)
python _build_rasters.py
```

The script translates the SVG mascot geometry directly into Pillow draw calls — so cairosvg is **not** required. The splash is composed from a radial gradient + the mascot + system fonts (Segoe UI on Windows, Helvetica on macOS, DejaVu on Linux).

### Missing-lib fallback

- **Pillow missing** -> script exits with `pip install Pillow` hint. SVG assets (`mascot.svg`, `logo.svg`) remain consumable directly via Qt / RN renderers. Follow-up: `pip install Pillow` then re-run `python _build_rasters.py`.
- **cairosvg missing** -> no impact today (`_build_rasters.py` doesn't import it). Listed in `requirements.txt` for any future asset that needs raw SVG -> PNG.

## Palette

`palette.json` is the canonical token table. Keys:

| Token | Hex | Use |
|---|---|---|
| `purpleAccent` | `#A06EFF` | Primary purple — buttons, links, focus rings. |
| `purpleDeep` | `#7A3DD4` | Darker purple — gradient bottoms, pressed states. |
| `purpleHalo` | `#C39DFF` | Lighter purple — gradient tops, hover glow. |
| `lightPurple` | `#E8D6FF` | Text / wordmark on dark bg. |
| `bg` | `#0E0A14` | App background. |
| `bgGlass1` | `#15131A` | Panel layer 1 (closest to bg). |
| `bgGlass2` | `#1C1626` | Panel layer 2 (cards / inputs). |
| `bgGlow` | `#2A1F3D` | Inner glow / radial center. |
| `borderGlass` | `#3A2A55` | 1px panel borders. |
| `soft` | `#999AB0` | Secondary text. |
| `dim` | `#6E6E84` | Muted / disabled text. |
| `greenAccent` | `#85C86E` | Success / online indicators. |

## Usage

### PyQt6 desktop

SVG via `QSvgWidget`:

```python
from PyQt6.QtSvgWidgets import QSvgWidget
mascot = QSvgWidget("assets/mascot.svg")
mascot.setFixedSize(60, 60)
```

PNG via `QPixmap`:

```python
from PyQt6.QtGui import QPixmap, QIcon
icon = QIcon(QPixmap("assets/icon-128.png"))
window.setWindowIcon(icon)
```

Palette consumption:

```python
import json
from pathlib import Path
palette = json.loads((Path(__file__).parent / "assets" / "palette.json").read_text())
accent = palette["purpleAccent"]   # "#A06EFF"
app.setStyleSheet(f"QPushButton {{ background: {palette['purpleDeep']}; color: {palette['lightPurple']}; }}")
```

### React Native mobile (`projects/sinister-claw`)

SVG via `react-native-svg`:

```tsx
import { SvgUri } from "react-native-svg";
<SvgUri width={60} height={60} uri={require("./assets/mascot.svg")} />
```

PNG via standard `Image`:

```tsx
import { Image } from "react-native";
<Image source={require("./assets/icon-256.png")} style={{ width: 64, height: 64 }} />
```

iOS splash — wire `splash-1290x2796.png` into `app.json` (Expo):

```json
{
  "expo": {
    "splash": {
      "image": "./assets/splash-1290x2796.png",
      "resizeMode": "cover",
      "backgroundColor": "#0E0A14"
    }
  }
}
```

Palette consumption:

```ts
import palette from "./assets/palette.json";
const styles = StyleSheet.create({
  button: { backgroundColor: palette.purpleDeep, color: palette.lightPurple },
});
```

## Source provenance

- Mascot geometry derived from `D:/Sinister Sanctum/automations/window-manager/web/skull.svg` (RKOJ devil silhouette).
- Wordmark derived from `D:/Sinister Sanctum/automations/window-manager/web/rkoj-logo.png` (re-rendered as live SVG text for crisp scaling).
- Gradient + palette mirror `automations/window-manager/web/sinister-logo.png` + the Sinister Panel CSS.

## Ownership & lane discipline

- This `assets/` folder is owned by the brand-kit sub-agent (this commit).
- `tools/sinister-rkoj-qt/sinister_rkoj_qt/*.py` — owned by the strip-rewrite sub-agent. Do NOT modify from here.
- `projects/sinister-claw/` — owned by the mobile-rebrand sub-agent. Do NOT modify from here.
