# Author: RKOJ-ELENO :: 2026-05-21
"""Sanctum Panel-1:1 theme — tokens + global QSS + SVG icon helper.

Pixel-precise port of Sinister Panel's `panel/dashboard/styles/globals.css`
+ `components/sidebar.tsx` + `components/tab-header.tsx`. Updates 2026-05-21
to drop the prior 2-row header (Panel has ONE 96px header row).

Layout constants:
- SIDEBAR_WIDTH = 240
- HEADER_HEIGHT = 96
- OUTER_PADDING = 8 (body padding)
- OUTER_GAP = 8 (gap between sidebar and main)
- CARD_RADIUS = 16 (Panel `rounded-2xl`)
- WINDOW_RADIUS = 18 (outer window corner)

Color tokens (from globals.css `@theme`):
- BG = #000 (body bg — peeks through 8px gap)
- PANEL_BG = #0a0a0c (the two rounded cards)
- ELEVATED = #1c1c1e (Panel `--color-panel`)
- BORDER = #2c2c2e (Panel hairline)
- PURPLE_PRIMARY = #BF5AF2 (Panel `--color-purple`)
- MUTED_FG = #8e8e93
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
    - Dev: walk up from this module to ``projects/rkoj/source/assets/`` so
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
    """Return a freshly-loaded QSvgWidget sized for nav/header use."""
    w = QSvgWidget(_resolve_icon_path(name))
    w.setFixedSize(QSize(size, size))
    return w


# ── Color tokens — direct port of Panel globals.css `@theme` ────────────
# Body bg peeks through the 8px gap between the sidebar + main cards.
BG = "#000000"
# The two rounded outer cards (sidebar + main).
PANEL_BG = "#0a0a0c"
# Slightly elevated surface (cards, terminals, inputs).
ELEVATED = "#1c1c1e"
# Even more elevated (header round-icon hover, chip inactive).
ELEVATED_HI = "#2c2c2e"
# Hairline divider.
BORDER = "#2c2c2e"
BORDER_STRONG = "#38383a"
BORDER_SUBTLE = "rgba(255, 255, 255, 0.06)"
# Text.
FG = "#ffffff"
MUTED_FG = "#8e8e93"
MUTED = "#636366"
# Brand purple — Panel `--color-purple`.
PURPLE_PRIMARY = "#BF5AF2"
PURPLE_DEEP = "#7B2CBF"
PURPLE_HALO = "#A78BFA"
# Status.
SUCCESS = "#30D158"
DANGER = "#FF453A"
WARNING = "#FF9F0A"
INFO = "#0A84FF"

# ── Backwards-compat aliases for legacy modules ─────────────────────────
PURPLE_ACCENT = PURPLE_PRIMARY
PURPLE_NAV_ACTIVE = PURPLE_PRIMARY
LIGHT_PURPLE = "#E8D6FF"
SOFT = MUTED_FG
DIM = "#6E6E84"
BG_GLASS_1 = ELEVATED
BG_GLASS_2 = "#2a2a2c"
BG_GLOW = "#2A1F3D"
BORDER_GLASS = "#3A2A55"
BORDER_HAIRLINE = BORDER
GREEN_ACCENT = SUCCESS
RED_ACCENT = DANGER
AMBER_ACCENT = WARNING
INFO_BLUE = INFO
BLACK = "#000000"

# ── Sizes — Panel layout.tsx + sidebar.tsx + tab-header.tsx ─────────────
SIDEBAR_WIDTH = 280        # v1.6.84 — bigger per operator (was 240)
HEADER_HEIGHT = 96         # Panel `HEADER_HEIGHT = 96`
SIDEBAR_BANNER_HEIGHT = 160  # v1.6.84 — was HEADER_HEIGHT (96); banner now stands alone so logo is visible
OUTER_PADDING = 8          # Panel layout.tsx `p-2`
# v1.6.72 — operator wants sidebar + main connected (no gap of disconnect).
OUTER_GAP = 0
CARD_RADIUS = 16           # Panel `rounded-2xl` = 16px (Tailwind v4)
WINDOW_RADIUS = 18         # outer window mask radius (slightly bigger so the
                            # 8px black gap reads cleanly between cards)
LEFT_SPINE_WIDTH = 2       # Panel sidebar left-edge accent bar
# Backward-compat (header.py imports these but they're folded into HEADER_HEIGHT now)
HEADER_ROW1_HEIGHT = 0
HEADER_ROW2_HEIGHT = HEADER_HEIGHT

# Generic radii + spacings (centralized — no inline numerics elsewhere).
RADII = {"xs": 6, "sm": 10, "md": 14, "lg": 16, "xl": 20, "full": 999}
SPACINGS = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 20, "2xl": 24}

# ── Fonts — Panel `--font-sans` / `--font-mono` ─────────────────────────
UI_FONT = ("-apple-system, BlinkMacSystemFont, 'SF Pro Display', "
           "'Segoe UI', 'Inter', system-ui, sans-serif")
MONO_FONT = ("'JetBrains Mono', 'Cascadia Code', 'SF Mono', "
             "ui-monospace, Consolas, Menlo, 'DejaVu Sans Mono', monospace")


def build_qss() -> str:
    """Return the full app QSS — single source of styling.

    Pixel-precise translation of Panel's globals.css + sidebar.tsx +
    tab-header.tsx. Where Tailwind classes appear in comments, they map to
    the exact rule below.
    """
    return f"""
    /* ═══════════════════════════════════════════════════════════════════
       Sinister Sanctum — RKOJ.exe Panel-1:1 chrome
       Author: RKOJ-ELENO :: 2026-05-21
       Source-of-truth: projects/sinister-panel/source/Andrew Panel/
                        Sinister Panel/panel/dashboard/
       ═══════════════════════════════════════════════════════════════════ */

    QWidget {{
        background-color: transparent;
        color: {FG};
        font-family: {UI_FONT};
        font-size: 13px;
    }}

    /* Outer body — black, peeks through the 8px gap between the two cards.
       Panel layout.tsx: `bg-black` on <body>, `p-2 gap-2` wrapper. */
    QWidget#OuterBody {{
        background-color: {BG};
    }}

    /* The two rounded outer cards. Panel: `rounded-2xl border bg-[#0a0a0c]`. */
    QWidget#SidebarCard,
    QWidget#MainCard {{
        background-color: {PANEL_BG};
        border: 1px solid {BORDER};
        border-radius: {CARD_RADIUS}px;
    }}

    /* ── Sidebar (left aside) ────────────────────────────────────────── */
    QWidget#Sidebar {{
        background-color: transparent;
    }}
    /* Banner block — 96px, matches HEADER_HEIGHT so the bottom-borders of
       sidebar-banner and main-header line up across the whole window. */
    QFrame#BannerFrame {{
        background-color: {PANEL_BG};
        border-bottom: 1px solid {BORDER};
    }}
    /* Left-edge accent bar — purple gradient spine (Panel reads as a brand
       marker, not a literal divider). 2px wide, full-height. */
    QFrame#LeftSpine {{
        background: qlineargradient(x1:0 y1:0 x2:0 y2:1,
                                    stop:0 rgba(191,90,242,140),
                                    stop:1 rgba(123,44,191,50));
        border: none;
    }}

    /* Section header — Panel:
       `px-3 mb-2 pb-2 text-[12px] font-semibold text-[#8e8e93]
        uppercase tracking-[.12em] border-b border-[#1c1c1e]` */
    QLabel#SidebarSection {{
        color: {MUTED_FG};
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 1.8px;
        padding: 16px 14px 10px 14px;
        border-bottom: 1px solid {ELEVATED};
        margin: 0 0 6px 0;
    }}

    /* Nav item — Panel:
       `flex items-center gap-3 rounded-[10px] px-3 py-2.5 text-[14px]`
       Inactive: `text-[#8e8e93]` + hover `text-white bg-white/[0.05]`.
       Active: `text-[#BF5AF2] font-semibold` + gradient bg
               linear-gradient(180deg, rgba(191,90,242,0.22),
                                       rgba(191,90,242,0.08)). */
    QPushButton#NavItem {{
        background-color: transparent;
        color: {MUTED_FG};
        text-align: left;
        padding: 10px 12px;
        border: none;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 500;
        margin: 1px 8px;
    }}
    QPushButton#NavItem:hover {{
        background-color: rgba(255,255,255,0.05);
        color: white;
    }}
    QPushButton#NavItem[active="true"] {{
        color: {PURPLE_PRIMARY};
        font-weight: 600;
        background: qlineargradient(x1:0 y1:0 x2:0 y2:1,
                                    stop:0 rgba(191,90,242,56),
                                    stop:1 rgba(191,90,242,20));
    }}

    /* ── Header (single 96px row) ────────────────────────────────────── */
    /* Background: Panel applies a radial wash from top-left; we approximate
       with a vertical gradient (Qt QSS radial syntax is finicky for short
       horizontal washes). Plus 1px purple-tinted bottom border. */
    QWidget#Header {{
        background: qlineargradient(x1:0 y1:0 x2:1 y2:0,
                                    stop:0 rgba(191,90,242,10),
                                    stop:0.5 transparent,
                                    stop:1 transparent);
        border-bottom: 1px solid rgba(191,90,242,115);
    }}
    /* Page title — Panel: `text-[26px] font-bold tracking-tight leading-none`
       plus `text-shadow: 0 0 14px rgba(#BF5AF2, 0.35)` (we apply a QGraphics
       drop-shadow in header.py for the glow). */
    QLabel#PageTitle {{
        color: {PURPLE_PRIMARY};
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        padding: 0;
    }}

    /* Chip tab — Panel `<Chip variant=filter size=md>`:
       `h-7 px-2.5 text-[11.5px] rounded-full` + border + bg at tint alpha. */
    QPushButton#ChipTab {{
        background-color: rgba(191,90,242,26);   /* 10% alpha */
        color: {PURPLE_PRIMARY};
        border: 1px solid rgba(191,90,242,71);    /* 28% alpha */
        border-radius: 14px;                       /* h-7 = 28px → r=14 */
        padding: 0 10px;
        min-height: 26px;
        max-height: 28px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#ChipTab:hover {{
        background-color: rgba(191,90,242,56);
    }}
    QPushButton#ChipTab[active="true"] {{
        background-color: rgba(191,90,242,56);
        color: white;
        border: 1px solid rgba(191,90,242,140);
    }}

    /* Header round-icon button — Panel `btn-icon`:
       32x32, transparent until hover (subtle purple wash + purple icon). */
    QPushButton#HeaderIcon {{
        background-color: transparent;
        color: {MUTED_FG};
        border: 1px solid transparent;
        border-radius: 7px;
        min-width: 32px;
        min-height: 32px;
        max-width: 32px;
        max-height: 32px;
        padding: 0;
    }}
    QPushButton#HeaderIcon:hover {{
        background-color: rgba(191,90,242,31);     /* 12% alpha */
        color: {PURPLE_PRIMARY};
    }}
    /* Close button — red wash on hover (Panel doesn't have one; we add it
       because the frameless app needs its own X). */
    QPushButton#WinCtlClose:hover {{
        background-color: {DANGER};
        color: white;
    }}

    /* Create Agent button — Panel primary button:
       `h-8 px-3 text-[12px] rounded-[7px] bg-[#BF5AF2] shadow-[0_2px_10px
        rgba(191,90,242,0.30)]` + hover bg `#A78BFA`. */
    QPushButton#CreateAgentBtn {{
        background-color: {PURPLE_PRIMARY};
        color: white;
        border: none;
        border-radius: 7px;
        min-height: 32px;
        max-height: 32px;
        font-weight: 600;
        font-size: 12px;
    }}
    QPushButton#CreateAgentBtn:hover {{
        background-color: {PURPLE_HALO};
    }}

    /* Health pill — green dot + "online" — Panel `.pill .pill-ok` style. */
    QFrame#HealthPillFrame {{
        background-color: rgba(48, 209, 88, 38);    /* success-dim */
        border: 1px solid rgba(48, 209, 88, 70);
        border-radius: 12px;
    }}
    QLabel#HealthPill {{
        color: {SUCCESS};
        background: transparent;
        font-size: 11px;
        font-weight: 600;
        padding: 0;
    }}

    /* Live clock — mono tabular. */
    QLabel#Clock {{
        color: {MUTED_FG};
        font-family: {MONO_FONT};
        font-size: 12px;
        padding: 0 8px;
    }}

    /* ── Folder tab strip (above body) — Panel uses similar pill style ─ */
    QPushButton#FolderTab {{
        background-color: {ELEVATED};
        color: {MUTED_FG};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 4px 12px;
        font-size: 11px;
        font-weight: 600;
        min-height: 22px;
    }}
    QPushButton#FolderTab:hover {{
        color: white;
        border: 1px solid {PURPLE_PRIMARY};
    }}
    QPushButton#FolderTab[active="true"] {{
        background-color: rgba(191,90,242,56);
        color: white;
        border: 1px solid {PURPLE_PRIMARY};
    }}

    /* ── Agent cards — v1.6.84 transparent jcode-style (see dashboard
       through them) + breathing glow handled per-card in Python ────── */
    QFrame#AgentCard {{
        background-color: rgba(28,28,30,0.78);
        border: 1px solid rgba(191,90,242,0.35);
        border-radius: 14px;
    }}
    QFrame#AgentCard[needs_input="true"] {{
        border: 1px solid {PURPLE_PRIMARY};
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
        color: {MUTED_FG};
        font-size: 11px;
    }}
    QLabel#ModePill {{
        color: {PURPLE_PRIMARY};
        background-color: rgba(191,90,242,26);
        border: 1px solid rgba(191,90,242,71);
        border-radius: 10px;
        padding: 2px 9px;
        font-size: 10px;
        font-weight: 600;
    }}
    QFrame#ProjectDivider {{
        background-color: {BORDER};
        max-height: 1px;
        min-height: 1px;
    }}

    /* Embedded terminal (jcode-form) */
    QPlainTextEdit#Terminal {{
        background-color: #0a0a0c;
        color: #e8e8ea;
        border: 1px solid {BORDER};
        border-radius: 8px;
        font-family: {MONO_FONT};
        font-size: 12px;
        padding: 8px;
        selection-background-color: rgba(191,90,242,90);
    }}
    QLineEdit#TerminalInput {{
        background-color: {ELEVATED};
        color: white;
        border: 1px solid {BORDER};
        border-radius: 7px;
        padding: 7px 10px;
        font-family: {MONO_FONT};
        font-size: 12px;
    }}
    QLineEdit#TerminalInput:focus {{
        border: 1px solid {PURPLE_PRIMARY};
    }}

    QPushButton#SendBtn {{
        background-color: {PURPLE_PRIMARY};
        color: white;
        border: none;
        border-radius: 7px;
        padding: 7px 14px;
        font-weight: 600;
        font-size: 12px;
    }}
    QPushButton#SendBtn:hover {{
        background-color: {PURPLE_HALO};
    }}
    QPushButton#CardCloseBtn {{
        background-color: transparent;
        color: {MUTED_FG};
        border: none;
        min-width: 22px;
        min-height: 22px;
    }}
    QPushButton#CardCloseBtn:hover {{
        background-color: {DANGER};
        color: white;
        border-radius: 4px;
    }}

    /* Devices placeholder hero */
    QLabel#PlaceholderHero {{
        color: {PURPLE_PRIMARY};
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    QLabel#PlaceholderSub {{
        color: {MUTED_FG};
        font-size: 13px;
    }}

    /* Menus (any contextual popups) */
    QMenu {{
        background-color: {ELEVATED};
        color: white;
        border: 1px solid {BORDER};
        padding: 4px 0;
    }}
    QMenu::item {{
        padding: 6px 22px;
        background-color: transparent;
    }}
    QMenu::item:selected {{
        background-color: rgba(191,90,242,56);
        color: white;
    }}
    QMenu::item:disabled {{
        color: {MUTED};
    }}
    QMenu::separator {{
        height: 1px;
        background: {BORDER};
        margin: 4px 8px;
    }}

    /* Scrollbars — Panel uses 6px thin, transparent track, muted thumb */
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {MUTED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {BORDER};
        border-radius: 3px;
        min-width: 30px;
    }}
    """
