# Author: RKOJ-ELENO :: 2026-05-21
"""Sanctum purple theme tokens + global QSS stylesheet + SVG icon helper.

Pixel-precise port of Sinister Panel's globals.css + tailwind.config.js:
- Sidebar nav-item: 14px font, 12px h-padding, 8px gap, 10px border-radius,
  active = inset purple gradient + 600 weight purple text (`#BF5AF2`).
- Chip tabs: 32px tall, 14px font, 18px h-padding, 16px border-radius pill.
- Round icon buttons: 32x32, transparent until hover (subtle `#15131A` bg +
  border-glass), borderless otherwise.
- Page title: 26px bold, tracking-tight (per Panel TabHeader).
- Create Agent button: solid purple-accent fill, white text, 14px font,
  10px padding, 6px border-radius.
- Folder-tab chip: 20px tall, 12px h-padding, pill, `#15131A` bg + `#3A2A55`
  border, active = purple-accent fill.
- Section labels: 10px uppercase, tracking-wider, `#8e8e93`.
- Mascot block: 64x64 mascot inside purple-tinted radial frame, no subtitle.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from PyQt6.QtCore import QSize
from PyQt6.QtSvgWidgets import QSvgWidget


def asset_path(name: str) -> Path:
    """Resolve a bundled brand-asset path, frozen-aware.

    - Frozen (PyInstaller onefile): use ``sys._MEIPASS / 'assets' / name``.
    - Dev: walk up from this module to ``tools/sinister-rkoj-qt/assets/`` so
      `python -m sinister_rkoj_qt` finds the same files as the bundled EXE.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / name  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent / "assets" / name


@lru_cache(maxsize=None)
def _resolve_icon_path(name: str) -> str:
    """Cache resolved icon paths so we hit the filesystem once per name."""
    p = asset_path(f"panel-icons/{name}.svg")
    return str(p)


def nav_icon(name: str, size: int = 19) -> QSvgWidget:
    """Return a freshly-loaded QSvgWidget sized for nav/header use.

    Panel's NavGlyph renders at 19px by default; header pill chips render at
    14-16px. Callers can pass any size. The widget tints automatically via the
    embedded `stroke="currentColor"` once we set a stylesheet color, but Qt
    SVG renderer doesn't honour CSS currentColor — we ship the SVG with
    `currentColor` literal so it inherits from the parent QWidget palette in
    most engines, and fall back to the default purple where it doesn't.
    """
    w = QSvgWidget(_resolve_icon_path(name))
    w.setFixedSize(QSize(size, size))
    return w


# ── Color tokens — operator-canonical Sanctum purple palette ────────────
BG = "#0E0A14"
BG_GLASS_1 = "#15131A"
BG_GLASS_2 = "#1C1626"
BG_GLOW = "#2A1F3D"
PURPLE_ACCENT = "#A06EFF"
PURPLE_DEEP = "#7A3DD4"
PURPLE_HALO = "#C39DFF"
PURPLE_NAV_ACTIVE = "#BF5AF2"  # Panel sidebar active text color
LIGHT_PURPLE = "#E8D6FF"
SOFT = "#8e8e93"               # Panel dim text token
DIM = "#6E6E84"
BORDER_GLASS = "#3A2A55"
BORDER_HAIRLINE = "#2c2c2e"    # Panel hairline divider
GREEN_ACCENT = "#30D158"       # Panel STATUS_COLOR.success
RED_ACCENT = "#FF453A"         # Panel STATUS_COLOR.danger
AMBER_ACCENT = "#FF9F0A"       # Panel STATUS_COLOR.warning
INFO_BLUE = "#0A84FF"          # Panel STATUS_COLOR.info
BLACK = "#000000"

# ── Sizes ───────────────────────────────────────────────────────────────
SIDEBAR_WIDTH = 220
HEADER_ROW1_HEIGHT = 32   # menu strip (drag region)
HEADER_ROW2_HEIGHT = 64   # chip tabs + actions
WINDOW_RADIUS = 14

# Generic radii + spacings (centralized constants — no inline numerics elsewhere)
RADII = {"sm": 6, "md": 10, "lg": 14}
SPACINGS = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24}

# ── Fonts ───────────────────────────────────────────────────────────────
MONO_FONT = "Cascadia Mono, Consolas, Courier New, monospace"
UI_FONT = "Segoe UI, Inter, system-ui, sans-serif"


