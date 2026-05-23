# Author: RKOJ-ELENO :: 2026-05-23
"""Devices tab — live ADB device list with embedded scrcpy mirrors.

v1.6.4  — read-only inventory.
v1.6.72 — per-device action buttons (Mirror / Screenshot / Shell / Logcat).
v1.6.73 — embedded scrcpy in a rounded MirrorCard inside the tab itself
          (Win32 SetParent reparenting via QWindow.fromWinId). Per-device
          group-select checkbox + group action row (Mirror Selected,
          Screenshot Selected, Mirror All).
"""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QWindow
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
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
    sc = _find_scrcpy()
    if sc:
        cand = Path(sc).parent / "adb.exe"
        if cand.exists():
            return str(cand)
    return None


_SCRCPY = _find_scrcpy()
_ADB = _find_adb()

# v1.6.76 — suppress any cmd-window flash from spawned subprocesses
# (operator: no cmd popups when viewing phones).
_CREATE_NO_WINDOW = 0x08000000
_DETACHED = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


_STATE_COLOR: dict[str, str] = {
    "device": SUCCESS,
    "offline": MUTED_FG,
    "unauthorized": WARNING,
}


# ── Embedded scrcpy mirror card ────────────────────────────────────────
class _MirrorCard(QFrame):
    """v1.6.73 — rounded card that hosts a reparented scrcpy window.

    Spawns `scrcpy --serial <s> --window-title <unique> --window-borderless
    --max-size 480` in detached mode, then after ~2s scans for that
    window-title via Win32 FindWindowW, takes the HWND, wraps it with
    `QWindow.fromWinId()` + `QWidget.createWindowContainer()`, and
    embeds the result into this card's body slot.
    """

    closed = pyqtSignal(str)  # serial — DevicesView catches to clean up state

    # Operator wants the embed under ~480px so 2 phones fit side-by-side.
    MIRROR_SIZE = 360
    EMBED_RETRY_MS = 300
    EMBED_TIMEOUT_MS = 20000   # v1.6.79 — was 8s, sometimes too short

    def __init__(self, dev: state.Device, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.dev = dev
        self._proc: subprocess.Popen | None = None
        self._embed_container: QWidget | None = None
        self._embed_window: QWindow | None = None
        self._embed_attempts = 0
        self._unique_title = f"EVE-MIRROR-{dev.serial}-{int(time.time() * 1000)}"
        self.setObjectName("MirrorCard")
        self.setStyleSheet(
            f"QFrame#MirrorCard {{"
            f"  background-color: {ELEVATED};"
            f"  border: 1px solid {BORDER};"
            f"  border-radius: 14px;"
            f"}}"
        )
        self.setFixedWidth(self.MIRROR_SIZE + 16)
        self.setMinimumHeight(self.MIRROR_SIZE + 110)
        self._build()
        # Start scrcpy now; embed-poller fires soon after.
        QTimer.singleShot(0, self._spawn_scrcpy)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Header strip: USB pill · serial · model · close X
        hdr = QHBoxLayout()
        hdr.setSpacing(6)
        usb = QLabel("USB")
        usb.setStyleSheet(
            f"color: {SUCCESS}; background-color: rgba(48,209,88,30); "
            f"border: 1px solid rgba(48,209,88,120); border-radius: 6px; "
            f"padding: 1px 6px; font-size: 9px; font-weight: 700; "
            f"font-family: 'JetBrains Mono', monospace;"
        )
        hdr.addWidget(usb)

        serial = QLabel(self.dev.serial[-8:])
        serial.setStyleSheet(
            f"color: white; background: transparent; "
            f"font-family: 'JetBrains Mono', monospace; "
            f"font-size: 10px; font-weight: 700;"
        )
        hdr.addWidget(serial)

        model = QLabel(self.dev.model or "?")
        model.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; font-size: 10px;"
        )
        hdr.addWidget(model)

        hdr.addStretch(1)

        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            f"QPushButton {{ color: {MUTED_FG}; background: transparent; "
            f"border: none; font-size: 12px; font-weight: 700; }}"
            f"QPushButton:hover {{ color: white; "
            f"background-color: rgba(255,255,255,0.08); border-radius: 4px; }}"
        )
        close_btn.clicked.connect(self._on_close)
        hdr.addWidget(close_btn)
        root.addLayout(hdr)

        # Body — placeholder until scrcpy embeds; then SetParent'd into.
        # v1.6.74 — must be a NATIVE Qt widget (WA_NativeWindow) so it
        # has a real Win32 HWND for SetParent to attach scrcpy to.
        # v1.6.79 — also opaque-paint + no system-bg so adjacent widgets
        # don't bleed through the embed (operator screenshot showed the
        # agents-tab "no saved sessions" text leaking through).
        self._body_host = QFrame()
        self._body_host.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self._body_host.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)
        self._body_host.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self._body_host.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        self._body_host.setAutoFillBackground(True)
        self._body_host.setMinimumSize(self.MIRROR_SIZE, self.MIRROR_SIZE)
        self._body_host.setStyleSheet(
            f"QFrame {{ background-color: #000; border-radius: 10px; }}"
        )
        self._body_layout = QVBoxLayout(self._body_host)
        self._body_layout.setContentsMargins(0, 0, 0, 0)
        self._body_layout.setSpacing(0)
        self._body_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._status_label = QLabel("Launching scrcpy…")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 11px; padding: 20px;"
        )
        self._body_layout.addWidget(self._status_label)
        root.addWidget(self._body_host, stretch=1)

        # Footer — text-only action row (no cmd popups per operator)
        # v1.6.79 — added Advanced + owner badge on this card.
        ftr = QHBoxLayout()
        ftr.setSpacing(6)
        for label, slot in (
            ("Shot",     self._take_screenshot),
            ("Advanced", self._toggle_advanced),
        ):
            b = QPushButton(label)
            b.setFixedHeight(22)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton {{ color: {PURPLE_PRIMARY}; "
                f"background-color: rgba(191,90,242,30); "
                f"border: 1px solid rgba(191,90,242,120); border-radius: 11px; "
                f"padding: 0 10px; font-size: 10px; font-weight: 600; }}"
                f"QPushButton:hover {{ background-color: rgba(191,90,242,60); }}"
            )
            b.clicked.connect(slot)
            ftr.addWidget(b)
        # Owner badge on this card
        owner = state.who_owns(self.dev.serial)
        if owner:
            ob = QLabel(f"agent: {owner.get('agent_display') or owner.get('agent_id', '?')}")
            ob.setStyleSheet(
                f"color: {SUCCESS}; background-color: rgba(48,209,88,30); "
                f"border: 1px solid rgba(48,209,88,120); border-radius: 11px; "
                f"padding: 1px 8px; font-size: 9px; font-weight: 700;"
            )
            ftr.addWidget(ob)
        ftr.addStretch(1)
        root.addLayout(ftr)

        # v1.6.79 — Advanced log panel (hidden by default). Toggled by
        # the Advanced button. Shows live scrcpy stdout/stderr + the
        # last 10 adb commands fired against this serial.
        self._advanced_panel = QFrame()
        self._advanced_panel.setStyleSheet(
            f"QFrame {{ background-color: #0a0a0c; border: 1px solid {BORDER}; "
            f"border-radius: 8px; padding: 6px; }}"
        )
        ap_layout = QVBoxLayout(self._advanced_panel)
        ap_layout.setContentsMargins(6, 6, 6, 6)
        ap_layout.setSpacing(4)
        from PyQt6.QtWidgets import QPlainTextEdit
        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumHeight(120)
        self._log_view.setStyleSheet(
            f"QPlainTextEdit {{ background: transparent; color: {MUTED_FG}; "
            f"border: none; font-family: 'JetBrains Mono', monospace; "
            f"font-size: 10px; }}"
        )
        self._log_view.setPlaceholderText("live scrcpy log — opens on Advanced click")
        ap_layout.addWidget(self._log_view)
        self._advanced_panel.hide()
        root.addWidget(self._advanced_panel)

        # v1.6.79 — drain scrcpy stderr into the log view every 500ms.
        self._log_timer = QTimer(self)
        self._log_timer.setInterval(500)
        self._log_timer.timeout.connect(self._drain_proc_log)
        self._log_timer.start()

    def _toggle_advanced(self) -> None:
        if self._advanced_panel.isVisible():
            self._advanced_panel.hide()
        else:
            self._advanced_panel.show()

    def _drain_proc_log(self) -> None:
        if self._proc is None or self._proc.stderr is None:
            return
        try:
            import select
            # Non-blocking read of whatever's pending. On Windows we use
            # the simpler poll-the-fd approach via readable bytes count.
            # If reading blocks (Windows has no select on pipes), bail.
            import msvcrt  # type: ignore
            # Try a simple non-blocking peek via PeekNamedPipe
            import ctypes
            handle = msvcrt.get_osfhandle(self._proc.stderr.fileno())
            avail = ctypes.c_ulong(0)
            ok = ctypes.windll.kernel32.PeekNamedPipe(
                ctypes.c_void_p(handle), None, 0, None, ctypes.byref(avail), None
            )
            if ok and avail.value > 0:
                chunk = self._proc.stderr.read(avail.value)
                if chunk:
                    self._log_view.appendPlainText(chunk.rstrip())
        except Exception:
            # If anything goes sideways, just stop draining (don't crash).
            self._log_timer.stop()

    def _spawn_scrcpy(self) -> None:
        if not _SCRCPY:
            self._status_label.setText("scrcpy not found")
            return
        # v1.6.74 — force native HWND creation before scrcpy spawns so
        # the parent window exists when _try_embed runs SetParent.
        try:
            _ = int(self._body_host.winId())
        except Exception:
            pass
        try:
            # v1.6.79 — software renderer + capture stderr for diagnostics
            self._proc = subprocess.Popen(
                [
                    _SCRCPY,
                    "--serial", self.dev.serial,
                    "--window-title", self._unique_title,
                    "--window-borderless",
                    "--max-size", str(self.MIRROR_SIZE),
                    "--no-audio",
                    "--render-driver", "software",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=_DETACHED | _CREATE_NO_WINDOW,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self._status_label.setText("Connecting to phone…")
            QTimer.singleShot(self.EMBED_RETRY_MS, self._try_embed)
        except Exception as exc:
            self._status_label.setText(f"scrcpy failed:\n{exc}")

    def _try_embed(self) -> None:
        """v1.6.74 — Win32 SetParent reparenting (more reliable than
        QWindow.fromWinId, which previously rendered as a black box
        because Qt didn't drive scrcpy's D3D backend through resize/
        paint cycles correctly)."""
        self._embed_attempts += 1
        elapsed = self._embed_attempts * self.EMBED_RETRY_MS
        try:
            user32 = ctypes.windll.user32
            user32.FindWindowW.restype = ctypes.c_void_p
            user32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
            hwnd = user32.FindWindowW(None, self._unique_title)
        except Exception as exc:
            self._status_label.setText(f"reparent failed: {exc}")
            return
        if not hwnd:
            if elapsed > self.EMBED_TIMEOUT_MS:
                self._status_label.setText(
                    f"scrcpy window not found after {self.EMBED_TIMEOUT_MS // 1000}s"
                )
                return
            QTimer.singleShot(self.EMBED_RETRY_MS, self._try_embed)
            return
        try:
            # Win32 constants
            GWL_STYLE = -16
            WS_CHILD = 0x40000000
            WS_POPUP = 0x80000000
            WS_CAPTION = 0x00C00000
            WS_THICKFRAME = 0x00040000
            SWP_NOZORDER = 0x0004
            SWP_NOACTIVATE = 0x0010
            SWP_FRAMECHANGED = 0x0020

            user32.GetWindowLongW.restype = ctypes.c_long
            user32.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
            user32.SetWindowLongW.restype = ctypes.c_long
            user32.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                              ctypes.c_long]
            user32.SetParent.restype = ctypes.c_void_p
            user32.SetParent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            user32.SetWindowPos.restype = ctypes.c_int
            user32.SetWindowPos.argtypes = [
                ctypes.c_void_p, ctypes.c_void_p,
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                ctypes.c_uint,
            ]

            # 1. Strip top-level decorations + add WS_CHILD
            cur_style = user32.GetWindowLongW(hwnd, GWL_STYLE)
            new_style = ((cur_style | WS_CHILD)
                         & ~WS_POPUP & ~WS_CAPTION & ~WS_THICKFRAME)
            user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)

            # 2. Reparent into our body host widget
            parent_hwnd = int(self._body_host.winId())
            user32.SetParent(hwnd, parent_hwnd)

            # 3. Move to (0,0) inside parent + size to body
            w = max(200, self._body_host.width() or self.MIRROR_SIZE)
            h = max(200, self._body_host.height() or self.MIRROR_SIZE)
            user32.SetWindowPos(
                hwnd, None, 0, 0, w, h,
                SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
            )
            self._embedded_hwnd = hwnd
            self._status_label.hide()
        except Exception as exc:
            self._status_label.setText(f"embed failed: {exc}")

    def resizeEvent(self, event) -> None:
        """v1.6.74 — keep embedded HWND sized to body host on resize."""
        super().resizeEvent(event)
        hwnd = getattr(self, "_embedded_hwnd", None)
        if hwnd:
            try:
                w = max(200, self._body_host.width())
                h = max(200, self._body_host.height())
                ctypes.windll.user32.SetWindowPos(
                    ctypes.c_void_p(hwnd), None, 0, 0, w, h,
                    0x0004 | 0x0010,  # NOZORDER | NOACTIVATE
                )
            except Exception:
                pass

    def _on_close(self) -> None:
        # Kill scrcpy → its window vanishes → reparented container destroys
        if self._proc is not None:
            try:
                self._proc.kill()
                self._proc.wait(timeout=2)
            except Exception:
                pass
            self._proc = None
        self.closed.emit(self.dev.serial)
        self.setParent(None)
        self.deleteLater()

    # ── Quick-action footer slots ──────────────────────────────────────
    def _toast(self, msg: str, error: bool = False) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("Mirror" if not error else "Mirror error")
        box.setIcon(QMessageBox.Icon.Warning if error else QMessageBox.Icon.Information)
        box.setText(msg)
        box.exec()

    def _take_screenshot(self) -> None:
        if not _ADB:
            return self._toast("adb not found", error=True)
        ts = time.strftime("%Y%m%dT%H%M%S")
        out = Path.home() / "Desktop" / f"eve-{self.dev.serial}-{ts}.png"
        try:
            with open(out, "wb") as fh:
                subprocess.run([_ADB, "-s", self.dev.serial, "exec-out",
                                "screencap", "-p"], stdout=fh, timeout=15)
            self._toast(f"Saved: {out.name}")
        except Exception as exc:
            self._toast(f"screencap failed: {exc}", error=True)

    def _open_shell(self) -> None:
        if not _ADB:
            return self._toast("adb not found", error=True)
        subprocess.Popen(
            ["cmd", "/c", "start", "cmd", "/k",
             f'"{_ADB}" -s {self.dev.serial} shell'],
            creationflags=_DETACHED | _CREATE_NO_WINDOW,
        )

    def _tail_logcat(self) -> None:
        if not _ADB:
            return self._toast("adb not found", error=True)
        subprocess.Popen(
            ["cmd", "/c", "start", "cmd", "/k",
             f'"{_ADB}" -s {self.dev.serial} logcat -v threadtime'],
            creationflags=_DETACHED | _CREATE_NO_WINDOW,
        )


# ── Device list row ────────────────────────────────────────────────────
class _DeviceRow(QFrame):
    """Single device row — checkbox + status dot + serial + model + actions."""

    mirror_requested = pyqtSignal(str)        # serial
    group_toggled = pyqtSignal(str, bool)     # serial, selected

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

        # v1.6.73 — group-select checkbox
        self.group_cb = QCheckBox()
        self.group_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.group_cb.setToolTip("Add to group selection")
        self.group_cb.setStyleSheet(
            f"QCheckBox::indicator {{ width: 14px; height: 14px; "
            f"border: 1px solid {BORDER}; border-radius: 4px; "
            f"background-color: transparent; }}"
            f"QCheckBox::indicator:checked {{ background-color: {PURPLE_PRIMARY}; "
            f"border-color: {PURPLE_PRIMARY}; }}"
        )
        self.group_cb.toggled.connect(
            lambda checked: self.group_toggled.emit(self.dev.serial, checked)
        )
        row.addWidget(self.group_cb)

        dot = QLabel()
        dot.setFixedSize(10, 10)
        color = _STATE_COLOR.get(dev.state, MUTED_FG)
        dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
        row.addWidget(dot)

        serial = QLabel(dev.serial)
        serial.setStyleSheet(
            "color: white; background: transparent; "
            "font-family: 'JetBrains Mono', 'Cascadia Mono', monospace; "
            "font-size: 12px; font-weight: 600;"
        )
        row.addWidget(serial)

        model = QLabel(dev.model or "(unknown)")
        model.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; font-size: 12px;"
        )
        row.addWidget(model)

        row.addStretch(1)

        # v1.6.79 — owner badge if this phone is claimed by an agent
        owner = state.who_owns(dev.serial)
        if owner:
            ob = QLabel(f"owned by {owner.get('agent_display') or owner.get('agent_id', '?')}")
            ob.setStyleSheet(
                f"color: {PURPLE_PRIMARY}; background-color: rgba(191,90,242,30); "
                f"border: 1px solid rgba(191,90,242,120); border-radius: 8px; "
                f"padding: 2px 8px; font-size: 10px; font-weight: 600;"
            )
            row.addWidget(ob)

        if dev.state == "device":
            self._add_action_button(row, "Mirror", "Embed scrcpy mirror inline",
                                    lambda: self.mirror_requested.emit(self.dev.serial))
            self._add_action_button(row, "Screenshot",
                                    "Save adb screencap PNG to Desktop",
                                    self._take_screenshot)

        state_pill = QLabel(dev.state)
        state_pill.setStyleSheet(
            f"color: {color}; background: transparent; "
            f"font-size: 11px; font-weight: 600; text-transform: uppercase;"
            f"letter-spacing: 0.5px;"
        )
        row.addWidget(state_pill)

        transport = QLabel(dev.transport.upper())
        transport.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 10px; padding: 2px 8px; "
            f"border: 1px solid {BORDER}; border-radius: 8px;"
        )
        row.addWidget(transport)

    def _add_action_button(self, row, label: str, tip: str, slot) -> None:
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
        )
        btn.clicked.connect(slot)
        row.addWidget(btn)

    def _toast(self, msg: str, error: bool = False) -> None:
        box = QMessageBox(self)
        box.setWindowTitle("ADB Viewer" if not error else "ADB Viewer error")
        box.setText(msg)
        box.setIcon(QMessageBox.Icon.Warning if error else QMessageBox.Icon.Information)
        box.exec()

    def _take_screenshot(self) -> None:
        if not _ADB:
            return self._toast("adb not found", error=True)
        ts = time.strftime("%Y%m%dT%H%M%S")
        out = Path.home() / "Desktop" / f"eve-{self.dev.serial}-{ts}.png"
        try:
            with open(out, "wb") as fh:
                subprocess.run([_ADB, "-s", self.dev.serial, "exec-out",
                                "screencap", "-p"], stdout=fh, timeout=15)
            self._toast(f"Saved: {out}")
        except Exception as exc:
            self._toast(f"screencap failed: {exc}", error=True)

    def _open_shell(self) -> None:
        if not _ADB:
            return self._toast("adb not found", error=True)
        subprocess.Popen(
            ["cmd", "/c", "start", "cmd", "/k",
             f'"{_ADB}" -s {self.dev.serial} shell'],
            creationflags=_DETACHED | _CREATE_NO_WINDOW,
        )

    def _tail_logcat(self) -> None:
        if not _ADB:
            return self._toast("adb not found", error=True)
        subprocess.Popen(
            ["cmd", "/c", "start", "cmd", "/k",
             f'"{_ADB}" -s {self.dev.serial} logcat -v threadtime'],
            creationflags=_DETACHED | _CREATE_NO_WINDOW,
        )


