# Author: RKOJ-ELENO :: 2026-05-21
"""Devices tab — operator-canonical 2026-05-21 placeholder.

Operator brief (verbatim 2026-05-21): "have devices blank for now just agents
tab". This view renders a centered "Devices — coming soon" hero. Real device
wiring (adb / scrcpy / RKA) lands in a follow-up milestone.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DevicesView(QWidget):
    """Centered placeholder hero."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(8)
        root.addStretch(1)

        hero = QLabel("Devices — coming soon")
        hero.setObjectName("PlaceholderHero")
        hero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(hero)

        sub = QLabel("ADB / scrcpy / RKA wiring lands in milestone 2.")
        sub.setObjectName("PlaceholderSub")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(sub)

        root.addStretch(2)


# Backward-compat alias — older modules import PhonesTab.
PhonesTab = DevicesView
