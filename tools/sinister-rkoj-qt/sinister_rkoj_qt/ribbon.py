# Author: RKOJ-ELENO :: 2026-05-21
"""Excel-style ribbon — 5 labeled groups with action buttons."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget,
)

from .theme import RIBBON_HEIGHT


# Each group: (label, [(action_key, button_label, tooltip), ...])
GROUPS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("VIEW", [
        ("view.toggle_sidebar", "Toggle Sidebar", "Show/hide the 240px sidebar"),
        ("view.toggle_memory", "Toggle Memory", "Show shared-memory panel"),
        ("view.toggle_theme", "Toggle Theme", "Cycle purple variants"),
        ("view.mermaid", "Mermaid Render", "Render the current mermaid doc"),
    ]),
    ("SPAWN", [
        ("spawn.agent", "+ Agent", "Spawn a single EVE agent"),
        ("spawn.swarm3", "+ Swarm 3x", "Spawn 3 EVE agents on the same project"),
        ("spawn.codex", "+ Codex", "Open a Codex companion session"),
        ("spawn.resume", "Resume Project", "Resume the last paused project"),
    ]),
    ("AGENT", [
        ("agent.effort_fast", "/effort fast", "Set effort=fast on the focused agent"),
        ("agent.effort_xhigh", "/effort xhigh", "Set effort=xhigh on the focused agent"),
        ("agent.model_opus", "/model Opus", "Switch focused agent to Opus"),
        ("agent.model_sonnet", "/model Sonnet", "Switch focused agent to Sonnet"),
        ("agent.save", "/save", "Save focused agent state to disk"),
        ("agent.restart", "/restart", "Restart focused agent"),
    ]),
    ("AUTOMATE", [
        ("auto.watchdog_start", "Watchdog Start", "Start sinister-watchdog"),
        ("auto.watchdog_tail", "Watchdog Tail", "Tail watchdog log"),
        ("auto.backup_now", "Backup Now", "Run sanctum-backup immediately"),
        ("auto.push_now", "Auto-Push Now", "Trigger sanctum-git auto-push"),
    ]),
    ("MAINTAIN", [
        ("maint.brain_index", "Brain Index", "Rebuild knowledge index"),
        ("maint.sanctum_backup", "Sanctum Backup", "Open backups directory"),
        ("maint.vault_status", "Vault Status", "Probe sinister-vault :5078"),
        ("maint.mcp_probe", "MCP Probe", "Probe MCP servers (~/.claude/.mcp.json)"),
    ]),
]


class Ribbon(QWidget):
    """Horizontal Excel-ribbon strip."""

    action_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Ribbon")
        self.setFixedHeight(RIBBON_HEIGHT)
        self._build()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(10)

        for label, items in GROUPS:
            group_widget = QFrame(self)
            group_widget.setObjectName("RibbonGroup")
            group_layout = QVBoxLayout(group_widget)
            group_layout.setContentsMargins(6, 4, 6, 4)
            group_layout.setSpacing(2)

            # Buttons grid (2 cols)
            grid = QGridLayout()
            grid.setSpacing(2)
            grid.setContentsMargins(0, 0, 0, 0)
            for i, (key, btn_label, tooltip) in enumerate(items):
                btn = QPushButton(btn_label)
                btn.setObjectName("RibbonBtn")
                btn.setToolTip(tooltip)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _checked=False, k=key: self.action_clicked.emit(k))
                row, col = divmod(i, 2)
                grid.addWidget(btn, row, col)
            group_layout.addLayout(grid)

            # Group label centered at bottom
            group_label = QLabel(label)
            group_label.setObjectName("RibbonGroupLabel")
            group_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            group_layout.addWidget(group_label)

            root.addWidget(group_widget)

        root.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
