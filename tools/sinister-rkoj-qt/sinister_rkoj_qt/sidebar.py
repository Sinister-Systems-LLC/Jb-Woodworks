# Author: RKOJ-ELENO :: 2026-05-21
"""220px left sidebar — Sinister Panel 1:1 port.

Layout per `projects/sinister-panel/source/.../components/sidebar.tsx`:
  - Banner block (mascot, no subtitle).
  - Three sections (DAILY / INSIGHTS / MANAGE) — each is a 12px uppercase
    label with a 1px hairline divider underneath, followed by nav-item rows.
  - Every nav-item: SVG glyph (Panel's NavGlyph viewBox 24×24) + label,
    8px gap, 12px h-padding, 10px border-radius. Active row gets the Panel
    purple-deep fill `#7A3DD4` with white text + 1px purple-accent border.

NO emoji. NO ASCII fallback. Every glyph is loaded from
`assets/panel-icons/*.svg` via `theme.nav_icon()`.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget  # type: ignore
    _HAS_SVG = True
except Exception:  # pragma: no cover
    _HAS_SVG = False

from .theme import SIDEBAR_WIDTH, asset_path, nav_icon


# Sinister Panel 3-section layout: DAILY (Workspace) / INSIGHTS / MANAGE.
# Each entry: (nav-key, label, svg-icon-name)
SECTIONS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("DAILY", [
        ("overview", "Overview", "nav-overview"),
        ("accounts", "Accounts", "nav-accounts"),
        ("command",  "Command Center", "nav-command-center"),
    ]),
    ("INSIGHTS", [
        ("analytics", "Analytics", "nav-analytics"),
        ("sales",     "Sales",     "nav-sales"),
        ("database",  "Database",  "nav-database"),
        ("sanctum",   "Sanctum",   "nav-sanctum"),
    ]),
    ("MANAGE", [
        ("fleet",    "Fleet",    "nav-fleet"),
        ("proxies",  "Proxies",  "nav-proxies"),
        ("browsers", "Browsers", "nav-browsers"),
        ("eve",      "EVE AI",   "nav-eve-ai"),
        ("admin",    "Admin",    "nav-admin"),
    ]),
]


# Mascot SVG bundled at `assets/mascot.svg`.
_MASCOT_SVG = asset_path("mascot.svg")


class _NavRow(QPushButton):
    """Single sidebar nav row — SVG icon (left) + label, both wrapped in
    a QPushButton. We render the icon as a child QSvgWidget rather than a
    QIcon so the SVG strokes scale cleanly at high DPI."""

    def __init__(self, key: str, label: str, icon_name: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("NavItem")
        self.setProperty("active", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._key = key
        self._build(label, icon_name)

    def _build(self, label: str, icon_name: str) -> None:
        # Use HBox over the button's content so the SVG widget lives inside.
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(10)

        if _HAS_SVG:
            self._icon_widget = nav_icon(icon_name, size=18)
            row.addWidget(self._icon_widget)
        else:  # pragma: no cover — Qt without QtSvg
            self._icon_widget = None

        self._label_widget = QLabel(label)
        self._label_widget.setObjectName("NavItemLabel")
        self._label_widget.setStyleSheet("color: inherit; background: transparent;")
        row.addWidget(self._label_widget, stretch=1)
        # The button itself handles the click; we leave its text empty
        # (text would render on top of the layout otherwise).
        self.setText("")

    @property
    def nav_key(self) -> str:
        return self._key


class Sidebar(QWidget):
    """Left vertical sidebar — fixed 220px width (Panel SIDEBAR_WIDTH=240
    minus our denser 13px font)."""

    nav_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._active_nav: str = "sanctum"
        self._nav_rows: dict[str, _NavRow] = {}
        self._build()
        self._update_active(self._active_nav)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Mascot block (no subtitle — Panel banner has no label) ──────
        mascot_frame = QFrame(self)
        mascot_frame.setObjectName("MascotFrame")
        mascot_frame.setFixedHeight(96)  # Panel HEADER_HEIGHT
        mascot_layout = QVBoxLayout(mascot_frame)
        mascot_layout.setContentsMargins(0, 0, 0, 0)
        mascot_layout.setSpacing(0)
        mascot_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if _HAS_SVG and _MASCOT_SVG.exists():
            svg = QSvgWidget(str(_MASCOT_SVG))
            svg.setFixedSize(64, 64)
            mascot_layout.addWidget(svg, alignment=Qt.AlignmentFlag.AlignCenter)
        # No fallback — if SVG is missing the block just stays blank.

        root.addWidget(mascot_frame)

        # ── Scrollable nav (DAILY / INSIGHTS / MANAGE) ──────────────────
        nav_scroll = QScrollArea(self)
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        nav_host = QWidget()
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(0, 12, 0, 12)
        nav_layout.setSpacing(0)

        for section_label, items in SECTIONS:
            sec = QLabel(section_label)
            sec.setObjectName("SidebarSection")
            nav_layout.addWidget(sec)
            for key, label, icon_name in items:
                row = _NavRow(key, label, icon_name)
                row.clicked.connect(lambda _checked=False, k=key: self._on_nav_clicked(k))
                self._nav_rows[key] = row
                nav_layout.addWidget(row)
            # Spacer between sections (Panel uses mt-5 on subsequent sections)
            nav_layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        nav_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        nav_scroll.setWidget(nav_host)
        root.addWidget(nav_scroll, stretch=1)

    def _on_nav_clicked(self, key: str) -> None:
        self._update_active(key)
        self.nav_clicked.emit(key)

    def _update_active(self, key: str) -> None:
        self._active_nav = key
        for k, row in self._nav_rows.items():
            is_active = (k == key)
            row.setProperty("active", is_active)
            row.style().unpolish(row)
            row.style().polish(row)