# ── Top-level Devices tab ──────────────────────────────────────────────
class DevicesView(QWidget):
    """ADB devices: live list + group select + embedded scrcpy mirrors."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._device_rows: list[_DeviceRow] = []
        self._mirror_cards: dict[str, _MirrorCard] = {}  # serial → card
        self._group_selected: set[str] = set()
        self._auto_mirrored_once = False
        self._build()
        self._refresh()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(4_000)
        self._refresh_timer.timeout.connect(self._refresh)
        self._refresh_timer.start()
        # v1.6.74 — auto-mirror every connected phone on first build.
        # 1500ms delay so the widget tree is fully realized + native HWNDs
        # exist before SetParent runs (without this scrcpy reparents to
        # an unrealized parent and ends up as a black box).
        QTimer.singleShot(1500, self._auto_mirror_all)

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # Header strip — count + tooling + group actions + refresh
        header = QHBoxLayout()
        header.setSpacing(12)
        self._count_label = QLabel("Devices (—)")
        self._count_label.setStyleSheet(
            f"color: {PURPLE_PRIMARY}; background: transparent; "
            f"font-size: 18px; font-weight: 700;"
        )
        header.addWidget(self._count_label)
        header.addStretch(1)

        # Dashboard-skeleton: no emojis. Use "ok" / "missing" text instead.
        tooling = []
        tooling.append(f"scrcpy {'ok' if _SCRCPY else 'missing'}")
        tooling.append(f"adb {'ok' if _ADB else 'missing'}")
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

        # v1.6.73 — Group actions
        self._mirror_all_btn = QPushButton("Mirror All")
        self._mirror_all_btn.setObjectName("SendBtn")
        self._mirror_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mirror_all_btn.clicked.connect(self._mirror_all)
        header.addWidget(self._mirror_all_btn)

        self._mirror_sel_btn = QPushButton("Mirror Selected")
        self._mirror_sel_btn.setObjectName("SendBtn")
        self._mirror_sel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mirror_sel_btn.clicked.connect(self._mirror_selected)
        self._mirror_sel_btn.setEnabled(False)
        header.addWidget(self._mirror_sel_btn)

        self._shot_sel_btn = QPushButton("Screenshot Selected")
        self._shot_sel_btn.setObjectName("SendBtn")
        self._shot_sel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._shot_sel_btn.clicked.connect(self._screenshot_selected)
        self._shot_sel_btn.setEnabled(False)
        header.addWidget(self._shot_sel_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("SendBtn")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # v1.6.74 — Mirrors panel is the PRIMARY view (horizontal infinite
        # scroll, fills vertical space). Auto-loads every connected phone
        # on first build so the operator sees them all by default.
        self._mirrors_scroll = QScrollArea(self)
        self._mirrors_scroll.setWidgetResizable(True)
        self._mirrors_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._mirrors_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._mirrors_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._mirrors_host = QWidget()
        self._mirrors_row = QHBoxLayout(self._mirrors_host)
        self._mirrors_row.setContentsMargins(0, 0, 0, 0)
        self._mirrors_row.setSpacing(10)
        self._mirrors_row.addStretch(1)
        self._mirrors_scroll.setWidget(self._mirrors_host)
        root.addWidget(self._mirrors_scroll, stretch=1)

        # v1.6.79 — operator removed the redundant bottom device-list strip.
        # All actions live on the mirror cards themselves now; the strip
        # was just visual noise. Keep _host/_list_layout/_scroll for
        # internal device-row tracking (Mirror All button needs them) but
        # never add to the visible layout.
        self._host = QWidget()
        self._list_layout = QVBoxLayout(self._host)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch(1)
        self._scroll = QScrollArea()
        self._scroll.setWidget(self._host)
        self._scroll.hide()

        # Empty state
        self._empty_hero = QLabel("No ADB devices connected")
        self._empty_hero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hero.setStyleSheet(
            f"color: {MUTED_FG}; font-size: 18px; "
            f"padding: 60px 0; background: transparent;"
        )
        root.addWidget(self._empty_hero)

        self._empty_sub = QLabel(
            "Plug a phone in (USB cable) or run `adb connect <ip>:5555`. "
            "Auto-refreshes every 4 seconds."
        )
        self._empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_sub.setStyleSheet(
            f"color: {MUTED_FG}; font-size: 12px; "
            f"padding-bottom: 60px; background: transparent;"
        )
        root.addWidget(self._empty_sub)

    # ── Refresh device list ────────────────────────────────────────────
    def _clear_rows(self) -> None:
        for r in self._device_rows:
            r.setParent(None)
            r.deleteLater()
        self._device_rows.clear()

    def _refresh(self) -> None:
        devices = state.list_adb_devices()
        n = len(devices)
        self._count_label.setText(f"Devices ({n})")
        self._clear_rows()
        for dev in devices:
            row = _DeviceRow(dev, parent=self._host)
            row.mirror_requested.connect(self._embed_mirror)
            row.group_toggled.connect(self._on_group_toggled)
            self._list_layout.insertWidget(
                self._list_layout.count() - 1, row
            )
            self._device_rows.append(row)
        empty = (n == 0)
        self._scroll.setVisible(not empty)
        self._empty_hero.setVisible(empty)
        self._empty_sub.setVisible(empty)
        # Group action enable state
        self._update_group_buttons()

    # ── Mirror embed lifecycle ─────────────────────────────────────────
    def _embed_mirror(self, serial: str) -> None:
        if not _SCRCPY:
            QMessageBox.warning(self, "Mirror",
                                "scrcpy not found.\n\nInstall: winget install Genymobile.scrcpy")
            return
        if serial in self._mirror_cards:
            return  # already embedded
        dev = next((d for d in state.list_adb_devices() if d.serial == serial), None)
        if dev is None:
            return
        card = _MirrorCard(dev, parent=self._mirrors_host)
        card.closed.connect(self._on_mirror_closed)
        # Insert before the trailing stretch
        self._mirrors_row.insertWidget(self._mirrors_row.count() - 1, card)
        self._mirror_cards[serial] = card
        self._mirrors_scroll.show()

    def _on_mirror_closed(self, serial: str) -> None:
        self._mirror_cards.pop(serial, None)
        if not self._mirror_cards:
            self._mirrors_scroll.hide()

    # ── Group select ───────────────────────────────────────────────────
    def _on_group_toggled(self, serial: str, checked: bool) -> None:
        if checked:
            self._group_selected.add(serial)
        else:
            self._group_selected.discard(serial)
        self._update_group_buttons()

    def _update_group_buttons(self) -> None:
        n = len(self._group_selected)
        self._mirror_sel_btn.setEnabled(n > 0)
        self._mirror_sel_btn.setText(f"Mirror Selected ({n})" if n else "Mirror Selected")
        self._shot_sel_btn.setEnabled(n > 0)
        self._shot_sel_btn.setText(f"Screenshot Selected ({n})" if n else "Screenshot Selected")

    def _mirror_all(self) -> None:
        for r in self._device_rows:
            if r.dev.state == "device":
                self._embed_mirror(r.dev.serial)

    def _auto_mirror_all(self) -> None:
        """v1.6.74 — one-shot auto-mirror on first tab build so operator
        sees all phones embedded by default. Subsequent refreshes don't
        re-fire this (operator can close cards + use Mirror All button).
        v1.6.76 — force a refresh first so device rows are populated
        before iteration (adb daemon may not have answered the __init__
        call yet)."""
        if self._auto_mirrored_once:
            return
        self._auto_mirrored_once = True
        self._refresh()
        if not self._device_rows:
            # adb daemon may still be starting. Retry once after 1.5s.
            QTimer.singleShot(1500, self._auto_mirror_all_retry)
            return
        self._mirror_all()

    def _auto_mirror_all_retry(self) -> None:
        self._refresh()
        self._mirror_all()

    def _mirror_selected(self) -> None:
        for s in list(self._group_selected):
            self._embed_mirror(s)

    def _screenshot_selected(self) -> None:
        if not _ADB:
            return
        ts = time.strftime("%Y%m%dT%H%M%S")
        success: list[str] = []
        for s in list(self._group_selected):
            out = Path.home() / "Desktop" / f"eve-{s}-{ts}.png"
            try:
                with open(out, "wb") as fh:
                    subprocess.run([_ADB, "-s", s, "exec-out",
                                    "screencap", "-p"], stdout=fh, timeout=15)
                success.append(out.name)
            except Exception:
                pass
        QMessageBox.information(
            self, "Group Screenshot",
            f"Saved {len(success)} screenshot(s) to Desktop:\n\n"
            + "\n".join(success[:10])
        )


# Backward-compat alias — older modules import PhonesTab.
PhonesTab = DevicesView
