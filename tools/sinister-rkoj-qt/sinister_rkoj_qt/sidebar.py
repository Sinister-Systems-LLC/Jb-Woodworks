# Author: RKOJ-ELENO :: 2026-05-21
"""240px left sidebar — mascot block + 4 sections + status counters."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget,
)

from . import state
from .theme import SIDEBAR_WIDTH


# Sinister Panel 4-section layout — mirrors snap.sinijkr.com sidebar.tsx.
SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    ("WORKSPACE", [
        ("overview", "Overview"),
        ("accounts", "Accounts"),
        ("sales", "Sales"),
        ("analytics", "Analytics"),
    ]),
    ("OPERATIONS", [
        ("automation", "Automation"),
        ("phones", "Devices"),
        ("browsers", "Browsers"),
        ("database", "Database"),
        ("rka", "RKA"),
        ("videos", "Video Manager"),
    ]),
    ("AI", [
        ("eve", "EVE AI"),
        ("bitmoji", "Bitmoji Studio"),
    ]),
    ("SYSTEM", [
        ("admin", "Admin"),
    ]),
]


_MASCOT_ASCII = "  /\\_/\\  \n ( o.o ) \n  > ^ <  "


class Sidebar(QWidget):
    """Left vertical sidebar — fixed 240px width."""

    nav_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._active_nav: str = "overview"
        self._nav_buttons: dict[str, QPushButton] = {}
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_status)
        self._timer.start(5000)
        self._refresh_status()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Mascot block ────────────────────────────────────────────────
        mascot_frame = QFrame(self)
        mascot_frame.setObjectName("MascotFrame")
        mascot_layout = QVBoxLayout(mascot_frame)
        mascot_layout.setContentsMargins(16, 16, 16, 12)
        mascot_layout.setSpacing(4)
        mascot_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mascot = QLabel(_MASCOT_ASCII)
        mascot.setObjectName("Mascot")
        mascot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mono = QFont("Cascadia Mono")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        mascot.setFont(mono)
        mascot_layout.addWidget(mascot)

        eve_label = QLabel("E V E")
        eve_label.setObjectName("EveLabel")
        eve_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mascot_layout.addWidget(eve_label)

        root.addWidget(mascot_frame)

        # ── Scrollable nav ──────────────────────────────────────────────
        nav_scroll = QScrollArea(self)
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setFrameShape(QFrame.Shape.NoFrame)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        nav_host = QWidget()
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(8, 0, 8, 0)
        nav_layout.setSpacing(0)

        for section_label, items in SECTIONS:
            sec = QLabel(section_label)
            sec.setObjectName("SidebarSection")
            nav_layout.addWidget(sec)
            for key, label in items:
                btn = QPushButton(f"  •  {label}")
                btn.setObjectName("NavItem")
                btn.setProperty("active", False)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _checked=False, k=key: self._on_nav_clicked(k))
                self._nav_buttons[key] = btn
                nav_layout.addWidget(btn)

        nav_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        nav_scroll.setWidget(nav_host)
        root.addWidget(nav_scroll, stretch=1)

        # ── Status block ────────────────────────────────────────────────
        status_frame = QFrame(self)
        status_frame.setObjectName("StatusFrame")
        sl = QVBoxLayout(status_frame)
        sl.setContentsMargins(16, 12, 16, 16)
        sl.setSpacing(6)

        sl.addWidget(self._mk_section_label("STATUS"))
        self._row_agents = self._mk_status_row("Agents")
        self._row_inbox = self._mk_status_row("Inbox")
        self._row_brain = self._mk_status_row("Brain")
        for row in (self._row_agents, self._row_inbox, self._row_brain):
            sl.addLayout(row["layout"])
        root.addWidget(status_frame)

        # Mark initial active
        self._update_active(self._active_nav)

    def _mk_section_label(self, txt: str) -> QLabel:
        lbl = QLabel(txt)
        lbl.setObjectName("SidebarSection")
        lbl.setStyleSheet("border-bottom: none; padding: 0 0 4px 0;")
        return lbl

    def _mk_status_row(self, label: str) -> dict:
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        lab = QLabel(label.upper())
        lab.setObjectName("StatusRowLabel")
        val = QLabel("0")
        val.setObjectName("StatusRowValue")
        val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(lab)
        h.addStretch(1)
        h.addWidget(val)
        return {"layout": h, "label": lab, "value": val}

    def _on_nav_clicked(self, key: str) -> None:
        self._update_active(key)
        self.nav_clicked.emit(key)

    def _update_active(self, key: str) -> None:
        self._active_nav = key
        for k, btn in self._nav_buttons.items():
            is_active = (k == key)
            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _refresh_status(self) -> None:
        try:
            snap = state.snapshot()
            self._row_agents["value"].setText(f"{snap.agents_online} live / {snap.agents_total}")
            self._row_inbox["value"].setText(str(snap.inbox_count))
            self._row_brain["value"].setText(str(snap.brain_count))
        except Exception:
            self._row_agents["value"].setText("?")
            self._row_inbox["value"].setText("?")
            self._row_brain["value"].setText("?")
