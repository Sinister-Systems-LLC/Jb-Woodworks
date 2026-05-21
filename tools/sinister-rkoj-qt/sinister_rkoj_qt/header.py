# Author: RKOJ-ELENO :: 2026-05-21
"""96px header bar — title + chip tabs + action icons + draggable for window move."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)

from .theme import HEADER_HEIGHT


CHIPS: list[tuple[str, str, str]] = [
    ("agents", "Agents", "●"),
    ("phones", "Phones", "#"),
    ("workstation", "Workstation", "⚙"),
]


class Header(QWidget):
    """Top-row header — also handles frameless window dragging."""

    chip_clicked = pyqtSignal(str)
    icon_clicked = pyqtSignal(str)  # icon key: alerts/inbox/palette/settings/health

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Header")
        self.setFixedHeight(HEADER_HEIGHT)
        self._active_chip = "agents"
        self._chip_buttons: dict[str, QPushButton] = {}
        self._drag_origin: Optional[QPoint] = None
        self._build()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start(1000)
        self._tick_clock()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        root.setSpacing(14)

        # Title block
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("Sinister")
        title.setObjectName("HeaderTitle")
        sub = QLabel("Sanctum  ·  RKOJ.exe  ·  EVE")
        sub.setStyleSheet("color: #999AB0; font-size: 11px; letter-spacing: 1.5px;")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        root.addLayout(title_col)

        # Chip tabs
        chips_row = QHBoxLayout()
        chips_row.setSpacing(8)
        chips_row.setContentsMargins(16, 0, 0, 0)
        for key, label, glyph in CHIPS:
            btn = QPushButton(f"{glyph}  {label}")
            btn.setObjectName("HeaderChip")
            btn.setProperty("active", key == self._active_chip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, k=key: self._on_chip(k))
            self._chip_buttons[key] = btn
            chips_row.addWidget(btn)
        root.addLayout(chips_row)

        root.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Action icons
        actions_row = QHBoxLayout()
        actions_row.setSpacing(4)
        for key, glyph, tip in [
            ("alerts", "!", "Alerts"),
            ("inbox", "⏰", "Inbox"),
            ("palette", "⌕", "Command palette (Ctrl+K)"),
            ("settings", "⚙", "Settings"),
        ]:
            ib = QPushButton(glyph)
            ib.setObjectName("HeaderIcon")
            ib.setToolTip(tip)
            ib.setCursor(Qt.CursorShape.PointingHandCursor)
            ib.clicked.connect(lambda _checked=False, k=key: self.icon_clicked.emit(k))
            actions_row.addWidget(ib)
        root.addLayout(actions_row)

        # Health pill
        self.health_pill = QLabel("● online")
        self.health_pill.setObjectName("HealthPill")
        root.addWidget(self.health_pill)

        # Clock
        self.clock_label = QLabel("00:00")
        self.clock_label.setObjectName("Clock")
        root.addWidget(self.clock_label)

    # ── Drag-to-move (frameless support) ────────────────────────────
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win is not None:
                self._drag_origin = event.globalPosition().toPoint() - win.frameGeometry().topLeft()
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

    # ── State ──────────────────────────────────────────────────────
    def set_active_chip(self, key: str) -> None:
        self._active_chip = key
        for k, btn in self._chip_buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_chip(self, key: str) -> None:
        self.set_active_chip(key)
        self.chip_clicked.emit(key)

    def _tick_clock(self) -> None:
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))
