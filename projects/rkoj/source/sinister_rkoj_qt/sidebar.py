# Author: RKOJ-ELENO :: 2026-05-21
"""220px left sidebar — operator-canonical 2-tab layout (Agents + Devices).

Operator 2026-05-21 (verbatim): *"WHY THE FUCK do i not just have 2 fucking tabs.
where the fuck is the agents and devices tab on side bar."*

Layout:
  - Mascot block at top (no subtitle, no "EVE" label — Panel doesn't have one).
  - Two nav-items only: Agents + Devices. NO sections, NO 12-item nav.
  - Active row gets Panel purple-deep fill `#7A3DD4` with white text.

Every glyph is loaded from `assets/panel-icons/*.svg` via `theme.nav_icon()`.
NO emoji. NO ASCII fallback.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget  # type: ignore
    _HAS_SVG = True
except Exception:  # pragma: no cover
    _HAS_SVG = False

from .theme import SIDEBAR_WIDTH, asset_path, nav_icon


# Operator-canonical 2-tab layout. (nav-key, label, svg-icon-name)
NAV_ITEMS: list[tuple[str, str, str]] = [
    ("agents",  "Agents",  "nav-eve-ai"),
    ("devices", "Devices", "nav-phones"),
]


# Mascot SVG bundled at `assets/mascot.svg`.
_MASCOT_SVG = asset_path("mascot.svg")


class _NavRow(QPushButton):
    """Single sidebar nav row — SVG icon (left) + label."""

    def __init__(self, key: str, label: str, icon_name: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("NavItem")
        self.setProperty("active", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._key = key
        self._build(label, icon_name)

    def _build(self, label: str, icon_name: str) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)

        if _HAS_SVG:
            self._icon_widget = nav_icon(icon_name, size=20)
            row.addWidget(self._icon_widget)
        else:  # pragma: no cover — Qt without QtSvg
            self._icon_widget = None

        self._label_widget = QLabel(label)
        self._label_widget.setObjectName("NavItemLabel")
        self._label_widget.setStyleSheet("color: inherit; background: transparent;")
        row.addWidget(self._label_widget, stretch=1)
        # Empty button text — label widget owns the rendering.
        self.setText("")

    @property
    def nav_key(self) -> str:
        return self._key


class Sidebar(QWidget):
    """Left vertical sidebar — 2 nav items only (Agents / Devices)."""

    nav_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._active_nav: str = "agents"
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

        # ── 2 nav items (no sections, no scrolling — fits in fixed height) ──
        nav_host = QFrame(self)
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(6)

        for key, label, icon_name in NAV_ITEMS:
            row = _NavRow(key, label, icon_name)
            row.clicked.connect(lambda _checked=False, k=key: self._on_nav_clicked(k))
            self._nav_rows[key] = row
            nav_layout.addWidget(row)

        nav_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )
        root.addWidget(nav_host, stretch=1)

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
