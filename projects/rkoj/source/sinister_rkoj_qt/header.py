# Author: RKOJ-ELENO :: 2026-05-21
"""Single-row 96px header — 1:1 port of Sinister Panel's tab-header.tsx.

Panel has ONE header row, not two. Layout (28px horizontal padding):

    ┌───────────────────────────────────────────────────────────────────┐
    │  Agents (purple glow)  · Agents ●  Devices #   [icons][+ Create]  │
    │                                                       [pill] X    │
    └───────────────────────────────────────────────────────────────────┘

Total height 96px. Bottom border = `rgba(#BF5AF2, 0.45)` (workspace tint).
Background = `qradialgradient` from top-left at 6% tint over `#0a0a0c`.

X button lives top-right (frameless app must own its own close). Drag-to-move
is wired on the whole header (anywhere not on a clickable child).

Title h1 = `text-[26px] font-bold tracking-tight` with `text-shadow: 0 0 14px
rgba(#BF5AF2, 0.35)` — implemented via QGraphicsDropShadowEffect.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QWidget,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget  # type: ignore
    _HAS_SVG = True
except Exception:  # pragma: no cover
    _HAS_SVG = False

from .theme import HEADER_HEIGHT, PURPLE_PRIMARY, nav_icon


# v1.6.72 — operator-canonical: per-section chip sets. Sidebar nav drives
# which set is shown. "agents" view → Agents + Resume chips; "devices"
# view → no chips (Devices header is enough).
CHIP_SETS: dict[str, list[tuple[str, str]]] = {
    "agents":  [("agents", "Agents"), ("resume", "Resume")],
    "devices": [],
}
# Legacy alias kept so older callers don't break during the transition.
CHIPS: list[tuple[str, str]] = CHIP_SETS["agents"]

# v1.6.72 — operator removed the 4 header action icons (alerts, clock,
# search, settings). Only the Create button + health pill + clock +
# minimize + close remain.
HEADER_ACTIONS: list[tuple[str, str, str]] = []


class _ChipTabButton(QPushButton):
    """Panel pill chip — `h-7 px-2.5 text-[11.5px] rounded-full`."""

    def __init__(self, key: str, label: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.setObjectName("ChipTab")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._key = key

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
        self.setFixedSize(QSize(32, 32))
        self._key = key
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if _HAS_SVG:
            layout.addWidget(nav_icon(icon_name, size=15))

    @property
    def key(self) -> str:
        return self._key


class _CreateAgentButton(QPushButton):
    """Panel primary button — `h-8 px-3 text-[12px] rounded-[7px]` + glow."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CreateAgentBtn")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 12, 0)
        layout.setSpacing(6)
        if _HAS_SVG:
            layout.addWidget(nav_icon("plus", size=12))
        lbl = QLabel("Create Agent")
        lbl.setStyleSheet("color: white; background: transparent; "
                          "font-weight: 600; font-size: 12px;")
        layout.addWidget(lbl)
        self.setText("")


