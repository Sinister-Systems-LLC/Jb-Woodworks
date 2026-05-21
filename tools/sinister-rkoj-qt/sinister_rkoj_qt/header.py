# Author: RKOJ-ELENO :: 2026-05-21
"""Two-row header bar — 1:1 port of Sinister Panel's tab-header.tsx.

Row 1 = Sheets-style menu strip (File / Edit / View / Agent / Tools / Help) +
        window controls (custom SVG glyphs). Also the frameless-drag handle.

Row 2 = page title (Panel `text-[26px] font-bold tracking-tight`) + chip-tabs
        (Agents / Devices, pill 32px tall) + Panel round-icon action cluster
        (bell / chat / clock / settings) + Create Agent solid-purple button +
        health pill + live clock.

EVERY glyph is a QSvgWidget loaded from `assets/panel-icons/*.svg`. NO emoji.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget  # type: ignore
    _HAS_SVG = True
except Exception:  # pragma: no cover
    _HAS_SVG = False

from .theme import (
    HEADER_ROW1_HEIGHT, HEADER_ROW2_HEIGHT, nav_icon,
)


# Chip tabs — operator-canonical 2026-05-21: ONLY Agents + Devices.
# Each: (key, label, icon-name)
CHIPS: list[tuple[str, str, str]] = [
    ("agents",  "Agents",  "nav-accounts"),
    ("devices", "Devices", "nav-phones"),
]

# Menu strip definitions — each is (top-label, [(item-label, enabled)]).
MENUS: list[tuple[str, list[tuple[str, bool]]]] = [
    ("File", [
        ("New Agent", True),
        ("Open Project", False),
        ("Save Resume Point", False),
        ("Exit", True),
    ]),
    ("Edit", [
        ("Undo", False),
        ("Redo", False),
        ("Find...", False),
    ]),
    ("View", [
        ("Toggle Sidebar", True),
        ("Zoom In", False),
        ("Zoom Out", False),
    ]),
    ("Agent", [
        ("Spawn EVE", True),
        ("Resume Last", False),
        ("Terminate All", True),
    ]),
    ("Tools", [
        ("Open MCP Config", False),
        ("Sinister Watchdog", False),
        ("Vault Status", False),
    ]),
    ("Help", [
        ("About RKOJ", True),
        ("Operator Docs", False),
    ]),
]

# Round action icons in row 2 — (key, icon-name, tooltip)
HEADER_ACTIONS: list[tuple[str, str, str]] = [
    ("alerts",   "header-alert",    "Alerts"),
    ("inbox",    "header-clock",    "Inbox"),
    ("search",   "header-search",   "Search (Ctrl+K)"),
    ("settings", "header-settings", "Settings"),
]


class MenuStripRow(QWidget):
    """Header row 1 — Sheets-style menu strip + window controls.

    Frameless-drag is implemented HERE (operator brief: drag only on row 1).
    """

    menu_action = pyqtSignal(str)  # "menu.item" e.g. "Agent.Spawn EVE"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HeaderRow1")
        self.setFixedHeight(HEADER_ROW1_HEIGHT)
        self._drag_origin: Optional[QPoint] = None
        self._build()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 4, 0)
        root.setSpacing(0)

        # Brand tag (left)
        brand = QLabel("EVE")
        brand.setObjectName("MenuMascot")
        root.addWidget(brand)

        # Menu items (text-only, no emoji prefixes per operator brief)
        for top_label, items in MENUS:
            btn = QPushButton(top_label)
            btn.setObjectName("MenuItem")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, lbl=top_label, its=items, b=btn:
                                self._show_menu(b, lbl, its))
            root.addWidget(btn)

        root.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Window controls — custom SVG glyphs (no emoji / no unicode boxes)
        self.btn_min = self._make_win_button("win-min", "Minimize")
        self.btn_max = self._make_win_button("win-max", "Maximize")
        self.btn_close = self._make_win_button("win-close", "Close")
        self.btn_close.setObjectName("WinCtlClose")
        root.addWidget(self.btn_min)
        root.addWidget(self.btn_max)
        root.addWidget(self.btn_close)

    def _make_win_button(self, icon_name: str, tip: str) -> QPushButton:
        b = QPushButton()
        b.setObjectName("WinCtl")
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setToolTip(tip)
        b.setFixedSize(QSize(32, HEADER_ROW1_HEIGHT - 4))
        if _HAS_SVG:
            layout = QHBoxLayout(b)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            svg = nav_icon(icon_name, size=14)
            layout.addWidget(svg)
        else:  # pragma: no cover
            b.setText({"win-min": "-", "win-max": "[]", "win-close": "x"}.get(icon_name, ""))
        return b

    def _show_menu(self, anchor: QPushButton, top_label: str, items: list[tuple[str, bool]]) -> None:
        m = QMenu(self)
        for label, enabled in items:
            act = QAction(label, m)
            act.setEnabled(enabled)
            act.triggered.connect(lambda _checked=False, l=label, tl=top_label:
                                  self.menu_action.emit(f"{tl}.{l}"))
            m.addAction(act)
        m.addSeparator()
        coming = QAction("(coming soon)", m)
        coming.setEnabled(False)
        m.addAction(coming)
        global_pos = anchor.mapToGlobal(QPoint(0, anchor.height()))
        m.exec(global_pos)

    # ── Drag-to-move (frameless support — ONLY on row 1) ─────────────
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win is not None:
                self._drag_origin = (
                    event.globalPosition().toPoint() - win.frameGeometry().topLeft()
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            if win is not None:
                win.move(event.globalPosition().toPoint() - self._drag_origin)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_origin = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win is not None:
                if win.isMaximized():
                    win.showNormal()
                else:
                    win.showMaximized()
                event.accept()
                return
        super().mouseDoubleClickEvent(event)


class _ChipTabButton(QPushButton):
    """Chip pill = SVG icon + label inside a styled QPushButton."""

    def __init__(self, key: str, label: str, icon_name: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ChipTab")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._key = key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(7)
        if _HAS_SVG:
            self._icon_widget = nav_icon(icon_name, size=14)
            layout.addWidget(self._icon_widget)
        self._label = QLabel(label)
        self._label.setStyleSheet("color: inherit; background: transparent; font-weight: 600;")
        layout.addWidget(self._label)
        self.setText("")

    @property
    def key(self) -> str:
        return self._key


class _IconButton(QPushButton):
    """Header round action button — 32x32 with centered SVG glyph."""

    def __init__(self, key: str, icon_name: str, tip: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HeaderIcon")
        self.setToolTip(tip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._key = key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if _HAS_SVG:
            self._icon_widget = nav_icon(icon_name, size=15)
            layout.addWidget(self._icon_widget)
        self.setText("")

    @property
    def key(self) -> str:
        return self._key


class _CreateAgentButton(QPushButton):
    """+ Create Agent — plus glyph + label."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CreateAgentBtn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(6)
        if _HAS_SVG:
            plus_svg = nav_icon("plus", size=12)
            layout.addWidget(plus_svg)
        lbl = QLabel("Create Agent")
        lbl.setStyleSheet("color: white; background: transparent; font-weight: 600; font-size: 13px;")
        layout.addWidget(lbl)
        self.setText("")


