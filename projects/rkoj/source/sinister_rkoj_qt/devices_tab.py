# Author: RKOJ-ELENO :: 2026-05-21
"""Devices tab — live ADB device list with per-device action buttons.

v1.6.4 — read-only inventory.
v1.6.72 — operator escalation: ADB viewer must actually work for viewing
phones. Per-device row now has Mirror / Screenshot / Shell / Logcat
buttons that shell out to scrcpy + adb respectively. scrcpy auto-detected
via winget install path or PATH lookup.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from . import state
from .theme import (
    BORDER, ELEVATED, MUTED_FG, PURPLE_PRIMARY, SUCCESS, WARNING,
)


# v1.6.72 — locate scrcpy. Tries PATH first, then the standard winget
# install location (Genymobile.scrcpy package layout as of v3.3.x).
def _find_scrcpy() -> str | None:
    on_path = shutil.which("scrcpy") or shutil.which("scrcpy.exe")
    if on_path:
        return on_path
    winget_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_dir.exists():
        for pkg in winget_dir.glob("Genymobile.scrcpy_*"):
            for sub in pkg.glob("scrcpy-win*"):
                cand = sub / "scrcpy.exe"
                if cand.exists():
                    return str(cand)
    return None


def _find_adb() -> str | None:
    on_path = shutil.which("adb") or shutil.which("adb.exe")
    if on_path:
        return on_path
    # scrcpy ships adb in its folder
    sc = _find_scrcpy()
    if sc:
        cand = Path(sc).parent / "adb.exe"
        if cand.exists():
            return str(cand)
    return None


_SCRCPY = _find_scrcpy()
_ADB = _find_adb()


_STATE_COLOR: dict[str, str] = {
    "device": SUCCESS,
    "offline": MUTED_FG,
    "unauthorized": WARNING,
}


class _DeviceRow(QFrame):
    """Single device row — status dot + serial + model + state + transport."""

    def __init__(self, dev: state.Device, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.dev = dev
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

        # v1.6.72 — per-device action buttons (only when state == device)
        if dev.state == "device":
            self._add_action_button(row, "Mirror", "Open scrcpy screen mirror",
                                    self._launch_scrcpy)
            self._add_action_button(row, "Screenshot",
                                    "Save adb screencap PNG to Desktop",
                                    self._take_screenshot)
            self._add_action_button(row, "Shell", "Open adb shell in a terminal",
                                    self._open_shell)
            self._add_action_button(row, "Logcat",
                                    "Tail logcat in a new terminal",
                                    self._tail_logcat)

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

    def _add_action_button(self, row: QHBoxLayout, label: str,
                           tip: str, slot) -> None:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(tip)
        btn.setStyleSheet(
            f"QPushButton {{"
            f"  color: {PURPLE_PRIMARY}; background-color: rgba(191,90,242,30);"
            f"  border: 1px solid rgba(191,90,242,120); border-radius: 8px;"
            f"  padding: 4px 12px; font-size: 11px; font-weight: 600;"
            f"}}"
            f"QPushButton:hover {{ background-color: rgba(191,90,242,60); }}"
            f"QPushButton:disabled {{ color: {MUTED_FG}; "
            f"  background-color: transparent; border-color: {BORDER}; }}"
        )
        btn.clicked.connect(slot)
        row.addWidget(btn)

    # ── Action handlers ────────────────────────────────────────────────
    def _toast(self, msg: str, error: bool = False) -> None:
        # Lightweight inline feedback via QMessageBox.
        box = QMessageBox(self)
        box.setWindowTitle("ADB Viewer" if not error else "ADB Viewer error")
        box.setText(msg)
        box.setIcon(QMessageBox.Icon.Warning if error else QMessageBox.Icon.Information)
        box.exec()

    def _launch_scrcpy(self) -> None:
        if not _SCRCPY:
            self._toast(
                "scrcpy not found.\n\nInstall: winget install Genymobile.scrcpy",
                error=True,
            )
            return
        try:
            # Spawn detached; scrcpy opens its own window with the mirror.
            subprocess.Popen(
                [_SCRCPY, "--serial", self.dev.serial,
                 "--window-title", f"EVE/scrcpy · {self.dev.model or self.dev.serial}"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except Exception as exc:
            self._toast(f"scrcpy launch failed: {exc}", error=True)

    def _take_screenshot(self) -> None:
        if not _ADB:
            self._toast("adb not found on PATH (and not bundled with scrcpy).",
                        error=True)
            return
        ts = time.strftime("%Y%m%dT%H%M%S")
        out = Path.home() / "Desktop" / f"eve-{self.dev.serial}-{ts}.png"
        try:
            with open(out, "wb") as fh:
                r = subprocess.run(
                    [_ADB, "-s", self.dev.serial, "exec-out",
                     "screencap", "-p"],
                    stdout=fh,
                    stderr=subprocess.PIPE,
                    timeout=15,
                )
            if r.returncode != 0:
                self._toast(f"screencap exit {r.returncode}\n"
                            f"{r.stderr.decode('utf-8', 'replace')[:200]}",
                            error=True)
                return
            self._toast(f"Saved: {out}")
        except Exception as exc:
            self._toast(f"screenshot failed: {exc}", error=True)

    def _open_shell(self) -> None:
        if not _ADB:
            self._toast("adb not found on PATH.", error=True)
            return
        try:
            # Launch a NEW cmd window running `adb -s <serial> shell`.
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k",
                 f'"{_ADB}" -s {self.dev.serial} shell'],
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except Exception as exc:
            self._toast(f"shell launch failed: {exc}", error=True)

    def _tail_logcat(self) -> None:
        if not _ADB:
            self._toast("adb not found on PATH.", error=True)
            return
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "cmd", "/k",
                 f'"{_ADB}" -s {self.dev.serial} logcat -v threadtime'],
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except Exception as exc:
            self._toast(f"logcat launch failed: {exc}", error=True)


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

        # v1.6.72 — tooling status pill (scrcpy + adb detect)
        tooling = []
        if _SCRCPY:
            tooling.append("scrcpy ✓")
        else:
            tooling.append("scrcpy ✗ (winget install Genymobile.scrcpy)")
        if _ADB:
            tooling.append("adb ✓")
        else:
            tooling.append("adb ✗")
        tool_label = QLabel(" · ".join(tooling))
        tool_label.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 11px; font-family: 'JetBrains Mono', monospace;"
        )
        tool_label.setToolTip(
            f"scrcpy: {_SCRCPY or '(not found)'}\nadb: {_ADB or '(not found)'}"
        )
        header.addWidget(tool_label)
        header.addSpacing(12)

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
