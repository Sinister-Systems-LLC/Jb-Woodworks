# Author: RKOJ-ELENO :: 2026-05-21
"""Sanctum purple theme tokens + global QSS stylesheet.

NEVER inline hex anywhere else in the app — pull from this module.

Layout doctrine (2026-05-21 rewrite): mirrors Sinister Panel
(snap.sinijkr.com images 13/14/16/17). Two-chip header (Agents/Devices),
folder-tab strip above the niri-scroll grid, sidebar with mascot + DAILY /
INSIGHTS / MANAGE sections.
"""

# ── Color tokens — operator-canonical Sanctum purple palette ────────────
BG = "#0E0A14"
BG_GLASS_1 = "#15131A"
BG_GLASS_2 = "#1C1626"
BG_GLOW = "#2A1F3D"
PURPLE_ACCENT = "#A06EFF"
PURPLE_DEEP = "#7A3DD4"
PURPLE_HALO = "#C39DFF"
LIGHT_PURPLE = "#E8D6FF"
SOFT = "#999AB0"
DIM = "#6E6E84"
BORDER_GLASS = "#3A2A55"
GREEN_ACCENT = "#85C86E"
RED_ACCENT = "#E06464"
AMBER_ACCENT = "#E0B464"
BLACK = "#000000"

# ── Sizes ───────────────────────────────────────────────────────────────
SIDEBAR_WIDTH = 200
HEADER_ROW1_HEIGHT = 32   # menu strip (drag region)
HEADER_ROW2_HEIGHT = 60   # chip tabs + actions
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
        border: 1px solid {BORDER_GLASS};
    }}

    /* ── Sidebar ──────────────────────────────────────────────────── */
    QWidget#Sidebar {{
        background-color: {BG_GLASS_1};
        border-right: 1px solid {BORDER_GLASS};
    }}
    QFrame#MascotFrame {{
        background-color: {BG_GLOW};
        border-bottom: 1px solid {BORDER_GLASS};
    }}
    QLabel#Mascot {{
        color: {PURPLE_ACCENT};
        font-family: "{MONO_FONT}";
        font-size: 12px;
    }}
    QLabel#EveLabel {{
        color: {PURPLE_HALO};
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 4px;
        padding-top: 4px;
    }}
    QLabel#SidebarSection {{
        color: {DIM};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 2px;
        padding: 16px 18px 4px 18px;
    }}
    QPushButton#NavItem {{
        background-color: transparent;
        color: {SOFT};
        text-align: left;
        padding: 7px 14px;
        border: 1px solid transparent;
        border-radius: 8px;
        font-size: 12px;
        margin: 1px 6px;
    }}
    QPushButton#NavItem:hover {{
        background-color: rgba(255,255,255,0.04);
        color: {LIGHT_PURPLE};
    }}
    QPushButton#NavItem[active="true"] {{
        background-color: {BG_GLOW};
        color: {PURPLE_HALO};
        font-weight: 600;
        border: 1px solid {BORDER_GLASS};
    }}

    /* ── Header — row 1 (menu strip / drag handle) ────────────────── */
    QWidget#HeaderRow1 {{
        background-color: {BG_GLASS_1};
        border-bottom: 1px solid {BORDER_GLASS};
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
        background-color: {BG_GLOW};
        color: {PURPLE_HALO};
        border-radius: 4px;
    }}
    QLabel#MenuMascot {{
        color: {PURPLE_HALO};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        padding-left: 14px;
        padding-right: 12px;
    }}

    /* ── Header — row 2 (page title + chip tabs + actions) ────────── */
    QWidget#HeaderRow2 {{
        background-color: {BG_GLASS_1};
        border-bottom: 1px solid {BORDER_GLASS};
    }}
    QLabel#PageTitle {{
        color: {PURPLE_HALO};
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    QPushButton#ChipTab {{
        background-color: {BG_GLASS_2};
        color: {SOFT};
        border: 1px solid {BORDER_GLASS};
        border-radius: 16px;
        padding: 6px 18px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#ChipTab:hover {{
        color: {LIGHT_PURPLE};
        border: 1px solid {PURPLE_DEEP};
    }}
    QPushButton#ChipTab[active="true"] {{
        background-color: {BG_GLOW};
        color: {PURPLE_HALO};
        border: 1px solid {PURPLE_ACCENT};
    }}

    QPushButton#HeaderIcon {{
        background-color: transparent;
        color: {SOFT};
        border: 1px solid transparent;
        border-radius: 14px;
        font-size: 13px;
        min-width: 28px;
        min-height: 28px;
        max-width: 28px;
        max-height: 28px;
    }}
    QPushButton#HeaderIcon:hover {{
        background-color: {BG_GLASS_2};
        color: {PURPLE_HALO};
        border: 1px solid {BORDER_GLASS};
    }}

    QPushButton#CreateAgentBtn {{
        background-color: {PURPLE_DEEP};
        color: white;
        border: 1px solid {PURPLE_ACCENT};
        border-radius: 8px;
        padding: 7px 16px;
        font-weight: 700;
        font-size: 12px;
    }}
    QPushButton#CreateAgentBtn:hover {{
        background-color: {PURPLE_ACCENT};
    }}

    QLabel#HealthPill {{
        color: {GREEN_ACCENT};
        background-color: {BG_GLASS_2};
        border: 1px solid {BORDER_GLASS};
        border-radius: 12px;
        padding: 4px 12px;
        font-size: 11px;
        font-weight: 600;
    }}
    QLabel#Clock {{
        color: {LIGHT_PURPLE};
        font-family: "{MONO_FONT}";
        font-size: 12px;
        padding: 0 8px;
    }}

    /* Window controls (top-right of row 1) */
    QPushButton#WinCtl {{
        background-color: transparent;
        color: {SOFT};
        border: none;
        font-family: "{MONO_FONT}";
        font-size: 12px;
        min-width: 28px;
        min-height: 22px;
    }}
    QPushButton#WinCtl:hover {{
        background-color: {BG_GLOW};
        color: {PURPLE_HALO};
        border-radius: 4px;
    }}
    QPushButton#WinCtlClose:hover {{
        background-color: {RED_ACCENT};
        color: white;
        border-radius: 4px;
    }}

    /* ── Folder tab strip (above niri-scroll grid) ────────────────── */
    QPushButton#FolderTab {{
        background-color: {BG_GLASS_2};
        color: {SOFT};
        border: 1px solid {BORDER_GLASS};
        border-radius: 12px;
        padding: 5px 14px;
        font-size: 11px;
        font-weight: 600;
    }}
    QPushButton#FolderTab:hover {{
        color: {LIGHT_PURPLE};
    }}
    QPushButton#FolderTab[active="true"] {{
        background-color: {BG_GLOW};
        color: {PURPLE_HALO};
        border: 1px solid {PURPLE_ACCENT};
    }}

    /* ── Agent cards ──────────────────────────────────────────────── */
    QFrame#AgentCard {{
        background-color: {BG_GLASS_1};
        border: 1px solid {BORDER_GLASS};
        border-radius: 12px;
    }}
    QFrame#AgentCard[needs_input="true"] {{
        border: 1px solid {PURPLE_ACCENT};
    }}
    QLabel#AgentProject {{
        color: {PURPLE_HALO};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    QLabel#AgentTitle {{
        color: {LIGHT_PURPLE};
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
    QLabel#StatusDot[state="online"] {{
        color: {GREEN_ACCENT};
        font-size: 16px;
    }}
    QLabel#StatusDot[state="busy"] {{
        color: {AMBER_ACCENT};
        font-size: 16px;
    }}
    QLabel#StatusDot[state="awaiting-input"] {{
        color: {PURPLE_ACCENT};
        font-size: 16px;
    }}
    QLabel#StatusDot[state="offline"], QLabel#StatusDot[state="idle"] {{
        color: {DIM};
        font-size: 16px;
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
        border: 1px solid {BORDER_GLASS};
        border-radius: 6px;
        font-family: "{MONO_FONT}";
        font-size: 12px;
        padding: 6px;
        selection-background-color: {PURPLE_DEEP};
    }}
    QLineEdit#TerminalInput {{
        background-color: {BG_GLASS_2};
        color: {LIGHT_PURPLE};
        border: 1px solid {BORDER_GLASS};
        border-radius: 6px;
        padding: 6px 10px;
        font-family: "{MONO_FONT}";
        font-size: 12px;
    }}
    QLineEdit#TerminalInput:focus {{
        border: 1px solid {PURPLE_ACCENT};
    }}

    QPushButton#SendBtn {{
        background-color: {PURPLE_DEEP};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 600;
    }}
    QPushButton#SendBtn:hover {{
        background-color: {PURPLE_ACCENT};
    }}
    QPushButton#CardCloseBtn {{
        background-color: transparent;
        color: {SOFT};
        border: none;
        font-family: "{MONO_FONT}";
        font-size: 14px;
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
        color: {PURPLE_HALO};
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 2px;
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
        color: {PURPLE_HALO};
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
