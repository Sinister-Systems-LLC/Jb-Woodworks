# Author: RKOJ-ELENO :: 2026-05-21
"""QApplication + frameless rounded SinisterWindow wiring — Panel-1:1 chrome.

Outer chrome reflects Panel `layout.tsx`:

    body bg-black ─ p-2 gap-2 ──────────────────────────────────────
    ┌─────────────────┐  8px gap  ┌──────────────────────────────────┐
    │   SidebarCard   │ <- gap -> │            MainCard              │
    │ rounded-2xl     │           │ ┌──────────────────────────────┐ │
    │ border #2c2c2e  │           │ │  Header (96px, single row)   │ │
    │ bg #0a0a0c      │           │ ├──────────────────────────────┤ │
    │ ┌─ 2px purple ─┐│           │ │  Body (Agents | Devices)     │ │
    │ │  gradient    ││           │ └──────────────────────────────┘ │
    │ │  left spine  ││           │                                  │
    │ └──────────────┘│           │                                  │
    │ ┌──────────────┐│           │                                  │
    │ │  Banner 96px ││           │                                  │
    │ └──────────────┘│           │                                  │
    │ WORKSPACE       │           │                                  │
    │   • Agents      │           │                                  │
    │ OPERATIONS      │           │                                  │
    │   • Devices     │           │                                  │
    └─────────────────┘           └──────────────────────────────────┘
    body bg-black continues outside the two cards (peeks through 8px gap)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QGuiApplication, QIcon, QKeySequence, QPainterPath, QRegion, QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QMessageBox, QStackedWidget,
    QVBoxLayout, QWidget,
)

from .agents_tab import AgentsView
from .devices_tab import DevicesView
from .dialogs import NewAgentDialog
from .header import Header
from .sidebar import Sidebar
from .theme import (
    CARD_RADIUS, OUTER_GAP, OUTER_PADDING, WINDOW_RADIUS, build_qss,
)


# Sinister logo for window icon (optional)
ICON_PATH = Path(r"D:\Sinister Sanctum\automations\window-manager\web\sinister-logo.ico")


class SinisterWindow(QMainWindow):
    """Frameless rounded main window — RKOJ.exe entry surface."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sinister Sanctum — RKOJ.exe")
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(1100, 720)
        self.resize(1440, 920)
        self._center_on_screen()
        self._build()
        self._wire()

    def _center_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.center().x() - self.width() // 2
            y = geo.center().y() - self.height() // 2
            self.move(x, y)

    def _build(self) -> None:
        # ── Outer body: pure black, peeks through the 8px gap. ──────────
        body = QWidget(self)
        body.setObjectName("OuterBody")
        self.setCentralWidget(body)

        outer = QHBoxLayout(body)
        outer.setContentsMargins(
            OUTER_PADDING, OUTER_PADDING, OUTER_PADDING, OUTER_PADDING
        )
        outer.setSpacing(OUTER_GAP)

        # ── Sidebar card ───────────────────────────────────────────────
        self.sidebar = Sidebar(body)
        # Sidebar itself owns the SidebarCard styling via QSS objectName.
        outer.addWidget(self.sidebar)

        # ── Main card (Header + body stack) ────────────────────────────
        main_card = QWidget(body)
        main_card.setObjectName("MainCard")
        main_layout = QVBoxLayout(main_card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = Header(main_card)
        main_layout.addWidget(self.header)

        # Body — stacked Agents / Devices
        self.stack = QStackedWidget(main_card)
        self.agents_view = AgentsView(self.stack)
        self.devices_view = DevicesView(self.stack)
        self.stack.addWidget(self.agents_view)
        self.stack.addWidget(self.devices_view)
        main_layout.addWidget(self.stack, stretch=1)

        outer.addWidget(main_card, stretch=1)

    def _wire(self) -> None:
        # Chip tabs
        self.header.chip_clicked.connect(self._on_chip)
        # Create Agent
        self.header.create_agent_clicked.connect(self._on_create_agent)
        # Header icon cluster (placeholder dispatch)
        self.header.icon_clicked.connect(self._on_header_icon)
        # Window controls (single X — frameless)
        self.header.close_clicked.connect(self.close)
        # Sidebar nav → swap stack
        self.sidebar.nav_clicked.connect(self._on_nav)
        # Ctrl+K palette stub → header search
        QShortcut(QKeySequence("Ctrl+K"), self,
                  activated=lambda: self._on_header_icon("search"))

    # ── Routing ───────────────────────────────────────────────────────
    def _on_chip(self, key: str) -> None:
        if key == "agents":
            self.stack.setCurrentWidget(self.agents_view)
        elif key == "devices":
            self.stack.setCurrentWidget(self.devices_view)

    def _on_nav(self, key: str) -> None:
        # Sidebar nav mirrors chip-tab switching so either affordance works.
        self.header.set_active_chip(key)
        self._on_chip(key)

    def _on_create_agent(self) -> None:
        # Pop the picker; operator chooses project + name + mode.
        dlg = NewAgentDialog(self, default_project_key="sanctum")
        if dlg.exec() != NewAgentDialog.DialogCode.Accepted:
            return
        choice = dlg.result_dict or {}
        self.header.set_active_chip("agents")
        self.stack.setCurrentWidget(self.agents_view)
        self.agents_view.spawn_agent(
            project_key=choice.get("project_key", "sanctum"),
            agent_name=choice.get("agent_name"),
            mode=choice.get("mode", "claude"),
        )

    def _on_header_icon(self, key: str) -> None:
        # Stubs — wired in a follow-up. Operator brief: basic for now.
        _ = key

    # ── Rounded outer mask (chrome corners) ───────────────────────────
    def resizeEvent(self, event) -> None:
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()),
                            float(WINDOW_RADIUS), float(WINDOW_RADIUS))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        super().resizeEvent(event)

    # ── Clean shutdown (kills spawned claude children) ────────────────
    def closeEvent(self, event) -> None:
        try:
            self.agents_view.shutdown_all()
        except Exception:
            pass
        try:
            from .state import SHARED_MEMORY
            import json
            from datetime import datetime, timezone
            d = SHARED_MEMORY / "rkoj-qt"
            d.mkdir(parents=True, exist_ok=True)
            with open(d / "last-shutdown.json", "w", encoding="utf-8") as fh:
                json.dump({"shutdown_at": datetime.now(timezone.utc).isoformat()}, fh)
        except Exception:
            pass
        event.accept()
        super().closeEvent(event)


# Backward-compat alias
MainWindow = SinisterWindow


def run(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv
    app = QApplication(argv)
    app.setApplicationName("Sinister Sanctum")
    app.setOrganizationName("RKOJ-ELENO")
    app.setStyleSheet(build_qss())
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    app.setQuitOnLastWindowClosed(True)
    win = SinisterWindow()
    win.show()
    return app.exec()
