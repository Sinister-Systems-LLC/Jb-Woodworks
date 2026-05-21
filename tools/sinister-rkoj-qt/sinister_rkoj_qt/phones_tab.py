# Author: RKOJ-ELENO :: 2026-05-21
"""Phones tab — 4-stat strip + filter chips + 2-column device list / detail pane.

Polls `adb devices -l` every 10s. Detail pane shows logcat tail (3s refresh),
ADB shell input (10s timeout), and 3 action buttons (scrcpy / phone-viewer / list apps).
"""

from __future__ import annotations

import subprocess
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QVBoxLayout, QWidget,
)

from . import state
from .state import Device


class StatChip(QWidget):
    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("KpiTile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)
        self._lab = QLabel(label.upper())
        self._lab.setObjectName("KpiLabel")
        self._val = QLabel("0")
        self._val.setObjectName("KpiValue")
        self._val.setStyleSheet("font-size: 22px;")
        layout.addWidget(self._lab)
        layout.addWidget(self._val)

    def set_value(self, val: str) -> None:
        self._val.setText(val)


class DeviceCard(QFrame):
    """Selectable device row in the left rail."""
    def __init__(self, dev: Device, on_select, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.dev = dev
        self.setObjectName("DeviceCard")
        self.setProperty("selected", False)
        self._on_select = on_select
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)
        title = QLabel(dev.serial)
        title.setObjectName("AgentTitle")
        title.setStyleSheet("font-size: 12px;")
        layout.addWidget(title)
        sub = QLabel(f"{dev.model or '—'}  ·  {dev.state}  ·  {dev.transport}")
        sub.setObjectName("AgentMeta")
        layout.addWidget(sub)

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._on_select(self.dev.serial)
        super().mousePressEvent(ev)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)


class PhonesTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device_cards: dict[str, DeviceCard] = {}
        self._selected: Optional[str] = None
        self._filter: str = "all"
        self._build()
        # Polls
        self._adb_timer = QTimer(self)
        self._adb_timer.timeout.connect(self._refresh_devices)
        self._adb_timer.start(10000)
        self._refresh_devices()
        self._logcat_timer = QTimer(self)
        self._logcat_timer.timeout.connect(self._refresh_logcat)
        self._logcat_timer.start(3000)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 8, 20, 12)
        root.setSpacing(10)

        # 4-stat strip
        stats = QHBoxLayout()
        stats.setSpacing(10)
        self.stat_online = StatChip("Phones Online")
        self.stat_offline = StatChip("Offline")
        self.stat_auth = StatChip("Needs-Auth")
        self.stat_armed = StatChip("RKA-Armed")
        for s in (self.stat_online, self.stat_offline, self.stat_auth, self.stat_armed):
            stats.addWidget(s, stretch=1)
        root.addLayout(stats)

        # Filter chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)
        self._filter_chips: dict[str, QPushButton] = {}
        for key, label in [("all", "All"), ("online", "Online"), ("stale", "Stale"), ("locked", "Locked")]:
            btn = QPushButton(label)
            btn.setObjectName("ProjectChip")
            btn.setProperty("active", key == self._filter)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, k=key: self._set_filter(k))
            self._filter_chips[key] = btn
            chips_row.addWidget(btn)
        chips_row.addStretch(1)
        root.addLayout(chips_row)

        # 2-column body
        body = QHBoxLayout()
        body.setSpacing(12)

        # Left rail
        rail_scroll = QScrollArea(self)
        rail_scroll.setWidgetResizable(True)
        rail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        rail_scroll.setFixedWidth(280)
        self._rail_host = QWidget()
        self._rail_layout = QVBoxLayout(self._rail_host)
        self._rail_layout.setContentsMargins(0, 0, 0, 0)
        self._rail_layout.setSpacing(6)
        self._rail_layout.addStretch(1)
        rail_scroll.setWidget(self._rail_host)
        body.addWidget(rail_scroll)

        # Right detail pane
        detail = QVBoxLayout()
        detail.setSpacing(8)

        # Identity row
        self.identity_label = QLabel("(select a device)")
        self.identity_label.setObjectName("AgentTitle")
        detail.addWidget(self.identity_label)

        # Heartbeat / RKA / Kill-switch row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)
        self.heartbeat_label = QLabel("heartbeat: —")
        self.heartbeat_label.setObjectName("AgentMeta")
        self.rka_label = QLabel("RKA: —")
        self.rka_label.setObjectName("AgentMeta")
        self.kill_pill = QLabel("● ready")
        self.kill_pill.setObjectName("HealthPill")
        meta_row.addWidget(self.heartbeat_label)
        meta_row.addWidget(self.rka_label)
        meta_row.addStretch(1)
        meta_row.addWidget(self.kill_pill)
        detail.addLayout(meta_row)

        # ADB shell row
        shell_row = QHBoxLayout()
        shell_row.setSpacing(6)
        self.shell_input = QLineEdit()
        self.shell_input.setObjectName("TerminalInput")
        self.shell_input.setPlaceholderText("adb shell <cmd>  (Enter)")
        self.shell_input.returnPressed.connect(self._on_shell_send)
        self.shell_input.setEnabled(False)
        shell_btn = QPushButton("Run")
        shell_btn.setObjectName("PrimaryBtn")
        shell_btn.clicked.connect(self._on_shell_send)
        shell_row.addWidget(self.shell_input, stretch=1)
        shell_row.addWidget(shell_btn)
        detail.addLayout(shell_row)

        # Action buttons row
        actions = QHBoxLayout()
        actions.setSpacing(6)
        for label, fn in [("Open scrcpy", self._open_scrcpy), ("Open phone-viewer", self._open_phone_viewer), ("List apps", self._list_apps)]:
            btn = QPushButton(label)
            btn.setObjectName("GhostBtn")
            btn.clicked.connect(fn)
            actions.addWidget(btn)
        actions.addStretch(1)
        detail.addLayout(actions)

        # Logcat tail
        logcat_label = QLabel("LOGCAT (last 50, 3s refresh)")
        logcat_label.setObjectName("KpiLabel")
        detail.addWidget(logcat_label)
        self.logcat_view = QPlainTextEdit()
        self.logcat_view.setObjectName("Terminal")
        self.logcat_view.setReadOnly(True)
        font = QFont("Cascadia Mono", 9)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.logcat_view.setFont(font)
        detail.addWidget(self.logcat_view, stretch=1)

        body.addLayout(detail, stretch=1)
        root.addLayout(body, stretch=1)

    # ── Filters / selection ────────────────────────────────────────
    def _set_filter(self, key: str) -> None:
        self._filter = key
        for k, btn in self._filter_chips.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._apply_filter()

    def _apply_filter(self) -> None:
        for serial, card in self._device_cards.items():
            if self._filter == "all":
                card.setVisible(True)
            elif self._filter == "online":
                card.setVisible(card.dev.state == "device")
            elif self._filter == "stale":
                card.setVisible(card.dev.state == "offline")
            elif self._filter == "locked":
                card.setVisible(card.dev.state == "unauthorized")
            else:
                card.setVisible(True)

    def _select(self, serial: str) -> None:
        self._selected = serial
        for s, card in self._device_cards.items():
            card.set_selected(s == serial)
        card = self._device_cards.get(serial)
        if card:
            self.identity_label.setText(f"{card.dev.serial}  ·  {card.dev.model or '—'}  ·  {card.dev.state}")
            self.shell_input.setEnabled(card.dev.state == "device")
            self.heartbeat_label.setText(f"heartbeat: {card.dev.transport}")
            self.rka_label.setText(f"RKA: {'armed' if card.dev.state == 'device' else 'inactive'}")
            self.kill_pill.setText("● armed" if card.dev.state == "device" else "● inactive")
        self._refresh_logcat()

    # ── Refresh loops ──────────────────────────────────────────────
    def _refresh_devices(self) -> None:
        devices = state.list_adb_devices()
        # update stats
        online = sum(1 for d in devices if d.state == "device")
        offline = sum(1 for d in devices if d.state == "offline")
        auth = sum(1 for d in devices if d.state == "unauthorized")
        self.stat_online.set_value(str(online))
        self.stat_offline.set_value(str(offline))
        self.stat_auth.set_value(str(auth))
        self.stat_armed.set_value(str(online))

        # rebuild rail
        seen = set()
        for d in devices:
            seen.add(d.serial)
            if d.serial in self._device_cards:
                # update existing card's dev reference (state may change)
                self._device_cards[d.serial].dev = d
            else:
                card = DeviceCard(d, on_select=self._select, parent=self._rail_host)
                self._rail_layout.insertWidget(self._rail_layout.count() - 1, card)
                self._device_cards[d.serial] = card
        # remove stale
        for s in list(self._device_cards.keys()):
            if s not in seen:
                card = self._device_cards.pop(s)
                card.setParent(None)
                card.deleteLater()
                if self._selected == s:
                    self._selected = None
                    self.identity_label.setText("(select a device)")
                    self.shell_input.setEnabled(False)
        self._apply_filter()

    def _refresh_logcat(self) -> None:
        if not self._selected:
            return
        text = state.adb_logcat_tail(self._selected, lines=50)
        # cap to avoid runaway widget
        if len(text) > 30000:
            text = text[-30000:]
        self.logcat_view.setPlainText(text)
        sb = self.logcat_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Actions ────────────────────────────────────────────────────
    def _on_shell_send(self) -> None:
        if not self._selected:
            return
        cmd = self.shell_input.text().strip()
        if not cmd:
            return
        out = state.adb_shell(self._selected, cmd, timeout_s=10.0)
        self.logcat_view.appendPlainText(f"\n$ {cmd}\n{out}\n")
        self.shell_input.clear()

    def _open_scrcpy(self) -> None:
        if not self._selected:
            return
        try:
            subprocess.Popen(["scrcpy", "-s", self._selected],
                             creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            self.logcat_view.appendPlainText(f"\n[scrcpy] launched for {self._selected}\n")
        except FileNotFoundError:
            self.logcat_view.appendPlainText("\n[scrcpy] not installed — install from https://github.com/Genymobile/scrcpy/releases\n")
        except Exception as exc:
            self.logcat_view.appendPlainText(f"\n[scrcpy] error: {exc}\n")

    def _open_phone_viewer(self) -> None:
        # placeholder — would launch sinister-phone-viewer tool
        self.logcat_view.appendPlainText("\n[phone-viewer] not wired — see automations/sinister-phone-viewer/\n")

    def _list_apps(self) -> None:
        if not self._selected:
            return
        out = state.adb_shell(self._selected, "pm list packages -3", timeout_s=10.0)
        self.logcat_view.appendPlainText(f"\n[apps]\n{out}\n")
