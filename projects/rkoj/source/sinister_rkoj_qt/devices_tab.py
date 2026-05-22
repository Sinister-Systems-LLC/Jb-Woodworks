# Author: RKOJ-ELENO :: 2026-05-21
"""Devices tab — live ADB device list (read-only).

v1.6.4 — operator wants to see all connected ADB phones from the Devices tab.
Background poll every 4 seconds. Per-device row shows:
  ● status dot · serial · model · state · transport

Future (NOT in this milestone — per `forward-plan.md § C.1`):
  - scrcpy embed per device (MJPEG in-tab stream)
  - per-device logcat tail strip
  - adb shell input box
  - RKA armed/disarmed indicator
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from . import state
from .theme import (
    BORDER, ELEVATED, MUTED_FG, PURPLE_PRIMARY, SUCCESS, WARNING,
)


_STATE_COLOR: dict[str, str] = {
    "device": SUCCESS,
    "offline": MUTED_FG,
    "unauthorized": WARNING,
}


class _DeviceRow(QFrame):
    """Single device row — status dot + serial + model + state + transport."""

    def __init__(self, dev: state.Device, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DeviceRow")
        self.setStyleSheet(
            f"QFrame#DeviceRow {{"
            f"  background-color: {ELEVATED};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: 10px;"
            f"  padding: 0;"
            f"}}"
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(14)

        # Status dot
        dot = QLabel()
        dot.setFixedSize(10, 10)
        color = _STATE_COLOR.get(dev.state, MUTED_FG)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        row.addWidget(dot)

        # Serial (mono)
        serial = QLabel(dev.serial)
        serial.setStyleSheet(
            "color: white; background: transparent; "
            "font-family: 'JetBrains Mono', 'Cascadia Mono', monospace; "
            "font-size: 12px; font-weight: 600;"
        )
        row.addWidget(serial)

        # Model
        model = QLabel(dev.model or "(unknown)")
        model.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; font-size: 12px;"
        )
        row.addWidget(model)

        row.addStretch(1)

        # State pill
        state_pill = QLabel(dev.state)
        state_pill.setStyleSheet(
            f"color: {color}; background: transparent; "
            f"font-size: 11px; font-weight: 600; text-transform: uppercase;"
            f"letter-spacing: 0.5px;"
        )
        row.addWidget(state_pill)

        # Transport tag
        transport = QLabel(dev.transport.upper())
        transport.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 10px; padding: 2px 8px; "
            f"border: 1px solid {BORDER}; border-radius: 8px;"
        )
        row.addWidget(transport)


class DevicesView(QWidget):
    """ADB devices list + auto-refresh.

    No actions yet — read-only inventory. Operator can SEE every connected
    phone + its state at a glance. Actions (scrcpy / shell / logcat) land
    in a follow-up milestone per `forward-plan.md § C.1`.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device_rows: list[_DeviceRow] = []
        self._build()
        # Initial population + 4s refresh loop.
        self._refresh()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(4_000)
        self._refresh_timer.timeout.connect(self._refresh)
        self._refresh_timer.start()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # Header strip — count + refresh button.
        header = QHBoxLayout()
        header.setSpacing(12)
        self._count_label = QLabel("Devices (—)")
        self._count_label.setStyleSheet(
            f"color: {PURPLE_PRIMARY}; background: transparent; "
            f"font-size: 18px; font-weight: 700;"
        )
        header.addWidget(self._count_label)
        header.addStretch(1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("SendBtn")  # reuse the purple-primary button style
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # Scroll area — vertical list of device rows.
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._host = QWidget()
        self._list_layout = QVBoxLayout(self._host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch(1)
        self._scroll.setWidget(self._host)
        root.addWidget(self._scroll, stretch=1)

        # Empty-state hero (visible only when no devices).
        self._empty_hero = QLabel("No ADB devices connected")
        self._empty_hero.setObjectName("PlaceholderHero")
        self._empty_hero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hero.setStyleSheet(
            f"color: {MUTED_FG}; font-size: 18px; "
            f"padding: 60px 0; background: transparent;"
        )
        root.addWidget(self._empty_hero)

        self._empty_sub = QLabel(
            "Plug a phone in (USB cable) or run `adb connect <ip>:5555` "
            "to add a wireless device. Auto-refreshes every 4 seconds."
        )
        self._empty_sub.setObjectName("PlaceholderSub")
        self._empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_sub.setStyleSheet(
            f"color: {MUTED_FG}; font-size: 12px; "
            f"padding-bottom: 60px; background: transparent;"
        )
        root.addWidget(self._empty_sub)

    def _clear_rows(self) -> None:
        for row in self._device_rows:
            row.setParent(None)
            row.deleteLater()
        self._device_rows.clear()

    def _refresh(self) -> None:
        devices = state.list_adb_devices()
        n = len(devices)
        self._count_label.setText(
            f"Devices ({n})" if n != 1 else "Devices (1)"
        )
        self._clear_rows()
        for dev in devices:
            row = _DeviceRow(dev, parent=self._host)
            # insertWidget at count-1 inserts before the trailing stretch
            self._list_layout.insertWidget(
                self._list_layout.count() - 1, row
            )
            self._device_rows.append(row)
        is_empty = (n == 0)
        self._scroll.setVisible(not is_empty)
        self._empty_hero.setVisible(is_empty)
        self._empty_sub.setVisible(is_empty)


# Backward-compat alias — older modules import PhonesTab.
PhonesTab = DevicesView
