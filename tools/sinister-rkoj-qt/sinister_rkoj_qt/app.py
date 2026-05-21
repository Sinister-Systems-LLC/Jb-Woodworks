# Author: RKOJ-ELENO :: 2026-05-21
"""QApplication + frameless rounded MainWindow wiring."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtGui import QGuiApplication, QIcon, QKeySequence, QPainterPath, QRegion, QShortcut
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from .agents_tab import AgentsTab
from .header import Header
from .kpis import KpiStrip
from .phones_tab import PhonesTab
from .ribbon import Ribbon
from .sidebar import Sidebar
from .theme import (
    BG, BORDER_GLASS, WINDOW_RADIUS, build_qss,
)
from .workstation_tab import WorkstationTab


# Sinister logo for window icon (optional)
ICON_PATH = Path(r"D:\Sinister Sanctum\automations\window-manager\web\sinister-logo.ico")


class WinControls(QWidget):
    """Min/Max/Close cluster, top-right."""
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._win = parent
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 8, 0)
        layout.setSpacing(2)

        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")
        for b in (self.btn_min, self.btn_max, self.btn_close):
            b.setObjectName("WinCtl")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setObjectName("WinCtlClose")
        self.btn_min.clicked.connect(self._on_min)
        self.btn_max.clicked.connect(self._on_max)
        self.btn_close.clicked.connect(self._on_close)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

    def _on_min(self) -> None:
        w = self.window()
        if w is not None:
            w.showMinimized()

    def _on_max(self) -> None:
        w = self.window()
        if w is None:
            return
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()

    def _on_close(self) -> None:
        w = self.window()
        if w is not None:
            w.close()


class MainWindow(QMainWindow):
    """Frameless rounded main window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sinister Sanctum — RKOJ.exe")
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        # Frameless + transparent (so rounded mask shows)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.resize(1480, 900)
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

        # ── Sidebar ────────────────────────────────────────────────
        self.sidebar = Sidebar(shell)
        outer.addWidget(self.sidebar)

        # ── Right column (header / ribbon / kpis / pane) ───────────
        right = QWidget(shell)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header + win controls overlaid
        header_row = QWidget(right)
        header_row.setObjectName("HeaderRow")
        hl = QHBoxLayout(header_row)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(0)
        self.header = Header(header_row)
        hl.addWidget(self.header, stretch=1)
        self.win_controls = WinControls(header_row)
        # Pin to top-right
        winctl_holder = QWidget(header_row)
        winctl_v = QVBoxLayout(winctl_holder)
        winctl_v.setContentsMargins(0, 0, 0, 0)
        winctl_v.setSpacing(0)
        winctl_v.addWidget(self.win_controls)
        winctl_v.addStretch(1)
        hl.addWidget(winctl_holder)
        right_layout.addWidget(header_row)

        # Ribbon
        self.ribbon = Ribbon(right)
        right_layout.addWidget(self.ribbon)

        # KPIs
        self.kpis = KpiStrip(right)
        right_layout.addWidget(self.kpis)

        # Main pane (stacked agents/phones/workstation)
        self.stack = QStackedWidget(right)
        self.agents_tab = AgentsTab(self.stack)
        self.phones_tab = PhonesTab(self.stack)
        self.workstation_tab = WorkstationTab(self.stack)
        self.stack.addWidget(self.agents_tab)
        self.stack.addWidget(self.phones_tab)
        self.stack.addWidget(self.workstation_tab)
        right_layout.addWidget(self.stack, stretch=1)

        outer.addWidget(right, stretch=1)

    def _wire(self) -> None:
        # Chip tabs
        self.header.chip_clicked.connect(self._on_chip)
        # Sidebar nav -> route shortcuts
        self.sidebar.nav_clicked.connect(self._on_nav)
        # Ribbon actions
        self.ribbon.action_clicked.connect(self._on_ribbon_action)
        # Header icon actions
        self.header.icon_clicked.connect(self._on_header_icon)
        # Ctrl+K palette
        QShortcut(QKeySequence("Ctrl+K"), self, activated=lambda: self._on_header_icon("palette"))

    # ── Routing ────────────────────────────────────────────────────
    def _on_chip(self, key: str) -> None:
        if key == "agents":
            self.stack.setCurrentWidget(self.agents_tab)
        elif key == "phones":
            self.stack.setCurrentWidget(self.phones_tab)
        elif key == "workstation":
            self.stack.setCurrentWidget(self.workstation_tab)

    def _on_nav(self, key: str) -> None:
        # Map sidebar nav keys onto top-tabs where applicable.
        if key == "phones":
            self.header.set_active_chip("phones")
            self.stack.setCurrentWidget(self.phones_tab)
        elif key in ("eve", "automation"):
            self.header.set_active_chip("agents")
            self.stack.setCurrentWidget(self.agents_tab)
        elif key == "admin":
            self.header.set_active_chip("workstation")
            self.stack.setCurrentWidget(self.workstation_tab)
        # other nav keys (overview/accounts/...) leave the main pane alone

    def _on_ribbon_action(self, key: str) -> None:
        # Map ribbon actions onto wired stubs.
        if key == "view.toggle_sidebar":
            self.sidebar.setVisible(not self.sidebar.isVisible())
        elif key == "spawn.agent":
            self.header.set_active_chip("agents")
            self.stack.setCurrentWidget(self.agents_tab)
            self.agents_tab.spawn_agent("sanctum")
        elif key == "spawn.swarm3":
            self.header.set_active_chip("agents")
            self.stack.setCurrentWidget(self.agents_tab)
            for _ in range(3):
                self.agents_tab.spawn_agent("sanctum")
        elif key == "spawn.codex":
            self.header.set_active_chip("agents")
            self.stack.setCurrentWidget(self.agents_tab)
            self.agents_tab.spawn_agent("sanctum", mode="codex")
        elif key == "spawn.resume":
            self.agents_tab.spawn_agent("sanctum", mode="resume")
        elif key.startswith("agent."):
            # Forward as a slash to the most recent agent if any
            self._dispatch_to_latest_agent(key.split(".", 1)[1].replace("_", " "))
        elif key == "auto.watchdog_start":
            import subprocess
            try:
                subprocess.Popen(["powershell", "-NoExit", "-Command", "sinister-watchdog start"],
                                 creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            except Exception:
                pass
        elif key == "auto.watchdog_tail":
            import subprocess
            try:
                subprocess.Popen(["powershell", "-NoExit", "-Command", "Get-Content -Wait $env:USERPROFILE\\.sinister\\watchdog.log"],
                                 creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            except Exception:
                pass
        elif key == "auto.backup_now":
            import subprocess
            try:
                subprocess.Popen(["powershell", "-NoExit", "-Command", "& 'D:\\Sinister Sanctum\\automations\\sanctum-backup\\run.ps1'"],
                                 creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            except Exception:
                pass
        elif key == "auto.push_now":
            import subprocess
            try:
                subprocess.Popen(["powershell", "-NoExit", "-Command", "& 'D:\\Sinister Sanctum\\automations\\sanctum-git\\auto-push.ps1'"],
                                 creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            except Exception:
                pass
        elif key.startswith("maint."):
            self._on_maint(key.split(".", 1)[1])

    def _on_maint(self, action: str) -> None:
        import subprocess
        from pathlib import Path
        if action == "brain_index":
            try:
                subprocess.Popen(["powershell", "-NoExit", "-Command",
                                 "Get-ChildItem 'D:\\Sinister Sanctum\\_shared-memory\\knowledge\\*.md' | Measure-Object | Select-Object -ExpandProperty Count"],
                                creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
            except Exception:
                pass
        elif action == "sanctum_backup":
            import os
            try:
                os.startfile(r"D:\Sinister Sanctum\_shared-memory\backups")
            except Exception:
                pass
        elif action == "vault_status":
            import webbrowser
            webbrowser.open("http://localhost:5078/health")
        elif action == "mcp_probe":
            import os
            try:
                os.startfile(str(Path.home() / ".claude" / ".mcp.json"))
            except Exception:
                pass

    def _dispatch_to_latest_agent(self, slash_text: str) -> None:
        cards = list(self.agents_tab._cards.values()) if hasattr(self.agents_tab, "_cards") else []
        if not cards:
            return
        latest = cards[-1]
        latest.input.setText("/" + slash_text)
        latest._on_send()

    def _on_header_icon(self, key: str) -> None:
        if key == "palette":
            # placeholder — eventually a QDialog with a search line
            pass
        elif key == "settings":
            import os
            try:
                os.startfile(str(Path(r"D:\Sinister Sanctum\automations\session-templates\projects.json")))
            except Exception:
                pass
        elif key == "inbox":
            import os
            try:
                os.startfile(r"D:\Sinister Sanctum\_shared-memory\inbox\sanctum")
            except Exception:
                pass

    # ── Rounded mask ───────────────────────────────────────────────
    def resizeEvent(self, event) -> None:
        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(self.width()), float(self.height()),
                           float(WINDOW_RADIUS), float(WINDOW_RADIUS))
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        super().resizeEvent(event)

    # ── Clean shutdown ─────────────────────────────────────────────
    def closeEvent(self, event) -> None:
        try:
            self.agents_tab.shutdown_all()
        except Exception:
            pass
        # write a tiny resume-point breadcrumb
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
        super().closeEvent(event)


def run(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv
    app = QApplication(argv)
    app.setApplicationName("Sinister Sanctum")
    app.setOrganizationName("RKOJ-ELENO")
    app.setStyleSheet(build_qss())
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    win = MainWindow()
    win.show()
    return app.exec()
