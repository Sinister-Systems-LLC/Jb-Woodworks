# Author: RKOJ-ELENO :: 2026-05-21
"""Two-row header bar.

Row 1 = Sheets-style menu strip (File / Edit / View / Agent / Tools / Help) +
        window controls (min / max / close). This row also serves as the
        frameless-drag handle.

Row 2 = page title + chip-tabs (Agents / Devices) + icon cluster + Create
        Agent button + health pill + clock.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QMouseEvent
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget,
)

from .theme import HEADER_ROW1_HEIGHT, HEADER_ROW2_HEIGHT


# Chip tabs — operator-canonical 2026-05-21: ONLY Agents + Devices.
CHIPS: list[tuple[str, str, str]] = [
    ("agents", "Agents", "●"),
    ("devices", "Devices", "#"),
]

# Menu strip definitions — each is (top-label, [(item-label, enabled)]).
# All items are placeholder; one "(coming soon)" footer at the bottom.
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

        # Mascot / brand tag (left)
        brand = QLabel("EVE")
        brand.setObjectName("MenuMascot")
        root.addWidget(brand)

        # Menu items
        for top_label, items in MENUS:
            btn = QPushButton(top_label)
            btn.setObjectName("MenuItem")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, lbl=top_label, its=items, b=btn:
                                self._show_menu(b, lbl, its))
            root.addWidget(btn)

        root.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Win controls
        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")
        for b in (self.btn_min, self.btn_max, self.btn_close):
            b.setObjectName("WinCtl")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setObjectName("WinCtlClose")
        root.addWidget(self.btn_min)
        root.addWidget(self.btn_max)
        root.addWidget(self.btn_close)

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
        # Double-click toggles maximize (matches Windows convention)
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
        self._chip_buttons: dict[str, QPushButton] = {}
        self._build()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 8, 16, 8)
        root.setSpacing(12)

        # Page title (left)
        self.page_title = QLabel("Agents")
        self.page_title.setObjectName("PageTitle")
        root.addWidget(self.page_title)

        # Chip tabs (middle)
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        chips_row.setContentsMargins(20, 0, 0, 0)
        for key, label, glyph in CHIPS:
            btn = QPushButton(f"{glyph}  {label}")
            btn.setObjectName("ChipTab")
            btn.setProperty("active", key == self._active_chip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, k=key: self._on_chip(k))
            self._chip_buttons[key] = btn
            chips_row.addWidget(btn)
        root.addLayout(chips_row)

        root.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Round icon cluster (right)
        for key, glyph, tip in [
            ("alerts", "!", "Alerts"),
            ("inbox", "⏰", "Inbox"),
            ("search", "🔍", "Search (Ctrl+K)"),
            ("settings", "⚙", "Settings"),
        ]:
            ib = QPushButton(glyph)
            ib.setObjectName("HeaderIcon")
            ib.setToolTip(tip)
            ib.setCursor(Qt.CursorShape.PointingHandCursor)
            ib.clicked.connect(lambda _checked=False, k=key: self.icon_clicked.emit(k))
            root.addWidget(ib)

        # Create Agent button
        self.create_btn = QPushButton("+ Create Agent")
        self.create_btn.setObjectName("CreateAgentBtn")
        self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.create_btn.clicked.connect(self.create_agent_clicked.emit)
        root.addWidget(self.create_btn)

        # Health pill
        self.health_pill = QLabel("● online")
        self.health_pill.setObjectName("HealthPill")
        root.addWidget(self.health_pill)

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
