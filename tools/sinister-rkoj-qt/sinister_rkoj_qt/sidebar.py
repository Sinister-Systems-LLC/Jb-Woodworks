# Author: RKOJ-ELENO :: 2026-05-21
"""200px left sidebar — mascot block + DAILY / INSIGHTS / MANAGE sections.

Matches Sinister Panel image 13 layout (mascot tile up top, three label-cap
sections beneath). Click-only nav (no content swap yet — placeholder per
operator brief).
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget  # type: ignore
    _HAS_SVG = True
except Exception:  # pragma: no cover — fall back to ASCII devil
    _HAS_SVG = False

from .theme import SIDEBAR_WIDTH


# Sinister Panel 3-section layout — DAILY / INSIGHTS / MANAGE.
SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    ("DAILY", [
        ("overview", "Overview"),
        ("accounts", "Accounts"),
        ("command", "Command Center"),
    ]),
    ("INSIGHTS", [
        ("analytics", "Analytics"),
        ("sales", "Sales"),
        ("database", "Database"),
        ("sanctum", "Sanctum"),
    ]),
    ("MANAGE", [
        ("fleet", "Fleet"),
        ("proxies", "Proxies"),
        ("browsers", "Browsers"),
        ("eve", "EVE AI"),
        ("admin", "Admin"),
    ]),
]

# Skull SVG (Sanctum mascot) — bundled with window-manager web assets.
_SKULL_SVG = Path(r"D:\Sinister Sanctum\automations\window-manager\web\skull.svg")

# ASCII fallback if SVG won't load.
_MASCOT_ASCII = (
    "  /\\_/\\  \n"
    " ( o.o ) \n"
    "  > ^ <  "
)


class Sidebar(QWidget):
    """Left vertical sidebar — fixed 200px width per operator brief."""

    nav_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._active_nav: str = "overview"
        self._nav_buttons: dict[str, QPushButton] = {}
        self._build()
        self._update_active(self._active_nav)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Mascot block ────────────────────────────────────────────────
        mascot_frame = QFrame(self)
        mascot_frame.setObjectName("MascotFrame")
        mascot_frame.setFixedHeight(140)
        mascot_layout = QVBoxLayout(mascot_frame)
        mascot_layout.setContentsMargins(12, 14, 12, 10)
        mascot_layout.setSpacing(4)
        mascot_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if _HAS_SVG and _SKULL_SVG.exists():
            svg = QSvgWidget(str(_SKULL_SVG))
            svg.setFixedSize(72, 72)
            mascot_layout.addWidget(svg, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            mascot = QLabel(_MASCOT_ASCII)
            mascot.setObjectName("Mascot")
            mascot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mono = QFont("Cascadia Mono")
            mono.setStyleHint(QFont.StyleHint.Monospace)
            mascot.setFont(mono)
            mascot_layout.addWidget(mascot)

        eve_label = QLabel("E V E")
        eve_label.setObjectName("EveLabel")
        eve_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mascot_layout.addWidget(eve_label)

        root.addWidget(mascot_frame)

        # ── Scrollable nav (DAILY / INSIGHTS / MANAGE) ──────────────────
        nav_scroll = QScrollArea(self)
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        nav_host = QWidget()
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(0, 4, 0, 12)
        nav_layout.setSpacing(0)

        for section_label, items in SECTIONS:
            sec = QLabel(section_label)
            sec.setObjectName("SidebarSection")
            nav_layout.addWidget(sec)
            for key, label in items:
                btn = QPushButton(label)
                btn.setObjectName("NavItem")
                btn.setProperty("active", False)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _checked=False, k=key: self._on_nav_clicked(k))
                self._nav_buttons[key] = btn
                nav_layout.addWidget(btn)

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
        for k, btn in self._nav_buttons.items():
            is_active = (k == key)
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