class ActionsRow(QWidget):
    """Header row 2 — page title + chip tabs + actions + Create Agent + clock."""

    chip_clicked = pyqtSignal(str)
    icon_clicked = pyqtSignal(str)
    create_agent_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("HeaderRow2")
        self.setFixedHeight(HEADER_ROW2_HEIGHT)
        self._active_chip = "agents"
        self._chip_buttons: dict[str, _ChipTabButton] = {}
        self._build()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(28, 12, 16, 12)
        root.setSpacing(12)

        # Page title (left) — Panel `text-[26px] font-bold tracking-tight`
        self.page_title = QLabel("Agents")
        self.page_title.setObjectName("PageTitle")
        root.addWidget(self.page_title)

        # Chip tabs (middle)
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        chips_row.setContentsMargins(20, 0, 0, 0)
        for key, label, icon_name in CHIPS:
            btn = _ChipTabButton(key, label, icon_name)
            btn.setProperty("active", key == self._active_chip)
            btn.clicked.connect(lambda _checked=False, k=key: self._on_chip(k))
            self._chip_buttons[key] = btn
            chips_row.addWidget(btn)
        root.addLayout(chips_row)

        root.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Round icon cluster (right) — all SVG, no emoji
        for key, icon_name, tip in HEADER_ACTIONS:
            ib = _IconButton(key, icon_name, tip)
            ib.clicked.connect(lambda _checked=False, k=key: self.icon_clicked.emit(k))
            root.addWidget(ib)

        # Create Agent button (purple solid)
        self.create_btn = _CreateAgentButton()
        self.create_btn.clicked.connect(self.create_agent_clicked.emit)
        root.addWidget(self.create_btn)

        # Health pill (small green dot + text — dot is also SVG)
        health_wrap = QFrame()
        health_wrap.setObjectName("HealthPillFrame")
        health_layout = QHBoxLayout(health_wrap)
        health_layout.setContentsMargins(8, 3, 10, 3)
        health_layout.setSpacing(5)
        if _HAS_SVG:
            health_layout.addWidget(nav_icon("dot-online", size=10))
        self.health_pill = QLabel("online")
        self.health_pill.setObjectName("HealthPill")
        self.health_pill.setStyleSheet(
            "color: #30D158; background: transparent; border: none; padding: 0; "
            "font-size: 11px; font-weight: 600;"
        )
        health_layout.addWidget(self.health_pill)
        health_wrap.setStyleSheet(
            "QFrame#HealthPillFrame {"
            "  background: #15131A; border: 1px solid #2c2c2e; border-radius: 12px;"
            "}"
        )
        root.addWidget(health_wrap)

        # Clock
        self.clock_label = QLabel("00:00:00")
        self.clock_label.setObjectName("Clock")
        root.addWidget(self.clock_label)

    def set_active_chip(self, key: str) -> None:
        self._active_chip = key
        for k, btn in self._chip_buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.page_title.setText(
            "Agents" if key == "agents" else "Devices" if key == "devices" else key.capitalize()
        )

    def _on_chip(self, key: str) -> None:
        self.set_active_chip(key)
        self.chip_clicked.emit(key)

    def _tick_clock(self) -> None:
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))


class Header(QWidget):
    """Compound header — row 1 (menu strip) on top of row 2 (chip-tabs + actions)."""

    chip_clicked = pyqtSignal(str)
    icon_clicked = pyqtSignal(str)
    create_agent_clicked = pyqtSignal()
    menu_action = pyqtSignal(str)
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Header")
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.row1 = MenuStripRow(self)
        self.row2 = ActionsRow(self)
        root.addWidget(self.row1)
        root.addWidget(self.row2)

        # Re-emit row signals at compound level
        self.row1.menu_action.connect(self.menu_action.emit)
        self.row1.btn_min.clicked.connect(self.minimize_clicked.emit)
        self.row1.btn_max.clicked.connect(self.maximize_clicked.emit)
        self.row1.btn_close.clicked.connect(self.close_clicked.emit)

        self.row2.chip_clicked.connect(self.chip_clicked.emit)
        self.row2.icon_clicked.connect(self.icon_clicked.emit)
        self.row2.create_agent_clicked.connect(self.create_agent_clicked.emit)

    def set_active_chip(self, key: str) -> None:
        self.row2.set_active_chip(key)
