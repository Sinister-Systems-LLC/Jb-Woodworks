# Author: RKOJ-ELENO :: 2026-05-21
"""4 KPI tiles strip — PHONES ONLINE / AGENTS ONLINE / VAULT USED / PENDING REQUESTS."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from . import state
from .theme import KPI_HEIGHT


class KpiTile(QWidget):
    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("KpiTile")
        self.setMinimumHeight(KPI_HEIGHT)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.lbl = QLabel(label.upper())
        self.lbl.setObjectName("KpiLabel")
        self.val = QLabel("—")
        self.val.setObjectName("KpiValue")
        self.sub = QLabel("")
        self.sub.setObjectName("KpiSub")
        layout.addWidget(self.lbl)
        layout.addWidget(self.val)
        layout.addWidget(self.sub)

    def set_value(self, value: str, sub: str = "") -> None:
        self.val.setText(value)
        self.sub.setText(sub)


class KpiStrip(QWidget):
    """Horizontal 4-tile strip with 5s live refresh."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("KpiStrip")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        self.phones_tile = KpiTile("Phones Online")
        self.agents_tile = KpiTile("Agents Online")
        self.vault_tile = KpiTile("Vault Used")
        self.pending_tile = KpiTile("Pending Requests")
        for tile in (self.phones_tile, self.agents_tile, self.vault_tile, self.pending_tile):
            layout.addWidget(tile, stretch=1)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(5000)
        self._refresh()

    def _refresh(self) -> None:
        try:
            snap = state.snapshot()
            self.phones_tile.set_value(str(snap.phones_online), f"{snap.phones_offline} offline · {snap.phones_needs_auth} auth")
            self.agents_tile.set_value(str(snap.agents_online), f"of {snap.agents_total} total")
            self.vault_tile.set_value(f"{snap.vault_used_pct:.1f}%", "D:/sinister-vault")
            self.pending_tile.set_value(str(snap.pending_requests), "inbox/sanctum")
        except Exception:
            for tile in (self.phones_tile, self.agents_tile, self.vault_tile, self.pending_tile):
                tile.set_value("?", "")