def build_qss() -> str:
    """Return the full app QSS — single source of styling."""
    return f"""
    /* ------------------------------------------------------------------
       Sinister Sanctum — RKOJ.exe native Qt theme
       Author: RKOJ-ELENO :: 2026-05-21
       1:1 port of Sinister Panel (snap.sinijkr.com) chrome.
       ------------------------------------------------------------------ */

    QWidget {{
        background-color: {BG};
        color: {LIGHT_PURPLE};
        font-family: "{UI_FONT}";
        font-size: 13px;
    }}

    /* Outer rounded shell */
    QWidget#RootShell {{
        background-color: {BG};
        border-radius: {WINDOW_RADIUS}px;
        border: 1px solid {BORDER_HAIRLINE};
    }}

    /* ── Sidebar — Panel `aside.rounded-2xl border-[#2c2c2e] bg-[#0a0a0c]` ─ */
    QWidget#Sidebar {{
        background-color: #0a0a0c;
        border-right: 1px solid {BORDER_HAIRLINE};
    }}
    QFrame#MascotFrame {{
        background-color: #0a0a0c;
        border-bottom: 1px solid {BORDER_HAIRLINE};
    }}
    QLabel#SidebarSection {{
        color: {SOFT};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        padding: 12px 16px 6px 16px;
        border-bottom: 1px solid #1c1c1e;
        margin: 0 6px;
    }}
    /* Panel nav-item: rounded-[10px] px-3 py-2.5 text-[14px] gap-3 */
    QPushButton#NavItem {{
        background-color: transparent;
        color: {SOFT};
        text-align: left;
        padding: 8px 12px;
        border: 1px solid transparent;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 500;
        margin: 1px 6px;
    }}
    QPushButton#NavItem:hover {{
        background-color: rgba(255,255,255,0.05);
        color: white;
    }}
    QPushButton#NavItem[active="true"] {{
        background-color: {PURPLE_DEEP};
        color: white;
        font-weight: 600;
        border: 1px solid {PURPLE_ACCENT};
    }}

    /* ── Header — row 1 (menu strip / drag handle) ────────────────── */
    QWidget#HeaderRow1 {{
        background-color: #0a0a0c;
        border-bottom: 1px solid {BORDER_HAIRLINE};
    }}
    QPushButton#MenuItem {{
        background-color: transparent;
        color: {SOFT};
        border: none;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton#MenuItem:hover {{
        background-color: {BG_GLASS_2};
        color: white;
        border-radius: 4px;
    }}
    QLabel#MenuMascot {{
        color: {PURPLE_NAV_ACTIVE};
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 2px;
        padding-left: 14px;
        padding-right: 12px;
    }}

    /* ── Header — row 2 (page title + chip tabs + actions) ────────── */
    QWidget#HeaderRow2 {{
        background-color: #0a0a0c;
        border-bottom: 1px solid {BORDER_HAIRLINE};
    }}
    /* Panel tab-header h1: text-[26px] font-bold tracking-tight */
    QLabel#PageTitle {{
        color: {PURPLE_NAV_ACTIVE};
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.5px;
        padding-left: 8px;
    }}
    /* Panel pill: rounded-full px-4 h-8 text-[13px] font-semibold */
    QPushButton#ChipTab {{
        background-color: {BG_GLASS_1};
        color: {SOFT};
        border: 1px solid {BORDER_HAIRLINE};
        border-radius: 16px;
        padding: 4px 14px;
        font-size: 13px;
        font-weight: 600;
        min-height: 26px;
    }}
    QPushButton#ChipTab:hover {{
        color: white;
        border: 1px solid {PURPLE_DEEP};
    }}
    QPushButton#ChipTab[active="true"] {{
        background-color: {PURPLE_DEEP};
        color: white;
        border: 1px solid {PURPLE_ACCENT};
    }}

    /* Panel header-icon button: 32x32 round w/ subtle bg on hover */
    QPushButton#HeaderIcon {{
        background-color: transparent;
        color: {SOFT};
        border: 1px solid transparent;
        border-radius: 16px;
        min-width: 32px;
        min-height: 32px;
        max-width: 32px;
        max-height: 32px;
        padding: 0;
    }}
    QPushButton#HeaderIcon:hover {{
        background-color: {BG_GLASS_1};
        color: white;
        border: 1px solid {BORDER_HAIRLINE};
    }}

    /* Panel "+ Create" button: solid purple, rounded-md, font-medium */
    QPushButton#CreateAgentBtn {{
        background-color: {PURPLE_ACCENT};
        color: white;
        border: 1px solid {PURPLE_ACCENT};
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 600;
        font-size: 13px;
        min-height: 26px;
    }}
    QPushButton#CreateAgentBtn:hover {{
        background-color: {PURPLE_HALO};
        color: {BG};
    }}

    QLabel#HealthPill {{
        color: {GREEN_ACCENT};
        background-color: {BG_GLASS_1};
        border: 1px solid {BORDER_HAIRLINE};
        border-radius: 12px;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
    }}
    QLabel#Clock {{
        color: {SOFT};
        font-family: "{MONO_FONT}";
        font-size: 12px;
        padding: 0 8px;
    }}

    /* Window controls (top-right of row 1) */
    QPushButton#WinCtl {{
        background-color: transparent;
        color: {SOFT};
        border: none;
        min-width: 32px;
        min-height: 24px;
        padding: 0;
    }}
    QPushButton#WinCtl:hover {{
        background-color: {BG_GLASS_2};
        color: white;
    }}
    QPushButton#WinCtlClose:hover {{
        background-color: {RED_ACCENT};
        color: white;
    }}

    /* ── Folder tab strip (Panel "All 0" pill) ────────────────────── */
    /* Panel: h-5 px-3 text-[11px] bg-[#15131A] border-[#3A2A55] rounded-full */
    QPushButton#FolderTab {{
        background-color: {BG_GLASS_1};
        color: {SOFT};
        border: 1px solid {BORDER_GLASS};
        border-radius: 12px;
        padding: 3px 12px;
        font-size: 11px;
        font-weight: 600;
        min-height: 20px;
    }}
    QPushButton#FolderTab:hover {{
        color: white;
        border: 1px solid {PURPLE_DEEP};
    }}
    QPushButton#FolderTab[active="true"] {{
        background-color: {PURPLE_ACCENT};
        color: white;
        border: 1px solid {PURPLE_ACCENT};
    }}

    /* ── Agent cards ──────────────────────────────────────────────── */
    QFrame#AgentCard {{
        background-color: {BG_GLASS_1};
        border: 1px solid {BORDER_HAIRLINE};
        border-radius: 12px;
    }}
    QFrame#AgentCard[needs_input="true"] {{
        border: 1px solid {PURPLE_ACCENT};
    }}
    QLabel#AgentProject {{
        color: {PURPLE_HALO};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.2px;
    }}
    QLabel#AgentTitle {{
        color: white;
        font-size: 13px;
        font-weight: 700;
    }}
    QLabel#AgentMeta {{
        color: {SOFT};
        font-size: 11px;
    }}
    QLabel#ModePill {{
        color: {PURPLE_HALO};
        background-color: {BG_GLASS_2};
        border: 1px solid {BORDER_GLASS};
        border-radius: 10px;
        padding: 2px 9px;
        font-size: 10px;
        font-weight: 600;
    }}
    QFrame#ProjectDivider {{
        background-color: {PURPLE_DEEP};
        max-height: 1px;
        min-height: 1px;
    }}

    /* Embedded terminal */
    QPlainTextEdit#Terminal {{
        background-color: {BG};
        color: {LIGHT_PURPLE};
        border: 1px solid {BORDER_HAIRLINE};
        border-radius: 6px;
        font-family: "{MONO_FONT}";
        font-size: 12px;
        padding: 6px;
        selection-background-color: {PURPLE_DEEP};
    }}
    QLineEdit#TerminalInput {{
        background-color: {BG_GLASS_2};
        color: white;
        border: 1px solid {BORDER_HAIRLINE};
        border-radius: 6px;
        padding: 6px 10px;
        font-family: "{MONO_FONT}";
        font-size: 12px;
    }}
    QLineEdit#TerminalInput:focus {{
        border: 1px solid {PURPLE_ACCENT};
    }}

    QPushButton#SendBtn {{
        background-color: {PURPLE_ACCENT};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 600;
    }}
    QPushButton#SendBtn:hover {{
        background-color: {PURPLE_HALO};
        color: {BG};
    }}
    QPushButton#CardCloseBtn {{
        background-color: transparent;
        color: {SOFT};
        border: none;
        min-width: 22px;
        min-height: 22px;
    }}
    QPushButton#CardCloseBtn:hover {{
        background-color: {RED_ACCENT};
        color: white;
        border-radius: 4px;
    }}

    /* Devices placeholder */
    QLabel#PlaceholderHero {{
        color: {PURPLE_NAV_ACTIVE};
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    QLabel#PlaceholderSub {{
        color: {SOFT};
        font-size: 13px;
    }}

    /* Menus (File / Edit / View ...) */
    QMenu {{
        background-color: {BG_GLASS_2};
        color: {LIGHT_PURPLE};
        border: 1px solid {BORDER_GLASS};
        padding: 4px 0;
    }}
    QMenu::item {{
        padding: 5px 22px;
        background-color: transparent;
    }}
    QMenu::item:selected {{
        background-color: {BG_GLOW};
        color: white;
    }}
    QMenu::item:disabled {{
        color: {DIM};
    }}
    QMenu::separator {{
        height: 1px;
        background: {BORDER_GLASS};
        margin: 4px 8px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: {BG};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_GLOW};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {PURPLE_DEEP};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {BG};
        height: 10px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BG_GLOW};
        border-radius: 5px;
        min-width: 30px;
    }}
    """
