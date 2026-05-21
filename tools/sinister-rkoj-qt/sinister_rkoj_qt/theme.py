# Author: RKOJ-ELENO :: 2026-05-21
"""Sanctum purple theme tokens + global QSS stylesheet.

NEVER inline hex anywhere else in the app — pull from this module.
"""

# Color tokens — operator-canonical Sanctum purple palette (2026-05-21).
BG = "#0E0A14"
BG_GLASS_1 = "#15131A"
BG_GLASS_2 = "#1B1722"
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

# Sizes
SIDEBAR_WIDTH = 240
HEADER_HEIGHT = 96
RIBBON_HEIGHT = 110
KPI_HEIGHT = 100
WINDOW_RADIUS = 18

# Fonts
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

    /* Sidebar */
    QWidget#Sidebar {{
        background-color: {BG_GLASS_1};
        border-right: 1px solid {BORDER_GLASS};
    }}
    QLabel#SidebarSection {{
        color: {DIM};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        padding: 18px 18px 4px 18px;
        border-bottom: 1px solid {BG_GLASS_2};
        margin-bottom: 4px;
    }}
    QPushButton#NavItem {{
        background-color: transparent;
        color: {SOFT};
        text-align: left;
        padding: 9px 16px;
        border: none;
        border-radius: 10px;
        font-size: 13px;
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

    QLabel#Mascot {{
        color: {PURPLE_ACCENT};
        font-family: "{MONO_FONT}";
        font-size: 12px;
        padding: 8px;
    }}
    QLabel#EveLabel {{
        color: {PURPLE_HALO};
        font-size: 14px;
        font-weight: 700;
        letter-spacing: 4px;
    }}

    /* Header */
    QWidget#Header {{
        background-color: {BG_GLASS_1};
        border-bottom: 1px solid {BORDER_GLASS};
    }}
    QLabel#HeaderTitle {{
        color: {PURPLE_HALO};
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 1.5px;
    }}
    QPushButton#HeaderChip {{
        background-color: {BG_GLASS_2};
        color: {SOFT};
        border: 1px solid {BORDER_GLASS};
        border-radius: 16px;
        padding: 6px 16px;
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#HeaderChip:hover {{
        color: {LIGHT_PURPLE};
        border: 1px solid {PURPLE_DEEP};
    }}
    QPushButton#HeaderChip[active="true"] {{
        background-color: {BG_GLOW};
        color: {PURPLE_HALO};
        border: 1px solid {PURPLE_ACCENT};
    }}

    QPushButton#HeaderIcon {{
        background-color: transparent;
        color: {SOFT};
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 6px 8px;
        font-size: 13px;
        min-width: 28px;
    }}
    QPushButton#HeaderIcon:hover {{
        background-color: {BG_GLASS_2};
        color: {PURPLE_HALO};
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
        font-size: 13px;
        padding: 0 8px;
    }}

    /* Title-bar window controls */
    QPushButton#WinCtl {{
        background-color: transparent;
        color: {SOFT};
        border: none;
        font-family: "{MONO_FONT}";
        font-size: 14px;
        min-width: 30px;
        min-height: 22px;
    }}
    QPushButton#WinCtl:hover {{
        background-color: {BG_GLOW};
        color: {PURPLE_HALO};
        border-radius: 6px;
    }}
    QPushButton#WinCtlClose:hover {{
        background-color: {RED_ACCENT};
        color: white;
        border-radius: 6px;
    }}

    /* Ribbon */
    QWidget#Ribbon {{
        background-color: {BG_GLASS_1};
        border-bottom: 1px solid {BORDER_GLASS};
    }}
    QWidget#RibbonGroup {{
        background-color: {BG_GLASS_2};
        border: 1px solid {BORDER_GLASS};
        border-radius: 8px;
    }}
    QLabel#RibbonGroupLabel {{
        color: {DIM};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.5px;
        padding: 2px 6px;
    }}
    QPushButton#RibbonBtn {{
        background-color: transparent;
        color: {LIGHT_PURPLE};
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 11px;
        text-align: left;
    }}
    QPushButton#RibbonBtn:hover {{
        background-color: {BG_GLOW};
        border: 1px solid {PURPLE_DEEP};
        color: {PURPLE_HALO};
    }}

    /* KPIs */
    QWidget#KpiTile {{
        background-color: {BG_GLASS_1};
        border: 1px solid {BORDER_GLASS};
        border-radius: 10px;
    }}
    QLabel#KpiLabel {{
        color: {DIM};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
    }}
    QLabel#KpiValue {{
        color: {PURPLE_HALO};
        font-size: 28px;
        font-weight: 700;
        font-family: "{MONO_FONT}";
    }}
    QLabel#KpiSub {{
        color: {SOFT};
        font-size: 10px;
    }}

    /* Project chip strip */
    QPushButton#ProjectChip {{
        background-color: {BG_GLASS_2};
        color: {SOFT};
        border: 1px solid {BORDER_GLASS};
        border-radius: 14px;
        padding: 5px 12px;
        font-size: 11px;
    }}
    QPushButton#ProjectChip:hover {{
        color: {LIGHT_PURPLE};
    }}
    QPushButton#ProjectChip[active="true"] {{
        background-color: {BG_GLOW};
        color: {PURPLE_HALO};
        border: 1px solid {PURPLE_ACCENT};
        font-weight: 600;
    }}

    /* Agent cards */
    QFrame#AgentCard {{
        background-color: {BG_GLASS_1};
        border: 1px solid {BORDER_GLASS};
        border-radius: 12px;
    }}
    QLabel#AgentTitle {{
        color: {PURPLE_HALO};
        font-size: 13px;
        font-weight: 700;
    }}
    QLabel#AgentMeta {{
        color: {SOFT};
        font-size: 11px;
    }}
    QLabel#StatusDot[state="online"] {{
        color: {GREEN_ACCENT};
        font-size: 16px;
    }}
    QLabel#StatusDot[state="busy"] {{
        color: {AMBER_ACCENT};
        font-size: 16px;
    }}
    QLabel#StatusDot[state="offline"] {{
        color: {DIM};
        font-size: 16px;
    }}

    /* Embedded terminal */
    QPlainTextEdit#Terminal {{
        background-color: {BLACK};
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

    QPushButton#PrimaryBtn {{
        background-color: {PURPLE_DEEP};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-weight: 600;
    }}
    QPushButton#PrimaryBtn:hover {{
        background-color: {PURPLE_ACCENT};
    }}
    QPushButton#GhostBtn {{
        background-color: transparent;
        color: {SOFT};
        border: 1px solid {BORDER_GLASS};
        border-radius: 6px;
        padding: 5px 12px;
    }}
    QPushButton#GhostBtn:hover {{
        color: {PURPLE_HALO};
        border: 1px solid {PURPLE_DEEP};
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

    /* Status counters */
    QLabel#StatusRowLabel {{
        color: {DIM};
        font-size: 10px;
        letter-spacing: 1px;
    }}
    QLabel#StatusRowValue {{
        color: {PURPLE_HALO};
        font-size: 13px;
        font-family: "{MONO_FONT}";
        font-weight: 600;
    }}

    /* Phone device card */
    QFrame#DeviceCard {{
        background-color: {BG_GLASS_1};
        border: 1px solid {BORDER_GLASS};
        border-radius: 8px;
        padding: 8px;
    }}
    QFrame#DeviceCard[selected="true"] {{
        border: 1px solid {PURPLE_ACCENT};
        background-color: {BG_GLOW};
    }}

    /* Workstation action cards */
    QPushButton#ActionCard {{
        background-color: {BG_GLASS_1};
        color: {LIGHT_PURPLE};
        border: 1px solid {BORDER_GLASS};
        border-radius: 12px;
        padding: 22px;
        text-align: left;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton#ActionCard:hover {{
        background-color: {BG_GLOW};
        border: 1px solid {PURPLE_ACCENT};
        color: {PURPLE_HALO};
    }}
    """
