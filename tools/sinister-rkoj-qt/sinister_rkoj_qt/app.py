# Author: RKOJ-ELENO :: 2026-05-21
"""QApplication + frameless rounded SinisterWindow wiring.

Layout (operator-canonical 2026-05-21 rewrite):

    ┌────────────────────────────────────────────────────────────┐
    │  Header.row1 — File / Edit / View / ... | — □ ✕           │
    │  Header.row2 — Page Title  · Chips · Icons · + Create     │
    ├──────────┬─────────────────────────────────────────────────┤
    │ Sidebar  │ AgentsView (folder tabs + niri-scroll grid)     │
    │  EVE     │ or DevicesView (placeholder)                    │
    │  DAILY   │                                                 │
    │  INSIGHTS│                                                 │
    │  MANAGE  │                                                 │
    └──────────┴─────────────────────────────────────────────────┘
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QIcon, QKeySequence, QPainterPath, QRegion, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QHBoxLayout, QMainWindow, QMessageBox, QStackedWidget,
    QVBoxLayout, QWidget,
)

from .agents_tab import AgentsView
from .devices_tab import DevicesView
from .header import Header
from .sidebar import Sidebar
from .theme import WINDOW_RADIUS, build_qss


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
        self.resize(1400, 900)
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
        # Root shell widget (rounded)
        shell = QWidget(self)
        shell.setObjectName("RootShell")
        self.setCentralWidget(shell)

        outer = QHBoxLayout(shell)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────
        self.sidebar = Sidebar(shell)
        outer.addWidget(self.sidebar)

        # ── Right column (header + body) ──────────────────────────
        right = QWidget(shell)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.header = Header(right)
        right_layout.addWidget(self.header)

        # Body — stacked Agents / Devices
        self.stack = QStackedWidget(right)
        self.agents_view = AgentsView(self.stack)
        self.devices_view = DevicesView(self.stack)
        self.stack.addWidget(self.agents_view)
        self.stack.addWidget(self.devices_view)
        right_layout.addWidget(self.stack, stretch=1)

        outer.addWidget(right, stretch=1)

    def _wire(self) -> None:
        # Chip tabs
        self.header.chip_clicked.connect(self._on_chip)
        # Create Agent
        self.header.create_agent_clicked.connect(self._on_create_agent)
        # Header icon cluster
        self.header.icon_clicked.connect(self._on_header_icon)
        # Window controls
        self.header.minimize_clicked.connect(self.showMinimized)
        self.header.maximize_clicked.connect(self._toggle_max)
        self.header.close_clicked.connect(self.close)
        # Menu strip actions
        self.header.menu_action.connect(self._on_menu_action)
        # Sidebar nav (placeholder — only highlights for now)
        self.sidebar.nav_clicked.connect(self._on_nav)
        # Ctrl+K palette stub
        QShortcut(QKeySequence("Ctrl+K"), self,
                  activated=lambda: self._on_header_icon("search"))

    # ── Routing ───────────────────────────────────────────────────
    def _on_chip(self, key: str) -> None:
        if key == "agents":
            self.stack.setCurrentWidget(self.agents_view)
        elif key == "devices":
            self.stack.setCurrentWidget(self.devices_view)

    def _on_nav(self, key: str) -> None:
        # Placeholder per operator brief — clicking nav only highlights.
        # If desired later we'd swap the body content here.
        _ = key

    def _on_create_agent(self) -> None:
        # Default to sanctum project — multi-project picker is milestone 2.
        self.header.set_active_chip("agents")
        self.stack.setCurrentWidget(self.agents_view)
        self.agents_view.spawn_agent(project_key="sanctum")

    def _on_header_icon(self, key: str) -> None:
        # Stubs — wired in a follow-up. Operator brief: very basic for now.
        _ = key

    def _on_menu_action(self, action: str) -> None:
        if action == "File.Exit":
            self.close()
            return
        if action == "File.New Agent" or action == "Agent.Spawn EVE":
            self._on_create_agent()
            return
        if action == "View.Toggle Sidebar":
            self.sidebar.setVisible(not self.sidebar.isVisible())
            return
        if action == "Agent.Terminate All":
            self.agents_view.shutdown_all()
            return
        if action == "Help.About RKOJ":
            QMessageBox.information(
                self,
                "About RKOJ",
                "RKOJ.exe — Sinister Sanctum workstation\n"
                "EVE orchestration agent · Sanctum purple · RKOJ-ELENO.\n"
                "Build 2026-05-21 — milestone 1 (Agents shell).",
            )
            return
        # Other items are placeholders; ignore silently.

    def _toggle_max(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ── Rounded mask ──────────────────────────────────────────────
    def resizeEvent(self, event) -> None:
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()),
                            float(WINDOW_RADIUS), float(WINDOW_RADIUS))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        super().resizeEvent(event)

    # ── Clean shutdown ────────────────────────────────────────────
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
    # Important — quit when the last window closes (so X actually exits)
    app.setQuitOnLastWindowClosed(True)

    win = SinisterWindow()
    win.show()
    return app.exec()
