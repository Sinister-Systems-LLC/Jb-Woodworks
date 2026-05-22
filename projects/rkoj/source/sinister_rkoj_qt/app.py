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
import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (
    QGuiApplication, QIcon, QKeySequence, QPainterPath, QRegion, QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from . import state
from .agent_window import AgentWindow
from .agents_tab import AgentsView
from .devices_tab import DevicesView
from .dialogs import NewAgentDialog, SavedSessionsPicker
from .header import Header
from .sidebar import Sidebar
from .theme import (
    BORDER, CARD_RADIUS, MUTED_FG, OUTER_GAP, OUTER_PADDING, PANEL_BG,
    PURPLE_PRIMARY, SUCCESS, WINDOW_RADIUS, build_qss,
)


class _StatusBar(QFrame):
    """Bottom status strip — fleet snapshot at a glance.

    Refreshes every 5s. Reads `state.snapshot()` (heartbeats + inbox count
    + brain count + ADB devices) and renders a single horizontal row:

      ●  3 agents · 5 inbox · 96 brain · 2 phones · uptime 04:21
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBar")
        self.setFixedHeight(28)
        self.setStyleSheet(
            f"QFrame#StatusBar {{"
            f"  background-color: {PANEL_BG};"
            f"  border-top: 1px solid {BORDER};"
            f"}}"
        )
        self._t0 = time.time()
        self._build()
        self._timer = QTimer(self)
        self._timer.setInterval(5_000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    def _build(self) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(16, 0, 16, 0)
        row.setSpacing(14)

        # Online dot
        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._dot.setStyleSheet(
            f"background-color: {SUCCESS}; border-radius: 4px;"
        )
        row.addWidget(self._dot)

        # The label cluster
        self._agents_lbl = self._make_label("0 agents")
        self._inbox_lbl  = self._make_label("0 inbox")
        self._brain_lbl  = self._make_label("0 brain")
        self._phones_lbl = self._make_label("0 phones")
        self._uptime_lbl = self._make_label("uptime 0s")
        for lbl in (self._agents_lbl, self._inbox_lbl, self._brain_lbl,
                    self._phones_lbl):
            row.addWidget(lbl)
            row.addWidget(self._make_sep())
        row.addWidget(self._uptime_lbl)
        row.addStretch(1)

        # Right side: branch label
        self._branch_lbl = QLabel("EVE on Sanctum · v1.6.5")
        self._branch_lbl.setStyleSheet(
            f"color: {PURPLE_PRIMARY}; background: transparent; "
            f"font-size: 11px; font-weight: 600;"
        )
        row.addWidget(self._branch_lbl)

    def _make_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {MUTED_FG}; background: transparent; "
            f"font-size: 11px; font-weight: 500;"
        )
        return lbl

    def _make_sep(self) -> QLabel:
        sep = QLabel("·")
        sep.setStyleSheet(
            f"color: {BORDER}; background: transparent; font-size: 11px;"
        )
        return sep

    def _refresh(self) -> None:
        try:
            snap = state.snapshot()
            self._agents_lbl.setText(
                f"{snap.agents_online}/{snap.agents_total} agents"
            )
            self._inbox_lbl.setText(f"{snap.inbox_count} inbox")
            self._brain_lbl.setText(f"{snap.brain_count} brain")
            self._phones_lbl.setText(
                f"{snap.phones_online + snap.phones_offline + snap.phones_needs_auth} phones"
            )
            elapsed = int(time.time() - self._t0)
            mm, ss = divmod(elapsed, 60)
            hh, mm = divmod(mm, 60)
            self._uptime_lbl.setText(
                f"uptime {hh:02d}:{mm:02d}:{ss:02d}" if hh else f"uptime {mm:02d}:{ss:02d}"
            )
            # If no live agents, dim the dot.
            color = SUCCESS if snap.agents_online > 0 else MUTED_FG
            self._dot.setStyleSheet(
                f"background-color: {color}; border-radius: 4px;"
            )
        except Exception:
            # Status bar must never crash the app.
            pass


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
        # Track every spawned agent window so they don't get garbage-collected
        # the moment the dialog returns. Keyed by pane_id; auto-cleaned on
        # window close via destroyed-signal hook.
        self._agent_windows: dict[str, AgentWindow] = {}
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

        # Bottom status bar — fleet snapshot
        self.status_bar = _StatusBar(main_card)
        main_layout.addWidget(self.status_bar)

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
        # Sidebar nav: agents / devices mirror chip-tabs. "sessions" pops
        # the saved-sessions picker directly (one-click resume flow).
        if key == "sessions":
            self._open_sessions_picker()
            return
        self.header.set_active_chip(key)
        self._on_chip(key)

    def _open_sessions_picker(self) -> None:
        """Open the saved-sessions picker without going through New Agent.

        Picked session opens INLINE in the Agents tab body with --resume
        wiring (operator wants everything in the main window).
        """
        picker = SavedSessionsPicker(self)
        if picker.exec() != SavedSessionsPicker.DialogCode.Accepted:
            return
        data = picker.result_data or {}
        self._spawn_inline(
            project_key=data.get("project_key", "sanctum"),
            agent_name=data.get("agent_name"),
            mode=data.get("mode", "claude"),
            session_uuid=data.get("session_uuid"),
        )

    def _on_create_agent(self) -> None:
        """Pop the picker; spawn the agent INSIDE the main window's
        Agents tab body (operator-corrected 2026-05-22: *"this needs to
        work and come up in the window itself"*). Cards appear inline in
        the niri-scroll grid; the empty-state hint disappears the moment
        the first agent lands.
        """
        dlg = NewAgentDialog(self, default_project_key="sanctum")
        if dlg.exec() != NewAgentDialog.DialogCode.Accepted:
            return
        choice = dlg.result_dict or {}
        self._spawn_inline(
            project_key=choice.get("project_key", "sanctum"),
            agent_name=choice.get("agent_name"),
            mode=choice.get("mode", "claude"),
            session_uuid=choice.get("session_uuid"),
        )

    def _spawn_inline(self, *, project_key: str,
                      agent_name: Optional[str],
                      mode: str,
                      session_uuid: Optional[str]) -> str:
        """Spawn an agent card inside the Agents tab body + focus the tab.

        Same path for fresh agents AND for resumed sessions — the only
        difference is whether session_uuid is None (fresh) or a saved
        UUID (resume mode).
        """
        self.header.set_active_chip("agents")
        self.stack.setCurrentWidget(self.agents_view)
        return self.agents_view.spawn_agent(
            project_key=project_key,
            agent_name=agent_name,
            mode=mode,
            session_uuid=session_uuid,
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
        # Close every spawned AgentWindow first — each fires its own
        # closeEvent which kills its subprocess.
        try:
            for win in list(self._agent_windows.values()):
                try:
                    win.close()
                except Exception:
                    pass
            self._agent_windows.clear()
        except Exception:
            pass
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
