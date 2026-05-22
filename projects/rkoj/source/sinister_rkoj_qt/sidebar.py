# Author: RKOJ-ELENO :: 2026-05-21
"""240px left sidebar (Panel SidebarCard) — 1:1 port of Sinister Panel's
`components/sidebar.tsx`.

Layout (top→bottom):
  - 2px purple gradient spine on the LEFT edge (Panel brand marker, full-height).
  - Banner block (96px tall, matches HEADER_HEIGHT so bottom-borders line up).
    Renders `assets/mascot.svg` centered. Future: swap to a wide banner.png.
  - Nav (px-3 py-4) with one section per logical group:
      WORKSPACE
        ▸ Agents      (default active)
      OPERATIONS
        ▸ Devices

Section style (Panel):
  `px-3 mb-2 pb-2 text-[12px] font-semibold text-[#8e8e93] uppercase
   tracking-[.12em] border-b border-[#1c1c1e]`

Nav-item style (Panel):
  `flex items-center gap-3 rounded-[10px] px-3 py-2.5 text-[14px]`
  inactive  → `text-[#8e8e93]` + hover `text-white bg-white/[0.05]`
  active    → `text-[#BF5AF2] font-semibold` + gradient bg
              `linear-gradient(180deg, rgba(191,90,242,0.22),
                                       rgba(191,90,242,0.08))`

EVE/profile block at the bottom is intentionally omitted — RKOJ has no
multi-user auth yet. We'll add it when ProfileBlock equivalents exist.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget  # type: ignore
    _HAS_SVG = True
except Exception:  # pragma: no cover
    _HAS_SVG = False

from .theme import (
    HEADER_HEIGHT, LEFT_SPINE_WIDTH, SIDEBAR_WIDTH, asset_path, nav_icon,
)


# Panel-style sections. Each section = (label, [(key, label, svg-icon-name)]).
SECTIONS: list[tuple[str, list[tuple[str, str, str]]]] = [
    ("WORKSPACE", [
        ("agents",   "Agents",   "nav-eve-ai"),
        ("sessions", "Sessions", "nav-database"),
    ]),
    ("OPERATIONS", [
        ("devices",  "Devices",  "nav-phones"),
    ]),
]


_MASCOT_SVG = asset_path("mascot.svg")
_BANNER_PNG = asset_path("banner.png")   # optional — falls back to mascot SVG


class _NavRow(QPushButton):
    """Single sidebar nav row — SVG icon (left) + label.

    The whole row is a QPushButton with `active` property toggled to swap
    QSS. We don't use `setText` directly — a QLabel inside owns the rendered
    label so the SVG icon can sit next to it cleanly.
    """

    def __init__(self, key: str, label: str, icon_name: str,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("NavItem")
        self.setProperty("active", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._key = key
        self._build(label, icon_name)

    def _build(self, label: str, icon_name: str) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)
        if _HAS_SVG:
            row.addWidget(nav_icon(icon_name, size=18))
        self._label_widget = QLabel(label)
        self._label_widget.setStyleSheet(
            "color: inherit; background: transparent; "
            "font-size: 14px; font-weight: 500;"
        )
        row.addWidget(self._label_widget, stretch=1)
        # v1.6.22 — optional count badge (hidden by default). Set via
        # set_badge(text) to show e.g. "5" next to "Sessions".
        self._badge = QLabel("")
        self._badge.setVisible(False)
        self._badge.setStyleSheet(
            "color: white; background-color: rgba(191,90,242,180); "
            "border-radius: 9px; padding: 1px 7px; "
            "font-size: 10px; font-weight: 700; "
            "min-width: 14px; "
        )
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self._badge)
        self.setText("")

    def set_badge(self, text: str | None) -> None:
        """Show/hide the small count pill at the right of the nav row.
        Pass None or empty string to hide."""
        if not text:
            self._badge.setVisible(False)
            self._badge.setText("")
        else:
            self._badge.setText(str(text))
            self._badge.setVisible(True)

    @property
    def nav_key(self) -> str:
        return self._key


class Sidebar(QWidget):
    """Left vertical sidebar — Panel-1:1 chrome with 2 nav items."""

    nav_clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # objectName matches the rounded-card QSS rule (`QWidget#SidebarCard`)
        # so the Sidebar itself IS the card (no wrapper needed).
        self.setObjectName("SidebarCard")
        self.setFixedWidth(SIDEBAR_WIDTH)
        self._active_nav: str = "agents"
        self._nav_rows: dict[str, _NavRow] = {}
        self._build()
        self._update_active(self._active_nav)
        # v1.6.22 — refresh Sessions count badge every 30s + at startup
        from PyQt6.QtCore import QTimer
        self._badge_timer = QTimer(self)
        self._badge_timer.setInterval(30_000)
        self._badge_timer.timeout.connect(self.refresh_sessions_badge)
        self._badge_timer.start()
        self.refresh_sessions_badge()

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left-edge accent spine (2px, full-height, purple gradient) ──
        spine = QFrame(self)
        spine.setObjectName("LeftSpine")
        spine.setFixedWidth(LEFT_SPINE_WIDTH)
        spine.setSizePolicy(QSizePolicy.Policy.Fixed,
                            QSizePolicy.Policy.Expanding)
        root.addWidget(spine)

        # ── Main column (banner + nav + footer slot) ───────────────────
        col = QFrame(self)
        col.setObjectName("SidebarInner")
        col_layout = QVBoxLayout(col)
        col_layout.setContentsMargins(0, 0, 0, 0)
        col_layout.setSpacing(0)

        # Banner block — 96px tall (HEADER_HEIGHT match).
        banner = QFrame(col)
        banner.setObjectName("BannerFrame")
        banner.setFixedHeight(HEADER_HEIGHT)
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(0, 0, 0, 0)
        banner_layout.setSpacing(0)
        banner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Prefer banner.png if shipped; else center the mascot SVG.
        if _HAS_SVG and _BANNER_PNG.exists():
            # banner.png landed — render as full-width via QLabel + QPixmap
            # (kept inside QSvgWidget-aware code path for symmetry).
            from PyQt6.QtGui import QPixmap
            from PyQt6.QtCore import QSize
            pm = QPixmap(str(_BANNER_PNG))
            if not pm.isNull():
                lbl = QLabel(banner)
                lbl.setPixmap(pm.scaled(
                    QSize(SIDEBAR_WIDTH - LEFT_SPINE_WIDTH, HEADER_HEIGHT),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                ))
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet("background: transparent;")
                banner_layout.addWidget(lbl)
        elif _HAS_SVG and _MASCOT_SVG.exists():
            svg = QSvgWidget(str(_MASCOT_SVG))
            svg.setFixedSize(64, 64)
            banner_layout.addWidget(svg, alignment=Qt.AlignmentFlag.AlignCenter)

        col_layout.addWidget(banner)

        # ── Nav: sections + items ──────────────────────────────────────
        nav_host = QFrame(col)
        nav_layout = QVBoxLayout(nav_host)
        nav_layout.setContentsMargins(8, 14, 8, 14)
        nav_layout.setSpacing(4)

        for si, (section_label, items) in enumerate(SECTIONS):
            if si > 0:
                # 20px gap between sections (Panel `mt-5`)
                gap = QSpacerItem(0, 20, QSizePolicy.Policy.Minimum,
                                  QSizePolicy.Policy.Fixed)
                nav_layout.addSpacerItem(gap)

            section_lbl = QLabel(section_label)
            section_lbl.setObjectName("SidebarSection")
            nav_layout.addWidget(section_lbl)

            for key, label, icon_name in items:
                row = _NavRow(key, label, icon_name)
                row.clicked.connect(
                    lambda _checked=False, k=key: self._on_nav_clicked(k)
                )
                self._nav_rows[key] = row
                nav_layout.addWidget(row)

        nav_layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum,
                        QSizePolicy.Policy.Expanding)
        )
        col_layout.addWidget(nav_host, stretch=1)

        root.addWidget(col, stretch=1)

    def _on_nav_clicked(self, key: str) -> None:
        self._update_active(key)
        self.nav_clicked.emit(key)

    def _update_active(self, key: str) -> None:
        self._active_nav = key
        for k, row in self._nav_rows.items():
            is_active = (k == key)
            row.setProperty("active", is_active)
            row.style().unpolish(row)
            row.style().polish(row)

    # v1.6.23 — external setter for the Agents nav row badge. Called from
    # app.py when AgentsView's card count changes (spawn / close).
    def set_agents_count(self, n: int) -> None:
        agents_row = self._nav_rows.get("agents")
        if agents_row is None:
            return
        agents_row.set_badge(str(n) if n > 0 else None)

    # v1.6.22 — count saved sessions on disk and update the Sessions
    # nav row's badge. Skips entries without a session_uuid (pre-v1.6.3).
    def refresh_sessions_badge(self) -> None:
        sessions_row = self._nav_rows.get("sessions")
        if sessions_row is None:
            return
        try:
            import json
            from pathlib import Path
            from . import state
            rp_root = state.SHARED_MEMORY / "resume-points"
            if not rp_root.exists():
                sessions_row.set_badge(None)
                return
            uuids: set[str] = set()
            for proj_dir in rp_root.iterdir():
                if not proj_dir.is_dir():
                    continue
                for fp in proj_dir.glob("*.json"):
                    try:
                        with open(fp, "r", encoding="utf-8") as fh:
                            d = json.load(fh)
                        suid = d.get("session_uuid") or ""
                        if suid:
                            uuids.add(suid)
                    except Exception:
                        continue
            n = len(uuids)
            sessions_row.set_badge(str(n) if n > 0 else None)
        except Exception:
            sessions_row.set_badge(None)