class Header(QWidget):
    """Single 96px Panel TabHeader — title + chip tabs + actions + close.

    The whole bar is the frameless-drag region (mouse-press anywhere except
    on a clickable child starts a window-drag).
    """

    chip_clicked = pyqtSignal(str)
    icon_clicked = pyqtSignal(str)
    create_agent_clicked = pyqtSignal()
    menu_action = pyqtSignal(str)            # kept for app.py backward compat
    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Header")
        self.setFixedHeight(HEADER_HEIGHT)
        self._active_chip = "agents"
        self._chip_buttons: dict[str, _ChipTabButton] = {}
        self._drag_origin: Optional[QPoint] = None
        self._build()
        # Live clock tick
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(28, 0, 16, 0)
        root.setSpacing(24)

        # ── Left cluster: page title + chip tabs ─────────────────────
        left_cluster = QHBoxLayout()
        left_cluster.setSpacing(24)

        self.page_title = QLabel("Agents")
        self.page_title.setObjectName("PageTitle")
        # Panel title glow — text-shadow: 0 0 14px rgba(#BF5AF2, 0.35)
        glow = QGraphicsDropShadowEffect(self.page_title)
        glow.setBlurRadius(14)
        c = QColor(PURPLE_PRIMARY)
        c.setAlpha(90)
        glow.setColor(c)
        glow.setOffset(0, 0)
        self.page_title.setGraphicsEffect(glow)
        left_cluster.addWidget(self.page_title)

        # v1.6.72 — chip row is rebuilt by set_chip_set() when sidebar
        # nav changes. Default is the "agents" set (Agents + Resume).
        self._chips_host = QFrame()
        self._chips_row = QHBoxLayout(self._chips_host)
        self._chips_row.setContentsMargins(0, 0, 0, 0)
        self._chips_row.setSpacing(4)
        left_cluster.addWidget(self._chips_host)
        root.addLayout(left_cluster)
        self.set_chip_set("agents")

        # ── Stretch eats the middle ──────────────────────────────────
        root.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding,
                                 QSizePolicy.Policy.Minimum))

        # ── Right cluster: actions + Create + clock + close ──────────
        right = QHBoxLayout()
        right.setSpacing(8)

        for key, icon_name, tip in HEADER_ACTIONS:
            ib = _IconButton(key, icon_name, tip)
            ib.clicked.connect(lambda _checked=False, k=key: self.icon_clicked.emit(k))
            right.addWidget(ib)

        self.create_btn = _CreateAgentButton()
        self.create_btn.clicked.connect(self.create_agent_clicked.emit)
        right.addWidget(self.create_btn)

        # Health pill — green dot + "online"
        health_wrap = QFrame()
        health_wrap.setObjectName("HealthPillFrame")
        health_layout = QHBoxLayout(health_wrap)
        health_layout.setContentsMargins(8, 3, 10, 3)
        health_layout.setSpacing(5)
        if _HAS_SVG:
            health_layout.addWidget(nav_icon("dot-online", size=10))
        self.health_pill = QLabel("online")
        self.health_pill.setObjectName("HealthPill")
        health_layout.addWidget(self.health_pill)
        right.addWidget(health_wrap)

        # Live mono clock
        self.clock_label = QLabel("00:00:00")
        self.clock_label.setObjectName("Clock")
        right.addWidget(self.clock_label)

        # v1.6.72 — operator wants minimize button beside the X.
        # We don't have a "win-minimize" SVG glyph in the asset pack;
        # fall back to a unicode underscore character on a styled button.
        self.btn_minimize = QPushButton("─")
        self.btn_minimize.setObjectName("WinCtlMin")
        self.btn_minimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_minimize.setFixedSize(32, 32)
        self.btn_minimize.setToolTip("Minimize")
        self.btn_minimize.setStyleSheet(
            "QPushButton#WinCtlMin {"
            "  color: #8e8e93; background: transparent; border: none;"
            "  font-size: 18px; font-weight: 700;"
            "}"
            "QPushButton#WinCtlMin:hover { color: white; "
            "background-color: rgba(255,255,255,0.06); border-radius: 6px; }"
        )
        self.btn_minimize.clicked.connect(self.minimize_clicked.emit)
        right.addWidget(self.btn_minimize)

        # Frameless X button (Panel is a browser app; we need our own)
        self.btn_close = _IconButton("close", "win-close", "Close")
        self.btn_close.setObjectName("WinCtlClose")
        self.btn_close.clicked.connect(self.close_clicked.emit)
        right.addWidget(self.btn_close)

        root.addLayout(right)

    def set_chip_set(self, section: str) -> None:
        """v1.6.72 — rebuild chip-tabs row based on sidebar section.
        section ∈ {agents, devices}. Empty chip set hides the row."""
        # Clear existing
        while self._chips_row.count():
            item = self._chips_row.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._chip_buttons.clear()
        chips = CHIP_SETS.get(section, [])
        if not chips:
            self._chips_host.hide()
            return
        self._chips_host.show()
        # Reset active if it's not in the new set
        new_keys = [k for k, _ in chips]
        if self._active_chip not in new_keys:
            self._active_chip = new_keys[0]
        for key, label in chips:
            btn = _ChipTabButton(key, label)
            btn.setProperty("active", key == self._active_chip)
            btn.clicked.connect(lambda _checked=False, k=key: self._on_chip(k))
            self._chip_buttons[key] = btn
            self._chips_row.addWidget(btn)

    def set_active_chip(self, key: str) -> None:
        self._active_chip = key
        for k, btn in self._chip_buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        # v1.6.72 — page title swap covers new "resume" key too
        titles = {"agents": "Agents", "devices": "Devices",
                  "resume": "Resume — saved sessions"}
        self.page_title.setText(titles.get(key, key.capitalize()))

    def _on_chip(self, key: str) -> None:
        self.set_active_chip(key)
        self.chip_clicked.emit(key)

    def _tick_clock(self) -> None:
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))

    # ── Frameless-drag handle (whole header surface) ───────────────────
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
