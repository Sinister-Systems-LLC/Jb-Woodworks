# Author: RKOJ-ELENO :: 2026-05-21
"""Workstation tab — grid of action cards."""

from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGridLayout, QPushButton, QVBoxLayout, QWidget


SANCTUM_ROOT = Path(r"D:\Sinister Sanctum")


def _open_path(path: str | Path) -> None:
    p = Path(path)
    if not p.exists():
        return
    try:
        os.startfile(str(p))
    except Exception:
        subprocess.Popen(["explorer", str(p)])


def _open_url(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        pass


def _run_cmd(args: list[str]) -> None:
    try:
        subprocess.Popen(args, creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    except Exception:
        pass


ACTIONS: list[tuple[str, str, callable]] = [
    ("Open Vault :5078",
     "Browse the 1 TB sinister-vault daemon",
     lambda: _open_url("http://localhost:5078")),
    ("Open Brain Graph",
     "Visualise the knowledge brain (sinister-mind :5079)",
     lambda: _open_url("http://localhost:5079")),
    ("Restart Watchdog",
     "Restart sinister-watchdog process supervisor",
     lambda: _run_cmd(["powershell", "-Command",
                       "Stop-Process -Name 'python' -ErrorAction SilentlyContinue; "
                       "Start-Process powershell -ArgumentList '-NoExit','-Command','sinister-watchdog start' -WindowStyle Normal"])),
    ("Open Sanctum Backups",
     "Explorer to backups directory",
     lambda: _open_path(SANCTUM_ROOT / "_shared-memory" / "backups")),
    ("Edit ~/.claude/.mcp.json",
     "Open the MCP config in the system editor",
     lambda: _open_path(Path.home() / ".claude" / ".mcp.json")),
    ("Open _shared-memory",
     "Explorer to the shared-memory tree",
     lambda: _open_path(SANCTUM_ROOT / "_shared-memory")),
]


class WorkstationTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(12)
        for i, (label, tooltip, fn) in enumerate(ACTIONS):
            btn = QPushButton(label)
            btn.setObjectName("ActionCard")
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(110)
            btn.clicked.connect(lambda _checked=False, f=fn: f())
            row, col = divmod(i, 3)
            grid.addWidget(btn, row, col)
        root.addLayout(grid)
        root.addStretch(1)
